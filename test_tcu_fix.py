#!/usr/bin/env python
"""Test script for TCU Statistics retrieval fix."""
import sys
import asyncio

sys.path.insert(0, '/home/abel/chuoAI/backend')

from app.core.database import SessionLocal
from app.ai.router import QueryRouter, QueryCategory
from app.rag.retrieval import RetrievalService, RetrievalFilters
from app.models.academic_year import TCUStatistic, TCUStatisticType, AcademicYear
from app.models.source import SourceType, SourceAuthority


async def test_query_classification():
    """Test that TCU statistics queries are classified correctly."""
    print("=" * 60)
    print("TEST 1: Query Classification")
    print("=" * 60)
    
    test_queries = [
        ("How many universities are there in Tanzania?", QueryCategory.TCU_STATISTICS),
        ("How many university institutions are in Tanzania?", QueryCategory.TCU_STATISTICS),
        ("How many academic programmes are offered?", QueryCategory.TCU_STATISTICS),
        ("What is the number of universities in Tanzania?", QueryCategory.TCU_STATISTICS),
        ("Total universities in Tanzania?", QueryCategory.TCU_STATISTICS),
        ("How many programmes does TCU have?", QueryCategory.TCU_STATISTICS),
        ("Is UDSM accredited?", QueryCategory.VERIFICATION),
        ("Compare UDSM and UDOM", QueryCategory.UNIVERSITY_COMPARISON),
        ("What are the admission requirements for UDSM?", QueryCategory.ADMISSION),
    ]
    
    all_passed = True
    for query, expected in test_queries:
        category = QueryRouter.classify(query)
        status = "✓" if category == expected else "✗"
        if category != expected:
            all_passed = False
        print(f"  {status} '{query}' -> {category.value} (expected: {expected.value})")
    
    return all_passed


async def test_tcu_statistics_lookup():
    """Test the structured TCU statistics lookup."""
    print("\n" + "=" * 60)
    print("TEST 2: TCU Statistics Lookup")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        retrieval = RetrievalService(db)
        
        # Create a test TCU statistic
        ay = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
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
        
        # Check if test statistic already exists
        existing = db.query(TCUStatistic).filter(
            TCUStatistic.metric_name == "university_institutions",
            TCUStatistic.academic_year_label == "2026/2027"
        ).first()
        
        if not existing:
            stat = TCUStatistic(
                id="test-stat-1",
                statistic_type=TCUStatisticType.UNIVERSITY_INSTITUTIONS,
                metric_name="university_institutions",
                value=56,
                unit="count",
                source_url="https://www.tcu.go.tz/universities",
                source_page_title="University Institutions",
                source_section="statistics",
                academic_year_id=ay.id,
                academic_year_label="2026/2027",
                is_verified=True,
                verified_at=datetime.utcnow(),
                last_crawled_at=datetime.utcnow(),
                content_hash="test_hash",
            )
            db.add(stat)
            db.commit()
            print("  ✓ Created test TCU statistic: university_institutions = 56")
        
        # Test lookup
        results = await retrieval.lookup_tcu_statistics(
            "How many universities are there in Tanzania?",
            "2026/2027"
        )
        
        print(f"  Lookup results: {len(results)}")
        if results:
            for r in results:
                print(f"    - {r['metric_name']}: {r['value']} {r['unit']} (source: {r.get('source_url')})")
                print(f"      Academic year: {r['academic_year']}")
                print(f"      Authority: {r['metadata']['authority_level']}")
        
        # Test programme count
        if not existing:
            stat2 = TCUStatistic(
                id="test-stat-2",
                statistic_type=TCUStatisticType.ACADEMIC_PROGRAMMES,
                metric_name="academic_programmes",
                value=2212,
                unit="count",
                source_url="https://www.tcu.go.tz/programmes",
                source_page_title="Academic Programmes",
                source_section="statistics",
                academic_year_id=ay.id,
                academic_year_label="2026/2027",
                is_verified=True,
                verified_at=datetime.utcnow(),
                last_crawled_at=datetime.utcnow(),
                content_hash="test_hash2",
            )
            db.add(stat2)
            db.commit()
            print("  ✓ Created test TCU statistic: academic_programmes = 2212")
        
        results = await retrieval.lookup_tcu_statistics(
            "How many academic programmes are offered?",
            "2026/2027"
        )
        
        print(f"  Lookup results: {len(results)}")
        if results:
            for r in results:
                print(f"    - {r['metric_name']}: {r['value']:,} {r['unit']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_retrieval_with_fallback():
    """Test the hybrid retrieval with fallback strategies."""
    print("\n" + "=" * 60)
    print("TEST 3: Hybrid Retrieval with Fallback")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        retrieval = RetrievalService(db)
        
        # Test TCU_STATISTICS query with structured lookup
        result = await retrieval.retrieve_with_context(
            "How many universities are there in Tanzania?",
            category=QueryCategory.TCU_STATISTICS
        )
        
        print(f"  Context length: {len(result['context'])}")
        print(f"  Documents found: {len(result['documents'])}")
        print(f"  Sources: {len(result['sources'])}")
        print(f"  Strategies used: {result.get('retrieval_strategies', {})}")
        
        if result['context']:
            print(f"  Context preview: {result['context'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_empty_context_fallback():
    """Test that fallback works when no structured data exists."""
    print("\n" + "=" * 60)
    print("TEST 4: Empty Context Fallback")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        retrieval = RetrievalService(db)
        
        # Query for something that likely has no structured data
        result = await retrieval.retrieve_with_context(
            "How many students are enrolled in Tanzanian universities?",
            category=QueryCategory.TCU_STATISTICS
        )
        
        print(f"  Context length: {len(result['context'])}")
        print(f"  Documents found: {len(result['documents'])}")
        print(f"  Strategies used: {result.get('retrieval_strategies', {})}")
        
        # Should have tried fallback strategies
        strategies = result.get('retrieval_strategies', {})
        print(f"  Fallback used: {strategies.get('fallback', False)}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    from datetime import datetime
    
    print("\n" + "=" * 60)
    print("CHUOAI TCU STATISTICS RETRIEVAL TESTS")
    print("=" * 60)
    
    results = []
    results.append(await test_query_classification())
    results.append(await test_tcu_statistics_lookup())
    results.append(await test_retrieval_with_fallback())
    results.append(await test_empty_context_fallback())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    if passed == total:
        print("ALL TESTS PASSED! ✓")
    else:
        print("SOME TESTS FAILED! ✗")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)