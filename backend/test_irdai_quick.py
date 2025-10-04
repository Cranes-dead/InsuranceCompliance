"""
Quick test for IRDAI document-detail page with direct href links
"""

from smart_scraper import SmartMotorVehicleScraper
import logging

logging.basicConfig(level=logging.INFO)

def test_single_document():
    """Test a single IRDAI document-detail page"""
    print("\n" + "="*80)
    print("🧪 QUICK TEST: Single IRDAI Document Page")
    print("="*80 + "\n")
    
    scraper = SmartMotorVehicleScraper()
    
    # Test with a specific document-detail page that has the download link you found
    test_url = "https://irdai.gov.in/document-detail?documentId=818649"
    
    try:
        # Navigate to page
        if scraper.navigate_to_page(test_url):
            print("\n✅ Page loaded successfully")
            
            # Extract PDFs
            pdf_links = scraper.find_pdf_links()
            
            print(f"\n✅ Found {len(pdf_links)} PDF link(s)\n")
            
            for i, pdf in enumerate(pdf_links, 1):
                print(f"PDF {i}:")
                print(f"  Title: {pdf['text'][:100]}")
                print(f"  URL: {pdf['url'][:120]}...")
                print()
        
        print("="*80)
        print("✅ TEST COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    test_single_document()
