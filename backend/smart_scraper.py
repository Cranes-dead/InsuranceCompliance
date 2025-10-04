"""
Smart Motor Vehicle Compliance Document Scraper
Multi-stage filtering to download only relevant PDFs
Uses Legal-BERT for intelligent relevance classification
"""

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
from io import BytesIO
import PyPDF2
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import json

# Import base scraper for reuse
import sys
sys.path.append(str(Path(__file__).parent))
from scraper import MotorVehicleComplianceDocumentScraper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SmartMotorVehicleScraper(MotorVehicleComplianceDocumentScraper):
    """
    Enhanced scraper with multi-stage filtering:
    1. URL filtering
    2. Link text analysis
    3. PDF metadata extraction
    4. First-page BERT classification
    5. Full download (only if all checks pass)
    """
    
    def __init__(self, base_dir=None):
        # Use new directory for clean start
        if base_dir is None:
            base_dir = "D:/smart_motor_compliance_scraper"
        
        super().__init__(base_dir=base_dir)
        
        # Override paths for new structure
        self.base_dir = Path(base_dir)
        self.pdf_dir = self.base_dir / "relevant_pdfs"
        self.processed_urls_file = self.base_dir / "processed_urls.txt"
        self.csv_file = self.base_dir / "motor_vehicle_relevant_docs.csv"
        self.rejected_log = self.base_dir / "rejected_pdfs.json"
        self.stats_file = self.base_dir / "scraping_stats.json"
        
        # Filtering configuration
        self.config = {
            'thresholds': {
                'url_score': 10,           # Minimum URL relevance
                'link_score': 25,          # Minimum link text score (moderate)
                'metadata_confidence': 0.4, # Moderate metadata threshold
                'bert_confidence': 0.65,    # Moderate BERT confidence
                'first_page_min_length': 100  # Minimum text length
            },
            'enable_bert': True,  # Use GPU-accelerated BERT filtering
            'enable_metadata': True,
            'max_metadata_size': 100 * 1024,  # 100KB for metadata check
            'max_first_page_size': 500 * 1024,  # 500KB for first page
            'max_pages': 10,  # Maximum pages to scrape per paginated site
            'page_delay': 2  # Delay between pages (seconds)
        }
        
        # Blacklist terms (newsletters, notices, etc.)
        self.blacklist_terms = [
            'newsletter', 'annual report', 'quarterly report', 
            'election notice', 'election notification', 'electoral',
            'press release', 'media release', 'news bulletin',
            'advertisement', 'tender notice', 'recruitment',
            'vacancy', 'auction', 'rtf', 'rtt', 'rti',
            'health insurance', 'life insurance', 'fire insurance',
            'marine insurance', 'crop insurance', 'agriculture insurance'
        ]
        
        # Positive terms for moderate threshold (vehicle + general regulations)
        self.positive_terms = {
            # Primary (high weight)
            'primary': [
                'motor insurance', 'vehicle insurance', 'motor vehicle',
                'third party liability', 'motor tariff', 'tp insurance',
                'motor act', 'motor vehicle act', 'cmv act'
            ],
            # Secondary (medium weight)
            'secondary': [
                'motor', 'vehicle', 'automobile', 'auto insurance',
                'vehicular', 'third party', 'comprehensive insurance',
                'own damage', 'compulsory insurance'
            ],
            # Tertiary (low weight - general regulations)
            'tertiary': [
                'insurance regulation', 'compliance', 'coverage',
                'policy terms', 'insurance guidelines'
            ]
        }
        
        # Override parent's sites with paginated IRDAI search first
        self.sites = {
            # IRDAI Motor Insurance search (NEW - paginated, lots of results)
            "IRDAI_MOTOR_SEARCH": "https://irdai.gov.in/web/guest/search?q=motor&filterDepartment=NLF&archiveOn=true",
            
            # Original sites (fallback)
            **self.sites
        }
        
        # Load BERT model for relevance classification
        self.bert_model = None
        self.bert_tokenizer = None
        self.reference_embeddings = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        if self.config['enable_bert']:
            self._load_bert_model()
        
        # Enhanced statistics
        self.enhanced_stats = {
            'total_links_found': 0,
            'filtered_by_url': 0,
            'filtered_by_link_text': 0,
            'filtered_by_blacklist': 0,
            'filtered_by_metadata': 0,
            'filtered_by_bert': 0,
            'successfully_downloaded': 0,
            'stage_timings': {
                'url_filtering': 0,
                'link_filtering': 0,
                'metadata_check': 0,
                'bert_classification': 0,
                'download': 0
            }
        }
        
        # Rejected PDFs log (for analysis)
        self.rejected_pdfs = []
        
        logger.info(f"🚀 Smart Scraper initialized")
        logger.info(f"📁 Output directory: {self.base_dir}")
        logger.info(f"🎯 BERT model: {'Enabled' if self.bert_model else 'Disabled'}")
        logger.info(f"💻 Device: {self.device}")
    
    def _load_bert_model(self):
        """Load domain-adapted Legal-BERT for relevance classification"""
        try:
            model_path = Path(__file__).parent / "models" / "legal_bert_domain_adapted"
            
            if not model_path.exists():
                logger.warning(f"⚠️  BERT model not found at {model_path}")
                logger.warning("BERT filtering will be disabled")
                self.config['enable_bert'] = False
                return
            
            logger.info(f"Loading BERT model from {model_path}...")
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.bert_model = AutoModel.from_pretrained(model_path)
            self.bert_model.to(self.device)
            self.bert_model.eval()
            
            # Create reference embeddings for motor insurance
            self._create_reference_embeddings()
            
            logger.info(f"✅ BERT model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            self.config['enable_bert'] = False
    
    def _create_reference_embeddings(self):
        """Create reference embeddings for motor insurance documents"""
        # Reference texts for motor vehicle insurance
        reference_texts = [
            "Motor vehicle insurance third party liability coverage requirements under Motor Vehicles Act",
            "Third party insurance motor vehicle compulsory coverage policy terms conditions",
            "Motor insurance tariff premium rates third party liability own damage comprehensive",
            "Vehicle insurance compliance regulations IRDAI motor third party guidelines",
            "Motor vehicle act insurance provisions third party liability mandatory coverage"
        ]
        
        embeddings = []
        for text in reference_texts:
            embedding = self._get_bert_embedding(text)
            if embedding is not None:
                embeddings.append(embedding)
        
        if embeddings:
            self.reference_embeddings = np.mean(embeddings, axis=0)
            logger.info("✅ Reference embeddings created")
        else:
            logger.warning("⚠️  Failed to create reference embeddings")
    
    def _get_bert_embedding(self, text):
        """Get BERT embedding for text"""
        try:
            # Truncate to 512 tokens
            inputs = self.bert_tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                max_length=512,
                padding=True
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                # Mean pooling
                embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            
            return embedding
            
        except Exception as e:
            logger.warning(f"BERT embedding failed: {e}")
            return None
    
    def calculate_bert_relevance(self, text):
        """Calculate relevance score using BERT embeddings"""
        if not self.config['enable_bert'] or self.reference_embeddings is None:
            return 1.0  # Pass-through if BERT disabled
        
        try:
            text_embedding = self._get_bert_embedding(text)
            
            if text_embedding is None:
                return 0.5  # Neutral score on failure
            
            # Cosine similarity with reference
            similarity = cosine_similarity(
                text_embedding.reshape(1, -1),
                self.reference_embeddings.reshape(1, -1)
            )[0][0]
            
            # Convert to 0-1 range
            score = (similarity + 1) / 2
            
            return float(score)
            
        except Exception as e:
            logger.warning(f"BERT relevance calculation failed: {e}")
            return 0.5
    
    def score_url(self, url):
        """Score URL relevance (Stage 1)"""
        url_lower = url.lower()
        score = 0
        
        # Check for positive terms in URL
        for term in self.positive_terms['primary']:
            if term.replace(' ', '-') in url_lower or term.replace(' ', '_') in url_lower:
                score += 20
        
        for term in self.positive_terms['secondary']:
            if term in url_lower:
                score += 10
        
        # Check for blacklist terms
        for term in self.blacklist_terms:
            if term.replace(' ', '-') in url_lower:
                score -= 30
        
        return max(score, 0)
    
    def calculate_relevance_score(self, link_data):
        """Calculate relevance score from link text (Stage 2)"""
        text = f"{link_data['text']} {link_data['parent_text']}".lower()
        score = 0
        
        # Primary keywords (high value)
        for keyword in self.positive_terms['primary']:
            if keyword in text:
                score += 25
        
        # Secondary keywords (medium value)
        for keyword in self.positive_terms['secondary']:
            if keyword in text:
                score += 10
        
        # Tertiary keywords (low value)
        for keyword in self.positive_terms['tertiary']:
            if keyword in text:
                score += 5
        
        return min(score, 100)
    
    def is_blacklisted(self, text):
        """Check if text contains blacklisted terms"""
        text_lower = text.lower()
        
        for term in self.blacklist_terms:
            if term in text_lower:
                logger.info(f"🚫 Blacklisted term found: '{term}'")
                return True
        
        return False
    
    def check_pdf_metadata(self, pdf_url):
        """Check PDF metadata before full download (Stage 3)"""
        if not self.config['enable_metadata']:
            return True, {}
        
        try:
            start_time = time.time()
            
            # Download first chunk for metadata
            response = self.make_request_with_retry(pdf_url, stream=True)
            
            pdf_header = b''
            for chunk in response.iter_content(chunk_size=8192):
                pdf_header += chunk
                if len(pdf_header) >= self.config['max_metadata_size']:
                    break
            
            # Close connection
            response.close()
            
            # Extract metadata
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_header))
            metadata = pdf_reader.metadata or {}
            
            # Extract text content
            meta_text = ''
            if metadata:
                meta_text = ' '.join([
                    str(metadata.get('/Title', '')),
                    str(metadata.get('/Subject', '')),
                    str(metadata.get('/Keywords', '')),
                    str(metadata.get('/Author', ''))
                ])
            
            # Check blacklist
            if self.is_blacklisted(meta_text):
                elapsed = time.time() - start_time
                self.enhanced_stats['stage_timings']['metadata_check'] += elapsed
                return False, {'reason': 'blacklisted', 'metadata': meta_text}
            
            # Check relevance
            is_relevant = self.is_motor_vehicle_related(meta_text)
            
            elapsed = time.time() - start_time
            self.enhanced_stats['stage_timings']['metadata_check'] += elapsed
            
            return is_relevant, {'metadata': meta_text}
            
        except Exception as e:
            logger.warning(f"Metadata check failed: {e}")
            return True, {}  # Pass through on error
    
    def extract_first_page_text(self, pdf_url):
        """Extract first page text for BERT classification (Stage 4)"""
        try:
            start_time = time.time()
            
            # Download first chunk (usually covers first page)
            response = self.make_request_with_retry(pdf_url, stream=True)
            
            partial_pdf = b''
            for chunk in response.iter_content(chunk_size=8192):
                partial_pdf += chunk
                if len(partial_pdf) >= self.config['max_first_page_size']:
                    break
            
            response.close()
            
            # Extract first page
            with pdfplumber.open(BytesIO(partial_pdf)) as pdf:
                if len(pdf.pages) > 0:
                    text = pdf.pages[0].extract_text() or ''
                    
                    elapsed = time.time() - start_time
                    self.enhanced_stats['stage_timings']['bert_classification'] += elapsed
                    
                    return text
            
            return ''
            
        except Exception as e:
            logger.warning(f"First page extraction failed: {e}")
            return ''
    
    def smart_download_pipeline(self, link_data, page_context=''):
        """Multi-stage filtering pipeline"""
        
        url = link_data['url']
        title = link_data['text']
        
        self.enhanced_stats['total_links_found'] += 1
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 Evaluating: {title[:60]}...")
        logger.info(f"📎 URL: {url}")
        
        rejection_reason = None
        
        # STAGE 1: URL Filtering
        start_time = time.time()
        url_score = self.score_url(url)
        self.enhanced_stats['stage_timings']['url_filtering'] += time.time() - start_time
        
        if url_score < self.config['thresholds']['url_score']:
            rejection_reason = f"URL score too low ({url_score})"
            self.enhanced_stats['filtered_by_url'] += 1
            self._log_rejection(url, title, rejection_reason, stage=1)
            logger.info(f"❌ STAGE 1 REJECT: {rejection_reason}")
            return None
        
        logger.info(f"✅ Stage 1 passed: URL score = {url_score}")
        
        # STAGE 2: Link Text Analysis (adjusted threshold for IRDAI)
        start_time = time.time()
        link_score = self.calculate_relevance_score(link_data)
        self.enhanced_stats['stage_timings']['link_filtering'] += time.time() - start_time
        
        # Lower threshold for IRDAI documents (they have minimal link text but are pre-filtered)
        is_irdai_doc = link_data.get('is_irdai_pdf', False) or ('irdai.gov.in/documents/' in url)
        threshold = 15 if is_irdai_doc else self.config['thresholds']['link_score']
        
        if link_score < threshold:
            rejection_reason = f"Link score too low ({link_score}, threshold: {threshold})"
            self.enhanced_stats['filtered_by_link_text'] += 1
            self._log_rejection(url, title, rejection_reason, stage=2, extra={'link_score': link_score, 'threshold': threshold, 'is_irdai': is_irdai_doc})
            logger.info(f"❌ STAGE 2 REJECT: {rejection_reason}")
            return None
        
        logger.info(f"✅ Stage 2 passed: Link score = {link_score} (threshold: {threshold}{'[IRDAI]' if is_irdai_doc else ''})")
        
        # STAGE 2.5: Blacklist Check
        combined_text = f"{title} {link_data['parent_text']}"
        if self.is_blacklisted(combined_text):
            rejection_reason = "Blacklisted term detected"
            self.enhanced_stats['filtered_by_blacklist'] += 1
            self._log_rejection(url, title, rejection_reason, stage=2.5)
            logger.info(f"❌ STAGE 2.5 REJECT: {rejection_reason}")
            return None
        
        logger.info(f"✅ Stage 2.5 passed: No blacklist terms")
        
        # STAGE 3: PDF Metadata Check
        is_relevant, metadata_info = self.check_pdf_metadata(url)
        
        if not is_relevant:
            rejection_reason = f"Metadata check failed: {metadata_info.get('reason', 'not relevant')}"
            self.enhanced_stats['filtered_by_metadata'] += 1
            self._log_rejection(url, title, rejection_reason, stage=3, extra=metadata_info)
            logger.info(f"❌ STAGE 3 REJECT: {rejection_reason}")
            return None
        
        logger.info(f"✅ Stage 3 passed: Metadata relevant")
        
        # STAGE 4: First Page BERT Classification
        if self.config['enable_bert']:
            first_page_text = self.extract_first_page_text(url)
            
            if len(first_page_text) < self.config['thresholds']['first_page_min_length']:
                logger.warning(f"⚠️  First page text too short ({len(first_page_text)} chars)")
            else:
                # Check blacklist in first page
                if self.is_blacklisted(first_page_text):
                    rejection_reason = "Blacklist term in first page content"
                    self.enhanced_stats['filtered_by_blacklist'] += 1
                    self._log_rejection(url, title, rejection_reason, stage=4)
                    logger.info(f"❌ STAGE 4 REJECT: {rejection_reason}")
                    return None
                
                # BERT classification
                bert_score = self.calculate_bert_relevance(first_page_text)
                
                if bert_score < self.config['thresholds']['bert_confidence']:
                    rejection_reason = f"BERT confidence too low ({bert_score:.3f})"
                    self.enhanced_stats['filtered_by_bert'] += 1
                    self._log_rejection(url, title, rejection_reason, stage=4, extra={'bert_score': bert_score})
                    logger.info(f"❌ STAGE 4 REJECT: {rejection_reason}")
                    return None
                
                logger.info(f"✅ Stage 4 passed: BERT score = {bert_score:.3f}")
        else:
            logger.info(f"⏭️  Stage 4 skipped: BERT disabled")
        
        # STAGE 5: Full Download
        logger.info(f"🎉 ALL CHECKS PASSED - Downloading full PDF...")
        
        start_time = time.time()
        local_path = self.download_pdf(url, title)
        self.enhanced_stats['stage_timings']['download'] += time.time() - start_time
        
        if local_path:
            self.enhanced_stats['successfully_downloaded'] += 1
            logger.info(f"✅ Successfully downloaded: {Path(local_path).name}")
        else:
            logger.warning(f"⚠️  Download failed")
        
        return local_path
    
    def _log_rejection(self, url, title, reason, stage, extra=None):
        """Log rejected PDF for analysis"""
        self.rejected_pdfs.append({
            'url': url,
            'title': title,
            'reason': reason,
            'stage': stage,
            'timestamp': datetime.now().isoformat(),
            'extra': extra or {}
        })
    
    def detect_pagination_pattern(self, url):
        """Detect if URL is IRDAI paginated search and return pagination info"""
        # IRDAI pagination pattern
        if 'irdai.gov.in' in url.lower() and ('search?' in url or 'cur=' in url):
            return {
                'type': 'irdai_search',
                'base_url': url.split('&cur=')[0] if '&cur=' in url else url,
                'has_pagination': True
            }
        
        return {
            'type': 'standard',
            'has_pagination': False
        }
    
    def get_next_page_url(self, current_url, page_num):
        """Generate next page URL based on pagination pattern"""
        if '&cur=' in current_url:
            # Replace existing page number
            return re.sub(r'&cur=\d+', f'&cur={page_num}', current_url)
        else:
            # Add page number parameter
            if 'irdai.gov.in' in current_url:
                if 'p_p_id=' not in current_url:
                    # First page format - convert to paginated format
                    base_url = "https://irdai.gov.in/search?p_p_id=com_irdai_custom_search_results_CustomSearchResultsPortlet_INSTANCE_QtdSmUnYs3ko&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view"
                    params = current_url.split('?')[1] if '?' in current_url else ''
                    return f"{base_url}&{params}&delta=20&resetCur=false&cur={page_num}"
                else:
                    return f"{current_url}&cur={page_num}"
            separator = '&' if '?' in current_url else '?'
            return f"{current_url}{separator}page={page_num}"
    
    def scrape_site_with_smart_filtering(self, site_name, url):
        """Override parent method to use smart filtering with pagination support"""
        try:
            logger.info(f"\n{'#'*80}")
            logger.info(f"# Scraping {site_name}")
            logger.info(f"# URL: {url}")
            logger.info(f"{'#'*80}\n")
            
            # Detect pagination
            pagination_info = self.detect_pagination_pattern(url)
            
            if pagination_info['has_pagination']:
                logger.info(f"📄 Detected paginated site ({pagination_info['type']})")
                logger.info(f"🔄 Will scrape up to {self.config.get('max_pages', 10)} pages")
                
                # Scrape multiple pages
                for page_num in range(1, self.config.get('max_pages', 10) + 1):
                    if page_num == 1:
                        page_url = url
                    else:
                        page_url = self.get_next_page_url(pagination_info['base_url'], page_num)
                    
                    logger.info(f"\n{'='*80}")
                    logger.info(f"📄 PAGE {page_num}/{self.config.get('max_pages', 10)}")
                    logger.info(f"🔗 {page_url}")
                    logger.info(f"{'='*80}\n")
                    
                    # Scrape single page
                    found_pdfs = self._scrape_single_page(site_name, page_url)
                    
                    # If no PDFs found, might be end of results
                    if found_pdfs == 0 and page_num > 1:
                        logger.info(f"⏹️  No PDFs found on page {page_num}, stopping pagination")
                        break
                    
                    # Delay between pages
                    if page_num < self.config.get('max_pages', 10):
                        delay = 2
                        logger.info(f"⏳ Waiting {delay}s before next page...")
                        time.sleep(delay)
            else:
                # Single page scraping
                self._scrape_single_page(site_name, url)
            
            logger.info(f"\n✅ Completed scraping {site_name}")
            self._print_progress_stats()
            
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")
    
    def _scrape_single_page(self, site_name, url):
        """Scrape a single page with smart filtering"""
        try:
            # Navigate to page
            if not self.navigate_to_page(url):
                return 0
            
            # Find PDF links (or document-detail links for IRDAI)
            pdf_links = self.find_pdf_links()
            
            if not pdf_links:
                logger.warning(f"No PDF links found on this page")
                return 0
            
            logger.info(f"📊 Found {len(pdf_links)} links to evaluate")
            
            # Check if these are IRDAI document-detail links (need to navigate to each)
            if pdf_links and pdf_links[0].get('is_irdai_document', False):
                logger.info(f"🔍 Processing IRDAI document-detail links...")
                return self._process_irdai_document_links(site_name, pdf_links)
            
            # Process each PDF with smart filtering
            for i, link_data in enumerate(pdf_links, 1):
                logger.info(f"\n[{i}/{len(pdf_links)}] Processing PDF...")
                
                # Skip if already processed
                if link_data['url'] in self.processed_urls:
                    logger.info(f"⏭️  Already processed: {link_data['text'][:50]}")
                    continue
                
                # Smart download pipeline
                local_path = self.smart_download_pipeline(link_data)
                
                # Mark as processed regardless of outcome
                self.mark_as_processed(link_data['url'])
                
                # If downloaded, extract and save
                if local_path:
                    text = self.extract_text_from_pdf(local_path)
                    
                    data = {
                        'source': site_name,
                        'title': link_data['text'] or Path(local_path).stem,
                        'publication_date': self.extract_date_from_text(link_data['parent_text']),
                        'pdf_url': link_data['url'],
                        'local_path': local_path,
                        'extracted_text': text
                    }
                    
                    self.save_to_csv(data)
                
                # Delay between requests
                delay = self.get_dynamic_delay(site_name)
                time.sleep(delay)
            
            return len(pdf_links)
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return 0
    
    def _process_irdai_document_links(self, site_name, document_links):
        """Process IRDAI document-detail links by navigating to each and extracting PDFs"""
        total_pdfs_found = 0
        
        try:
            for i, doc_link in enumerate(document_links, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"📄 IRDAI Document {i}/{len(document_links)}")
                logger.info(f"🔗 {doc_link['url']}")
                logger.info(f"📝 {doc_link['text'][:80]}")
                logger.info(f"{'='*80}")
                
                # Skip if already processed
                if doc_link['url'] in self.processed_urls:
                    logger.info(f"⏭️  Already processed")
                    continue
                
                # Mark document link as processed
                self.mark_as_processed(doc_link['url'])
                
                # Navigate to document-detail page
                if not self.navigate_to_page(doc_link['url']):
                    logger.warning(f"⚠️  Failed to load document page")
                    continue
                
                # Extract PDF links from document page
                pdf_links = self.find_pdf_links()
                
                if not pdf_links:
                    logger.warning(f"⚠️  No PDF links found on document page")
                    continue
                
                logger.info(f"✅ Found {len(pdf_links)} PDF(s) on document page")
                
                # Process each PDF with smart filtering
                for j, pdf_link in enumerate(pdf_links, 1):
                    logger.info(f"\n  📥 PDF {j}/{len(pdf_links)}: {pdf_link['text'][:60]}...")
                    
                    # Use document title if PDF has no text
                    if not pdf_link['text']:
                        pdf_link['text'] = doc_link['text']
                    
                    # Skip if already processed
                    if pdf_link['url'] in self.processed_urls:
                        logger.info(f"  ⏭️  Already processed")
                        continue
                    
                    # Evaluate with smart pipeline
                    logger.info(f"\n{'='*80}")
                    logger.info(f"🔍 Evaluating: {pdf_link['text'][:60]}...")
                    logger.info(f"📎 URL: {pdf_link['url'][:100]}...")
                    
                    # Smart download pipeline
                    local_path = self.smart_download_pipeline(pdf_link)
                    
                    # Mark as processed
                    self.mark_as_processed(pdf_link['url'])
                    
                    # If downloaded, extract and save
                    if local_path:
                        text = self.extract_text_from_pdf(local_path)
                        
                        data = {
                            'source': site_name,
                            'title': pdf_link['text'] or Path(local_path).stem,
                            'publication_date': self.extract_date_from_text(pdf_link.get('parent_text', '')),
                            'pdf_url': pdf_link['url'],
                            'local_path': local_path,
                            'extracted_text': text
                        }
                        
                        self.save_to_csv(data)
                        total_pdfs_found += 1
                    
                    # Delay between PDFs
                    delay = self.get_dynamic_delay(site_name)
                    time.sleep(delay)
                
                # Delay between document pages
                time.sleep(2)
            
            return total_pdfs_found
            
        except Exception as e:
            logger.error(f"Error processing IRDAI document links: {e}")
            return total_pdfs_found
    
    def _print_progress_stats(self):
        """Print progress statistics"""
        total = self.enhanced_stats['total_links_found']
        downloaded = self.enhanced_stats['successfully_downloaded']
        
        if total == 0:
            return
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 PROGRESS STATISTICS")
        logger.info(f"{'='*80}")
        logger.info(f"Total links evaluated: {total}")
        logger.info(f"✅ Successfully downloaded: {downloaded} ({downloaded/total*100:.1f}%)")
        logger.info(f"❌ Filtered by URL: {self.enhanced_stats['filtered_by_url']} ({self.enhanced_stats['filtered_by_url']/total*100:.1f}%)")
        logger.info(f"❌ Filtered by link text: {self.enhanced_stats['filtered_by_link_text']} ({self.enhanced_stats['filtered_by_link_text']/total*100:.1f}%)")
        logger.info(f"❌ Filtered by blacklist: {self.enhanced_stats['filtered_by_blacklist']} ({self.enhanced_stats['filtered_by_blacklist']/total*100:.1f}%)")
        logger.info(f"❌ Filtered by metadata: {self.enhanced_stats['filtered_by_metadata']} ({self.enhanced_stats['filtered_by_metadata']/total*100:.1f}%)")
        logger.info(f"❌ Filtered by BERT: {self.enhanced_stats['filtered_by_bert']} ({self.enhanced_stats['filtered_by_bert']/total*100:.1f}%)")
        logger.info(f"{'='*80}\n")
    
    def save_final_stats(self):
        """Save final statistics and rejected PDFs log"""
        try:
            # Save stats
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.enhanced_stats, f, indent=2)
            
            logger.info(f"📊 Stats saved to: {self.stats_file}")
            
            # Save rejected PDFs
            with open(self.rejected_log, 'w', encoding='utf-8') as f:
                json.dump(self.rejected_pdfs, f, indent=2)
            
            logger.info(f"📝 Rejected PDFs log saved to: {self.rejected_log}")
            
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def run(self):
        """Main execution method"""
        try:
            logger.info("\n" + "="*80)
            logger.info("🚀 SMART MOTOR VEHICLE COMPLIANCE SCRAPER")
            logger.info("="*80 + "\n")
            
            # Setup environment
            self.setup_environment()
            
            # Scrape each site
            for site_name, site_url in self.sites.items():
                self.scrape_site_with_smart_filtering(site_name, site_url)
            
            # Final statistics
            logger.info("\n" + "="*80)
            logger.info("🎉 SCRAPING COMPLETED")
            logger.info("="*80 + "\n")
            
            self._print_progress_stats()
            
            # Print timing breakdown
            logger.info("⏱️  TIMING BREAKDOWN:")
            for stage, time_spent in self.enhanced_stats['stage_timings'].items():
                logger.info(f"  {stage}: {time_spent:.2f}s")
            
            # Save final stats
            self.save_final_stats()
            
        except KeyboardInterrupt:
            logger.info("\n⚠️  Scraping interrupted by user")
            self.save_final_stats()
        
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.save_final_stats()
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔒 WebDriver closed")


def main():
    """Run the smart scraper"""
    scraper = SmartMotorVehicleScraper()
    scraper.run()


if __name__ == "__main__":
    main()
