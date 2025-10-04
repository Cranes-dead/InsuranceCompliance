"""
Test script for enhanced IRDAI document-detail scraping
"""

from smart_scraper import SmartMotorVehicleScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_irdai_search_page():
    """Test IRDAI search page with document-detail links"""
    print("\n" + "="*80)
    print("🧪 TEST: IRDAI Search Page with Document-Detail Links")
    print("="*80 + "\n")
    
    scraper = SmartMotorVehicleScraper()
    
    # Test with first page of IRDAI search
    test_url = "https://irdai.gov.in/web/guest/search?q=motor&filterDepartment=NLF&archiveOn=true"
    
    try:
        scraper.scrape_site_with_smart_filtering('IRDAI_MOTOR_SEARCH_TEST', test_url)
        scraper.save_final_stats()
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED")
        print("="*80)
        print(f"\nResults saved to: D:\\smart_motor_compliance_scraper\\")
        print(f"Check scraping_stats.json for statistics")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        scraper.save_final_stats()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.driver:
            scraper.driver.quit()

def test_irdai_document_detail_page():
    """Test direct navigation to IRDAI document-detail page"""
    print("\n" + "="*80)
    print("🧪 TEST: IRDAI Document-Detail Page Direct")
    print("="*80 + "\n")
    
    scraper = SmartMotorVehicleScraper()
    
    # Test with a specific document-detail page
    test_url = "https://irdai.gov.in/document-detail?documentId=818649"
    
    try:
        # Navigate to page
        if scraper.navigate_to_page(test_url):
            # Extract PDFs
            pdf_links = scraper.find_pdf_links()
            
            print(f"\n✅ Found {len(pdf_links)} PDF links")
            
            for i, pdf in enumerate(pdf_links, 1):
                print(f"\nPDF {i}:")
                print(f"  Title: {pdf['text']}")
                print(f"  URL: {pdf['url'][:100]}...")
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║           🧪 IRDAI ENHANCED SCRAPER TEST                                 ║
║                                                                           ║
║  Tests the new IRDAI document-detail link handling                       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

Choose a test:

1. Test IRDAI search page (finds document-detail links, navigates to each)
2. Test IRDAI document-detail page directly (extracts PDF download links)

""")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_irdai_search_page()
    elif choice == "2":
        test_irdai_document_detail_page()
    else:
        print("❌ Invalid choice")
