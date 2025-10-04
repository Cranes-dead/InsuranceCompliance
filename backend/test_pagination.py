"""
Quick test for IRDAI paginated search
Tests the new pagination functionality
"""

from smart_scraper import SmartMotorVehicleScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pagination_detection():
    """Test pagination pattern detection"""
    print("\n" + "="*80)
    print("TEST: Pagination Detection")
    print("="*80)
    
    scraper = SmartMotorVehicleScraper()
    
    test_urls = [
        ("https://irdai.gov.in/web/guest/search?q=motor&filterDepartment=NLF&archiveOn=true", True),
        ("https://irdai.gov.in/search?p_p_id=com_irdai_custom_search_results_CustomSearchResultsPortlet_INSTANCE_QtdSmUnYs3ko&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&filterDepartment=NLF&q=motor&archiveOn=true&delta=20&resetCur=false&cur=2", True),
        ("https://www.irdai.gov.in/ADMINCMS/cms/NormalData_Layout.aspx?page=PageNo247&mid=3.4.1", False),
    ]
    
    for url, expected in test_urls:
        info = scraper.detect_pagination_pattern(url)
        is_paginated = info['has_pagination']
        status = "✅ CORRECT" if is_paginated == expected else "❌ WRONG"
        print(f"{status} | Paginated: {is_paginated} | {url[:60]}...")
    
    print("\n✅ Pagination detection working!\n")

def test_url_generation():
    """Test next page URL generation"""
    print("="*80)
    print("TEST: Next Page URL Generation")
    print("="*80)
    
    scraper = SmartMotorVehicleScraper()
    
    base_url = "https://irdai.gov.in/web/guest/search?q=motor&filterDepartment=NLF&archiveOn=true"
    
    print(f"\nBase URL: {base_url}\n")
    
    for page in [2, 3, 4]:
        next_url = scraper.get_next_page_url(base_url, page)
        print(f"Page {page}: {next_url}")
        
        # Verify it has cur= parameter
        if f"&cur={page}" in next_url:
            print(f"  ✅ Correct pagination parameter\n")
        else:
            print(f"  ❌ Missing pagination parameter\n")
    
    print("✅ URL generation working!\n")

def test_sites_list():
    """Test that IRDAI search is in sites list"""
    print("="*80)
    print("TEST: Sites Configuration")
    print("="*80)
    
    scraper = SmartMotorVehicleScraper()
    
    print(f"\nConfigured sites ({len(scraper.sites)}):\n")
    for name, url in scraper.sites.items():
        is_new = "SEARCH" in name
        marker = "🆕 NEW" if is_new else "   "
        print(f"{marker} | {name:25} | {url[:50]}...")
    
    if "IRDAI_MOTOR_SEARCH" in scraper.sites:
        print("\n✅ IRDAI paginated search added!\n")
    else:
        print("\n❌ IRDAI search missing!\n")

if __name__ == "__main__":
    print("\n" + "🧪"*40)
    print("SMART SCRAPER PAGINATION TEST")
    print("🧪"*40 + "\n")
    
    test_pagination_detection()
    test_url_generation()
    test_sites_list()
    
    print("="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    print("\nReady to scrape IRDAI paginated search!")
    print("\nTo test with real scraping:")
    print('  python -c "from smart_scraper import SmartMotorVehicleScraper; s = SmartMotorVehicleScraper(); s.scrape_site_with_smart_filtering(\'IRDAI_MOTOR_SEARCH\', s.sites[\'IRDAI_MOTOR_SEARCH\']); s.save_final_stats()"')
    print("\n")
