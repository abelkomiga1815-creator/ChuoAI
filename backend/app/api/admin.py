# backend/app/api/admin.py
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from ..core.database import get_db
from ..auth.dependencies import require_admin
from ..services.university_service import UniversityService
from ..services.programme_service import ProgrammeService
from ..services.document_service import DocumentService
from ..rag.ingestion import DocumentIngestionService
from ..rag.ingestion_pipeline import IngestionPipeline, VerificationService
from ..schemas.university import UniversityCreate, UniversityUpdate
from ..schemas.programmes import ProgrammeCreate, ProgrammeUpdate
from ..models.academic_year import IngestionJob, AcademicYear, FeeStructure

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
    """Upload a document (PDF/DOCX/TXT/CSV) and index it into the RAG store."""
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


# === New Verification Endpoints ===

@admin_router.post("/verify/university/{university_id}")
async def verify_university(
    university_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Verify a university against official TCU sources."""
    verification = VerificationService(db)
    result = await verification.verify_university(university_id)
    return result


@admin_router.post("/verify/programme/{programme_id}")
async def verify_programme(
    programme_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Verify a programme against official sources."""
    verification = VerificationService(db)
    result = await verification.verify_programme(programme_id)
    return result


@admin_router.post("/verify/all")
async def verify_all(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Verify all universities and programmes."""
    verification = VerificationService(db)
    result = await verification.verify_all()
    return result


# === Ingestion Pipeline Endpoints ===

@admin_router.post("/ingest/tcu-crawl")
async def run_tcu_crawl(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Trigger TCU website crawl and ingestion."""
    pipeline = IngestionPipeline(db)
    
    # Create job record
    job = IngestionJob(
        id=str(uuid.uuid4()),
        job_type="TCU_CRAWL",
        source_url="https://www.tcu.go.tz/",
        status="PENDING",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Run in background
    async def run_crawl():
        await pipeline.run_tcu_crawl(job)
    
    background_tasks.add_task(run_crawl)
    
    return {"job_id": job.id, "status": "started", "message": "TCU crawl started in background"}


@admin_router.post("/ingest/university-crawl/{university_id}")
async def run_university_crawl(
    university_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Trigger crawl for a specific university."""
    pipeline = IngestionPipeline(db)
    
    job = IngestionJob(
        id=str(uuid.uuid4()),
        job_type="UNIVERSITY_CRAWL",
        target_university_id=university_id,
        status="PENDING",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    async def run_crawl():
        await pipeline.run_university_crawl(job, university_id)
    
    background_tasks.add_task(run_crawl)
    
    return {"job_id": job.id, "status": "started", "message": f"University crawl started in background"}


@admin_router.post("/ingest/pdf-download")
async def download_pdfs(
    urls: List[str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Download and ingest PDF documents."""
    pipeline = IngestionPipeline(db)
    
    job = IngestionJob(
        id=str(uuid.uuid4()),
        job_type="PDF_DOWNLOAD",
        status="PENDING",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    async def run_download():
        await pipeline.download_and_ingest_pdfs(job, urls)
    
    background_tasks.add_task(run_download)
    
    return {"job_id": job.id, "status": "started", "message": f"PDF download started for {len(urls)} URLs"}


@admin_router.get("/ingest/jobs")
async def list_ingestion_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """List ingestion jobs."""
    query = db.query(IngestionJob)
    if status_filter:
        query = query.filter(IngestionJob.status == status_filter)
    return query.order_by(IngestionJob.created_at.desc()).offset(skip).limit(limit).all()


@admin_router.get("/ingest/jobs/{job_id}")
async def get_ingestion_job(
    job_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Get ingestion job details."""
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# === Academic Year Endpoints ===

@admin_router.post("/academic-years", status_code=status.HTTP_201_CREATED)
async def create_academic_year(
    year_label: str = Form(...),
    start_year: int = Form(...),
    end_year: int = Form(...),
    is_current: bool = Form(False),
    description: str = Form(""),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Create an academic year."""
    if is_current:
        # Unset current flag on other years
        db.query(AcademicYear).filter(AcademicYear.is_current == True).update({"is_current": False})
    
    ay = AcademicYear(
        id=str(uuid.uuid4()),
        year_label=year_label,
        start_year=start_year,
        end_year=end_year,
        is_current=is_current,
        is_active=True,
        description=description,
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay


@admin_router.get("/academic-years")
async def list_academic_years(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """List all academic years."""
    return db.query(AcademicYear).order_by(AcademicYear.start_year.desc()).all()


@admin_router.put("/academic-years/{ay_id}/set-current")
async def set_current_academic_year(
    ay_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Set an academic year as current."""
    ay = db.query(AcademicYear).filter(AcademicYear.id == ay_id).first()
    if not ay:
        raise HTTPException(status_code=404, detail="Academic year not found")
    
    db.query(AcademicYear).filter(AcademicYear.is_current == True).update({"is_current": False})
    ay.is_current = True
    db.commit()
    return {"message": "Current academic year updated", "year": ay.year_label}


@admin_router.post("/academic-years/initialize")
async def initialize_academic_years(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Initialize standard academic years (2020-present+2)."""
    pipeline = IngestionPipeline(db)
    years = await pipeline.create_academic_years()
    return {"created": len(years), "years": [ay.year_label for ay in years]}


# === Fee Structure Endpoints ===

@admin_router.post("/fee-structures", status_code=status.HTTP_201_CREATED)
async def create_fee_structure(
    programme_id: str = Form(...),
    academic_year_id: str = Form(...),
    tuition_fee_tzs: int = Form(...),
    registration_fee_tzs: Optional[int] = Form(0),
    examination_fee_tzs: Optional[int] = Form(0),
    library_fee_tzs: Optional[int] = Form(0),
    medical_fee_tzs: Optional[int] = Form(0),
    student_union_fee_tzs: Optional[int] = Form(0),
    other_fees_tzs: Optional[int] = Form(0),
    other_fees_description: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    is_verified: bool = Form(False),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Create a fee structure for a programme."""
    total = (tuition_fee_tzs or 0) + (registration_fee_tzs or 0) + (examination_fee_tzs or 0) + \
            (library_fee_tzs or 0) + (medical_fee_tzs or 0) + (student_union_fee_tzs or 0) + (other_fees_tzs or 0)
    
    fs = FeeStructure(
        id=str(uuid.uuid4()),
        programme_id=programme_id,
        academic_year_id=academic_year_id,
        tuition_fee_tzs=tuition_fee_tzs,
        registration_fee_tzs=registration_fee_tzs,
        examination_fee_tzs=examination_fee_tzs,
        library_fee_tzs=library_fee_tzs,
        medical_fee_tzs=medical_fee_tzs,
        student_union_fee_tzs=student_union_fee_tzs,
        other_fees_tzs=other_fees_tzs,
        other_fees_description=other_fees_description,
        total_estimated_tzs=total,
        source_url=source_url,
        is_verified=is_verified,
        verified_at=datetime.utcnow() if is_verified else None,
    )
    db.add(fs)
    db.commit()
    db.refresh(fs)
    return fs


@admin_router.get("/fee-structures")
async def list_fee_structures(
    programme_id: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """List fee structures."""
    query = db.query(FeeStructure)
    if programme_id:
        query = query.filter(FeeStructure.programme_id == programme_id)
    if academic_year_id:
        query = query.filter(FeeStructure.academic_year_id == academic_year_id)
    return query.all()