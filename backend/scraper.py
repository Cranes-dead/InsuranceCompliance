import requests 
import pdfplumber
import os
import csv
import time
import re
import random
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
from pathlib import Path
from langdetect import detect
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Disable SSL warnings for government sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MotorVehicleComplianceDocumentScraper:
    def __init__(self, base_dir=None):
        # Fix constructor logic - use provided base_dir or default
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path("D:/motor_compliance_scraper")
        
        # Ensure directory exists
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.pdf_dir = self.base_dir / "motor_insurance_pdfs"
        self.processed_urls_file = self.base_dir / "processed_motor_urls.txt"
        self.csv_file = self.base_dir / "motor_vehicle_compliance_documents.csv"
        self.processed_urls = set()
        
        # File size limit (50MB)
        self.max_file_size = 50 * 1024 * 1024
        
        # Setup Selenium WebDriver
        self.driver = None
        self.setup_webdriver()
        
        # Setup session for PDF downloads with retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers for PDF downloads
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        self.session.headers.update(self.headers)
        
        # Website configurations - Motor Vehicle Insurance focused URLs
        self.sites = {
            # IRDAI Motor Insurance specific pages
            "IRDAI_MOTOR": "https://www.irdai.gov.in/ADMINCMS/cms/NormalData_Layout.aspx?page=PageNo247&mid=3.4.1",
            "IRDAI_GUIDELINES": "https://www.irdai.gov.in/guidelines/motor-insurance",
            "IRDAI_TARIFF": "https://www.irdai.gov.in/motor-third-party-tariff",
            
            # MoRTH Vehicle Insurance Rules
            "MoRTH_MOTOR": "https://morth.nic.in/motor-vehicle-act",
            "MoRTH_INSURANCE": "https://morth.nic.in/insurance-provisions",
            "MoRTH": "https://morth.nic.in",
            
            # General Insurance Council - Motor specific
            "GIC_MOTOR": "https://www.gicre.in/en/motor-insurance",
            "GIC": "https://www.gicre.in/en//"
        }
        
        # Motor Vehicle Insurance specific keywords for document filtering
        self.motor_keywords = [
            'motor insurance', 'vehicle insurance', 'third party', 'motor vehicle',
            'third party liability', 'motor tariff', 'vehicle coverage',
            'two wheeler', 'four wheeler', 'commercial vehicle', 'private car',
            'motor third party', 'vehicle act', 'compulsory insurance',
            'motor policy', 'vehicle policy', 'automobile insurance',
            'motor coverage', 'vehicular insurance', 'tp liability',
            'own damage', 'comprehensive motor', 'motor claim'
        ]
        
        # Date patterns for better extraction
        self.date_patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',  # YYYY/MM/DD or YYYY-MM-DD
            r'\b\d{1,2}\s+\w+\s+\d{4}\b',       # DD Month YYYY
            r'\b\w+\s+\d{1,2},\s+\d{4}\b',     # Month DD, YYYY
        ]
        
        # Statistics
        self.stats = {
            'total_pdfs_found': 0,
            'new_pdfs_downloaded': 0,
            'skipped_large_files': 0,
            'failed_downloads': 0,
            'text_extraction_failures': 0,
            'language_detection_failures': 0,
            'connection_retries': 0,
            'selenium_errors': 0
        }

    def setup_webdriver(self):
        """Setup Selenium WebDriver with Chrome and Firefox fallback"""
        try:
            # Try Chrome first
            if self._setup_chrome_driver():
                return
            
            # Fall back to Firefox if Chrome fails
            logger.warning("Chrome setup failed, trying Firefox...")
            if self._setup_firefox_driver():
                return
            
            raise Exception("Both Chrome and Firefox WebDriver setup failed")
            
        except Exception as e:
            logger.error(f"Failed to setup any WebDriver: {e}")
            raise

    def _setup_chrome_driver(self):
        """Setup Chrome WebDriver with multiple fallback options"""
        try:
            chrome_options = ChromeOptions()
            
            # Headless mode
            chrome_options.add_argument("--headless")
            
            # Windows-specific compatibility options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Performance options
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            
            # Security and stability options
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors-spki-list")
            chrome_options.add_argument("--ignore-insecure-origin")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # User agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Try to find Chrome binary
            possible_chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
            ]
            
            for chrome_path in possible_chrome_paths:
                expanded_path = os.path.expandvars(chrome_path)
                if os.path.exists(expanded_path):
                    chrome_options.binary_location = expanded_path
                    logger.info(f"Found Chrome at: {expanded_path}")
                    break
            
            # Try ChromeDriverManager first
            try:
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Chrome WebDriver setup with ChromeDriverManager successful")
            except Exception as e:
                logger.warning(f"ChromeDriverManager failed: {e}")
                
                # Try system Chrome driver
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    logger.info("Chrome WebDriver setup with system driver successful")
                except Exception as e2:
                    logger.error(f"System Chrome driver also failed: {e2}")
                    return False
            
            # Configure timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome WebDriver setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Chrome WebDriver setup failed: {e}")
            return False

    def _setup_firefox_driver(self):
        """Setup Firefox WebDriver as fallback"""
        try:
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            
            try:
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=firefox_options)
                logger.info("Firefox WebDriver setup successful")
            except Exception as e:
                logger.warning(f"GeckoDriverManager failed: {e}")
                # Try system Firefox driver
                self.driver = webdriver.Firefox(options=firefox_options)
                logger.info("Firefox WebDriver setup with system driver successful")
            
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            return True
            
        except Exception as e:
            logger.error(f"Firefox WebDriver setup failed: {e}")
            return False

    def setup_environment(self):
        """Create necessary directories and files"""
        try:
            # Create directories
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
                    writer.writerow(['source', 'title', 'publication_date', 'pdf_url', 'local_path', 'extracted_text', 'language', 'motor_vehicle_relevance'])
            
            logger.info(f"Motor Vehicle Compliance environment setup complete. {len(self.processed_urls)} URLs already processed.")
            
        except Exception as e:
            logger.error(f"Error setting up environment: {e}")
            raise

    def detect_language(self, text):
        """Detect language of text with focus on Hindi and English"""
        try:
            if not text or len(text.strip()) < 10:
                return "unknown"
            
            # Clean text for better detection
            clean_text = re.sub(r'[^\w\s\u0900-\u097F]', ' ', text)
            clean_text = ' '.join(clean_text.split())
            
            if len(clean_text.strip()) < 10:
                return "unknown"
            
            detected_lang = detect(clean_text)
            
            # Map common language codes to our supported languages
            if detected_lang in ['hi', 'ne', 'mr', 'bn']:  # Hindi and related languages
                return "hi"
            elif detected_lang in ['en']:
                return "en"
            else:
                # Check for Devanagari script presence
                if re.search(r'[\u0900-\u097F]', text):
                    return "hi"
                else:
                    return "en"  # Default to English for other languages
                    
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            self.stats['language_detection_failures'] += 1
            
            # Fallback: Check for Devanagari script
            if re.search(r'[\u0900-\u097F]', text):
                return "hi"
            else:
                return "en"

    def make_request_with_retry(self, url, method='GET', **kwargs):
        """Make HTTP request with custom retry logic for PDF downloads"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                kwargs.setdefault('verify', False)
                kwargs.setdefault('timeout', 30)
                
                if method.upper() == 'HEAD':
                    response = self.session.head(url, **kwargs)
                else:
                    response = self.session.get(url, **kwargs)
                
                response.raise_for_status()
                return response
                
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                
                self.stats['connection_retries'] += 1
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {url}: {e}")
                    raise
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [503, 502, 504]:
                    # Server errors - retry
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Server error {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"Server error persists for {url}: {e}")
                        raise
                else:
                    # Client errors - don't retry
                    logger.error(f"HTTP error for {url}: {e}")
                    raise

    def navigate_to_page(self, url, retries=3):
        """Navigate to a page using Selenium with retry logic"""
        for attempt in range(retries):
            try:
                logger.info(f"Navigating to: {url} (attempt {attempt + 1}/{retries})")
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Additional wait for dynamic content
                time.sleep(3)
                
                logger.info(f"Successfully loaded: {url}")
                return True
                
            except TimeoutException:
                logger.warning(f"Timeout loading page (attempt {attempt + 1}/{retries}): {url}")
                if attempt < retries - 1:
                    time.sleep(5)
                else:
                    self.stats['selenium_errors'] += 1
                    return False
                    
            except WebDriverException as e:
                logger.error(f"WebDriver error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(5)
                else:
                    self.stats['selenium_errors'] += 1
                    return False
        
        return False

    def find_pdf_links(self):
        """Find all PDF links on the current page using Selenium with motor vehicle insurance focus"""
        pdf_links = []
        motor_pdf_links = []
        
        try:
            current_url = self.driver.current_url
            
            # Special handling for IRDAI search/document pages
            if 'irdai.gov.in' in current_url.lower():
                # Check if this is a search results page with document-detail links
                if 'search?' in current_url or 'cur=' in current_url:
                    logger.info("🔍 Detected IRDAI search page - looking for document-detail links")
                    return self._find_irdai_document_links()
                # Check if this is a document detail page with download button
                elif 'document-detail?' in current_url or 'documentId=' in current_url:
                    logger.info("📄 Detected IRDAI document-detail page - extracting PDF download links")
                    return self._extract_irdai_document_pdfs()
            
            # Standard PDF link finding for other sites
            # Find all anchor tags
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    parent_text = self.get_parent_text(link)
                    combined_text = f"{text} {parent_text}".lower()
                    
                    if href and self.is_pdf_url(href):
                        # Get absolute URL
                        absolute_url = urljoin(self.driver.current_url, href)
                        
                        if absolute_url not in self.processed_urls:
                            link_data = {
                                'element': link,
                                'url': absolute_url,
                                'text': text,
                                'parent_text': parent_text
                            }
                            
                            pdf_links.append(link_data)
                            
                            # Check if this PDF is related to motor vehicle insurance
                            if self.is_motor_vehicle_related(combined_text):
                                motor_pdf_links.append(link_data)
                                logger.info(f"🚗 Motor vehicle PDF found: {text[:50]}...")
                            
                except Exception as e:
                    logger.warning(f"Error processing link: {e}")
                    continue
            
            # Prioritize motor vehicle related PDFs
            if motor_pdf_links:
                logger.info(f"🎯 Found {len(motor_pdf_links)} MOTOR VEHICLE related PDFs out of {len(pdf_links)} total PDFs")
                return motor_pdf_links
            else:
                logger.info(f"Found {len(pdf_links)} PDF links (no motor vehicle specific filters matched)")
                return pdf_links
            
        except Exception as e:
            logger.error(f"Error finding PDF links: {e}")
            self.stats['selenium_errors'] += 1
            return []
    
    def _find_irdai_document_links(self):
        """Find document-detail links on IRDAI search results page"""
        document_links = []
        
        try:
            # Wait for search results to load
            time.sleep(3)
            
            # Find all links on the page
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    # Look for document-detail links
                    if href and 'document-detail?' in href and 'documentId=' in href:
                        absolute_url = urljoin(self.driver.current_url, href)
                        
                        if absolute_url not in self.processed_urls:
                            link_data = {
                                'element': link,
                                'url': absolute_url,
                                'text': text,
                                'parent_text': '',
                                'is_irdai_document': True
                            }
                            document_links.append(link_data)
                            logger.info(f"📋 Found IRDAI document link: {text[:80]}...")
                
                except Exception as e:
                    logger.warning(f"Error processing document link: {e}")
                    continue
            
            logger.info(f"✅ Found {len(document_links)} IRDAI document-detail links")
            return document_links
            
        except Exception as e:
            logger.error(f"Error finding IRDAI document links: {e}")
            return []
    
    def _extract_irdai_document_pdfs(self, max_click_retries=2, current_retry=0):
        """Extract PDF download links from IRDAI document-detail page"""
        pdf_links = []
        
        try:
            # Wait for page to fully load
            time.sleep(3)
            
            # Get page title once for fallback use
            page_title = ""
            try:
                page_title = self.driver.find_element(By.TAG_NAME, "h1").text.strip()
            except:
                try:
                    page_title = self.driver.title
                except:
                    page_title = "IRDAI Document"
            
            # Strategy 1: Look for direct PDF download links with download=true in href
            # Priority 1: Find <a> tags with href containing download=true (best option)
            download_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'download=true')]")
            
            for link in download_links:
                try:
                    href = link.get_attribute("href")
                    
                    # Look for IRDAI PDF download links
                    if href and '.pdf' in href.lower() and 'irdai.gov.in/documents/' in href:
                        # Extract filename from URL for better text
                        filename_from_url = ""
                        try:
                            # Extract filename: /documents/37343/365561/Premium+Rates+for+Motor+Third+Party.pdf/uuid
                            # The .pdf part IS the filename, not the part before it
                            url_parts = href.split('/')
                            for part in url_parts:
                                if '.pdf' in part.lower():
                                    # Remove query parameters and get just the filename
                                    filename_from_url = part.split('?')[0].replace('+', ' ').replace('%20', ' ')
                                    break
                        except:
                            pass
                        
                        # Priority: link text → title attribute → filename from URL → page title → fallback
                        text = link.text.strip() or link.get_attribute("title") or filename_from_url or page_title or "IRDAI Document"
                        
                        absolute_url = urljoin(self.driver.current_url, href)
                        
                        # Ensure download=true parameter
                        if 'download=true' not in absolute_url:
                            if '?' in absolute_url:
                                absolute_url += '&download=true'
                            else:
                                absolute_url += '?download=true'
                        
                        if absolute_url not in self.processed_urls:
                            link_data = {
                                'element': link,
                                'url': absolute_url,
                                'text': text,
                                'parent_text': '',
                                'is_irdai_pdf': True
                            }
                            pdf_links.append(link_data)
                            logger.info(f"📥 Found IRDAI PDF: {text[:80]}...")
                
                except Exception as e:
                    logger.warning(f"Error extracting download link: {e}")
                    continue
            
            # Strategy 2: Fallback - Look for any PDF links if Strategy 1 found nothing
            if not pdf_links:
                logger.info("🔍 No download=true links found, checking all PDF links...")
                links = self.driver.find_elements(By.TAG_NAME, "a")
                
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        
                        # Look for direct PDF download links
                        if href and '.pdf' in href.lower():
                            # IRDAI pattern: /documents/{id1}/{id2}/{filename}.pdf/{uuid}?...&download=true
                            if 'irdai.gov.in/documents/' in href:
                                # Extract filename from URL as fallback
                                filename_from_url = ""
                                try:
                                    # Extract filename: /documents/37343/365561/Motor+Third+Party.pdf/uuid
                                    url_parts = href.split('/')
                                    for i, part in enumerate(url_parts):
                                        if '.pdf' in part.lower() and i > 0:
                                            filename_from_url = url_parts[i-1].replace('+', ' ').replace('%20', ' ')
                                            break
                                except:
                                    pass
                                
                                # Priority: link text → title attribute → filename from URL → page title → fallback
                                text = link.text.strip() or link.get_attribute("title") or filename_from_url or page_title or "IRDAI Document"
                                
                                absolute_url = urljoin(self.driver.current_url, href)
                                
                                # Ensure download=true parameter
                                if 'download=true' not in absolute_url:
                                    if '?' in absolute_url:
                                        absolute_url += '&download=true'
                                    else:
                                        absolute_url += '?download=true'
                                
                                if absolute_url not in self.processed_urls:
                                    link_data = {
                                        'element': link,
                                        'url': absolute_url,
                                        'text': text,
                                        'parent_text': '',
                                        'is_irdai_pdf': True
                                    }
                                    pdf_links.append(link_data)
                                    logger.info(f"📥 Found IRDAI PDF: {text[:80]}...")
                    
                    except Exception as e:
                        logger.warning(f"Error extracting PDF link (fallback): {e}")
                        continue
            
            # Strategy 3: Try to find and click download button if still no PDFs found (with retry limit)
            if not pdf_links and current_retry < max_click_retries:
                logger.info(f"🔍 No direct PDF links found, looking for download button (attempt {current_retry+1}/{max_click_retries})...")
                try:
                    # Look for download button/link
                    download_selectors = [
                        "//a[contains(@onclick, 'downloadAll')]",
                        "//a[contains(@title, 'Download')]",
                        "//label[contains(@class, 'label-download')]/..",
                        "//svg[contains(@class, 'lexicon-icon-download')]/../.."
                    ]
                    
                    for selector in download_selectors:
                        try:
                            download_elements = self.driver.find_elements(By.XPATH, selector)
                            if download_elements:
                                logger.info(f"✅ Found {len(download_elements)} download button(s)")
                                # Click the first download button
                                download_elements[0].click()
                                time.sleep(2)
                                # Recursive call with incremented retry counter
                                return self._extract_irdai_document_pdfs(max_click_retries, current_retry + 1)
                        except:
                            continue
                    
                except Exception as e:
                    logger.warning(f"Could not find/click download button: {e}")
            elif not pdf_links and current_retry >= max_click_retries:
                logger.warning(f"⚠️  No PDFs found after {max_click_retries} download button attempts")
            
            logger.info(f"✅ Extracted {len(pdf_links)} PDF links from IRDAI document page")
            return pdf_links
            
        except Exception as e:
            logger.error(f"Error extracting IRDAI PDFs: {e}")
            return []

    def is_motor_vehicle_related(self, text):
        """Check if text content is related to motor vehicle insurance"""
        text_lower = text.lower()
        
        # Check for motor vehicle insurance keywords
        for keyword in self.motor_keywords:
            if keyword.lower() in text_lower:
                return True
        
        # Additional patterns for motor vehicle insurance
        motor_patterns = [
            r'motor.*insurance',
            r'vehicle.*insurance', 
            r'third.*party.*liability',
            r'tp.*tariff',
            r'motor.*tariff',
            r'automobile.*insurance',
            r'vehicular.*coverage',
            r'compulsory.*insurance'
        ]
        
        for pattern in motor_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False

    def get_parent_text(self, element):
        """Get text from parent elements for date extraction"""
        try:
            parent = element.find_element(By.XPATH, "..")
            return parent.text.strip()
        except:
            return ""

    def sanitize_filename(self, filename):
        """Sanitize filename for filesystem compatibility"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:196] + ext
        
        return filename

    def extract_date_from_text(self, text):
        """Extract date from text using multiple patterns"""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return "N/A"

    def is_pdf_url(self, url):
        """Check if URL points to a PDF file"""
        return url.lower().endswith('.pdf') or 'pdf' in url.lower()

    def get_absolute_url(self, base_url, link):
        """Convert relative URLs to absolute URLs"""
        return urljoin(base_url, link)

    def validate_url(self, url):
        """Validate if URL is accessible"""
        try:
            response = self.make_request_with_retry(url, method='HEAD')
            return response.status_code == 200
        except Exception:
            return False

    def check_file_size(self, pdf_url):
        """Check file size before downloading"""
        try:
            response = self.make_request_with_retry(pdf_url, method='HEAD')
            content_length = response.headers.get('content-length')
            
            if content_length:
                file_size = int(content_length)
                if file_size > self.max_file_size:
                    logger.warning(f"Skipping large file ({file_size / 1024 / 1024:.1f}MB): {pdf_url}")
                    self.stats['skipped_large_files'] += 1
                    return False
                    
            return True
            
        except Exception as e:
            logger.warning(f"Could not check file size for {pdf_url}: {e}")
            return True  # Proceed if size check fails

    def download_pdf(self, pdf_url, filename):
        """Download PDF file to local directory with size checking"""
        try:
            # Check file size first
            if not self.check_file_size(pdf_url):
                return None
            
            response = self.make_request_with_retry(pdf_url, stream=True)
            
            # Sanitize filename
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
            
            downloaded_size = 0
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Check size during download
                        if downloaded_size > self.max_file_size:
                            logger.warning(f"File size exceeded limit during download: {pdf_url}")
                            local_path.unlink()  # Delete partial file
                            self.stats['skipped_large_files'] += 1
                            return None
            
            logger.info(f"Downloaded: {filename} ({downloaded_size / 1024:.1f}KB)")
            self.stats['new_pdfs_downloaded'] += 1
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Error downloading {pdf_url}: {e}")
            self.stats['failed_downloads'] += 1
            return None

    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF using pdfplumber with memory management"""
        try:
            text = ""
            page_count = 0
            max_pages = 100  # Limit pages to prevent memory issues
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = min(len(pdf.pages), max_pages)
                
                for i, page in enumerate(pdf.pages[:max_pages]):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        page_count += 1
                        
                        # Progress indicator for large files
                        if page_count % 20 == 0:
                            logger.info(f"Processed {page_count}/{total_pages} pages of {Path(file_path).name}")
                            
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {i} of {file_path}: {e}")
                        continue
            
            if page_count == max_pages and len(pdf.pages) > max_pages:
                logger.warning(f"Only extracted first {max_pages} pages from {file_path}")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            self.stats['text_extraction_failures'] += 1
            return ""

    def save_to_csv(self, data):
        """Save extracted data to CSV file with error handling and language detection"""
        try:
            # Detect language of extracted text
            text_language = self.detect_language(data['extracted_text'])
            
            # Also detect language of title for additional context
            title_language = self.detect_language(data['title'])
            
            # Use text language as primary, fall back to title language
            if text_language == "unknown" and title_language != "unknown":
                detected_language = title_language
            else:
                detected_language = text_language
            
            # Ensure text is not too long for CSV
            if len(data['extracted_text']) > 32767:  # Excel cell limit
                data['extracted_text'] = data['extracted_text'][:32760] + "..."
                logger.warning(f"Truncated extracted text for {data['title']}")
            
            # Check if document is motor vehicle related
            motor_relevance = "HIGH" if self.is_motor_vehicle_related(f"{data['title']} {data['extracted_text']}") else "LOW"
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['source'],
                    data['title'],
                    data['publication_date'],
                    data['pdf_url'],
                    data['local_path'],
                    data['extracted_text'],
                    detected_language,
                    motor_relevance
                ])
            
            logger.info(f"Saved motor vehicle document (relevance: {motor_relevance}) with language: {detected_language}")
            
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

    def get_dynamic_delay(self, site_name):
        """Get dynamic delay based on site and add randomization"""
        base_delays = {
            "IRDAI": 2,  # Government site, be more respectful
            "MoRTH": 2,  # Government site
            "GIC": 1     # Industry site
        }
        
        base_delay = base_delays.get(site_name, 1)
        # Add random variation (±50%)
        variation = random.uniform(0.5, 1.5)
        return base_delay * variation

    def scrape_site_with_selenium(self, site_name, url):
        """Generic site scraping method using Selenium"""
        try:
            logger.info(f"Scraping {site_name} with Selenium...")
            
            # Navigate to the page
            if not self.navigate_to_page(url):
                logger.error(f"Failed to load {site_name} page")
                return
            
            # Find PDF links
            pdf_links = self.find_pdf_links()
            
            logger.info(f"Found {len(pdf_links)} new PDF links for {site_name}")
            self.stats['total_pdfs_found'] += len(pdf_links)
            
            # Process each PDF link
            for i, link_data in enumerate(pdf_links, 1):
                logger.info(f"Processing {i}/{len(pdf_links)}: {site_name}")
                
                pdf_url = link_data['url']
                
                # Validate URL before processing
                if not self.validate_url(pdf_url):
                    logger.warning(f"Skipping inaccessible URL: {pdf_url}")
                    continue
                
                self.process_pdf_link_selenium(site_name, link_data)
                
                # Dynamic delay between requests
                delay = self.get_dynamic_delay(site_name)
                time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")
            self.stats['selenium_errors'] += 1

    def process_pdf_link_selenium(self, source, link_data):
        """Process a single PDF link with enhanced error handling"""
        try:
            pdf_url = link_data['url']
            title = link_data['text']
            parent_text = link_data['parent_text']
            
            if not title:
                title = Path(urlparse(pdf_url).path).name
            
            # Enhanced date extraction from both link text and parent text
            publication_date = "N/A"
            combined_text = f"{title} {parent_text}"
            extracted_date = self.extract_date_from_text(combined_text)
            if extracted_date != "N/A":
                publication_date = extracted_date
            
            # Generate unique filename
            base_filename = Path(urlparse(pdf_url).path).name
            if not base_filename:
                base_filename = f"document_{len(self.processed_urls) + 1}.pdf"
            
            filename = f"{source}_{datetime.now().strftime('%Y%m%d')}_{base_filename}"
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            # Download PDF
            local_path = self.download_pdf(pdf_url, filename)
            
            if local_path:
                # Extract text
                logger.info(f"Extracting text from {Path(local_path).name}")
                extracted_text = self.extract_text_from_pdf(local_path)
                
                # Prepare data for CSV
                data = {
                    'source': source,
                    'title': title,
                    'publication_date': publication_date,
                    'pdf_url': pdf_url,
                    'local_path': local_path,
                    'extracted_text': extracted_text
                }
                
                # Save to CSV
                self.save_to_csv(data)
                
                # Mark as processed
                self.mark_as_processed(pdf_url)
                
                logger.info(f"Successfully processed: {title}")
            
        except Exception as e:
            logger.error(f"Error processing PDF link {link_data['url']}: {e}")

    def scrape_irdai_motor(self):
        """Scrape IRDAI motor insurance circulars using Selenium"""
        self.scrape_site_with_selenium("IRDAI_MOTOR", self.sites["IRDAI_MOTOR"])
        # Also try specific motor insurance pages
        if "IRDAI_GUIDELINES" in self.sites:
            self.scrape_site_with_selenium("IRDAI_GUIDELINES", self.sites["IRDAI_GUIDELINES"])

    def scrape_morth_motor(self):
        """Scrape MoRTH motor vehicle insurance notifications using Selenium"""
        self.scrape_site_with_selenium("MoRTH_MOTOR", self.sites["MoRTH_MOTOR"])
        # Also try general MoRTH page
        self.scrape_site_with_selenium("MoRTH", self.sites["MoRTH"])

    def scrape_gic_motor(self):
        """Scrape General Insurance Council motor insurance circulars using Selenium"""
        self.scrape_site_with_selenium("GIC_MOTOR", self.sites["GIC_MOTOR"])
        # Also try general GIC page  
        self.scrape_site_with_selenium("GIC", self.sites["GIC"])

    def print_statistics(self):
        """Print scraping statistics"""
        logger.info("\n" + "="*50)
        logger.info("SCRAPING STATISTICS")
        logger.info("="*50)
        logger.info(f"Total PDF links found: {self.stats['total_pdfs_found']}")
        logger.info(f"New PDFs downloaded: {self.stats['new_pdfs_downloaded']}")
        logger.info(f"Large files skipped: {self.stats['skipped_large_files']}")
        logger.info(f"Failed downloads: {self.stats['failed_downloads']}")
        logger.info(f"Text extraction failures: {self.stats['text_extraction_failures']}")
        logger.info(f"Language detection failures: {self.stats['language_detection_failures']}")
        logger.info(f"Connection retries: {self.stats['connection_retries']}")
        logger.info(f"Selenium errors: {self.stats['selenium_errors']}")
        logger.info(f"Total URLs processed before: {len(self.processed_urls) - self.stats['new_pdfs_downloaded']}")
        logger.info("="*50)

    def cleanup(self):
        """Clean up resources with improved error handling"""
        errors = []
        
        # Close WebDriver
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                error_msg = f"Error closing WebDriver: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Close requests session
        if hasattr(self, 'session') and self.session:
            try:
                self.session.close()
                logger.info("Session closed successfully")
            except Exception as e:
                error_msg = f"Error closing session: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"Cleanup completed with {len(errors)} errors")
        else:
            logger.info("Cleanup completed successfully")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()

    def run(self):
        """Main execution function with improved error handling"""
        start_time = datetime.now()
        logger.info("Starting Motor Vehicle Insurance compliance document scraping with Selenium...")
        
        try:
            # Setup environment
            self.setup_environment()
            
            # Scrape each motor vehicle insurance focused site
            logger.info("🚗 Scraping IRDAI Motor Insurance regulations...")
            self.scrape_irdai_motor()
            
            logger.info("🚗 Scraping MoRTH Vehicle Insurance rules...")
            self.scrape_morth_motor()
            
            logger.info("🚗 Scraping GIC Motor Insurance guidelines...")
            self.scrape_gic_motor()
            
            # Print statistics
            self.print_statistics()
            
        except KeyboardInterrupt:
            logger.info("Motor Vehicle Insurance scraping interrupted by user")
        except Exception as e:
            logger.error(f"Critical error during motor vehicle insurance scraping: {e}")
        finally:
            # Cleanup resources
            self.cleanup()
            
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Motor Vehicle Insurance scraping completed in {duration}")

def main():
    """Main function with context manager"""
    try:
        with MotorVehicleComplianceDocumentScraper() as scraper:
            scraper.run()
    except Exception as e:
        logger.error(f"Failed to initialize motor vehicle compliance scraper: {e}")

if __name__ == "__main__":
    main()