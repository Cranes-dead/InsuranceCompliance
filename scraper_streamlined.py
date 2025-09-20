import pdfplumber
import os
import csv
import time
import re
import platform
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
from pathlib import Path
import requests

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComplianceDocumentScraper:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path("D:/compliance_scraper")
        self.pdf_dir = self.base_dir / "scraped_pdfs"
        self.processed_urls_file = self.base_dir / "processed_urls.txt"
        self.csv_file = self.base_dir / "compliance_documents.csv"
        self.processed_urls = set()
        
        # File size limit (50MB)
        self.max_file_size = 50 * 1024 * 1024
        
        # WebDriver
        self.driver = None
        
        # Website configurations
        self.sites = {
            "IRDAI": "https://www.irdai.gov.in/ADMINCMS/cms/NormalData_Layout.aspx?page=PageNo247&mid=3.4.1",
            "MoRTH": "https://morth.nic.in",
            "GIC": "https://www.gicre.in/en//"
        }
        
        # Statistics
        self.stats = {
            'total_pdfs_found': 0,
            'new_pdfs_downloaded': 0,
            'failed_downloads': 0,
            'text_extraction_failures': 0
        }

    def setup_webdriver(self):
        """Setup Chrome WebDriver with fallback options"""
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Try multiple approaches to setup ChromeDriver
        setup_methods = [
            self._setup_with_manager,
            self._setup_with_system_chrome,
            self._setup_with_manual_path
        ]
        
        for method in setup_methods:
            try:
                if method(chrome_options):
                    self.driver.set_page_load_timeout(30)
                    self.driver.implicitly_wait(10)
                    logger.info("Chrome WebDriver setup successful")
                    return
            except Exception as e:
                logger.warning(f"Setup method failed: {e}")
                continue
        
        raise Exception("All ChromeDriver setup methods failed")
    
    def _setup_with_manager(self, chrome_options):
        """Try setup with WebDriverManager"""
        try:
            # Force win64 architecture
            import platform
            if platform.machine().endswith('64'):
                service = ChromeService(ChromeDriverManager(version="latest", os_type="win64").install())
            else:
                service = ChromeService(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            return True
        except Exception as e:
            logger.warning(f"WebDriverManager setup failed: {e}")
            return False
    
    def _setup_with_system_chrome(self, chrome_options):
        """Try setup with system ChromeDriver"""
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            logger.warning(f"System ChromeDriver setup failed: {e}")
            return False
    
    def _setup_with_manual_path(self, chrome_options):
        """Try setup with manual ChromeDriver paths"""
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chromedriver.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",
            r"C:\chromedriver\chromedriver.exe",
            r".\chromedriver.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    service = ChromeService(executable_path=path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info(f"Using ChromeDriver at: {path}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed with ChromeDriver at {path}: {e}")
                    continue
        
        return False

    def setup_environment(self):
        """Create necessary directories and files"""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self.pdf_dir.mkdir(exist_ok=True)
            
            # Load processed URLs
            if self.processed_urls_file.exists():
                with open(self.processed_urls_file, 'r', encoding='utf-8') as f:
                    self.processed_urls = set(line.strip() for line in f if line.strip())
            
            # Create CSV with headers if it doesn't exist
            if not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['source', 'title', 'pdf_url', 'local_path', 'extracted_text', 'language'])
            
            logger.info(f"Environment setup complete. {len(self.processed_urls)} URLs already processed.")
            
        except Exception as e:
            logger.error(f"Error setting up environment: {e}")
            raise

    def detect_language(self, text):
        """Simple language detection based on Devanagari script"""
        if not text or len(text.strip()) < 10:
            return "unknown"
        
        # Check for Devanagari script (Hindi)
        if re.search(r'[\u0900-\u097F]', text):
            return "hi"
        else:
            return "en"

    def navigate_to_page(self, url):
        """Navigate to a page using Selenium"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(2)  # Brief wait for dynamic content
            logger.info(f"Successfully loaded: {url}")
            return True
            
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Failed to load page {url}: {e}")
            return False

    def find_pdf_links(self):
        """Find all PDF links on the current page"""
        pdf_links = []
        
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    if href and self.is_pdf_url(href):
                        absolute_url = urljoin(self.driver.current_url, href)
                        
                        if absolute_url not in self.processed_urls:
                            pdf_links.append({
                                'url': absolute_url,
                                'text': text or Path(urlparse(absolute_url).path).name
                            })
                            
                except Exception as e:
                    logger.warning(f"Error processing link: {e}")
                    continue
            
            logger.info(f"Found {len(pdf_links)} new PDF links")
            return pdf_links
            
        except Exception as e:
            logger.error(f"Error finding PDF links: {e}")
            return []

    def is_pdf_url(self, url):
        """Check if URL points to a PDF file"""
        return url.lower().endswith('.pdf') or 'pdf' in url.lower()

    def sanitize_filename(self, filename):
        """Sanitize filename for filesystem compatibility"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip('. ')
        
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:196] + ext
        
        return filename

    def download_pdf(self, pdf_url, filename):
        """Download PDF file"""
        try:
            response = requests.get(pdf_url, stream=True, timeout=30, verify=False)
            response.raise_for_status()
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                logger.warning(f"Skipping large file: {pdf_url}")
                return None
            
            filename = self.sanitize_filename(filename)
            local_path = self.pdf_dir / filename
            
            # Ensure unique filename
            counter = 1
            original_path = local_path
            while local_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                local_path = self.pdf_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded: {filename}")
            self.stats['new_pdfs_downloaded'] += 1
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Error downloading {pdf_url}: {e}")
            self.stats['failed_downloads'] += 1
            return None

    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:50]:  # Limit to first 50 pages
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting page from {file_path}: {e}")
                        continue
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            self.stats['text_extraction_failures'] += 1
            return ""

    def save_to_csv(self, data):
        """Save data to CSV file"""
        try:
            # Detect language
            language = self.detect_language(data['extracted_text'])
            
            # Truncate text if too long
            if len(data['extracted_text']) > 32767:
                data['extracted_text'] = data['extracted_text'][:32760] + "..."
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['source'],
                    data['title'],
                    data['pdf_url'],
                    data['local_path'],
                    data['extracted_text'],
                    language
                ])
            
            logger.info(f"Saved document: {data['title']}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")

    def mark_as_processed(self, url):
        """Mark URL as processed"""
        try:
            with open(self.processed_urls_file, 'a', encoding='utf-8') as f:
                f.write(url + '\n')
            self.processed_urls.add(url)
        except Exception as e:
            logger.error(f"Error marking URL as processed: {e}")

    def scrape_site(self, site_name, url):
        """Scrape a single site"""
        try:
            logger.info(f"Scraping {site_name}...")
            
            if not self.navigate_to_page(url):
                logger.error(f"Failed to load {site_name} page")
                return
            
            pdf_links = self.find_pdf_links()
            self.stats['total_pdfs_found'] += len(pdf_links)
            
            for i, link_data in enumerate(pdf_links, 1):
                logger.info(f"Processing {i}/{len(pdf_links)}: {site_name}")
                
                pdf_url = link_data['url']
                title = link_data['text']
                
                # Generate filename
                base_filename = Path(urlparse(pdf_url).path).name
                if not base_filename:
                    base_filename = f"document_{i}.pdf"
                
                filename = f"{site_name}_{datetime.now().strftime('%Y%m%d')}_{base_filename}"
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
                
                # Download and process
                local_path = self.download_pdf(pdf_url, filename)
                
                if local_path:
                    extracted_text = self.extract_text_from_pdf(local_path)
                    
                    data = {
                        'source': site_name,
                        'title': title,
                        'pdf_url': pdf_url,
                        'local_path': local_path,
                        'extracted_text': extracted_text
                    }
                    
                    self.save_to_csv(data)
                    self.mark_as_processed(pdf_url)
                
                # Respectful delay
                time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")

    def print_statistics(self):
        """Print scraping statistics"""
        logger.info("\n" + "="*40)
        logger.info("SCRAPING STATISTICS")
        logger.info("="*40)
        logger.info(f"Total PDF links found: {self.stats['total_pdfs_found']}")
        logger.info(f"New PDFs downloaded: {self.stats['new_pdfs_downloaded']}")
        logger.info(f"Failed downloads: {self.stats['failed_downloads']}")
        logger.info(f"Text extraction failures: {self.stats['text_extraction_failures']}")
        logger.info("="*40)

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def run(self):
        """Main execution function"""
        start_time = datetime.now()
        logger.info("Starting compliance document scraping...")
        
        try:
            self.setup_webdriver()
            self.setup_environment()
            
            # Scrape each site
            for site_name, url in self.sites.items():
                self.scrape_site(site_name, url)
            
            self.print_statistics()
            
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
        finally:
            self.cleanup()
            
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Scraping completed in {duration}")

def main():
    """Main function"""
    try:
        with ComplianceDocumentScraper() as scraper:
            scraper.run()
    except Exception as e:
        logger.error(f"Failed to initialize scraper: {e}")

if __name__ == "__main__":
    main()