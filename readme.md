# Compliance Document Scraper

A robust web scraping tool for gathering motor insurance compliance documents from Indian regulatory websites using Selenium WebDriver.
It should also work for text on the website as well and not only to download pdfs and extract text from the pdf

## Features

- **Multi-source scraping**: IRDAI, MoRTH, and GIC websites
- **Language detection**: Automatic detection of Hindi and English documents
- **Selenium-based**: Handles dynamic content and JavaScript-heavy sites
- **Dual browser support**: Chrome with Firefox fallback
- **Robust error handling**: Retry mechanisms and graceful degradation
- **File size management**: Configurable limits and validation
- **Duplicate prevention**: Tracks processed URLs to avoid re-downloads
- **UTF-8 support**: Proper handling of Hindi Devanagari script

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Chrome browser (recommended) or Firefox as fallback

3. The script will automatically download the appropriate WebDriver

## Usage

### Basic Usage
```python
from scraper import ComplianceDocumentScraper

# Use default directory (D:/compliance_scraper)
scraper = ComplianceDocumentScraper()
scraper.run()
```

### Custom Directory
all data should be stored in the D drive

### Context Manager (Recommended)
```python
# Automatic resource cleanup
with ComplianceDocumentScraper() as scraper:
    scraper.run()
```

## Output

The scraper creates:
- `scraped_pdfs/`: Downloaded PDF files
- `compliance_documents.csv`: Extracted data with columns:
  - source, title, publication_date, pdf_url, local_path, extracted_text, language
- `processed_urls.txt`: List of processed URLs to prevent duplicates

## Configuration

### File Size Limits
Default: 50MB per file. Modify in constructor:
```python
scraper.max_file_size = 100 * 1024 * 1024  # 100MB
```

### Site Delays
Configurable delays between requests (respectful scraping):
- IRDAI: 2 seconds (government site)
- MoRTH: 2 seconds (government site)  
- GIC: 1 second (industry site)

### Browser Options
The scraper tries Chrome first, then Firefox:
- Headless mode for background operation
- Windows compatibility optimizations
- SSL certificate bypass for government sites
- Memory and performance optimizations

## Error Handling

- **Network errors**: Exponential backoff retry (3 attempts)
- **WebDriver failures**: Automatic browser fallback
- **Large files**: Size validation before download
- **Memory management**: Limited page processing for large PDFs
- **Resource cleanup**: Automatic driver and session closure

## Logging

Comprehensive logging to console with timestamps:
- INFO: Progress updates and successful operations
- WARNING: Non-critical issues and retries
- ERROR: Failed operations with error details

## Troubleshooting

### Chrome Driver Issues
If Chrome fails to start:
1. Ensure Chrome browser is installed
2. Check Windows compatibility (script handles common issues)
3. Firefox will automatically be used as fallback

### Memory Issues
For large-scale scraping:
1. Monitor system memory usage
2. Adjust `max_pages` limit in PDF text extraction
3. Consider processing sites individually

### Network Issues
For government site connectivity:
1. Check internet connection
2. Verify site accessibility in browser
3. Script includes SSL bypass for government certificates

## Statistics

The scraper tracks and reports:
- Total PDF links found
- New PDFs downloaded
- Large files skipped
- Failed downloads
- Text extraction failures
- Language detection failures
- Connection retries
- Selenium errors

## Legal Compliance

- Respects robots.txt when accessible
- Implements respectful delays between requests
- Only scrapes publicly available documents
- Designed for compliance research purposes

## Requirements

- Python 3.7+
- Chrome or Firefox browser
- Windows/Linux/Mac compatibility
- Internet connection for initial driver download
