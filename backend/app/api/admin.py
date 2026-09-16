# backend/app/api/admin.py
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..auth.dependencies import require_admin
from ..services.university_service import UniversityService
from ..services.programme_service import ProgrammeService
from ..services.document_service import DocumentService
from ..rag.ingestion import DocumentIngestionService
from ..schemas.university import UniversityCreate, UniversityUpdate
from ..schemas.programmes import ProgrammeCreate, ProgrammeUpdate

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

admin_router = APIRouter()


@admin_router.get("/dashboard")
async def dashboard(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Admin dashboard statistics."""
    return {
        "universities": db.query(__import__("app.models", fromlist=["University"]).University).count(),
        "programmes": db.query(__import__("app.models", fromlist=["Programme"]).Programme).count(),
        "users": db.query(__import__("app.models", fromlist=["User"]).User).count(),
    }


@admin_router.post("/universities", status_code=status.HTTP_201_CREATED)
async def create_university(
    data: UniversityCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    service = UniversityService(db)
    return await service.create_university(data)


@admin_router.put("/universities/{university_id}")
async def update_university(
    university_id: str,
    data: UniversityUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    service = UniversityService(db)
    result = await service.update_university(university_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="University not found")
    return result


@admin_router.delete("/universities/{university_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_university(
    university_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    service = UniversityService(db)
    if not await service.delete_university(university_id):
        raise HTTPException(status_code=404, detail="University not found")


@admin_router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form("OTHER"),
    university_id: str | None = Form(None),
    academic_year: str | None = Form(None),
    source_url: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Upload a document (PDF/DOCX/TXT/CSV) and index it into the RAG store.

    Ingestion happens immediately here so the endpoint stays simple; for large
    files this could instead just save the file and enqueue a background job
    that calls DocumentIngestionService.ingest_document.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".pdf", ".docx", ".txt", ".csv"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext or 'unknown'}",
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_name = f"{uuid.uuid4()}{ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)

    contents = await file.read()
    with open(saved_path, "wb") as f:
        f.write(contents)

    ingestion_service = DocumentIngestionService(db)
    try:
        result = await ingestion_service.ingest_file(
            file_path=saved_path,
            title=title,
            document_type=document_type,
            university_id=university_id,
            academic_year=academic_year,
            source_url=source_url,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}",
        )

    return result


@admin_router.post("/documents/{document_id}/index")
async def index_document(
    document_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Re-run ingestion for a document that already has extracted text stored."""
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=400,
            detail="Original file not found on disk; re-upload the document instead.",
        )

    ingestion_service = DocumentIngestionService(db)
    text = await ingestion_service._extract_text(document.file_path)
    try:
        result = await ingestion_service.ingest_document(document_id=document_id, text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")
    return result