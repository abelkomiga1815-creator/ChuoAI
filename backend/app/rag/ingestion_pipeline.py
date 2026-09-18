# backend/app/rag/ingestion_pipeline.py
"""Automated ingestion pipeline for scheduled source updates."""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import uuid
import hashlib
import logging

from ..core.config import settings
from ..models.document import Document
from ..models.university import University, UniversityAlias
from ..models.programme import Programme, ProgrammeAlias
from ..models.academic_year import AcademicYear, FeeStructure, SubjectRequirement, IngestionJob, TCUStatistic, TCUStatisticType
from ..models.source import Source, SourceType, SourceAuthority
from ..models.admission import AdmissionRequirement, QualificationType
from .chunking import ChunkingService, Chunk
from .embedding import EmbeddingService
from .crawler import TCUCrawler, UniversityCrawler, PDFDownloader
from ..utils.logger import logger


class IngestionPipeline:
    """Main ingestion pipeline for automated source updates."""
    
    def __init__(self, db: Session):
        self.db = db
        self.chunking_service = ChunkingService(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.embedding_service = EmbeddingService(db)
    
    async def run_tcu_crawl(self, job: IngestionJob) -> Dict[str, Any]:
        """Run TCU website crawl and ingestion."""
        job.status = "RUNNING"
        job.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            results = {
                "documents_found": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "documents_failed": 0,
                "universities_found": 0,
                "programmes_found": 0,
            }
            
            async with TCUCrawler(job, self.db) as crawler:
                crawl_results = await crawler.crawl(max_pages=50)
            
            job.documents_found = len(crawl_results)
            results["documents_found"] = len(crawl_results)
            
            for crawl_result in crawl_results:
                try:
                    doc_result = await self._ingest_crawl_result(crawl_result)
                    if doc_result == "new":
                        results["documents_new"] += 1
                    elif doc_result == "updated":
                        results["documents_updated"] += 1
                except Exception as e:
                    logger.error(f"Failed to ingest crawl result {crawl_result.url}: {e}")
                    results["documents_failed"] += 1
            
            # Update job
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
            job.documents_new = results["documents_new"]
            job.documents_updated = results["documents_updated"]
            job.documents_failed = results["documents_failed"]
            self.db.commit()
            
            return results
            
        except Exception as e:
            job.status = "FAILED"
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            self.db.commit()
            raise
    
    async def run_university_crawl(self, job: IngestionJob, university_id: str) -> Dict[str, Any]:
        """Run crawl for a specific university."""
        university = self.db.query(University).filter(University.id == university_id).first()
        if not university or not university.website:
            raise ValueError(f"University {university_id} not found or has no website")
        
        job.target_university_id = university_id
        job.status = "RUNNING"
        job.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            results = {"documents_found": 0, "documents_new": 0, "documents_updated": 0, "documents_failed": 0}
            
            async with UniversityCrawler(job, self.db, university.website) as crawler:
                crawl_results = await crawler.crawl(max_pages=100)
            
            job.documents_found = len(crawl_results)
            results["documents_found"] = len(crawl_results)
            
            for crawl_result in crawl_results:
                try:
                    doc_result = await self._ingest_crawl_result(crawl_result, university_id)
                    if doc_result == "new":
                        results["documents_new"] += 1
                    elif doc_result == "updated":
                        results["documents_updated"] += 1
                except Exception as e:
                    logger.error(f"Failed to ingest crawl result {crawl_result.url}: {e}")
                    results["documents_failed"] += 1
            
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
            job.documents_new = results["documents_new"]
            job.documents_updated = results["documents_updated"]
            job.documents_failed = results["documents_failed"]
            self.db.commit()
            
            return results
            
        except Exception as e:
            job.status = "FAILED"
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            self.db.commit()
            raise
    
    async def _ingest_crawl_result(self, crawl_result, university_id: Optional[str] = None) -> str:
        """Ingest a single crawl result, return 'new', 'updated', or 'unchanged'."""
        # Check if document already exists by URL
        existing_doc = self.db.query(Document).filter(
            Document.source_url == crawl_result.url
        ).first()
        
        if existing_doc:
            # Check if content changed
            if existing_doc.content_hash == crawl_result.content_hash:
                return "unchanged"
            
            # Content changed - update
            return await self._update_document(existing_doc, crawl_result, university_id)
        
        # New document
        return await self._create_document(crawl_result, university_id)
    
    async def _create_document(self, crawl_result, university_id: Optional[str] = None) -> str:
        """Create new document from crawl result."""
        # Try to find university from URL or metadata
        if not university_id:
            university_id = crawl_result.metadata.get("university_id")
        
        # Try to find academic year
        academic_year = crawl_result.metadata.get("academic_year")
        academic_year_id = None
        if academic_year:
            ay = self.db.query(AcademicYear).filter(
                AcademicYear.year_label == academic_year
            ).first()
            if ay:
                academic_year_id = ay.id
        
        # Determine source type
        source_type = crawl_result.metadata.get("source_type", "OTHER")
        authority_level = crawl_result.metadata.get("authority_level", "LEVEL_5")
        
        # Create document
        doc = Document(
            id=str(uuid.uuid4()),
            title=crawl_result.title or crawl_result.url,
            document_type="WEB_PAGE",
            university_id=university_id,
            academic_year=academic_year,
            academic_year_id=academic_year_id,
            source_url=crawl_result.url,
            source_type=source_type,
            content_hash=crawl_result.content_hash,
            is_indexed=False,
            verification_status="PENDING",
            embedding_model=settings.EMBEDDING_MODEL,
            extra_metadata=str(crawl_result.metadata),
        )
        
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        # Ingest content
        await self._ingest_document_content(doc, crawl_result.content, crawl_result.metadata)
        
        # Extract and save TCU statistics if present
        if crawl_result.metadata.get("tcu_statistics"):
            await self._save_tcu_statistics(crawl_result.metadata["tcu_statistics"], crawl_result.url, academic_year, academic_year_id)
        
        # Create source record
        source = Source(
            id=str(uuid.uuid4()),
            title=crawl_result.title or crawl_result.url,
            source_type=SourceType(source_type) if source_type in [e.value for e in SourceType] else SourceType.OTHER,
            authority_level=SourceAuthority(authority_level) if authority_level in [e.value for e in SourceAuthority] else SourceAuthority.LEVEL_5,
            url=crawl_result.url,
            university_id=university_id,
            document_id=doc.id,
            academic_year=academic_year,
            academic_year_id=academic_year_id,
            is_verified=(authority_level in ["LEVEL_1", "LEVEL_2", "LEVEL_3"]),
            priority=1 if authority_level == "LEVEL_1" else 0,
        )
        self.db.add(source)
        self.db.commit()
        
        return "new"
    
    async def _save_tcu_statistics(self, statistics: List[Dict[str, Any]], source_url: str, academic_year: Optional[str] = None, academic_year_id: Optional[str] = None):
        """Save extracted TCU statistics to the database."""
        from ..models.academic_year import TCUStatistic, TCUStatisticType, AcademicYear
        
        for stat in statistics:
            try:
                statistic_type_str = stat.get("statistic_type")
                if not statistic_type_str:
                    continue
                
                try:
                    statistic_type = TCUStatisticType(statistic_type_str)
                except ValueError:
                    logger.warning(f"Unknown TCU statistic type: {statistic_type_str}")
                    continue
                
                metric_name = stat.get("metric_name", statistic_type.value.lower())
                value = stat.get("value")
                if value is None:
                    continue
                
                # Determine academic year
                stat_academic_year = stat.get("academic_year") or academic_year
                stat_academic_year_id = academic_year_id
                if stat_academic_year and not stat_academic_year_id:
                    ay = self.db.query(AcademicYear).filter(
                        AcademicYear.year_label == stat_academic_year
                    ).first()
                    if ay:
                        stat_academic_year_id = ay.id
                
                # Check if statistic already exists
                existing = self.db.query(TCUStatistic).filter(
                    TCUStatistic.metric_name == stat.get("metric_name", ""),
                    TCUStatistic.academic_year_label == stat.get("academic_year", "")
                ).first()
                
                if existing:
                    # Update if value changed
                    if existing.value != stat.get("value"):
                        existing.value = stat.get("value")
                        existing.last_crawled_at = datetime.utcnow()
                        existing.source_url = stat.get("source_url", "")
                        existing.content_hash = hashlib.sha256(str(stat).encode()).hexdigest()
                        existing.updated_at = datetime.utcnow()
                        logger.info(f"Updated TCU statistic: {existing.metric_name} = {existing.value}")
                else:
                    # Create new statistic
                    tcu_stat = TCUStatistic(
                        id=str(uuid.uuid4()),
                        statistic_type=statistic_type,
                        metric_name=stat.get("metric_name", statistic_type.value.lower()),
                        value=stat.get("value"),
                        unit=stat.get("unit", "count"),
                        source_url=source_url,
                        source_page_title=stat.get("source_page_title", ""),
                        source_section=stat.get("source_section", ""),
                        academic_year_id=stat_academic_year_id,
                        academic_year_label=stat.get("academic_year", ""),
                        is_verified=True,
                        verified_at=datetime.utcnow(),
                        last_crawled_at=datetime.utcnow(),
                        content_hash=hashlib.sha256(str(stat).encode()).hexdigest(),
                        metadata_json=str(stat),
                    )
                    self.db.add(tcu_stat)
                    logger.info(f"Saved new TCU statistic: {metric_name} = {value}")
            
            except Exception as e:
                logger.error(f"Failed to save TCU statistic: {e}")
        
        self.db.commit()
    
    async def _update_document(self, doc: Document, crawl_result, university_id: Optional[str] = None) -> str:
        """Update existing document with new content."""
        old_hash = doc.content_hash
        
        # Update document
        doc.content_hash = crawl_result.content_hash
        doc.updated_at = datetime.utcnow()
        doc.is_indexed = False  # Will be re-indexed
        
        # Update metadata
        import json
        try:
            metadata = json.loads(doc.extra_metadata) if doc.extra_metadata else {}
        except:
            metadata = {}
        metadata.update(crawl_result.metadata)
        doc.extra_metadata = str(metadata)
        
        self.db.commit()
        
        # Re-ingest content
        await self._ingest_document_content(doc, crawl_result.content, crawl_result.metadata)
        
        # Update source
        source = self.db.query(Source).filter(Source.document_id == doc.id).first()
        if source:
            source.content_hash = crawl_result.content_hash
            source.last_crawled_at = datetime.utcnow()
            self.db.commit()
        
        return "updated"
    
    async def _ingest_document_content(self, doc: Document, text: str, metadata: Dict[str, Any]):
        """Chunk, embed, and store document content."""
        # Prepare metadata for chunks
        doc_metadata = {
            "title": doc.title,
            "source_type": doc.source_type,
            "university_id": doc.university_id,
            "academic_year": doc.academic_year,
            "academic_year_id": doc.academic_year_id,
            "url": doc.source_url,
            **metadata
        }
        
        # Chunk the document
        chunks = self.chunking_service.chunk_text(text, doc_metadata)
        
        if not chunks:
            return
        
        # Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await self.embedding_service.generate_embeddings(chunk_texts)
        
        # Remove old chunks
        from sqlalchemy import text
        self.db.execute(text("DELETE FROM document_chunks WHERE document_id = :doc_id"), {"doc_id": doc.id})
        
        # Store new chunks
        chunk_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_metadata = {
                **chunk.metadata,
                "chunk_index": chunk.index,
                "total_chunks": len(chunks)
            }
            
            chunk_id = self.embedding_service.store_embedding(
                document_id=doc.id,
                chunk_index=i,
                chunk_text=chunk.text,
                embedding=embedding,
                metadata=chunk_metadata
            )
            chunk_ids.append(chunk_id)
        
        # Update document
        doc.is_indexed = True
        doc.chunk_count = len(chunks)
        doc.embedding_model = settings.EMBEDDING_MODEL
        doc.embedding_model_version = "v1"
        self.db.commit()
    
    async def download_and_ingest_pdfs(self, job: IngestionJob, pdf_urls: List[str]) -> Dict[str, Any]:
        """Download and ingest PDF documents."""
        job.status = "RUNNING"
        job.started_at = datetime.utcnow()
        self.db.commit()
        
        results = {"pdfs_found": 0, "pdfs_new": 0, "pdfs_updated": 0, "pdfs_failed": 0}
        
        try:
            async with PDFDownloader(self.db) as downloader:
                for url in pdf_urls:
                    results["pdfs_found"] += 1
                    try:
                        pdf_result = await downloader.download_pdf(url)
                        if pdf_result:
                            # Create a fake crawl result for ingestion
                            class FakeCrawlResult:
                                def __init__(self, data):
                                    self.url = data["metadata"]["source_url"]
                                    self.title = f"PDF: {url.split('/')[-1]}"
                                    self.content = data["content"]
                                    self.content_hash = data["content_hash"]
                                    self.metadata = data["metadata"]
                            
                            fake_result = FakeCrawlResult(pdf_result)
                            await self._ingest_crawl_result(fake_result)
                            results["pdfs_new"] += 1
                    except Exception as e:
                        logger.error(f"Failed to process PDF {url}: {e}")
                        results["pdfs_failed"] += 1
            
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
            job.documents_new = results["pdfs_new"]
            job.documents_failed = results["pdfs_failed"]
            self.db.commit()
            
            return results
            
        except Exception as e:
            job.status = "FAILED"
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            self.db.commit()
            raise
    
    async def create_academic_years(self) -> List[AcademicYear]:
        """Create standard academic years."""
        years = []
        current_year = datetime.now().year
        
        # Create years from 2020 to current+2
        for start in range(2020, current_year + 3):
            end = start + 1
            year_label = f"{start}/{end}"
            
            ay = self.db.query(AcademicYear).filter(
                AcademicYear.year_label == year_label
            ).first()
            
            if not ay:
                is_current = (year_label == self._get_current_academic_year())
                ay = AcademicYear(
                    id=str(uuid.uuid4()),
                    year_label=year_label,
                    start_year=start,
                    end_year=end,
                    is_current=is_current,
                    is_active=True,
                    description=f"Academic year {year_label}"
                )
                self.db.add(ay)
            years.append(ay)
        
        self.db.commit()
        return years
    
    def _get_current_academic_year(self) -> str:
        current_year = datetime.now().year
        if datetime.now().month >= 9:
            return f"{current_year}/{current_year + 1}"
        else:
            return f"{current_year - 1}/{current_year}"
    
    async def create_scheduled_jobs(self):
        """Create default scheduled ingestion jobs."""
        # TCU weekly crawl
        tcu_job = self.db.query(IngestionJob).filter(
            IngestionJob.job_type == "TCU_CRAWL",
            IngestionJob.is_scheduled == True
        ).first()
        
        if not tcu_job:
            tcu_job = IngestionJob(
                id=str(uuid.uuid4()),
                job_type="TCU_CRAWL",
                source_url="https://www.tcu.go.tz/",
                status="PENDING",
                is_scheduled=True,
                schedule_cron="0 2 * * 0",  # Weekly on Sunday at 2 AM
                next_run_at=self._calculate_next_run("0 2 * * 0")
            )
            self.db.add(tcu_job)
        
        # University monthly crawls
        universities = self.db.query(University).filter(
            University.is_active == True,
            University.website.isnot(None)
        ).all()
        
        for uni in universities:
            job = self.db.query(IngestionJob).filter(
                IngestionJob.job_type == "UNIVERSITY_CRAWL",
                IngestionJob.target_university_id == uni.id,
                IngestionJob.is_scheduled == True
            ).first()
            
            if not job:
                job = IngestionJob(
                    id=str(uuid.uuid4()),
                    job_type="UNIVERSITY_CRAWL",
                    source_url=uni.website,
                    target_university_id=uni.id,
                    status="PENDING",
                    is_scheduled=True,
                    schedule_cron="0 3 1 * *",  # Monthly on 1st at 3 AM
                    next_run_at=self._calculate_next_run("0 3 1 * *")
                )
                self.db.add(job)
        
        self.db.commit()
    
    def _calculate_next_run(self, cron_expr: str) -> datetime:
        """Calculate next run time from cron expression (simplified)."""
        # Simplified - just return next day for daily, next week for weekly, etc.
        if "0 2 * * 0" in cron_expr:  # Weekly
            return datetime.utcnow().replace(hour=2, minute=0, second=0, microsecond=0)
        elif "0 3 1 * *" in cron_expr:  # Monthly
            return datetime.utcnow().replace(day=1, hour=3, minute=0, second=0, microsecond=0)
        return datetime.utcnow()


class VerificationService:
    """Service for verifying universities and programmes against official sources."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def verify_university(self, university_id: str) -> Dict[str, Any]:
        """Verify a university against TCU sources."""
        university = self.db.query(University).filter(University.id == university_id).first()
        if not university:
            return {"verified": False, "error": "University not found"}
        
        # Search for TCU sources mentioning this university
        from ..rag.retrieval import RetrievalService, RetrievalFilters
        from ..models.source import SourceType, SourceAuthority
        
        retrieval = RetrievalService(self.db)
        results = await retrieval.retrieve_for_verification(
            university_name=university.name,
            top_k=20
        )
        
        # Check if TCU sources confirm this university
        tcu_sources = [r for r in results if r.get("metadata", {}).get("authority_level") == "LEVEL_1"]
        uni_sources = [r for r in results if r.get("metadata", {}).get("authority_level") in ["LEVEL_1", "LEVEL_2"]]
        
        is_verified = len(tcu_sources) > 0 or (len(uni_sources) >= 2)
        
        # Update university
        university.tcu_accredited = is_verified
        university.tcu_status = "VERIFIED" if is_verified else "UNVERIFIED"
        university.tcu_last_verified_at = datetime.utcnow()
        university.last_verified_at = datetime.utcnow()
        
        if tcu_sources:
            university.tcu_source_url = tcu_sources[0].get("metadata", {}).get("url")
        
        self.db.commit()
        
        return {
            "verified": is_verified,
            "tcu_sources_found": len(tcu_sources),
            "total_sources_found": len(results),
            "verification_date": datetime.utcnow().isoformat()
        }
    
    async def verify_programme(self, programme_id: str) -> Dict[str, Any]:
        """Verify a programme against official sources."""
        programme = self.db.query(Programme).filter(Programme.id == programme_id).first()
        if not programme:
            return {"verified": False, "error": "Programme not found"}
        
        university = self.db.query(University).filter(University.id == programme.university_id).first()
        
        # Search for official sources mentioning this programme at this university
        from ..rag.retrieval import RetrievalService
        from ..models.source import SourceType, SourceAuthority
        
        retrieval = RetrievalService(self.db)
        results = await retrieval.retrieve_for_verification(
            university_name=university.name if university else None,
            programme_name=programme.name,
            top_k=20
        )
        
        # Filter for highly authoritative sources
        official_sources = [
            r for r in results 
            if r.get("metadata", {}).get("authority_level") in ["LEVEL_1", "LEVEL_2", "LEVEL_3"]
        ]
        
        # Check if programme-university pair is confirmed
        is_verified = len(official_sources) >= 1
        
        programme.tcu_accredited = is_verified
        programme.tcu_status = "VERIFIED" if is_verified else "UNVERIFIED"
        programme.tcu_last_verified_at = datetime.utcnow()
        programme.last_verified_at = datetime.utcnow()
        
        if official_sources:
            programme.tcu_source_url = official_sources[0].get("metadata", {}).get("url")
        
        self.db.commit()
        
        return {
            "verified": is_verified,
            "official_sources_found": len(official_sources),
            "total_sources_found": len(results),
            "verification_date": datetime.utcnow().isoformat()
        }
    
    async def verify_all(self) -> Dict[str, Any]:
        """Verify all universities and programmes."""
        results = {"universities": [], "programmes": []}
        
        universities = self.db.query(University).filter(University.is_active == True).all()
        for uni in universities:
            result = await self.verify_university(uni.id)
            results["universities"].append({"id": uni.id, "name": uni.name, **result})
        
        programmes = self.db.query(Programme).filter(Programme.is_active == True).all()
        for prog in programmes:
            result = await self.verify_programme(prog.id)
            results["programmes"].append({"id": prog.id, "name": prog.name, **result})
        
        return results