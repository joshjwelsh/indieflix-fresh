#!/usr/bin/env python3
"""
Daily Pipeline for Indieflix
Runs all ingestion scripts in sequence to update movie data
Designed to be run as a cron job
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'ingestion'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'enrichment'))

from metrograph_v2 import MetrographScraperV2, save_to_db as save_metrograph
from syndicatedbk import SyndicatedBKScraper, save_to_db as save_syndicated
from ifc_center_v2 import IFCCenterScraperV2, save_to_db as save_ifc
from tmdb_enricher import TMDBEnricher


def run_pipeline():
    """Run the complete daily pipeline"""
    print("\n" + "="*60)
    print("INDIEFLIX DAILY PIPELINE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    results = {
        'metrograph': {'success': False, 'count': 0},
        'syndicated': {'success': False, 'count': 0},
        'ifc_center': {'success': False, 'count': 0},
        'enrichment': {'success': False, 'count': 0}
    }
    
    # 1. Scrape Metrograph
    print("📽️  STEP 1: Scraping Metrograph...")
    print("-" * 60)
    try:
        scraper = MetrographScraperV2()
        movies = scraper.scrape()
        save_metrograph(movies)
        results['metrograph'] = {'success': True, 'count': len(movies)}
        print(f"✅ Metrograph: {len(movies)} movies scraped\n")
    except Exception as e:
        print(f"❌ Metrograph failed: {e}\n")
        results['metrograph'] = {'success': False, 'error': str(e)}
    
    # 2. Scrape Syndicated BK
    print("📽️  STEP 2: Scraping Syndicated BK...")
    print("-" * 60)
    try:
        scraper = SyndicatedBKScraper()
        movies = scraper.scrape()
        save_syndicated(movies)
        results['syndicated'] = {'success': True, 'count': len(movies)}
        print(f"✅ Syndicated BK: {len(movies)} movies scraped\n")
    except Exception as e:
        print(f"❌ Syndicated BK failed: {e}\n")
        results['syndicated'] = {'success': False, 'error': str(e)}
    
    # 3. Scrape IFC Center
    print("📽️  STEP 3: Scraping IFC Center...")
    print("-" * 60)
    try:
        scraper = IFCCenterScraperV2()
        movies = scraper.scrape()
        save_ifc(movies)
        results['ifc_center'] = {'success': True, 'count': len(movies)}
        print(f"✅ IFC Center: {len(movies)} movies scraped\n")
    except Exception as e:
        print(f"❌ IFC Center failed: {e}\n")
        results['ifc_center'] = {'success': False, 'error': str(e)}
    
    # 4. Enrich with TMDB data
    print("🎬 STEP 4: Enriching with TMDB data...")
    print("-" * 60)
    try:
        enricher = TMDBEnricher()
        enriched_count = enricher.enrich_all_unenriched(limit=100)
        results['enrichment'] = {'success': True, 'count': enriched_count}
        print(f"✅ TMDB Enrichment: {enriched_count} movies enriched\n")
    except Exception as e:
        print(f"❌ TMDB enrichment failed: {e}\n")
        results['enrichment'] = {'success': False, 'error': str(e)}
    
    # Summary
    print("="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    
    total_scraped = (results['metrograph'].get('count', 0) + 
                     results['syndicated'].get('count', 0) + 
                     results['ifc_center'].get('count', 0))
    total_enriched = results['enrichment'].get('count', 0)
    
    print(f"✅ Total movies scraped: {total_scraped}")
    print(f"   - Metrograph: {results['metrograph'].get('count', 0)}")
    print(f"   - Syndicated BK: {results['syndicated'].get('count', 0)}")
    print(f"   - IFC Center: {results['ifc_center'].get('count', 0)}")
    print(f"🎬 Total movies enriched: {total_enriched}")
    
    # Check for failures
    failures = []
    for step, result in results.items():
        if not result.get('success'):
            failures.append(f"{step}: {result.get('error', 'Unknown error')}")
    
    if failures:
        print(f"\n⚠️  {len(failures)} step(s) failed:")
        for failure in failures:
            print(f"   - {failure}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Return exit code (0 = success, 1 = partial failure)
    return 0 if not failures else 1


if __name__ == '__main__':
    exit_code = run_pipeline()
    sys.exit(exit_code)
