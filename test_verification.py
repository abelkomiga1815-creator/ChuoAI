#!/usr/bin/env python
"""Test script for ChuoAI verification and accuracy features."""
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, '/home/abel/chuoAI/backend')

from app.core.database import SessionLocal
from app.models import (
    University, UniversityType, UniversityStatus, UniversityAlias,
    Programme, ProgrammeLevel, ProgrammeStatus, StudyMode, ProgrammeAlias,
    AcademicYear, FeeStructure, SubjectRequirement, IngestionJob,
    Source, AdmissionRequirement
)
from app.models.source import SourceType, SourceAuthority
from app.models.admission import QualificationType
from app.rag.retrieval import RetrievalService, RetrievalFilters
from app.rag.ingestion_pipeline import IngestionPipeline, VerificationService
from app.ai.router import QueryRouter
from app.models.source import SourceType as ST, SourceAuthority as SA
from datetime import datetime


def test_models():
    """Test that all models can be created and queried."""
    db = SessionLocal()
    try:
        # Test AcademicYear
        ay = db.query(AcademicYear).filter(AcademicYear.year_label == "2026/2027").first()
        if not ay:
            ay = AcademicYear(
                id="test-ay-1",
                year_label="2026/2027",
                start_year=2026,
                end_year=2027,
                is_current=True,
                is_active=True,
            )
            db.add(ay)
            db.commit()
            print(f"✓ Created AcademicYear: {ay.year_label}")
        else:
            print(f"✓ AcademicYear exists: {ay.year_label}")
        
        # Test University with verification fields
        uni = db.query(University).filter(University.name == "Test University").first()
        if not uni:
            uni = University(
                id="test-uni-1",
                name="Test University",
                abbreviation="TU",
                type=UniversityType.PUBLIC,
                website="https://test.ac.tz",
                tcu_accredited=True,
                tcu_status=UniversityStatus.VERIFIED,
                tcu_registration_number="TCU/2024/001",
                tcu_source_url="https://www.tcu.go.tz/universities/test-university",
            )
            db.add(uni)
            db.commit()
            print(f"✓ Created University: {uni.name} (TCU Status: {uni.tcu_status})")
        else:
            print(f"✓ University exists: {uni.name}")
        
        # Test UniversityAlias
        alias = db.query(UniversityAlias).filter(UniversityAlias.alias == "TU").first()
        if not alias:
            alias = UniversityAlias(
                id="test-alias-1",
                university_id=uni.id,
                alias="TU",
                is_primary=True,
            )
            db.add(alias)
            db.commit()
            print(f"✓ Created UniversityAlias: {alias.alias} for {uni.name}")
        
        # Test Programme with verification fields
        prog = db.query(Programme).filter(Programme.name == "Bachelor of Computer Science").first()
        if not prog:
            prog = Programme(
                id="test-prog-1",
                university_id=uni.id,
                name="Bachelor of Computer Science",
                code="BCS",
                level=ProgrammeLevel.BACHELOR,
                duration="3 years",
                faculty="Faculty of Science",
                study_mode=StudyMode.FULL_TIME,
                tcu_accredited=True,
                tcu_status=ProgrammeStatus.VERIFIED,
                tcu_programme_code="TCU/BCS/2024",
                tuition_fee_tzs=1500000,
                fee_currency="TZS",
                fee_year="2026/2027",
                heslb_eligible=True,
            )
            db.add(prog)
            db.commit()
            print(f"✓ Created Programme: {prog.name} (TCU Status: {prog.tcu_status})")
        else:
            print(f"✓ Programme exists: {prog.name}")
        
        # Test ProgrammeAlias
        prog_alias = db.query(ProgrammeAlias).filter(ProgrammeAlias.alias == "BCS").first()
        if not prog_alias:
            prog_alias = ProgrammeAlias(
                id="test-prog-alias-1",
                programme_id=prog.id,
                alias="BCS",
                is_primary=True,
            )
            db.add(prog_alias)
            db.commit()
            print(f"✓ Created ProgrammeAlias: {prog_alias.alias} for {prog.name}")
        
        # Test FeeStructure
        fs = db.query(FeeStructure).filter(FeeStructure.programme_id == prog.id).first()
        if not fs:
            fs = FeeStructure(
                id="test-fs-1",
                programme_id=prog.id,
                academic_year_id=ay.id,
                tuition_fee_tzs=1500000,
                registration_fee_tzs=50000,
                examination_fee_tzs=30000,
                total_estimated_tzs=1580000,
                source_url="https://test.ac.tz/fees",
                is_verified=True,
            )
            db.add(fs)
            db.commit()
            print(f"✓ Created FeeStructure: {fs.total_estimated_tzs} TZS for {prog.name}")
        
        # Test SubjectRequirement
        sr = db.query(SubjectRequirement).filter(SubjectRequirement.programme_id == prog.id).first()
        if not sr:
            sr = SubjectRequirement(
                id="test-sr-1",
                programme_id=prog.id,
                academic_year_id=ay.id,
                qualification_type="A-LEVEL",
                required_subjects="Physics, Chemistry, Mathematics",
                subject_combination="PCM",
                minimum_grades="C,C,C",
                minimum_points=4.0,
                source_url="https://test.ac.tz/admissions",
                source_type="UNIVERSITY_OFFICIAL",
                is_verified=True,
            )
            db.add(sr)
            db.commit()
            print(f"✓ Created SubjectRequirement: {sr.required_subjects} for {prog.name}")
        
        # Test Source with authority levels
        source = db.query(Source).filter(Source.url == "https://test.ac.tz/programmes/bcs").first()
        if not source:
            source = Source(
                id="test-source-1",
                title="Bachelor of Computer Science - Test University",
                source_type=SourceType.UNIVERSITY_OFFICIAL,
                authority_level=SourceAuthority.LEVEL_2,
                url="https://test.ac.tz/programmes/bcs",
                university_id=uni.id,
                academic_year="2026/2027",
                is_verified=True,
                priority=1,
            )
            db.add(source)
            db.commit()
            print(f"✓ Created Source: {source.title} (Authority: {source.authority_level})")
        
        # Test AdmissionRequirement
        ar = db.query(AdmissionRequirement).filter(AdmissionRequirement.programme_id == prog.id).first()
        if not ar:
            ar = AdmissionRequirement(
                id="test-ar-1",
                programme_id=prog.id,
                academic_year_id=ay.id,
                qualification_type=QualificationType.A_LEVEL,
                required_subjects="Physics, Chemistry, Mathematics",
                subject_combination="PCM",
                minimum_grades="C,C,C",
                minimum_points=4,
                source_url="https://test.ac.tz/admissions",
                source_type="UNIVERSITY_OFFICIAL",
                is_verified=True,
            )
            db.add(ar)
            db.commit()
            print(f"✓ Created AdmissionRequirement for {prog.name}")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_query_router():
    """Test query classification and entity extraction."""
    print("\n=== Testing QueryRouter ===")
    
    test_queries = [
        ("Does UDSM offer Bachelor of Computer Science?", {
            "university": "udsm",
            "programme": "computer science",
        }),
        ("What are the admission requirements for 2026/2027?", {
            "academic_year": "2026/2027",
        }),
        ("Compare UDSM and UDOM for Computer Science", {
            "category": "UNIVERSITY_COMPARISON",
        }),
        ("Verify if UDSM is accredited", {
            "university": "udsm",
            "category": "VERIFICATION",
        }),
    ]
    
    for query, expected in test_queries:
        category = QueryRouter.classify(query)
        entities = QueryRouter.extract_entities(query)
        
        print(f"Query: {query}")
        print(f"  Category: {category.value}")
        print(f"  Entities: {entities}")
        
        if "category" in expected:
            assert category.value == expected["category"], f"Expected {expected['category']}, got {category.value}"
        if "university" in expected:
            assert "university" in entities, f"Expected university entity"
        if "programme" in expected:
            assert "programme" in entities or "program" in str(entities).lower(), f"Expected programme entity"
        if "academic_year" in expected:
            assert "academic_year" in entities, f"Expected academic_year entity"
    
    print("✓ QueryRouter tests passed")


async def test_retrieval_service():
    """Test retrieval service with filters."""
    print("\n=== Testing RetrievalService ===")
    db = SessionLocal()
    try:
        retrieval = RetrievalService(db)
        
        # Test entity extraction and auto-filtering
        entities = QueryRouter.extract_entities("Does UDSM offer Computer Science?")
        print(f"Entities extracted: {entities}")
        
        # Test filters
        filters = RetrievalFilters(
            source_types=[ST.TCU_OFFICIAL, ST.UNIVERSITY_OFFICIAL],
            is_verified=True,
            authority_levels=[SA.LEVEL_1, SA.LEVEL_2],
        )
        print(f"Filters: source_types={[f.value for f in filters.source_types]}, is_verified={filters.is_verified}")
        
        # Test verification retrieval
        results = await retrieval.retrieve_for_verification(
            university_name="UDSM",
            programme_name="Computer Science",
            top_k=5
        )
        print(f"Verification retrieval returned {len(results)} results")
        
        print("✓ RetrievalService tests passed")
        return True
    except Exception as e:
        print(f"✗ RetrievalService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_verification_service():
    """Test verification service."""
    print("\n=== Testing VerificationService ===")
    db = SessionLocal()
    try:
        verification = VerificationService(db)
        
        # Test university verification
        uni = db.query(University).filter(University.name == "Test University").first()
        if uni:
            result = await verification.verify_university(uni.id)
            print(f"University verification: {result}")
        
        # Test programme verification
        prog = db.query(Programme).filter(Programme.name == "Bachelor of Computer Science").first()
        if prog:
            result = await verification.verify_programme(prog.id)
            print(f"Programme verification: {result}")
        
        print("✓ VerificationService tests passed")
        return True
    except Exception as e:
        print(f"✗ VerificationService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_ingestion_pipeline():
    """Test ingestion pipeline initialization."""
    print("\n=== Testing IngestionPipeline ===")
    db = SessionLocal()
    try:
        pipeline = IngestionPipeline(db)
        
        # Test academic year creation
        years = await pipeline.create_academic_years()
        print(f"Created/verified {len(years)} academic years")
        
        # Test scheduled jobs creation
        await pipeline.create_scheduled_jobs()
        print("Created scheduled ingestion jobs")
        
        # List jobs
        jobs = db.query(IngestionJob).filter(IngestionJob.is_scheduled == True).all()
        print(f"Scheduled jobs: {len(jobs)}")
        for job in jobs:
            print(f"  - {job.job_type}: {job.schedule_cron}")
        
        print("✓ IngestionPipeline tests passed")
        return True
    except Exception as e:
        print(f"✗ IngestionPipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    print("=" * 60)
    print("ChuoAI Verification & Accuracy Test Suite")
    print("=" * 60)
    
    # Test models
    print("\n=== Testing Models ===")
    if not test_models():
        sys.exit(1)
    
    # Test query router
    if not await test_query_router():
        sys.exit(1)
    
    # Test retrieval service
    if not await test_retrieval_service():
        sys.exit(1)
    
    # Test verification service
    if not await test_verification_service():
        sys.exit(1)
    
    # Test ingestion pipeline
    if not await test_ingestion_pipeline():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())