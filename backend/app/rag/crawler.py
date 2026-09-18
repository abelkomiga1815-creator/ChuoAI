# backend/app/rag/crawler.py
"""Web crawler for official Tanzanian higher education sources."""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import asyncio
import aiohttp
import hashlib
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from datetime import datetime

from ..core.config import settings
from ..models.academic_year import IngestionJob

logger = logging.getLogger(__name__)

@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    content_hash: str
    links: List[str]
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class BaseCrawler:
    """Base crawler with common functionality."""
    
    def __init__(self, job: IngestionJob, db_session):
        self.job = job
        self.db = db_session
        self.session: Optional[aiohttp.ClientSession] = None
        self.visited: Set[str] = set()
        self.content_hashes: Dict[str, str] = {}  # url -> hash
        
        # Rate limiting
        self.request_delay = 2.0  # seconds between requests
        self.max_concurrent = 3
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # Allowed domains for this crawler
        self.allowed_domains: List[str] = []
        self.start_urls: List[str] = []
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={
                "User-Agent": "ChuoAI Bot/1.0 (+https://chuo-ai.vercel.app; educational research)"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL domain is allowed."""
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.allowed_domains)
    
    def _normalize_url(self, url: str, base: str) -> str:
        """Normalize URL."""
        return urljoin(base, url)
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML."""
        # Remove scripts, styles, nav, footer
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from page."""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = self._normalize_url(href, base_url)
            if self._is_allowed_domain(full_url):
                links.append(full_url)
        return list(set(links))
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from page."""
        metadata = {
            "url": url,
            "crawled_at": datetime.utcnow().isoformat(),
        }
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_ = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name in ['description', 'keywords', 'author']:
                metadata[name] = content
            elif property_ in ['og:title', 'og:description', 'og:type']:
                metadata[property_.replace(':', '_')] = content
        
        return metadata
    
    async def _fetch_page(self, url: str) -> CrawlResult:
        """Fetch and parse a single page."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return CrawlResult(
                        url=url, title="", content="", content_hash="",
                        links=[], metadata={}, success=False,
                        error=f"HTTP {response.status}"
                    )
                
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type:
                    return CrawlResult(
                        url=url, title="", content="", content_hash="",
                        links=[], metadata={}, success=False,
                        error=f"Non-HTML content: {content_type}"
                    )
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                title = metadata.get("title", "") if (metadata := self._extract_metadata(soup, url)) else ""
                text = self._extract_text(soup)
                links = self._extract_links(soup, url)
                metadata = self._extract_metadata(soup, url)
                content_hash = self._compute_hash(text)
                
                return CrawlResult(
                    url=url,
                    title=title,
                    content=text,
                    content_hash=content_hash,
                    links=links,
                    metadata=metadata,
                    success=True
                )
                
        except asyncio.TimeoutError:
            return CrawlResult(url=url, title="", content="", content_hash="", links=[], metadata={}, success=False, error="Timeout")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return CrawlResult(url=url, title="", content="", content_hash="", links=[], metadata={}, success=False, error=str(e))
    
    async def crawl(self, max_pages: int = 100) -> List[CrawlResult]:
        """Crawl starting URLs."""
        results = []
        queue = list(self.start_urls)
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def crawl_with_semaphore(url: str) -> Optional[CrawlResult]:
            async with semaphore:
                if url in self.visited:
                    return None
                self.visited.add(url)
                
                # Rate limiting
                await asyncio.sleep(self.request_delay)
                
                result = await self._fetch_page(url)
                
                if result.success and result.content:
                    # Add new links to queue
                    for link in result.links:
                        if link not in self.visited and len(self.visited) < max_pages:
                            queue.append(link)
                
                return result
        
        while queue and len(self.visited) < max_pages:
            # Process batch
            batch = queue[:self.max_concurrent]
            queue = queue[self.max_concurrent:]
            
            tasks = [crawl_with_semaphore(url) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, CrawlResult) and result.success:
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Crawl task failed: {result}")
        
        return results


class TCUCrawler(BaseCrawler):
    """Crawler for TCU official website."""
    
    def __init__(self, job: IngestionJob, db_session):
        super().__init__(job, db_session)
        self.allowed_domains = ["tcu.go.tz", "www.tcu.go.tz"]
        self.start_urls = [
            "https://www.tcu.go.tz/",
            "https://www.tcu.go.tz/universities",
            "https://www.tcu.go.tz/accreditation",
            "https://www.tcu.go.tz/admissions",
        ]
        self.request_delay = 3.0  # Be respectful to TCU servers
    
    async def crawl(self, max_pages: int = 50) -> List[CrawlResult]:
        """Crawl TCU site with specialized parsing."""
        results = await super().crawl(max_pages)
        
        # Post-process for TCU-specific data
        for result in results:
            result.metadata["source_type"] = "TCU_OFFICIAL"
            result.metadata["authority_level"] = "LEVEL_1"
            
            # Try to extract university/programme info
            self._extract_tcu_entities(result)
            
            # Extract TCU statistics from page
            self._extract_tcu_statistics(result)
        
        return results
    
    def _extract_tcu_entities(self, result: CrawlResult):
        """Extract TCU-specific entities from content."""
        content = result.content.lower()
        
        # Look for university names
        uni_keywords = ['university', 'vyuo', 'chuo', 'institution']
        if any(kw in content for kw in uni_keywords):
            result.metadata["likely_contains_universities"] = True
        
        # Look for programme keywords
        prog_keywords = ['programme', 'course', 'degree', 'diploma', 'certificate']
        if any(kw in content for kw in prog_keywords):
            result.metadata["likely_contains_programmes"] = True
    
    def _extract_tcu_statistics(self, result: CrawlResult):
        """Extract TCU statistics from page content."""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(result.content, 'html.parser') if '<' in result.content[:100] else None
        text = result.content
        text_lower = text.lower()
        
        # Current academic year for context
        from datetime import datetime
        current_year = datetime.now().year
        if datetime.now().month >= 9:
            academic_year = f"{current_year}/{current_year + 1}"
        else:
            academic_year = f"{current_year - 1}/{current_year}"
        
        statistics_found = []
        
        # Pattern 1: Look for explicit counts in text
        # Pattern: "X university institutions" or "X universities"
        uni_institution_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*university\s+institutions?',
            r'(\d{1,3}(?:,\d{3})*)\s*universities',
            r'(\d{1,3}(?:,\d{3})*)\s*accredited\s+universities',
            r'(\d{1,3}(?:,\d{3})*)\s*registered\s+universities',
            r'total\s+(?:of\s+)?(\d{1,3}(?:,\d{3})*)\s+universit',
        ]
        
        for pattern in uni_institution_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    value = int(match.replace(',', ''))
                    if 1 <= value <= 1000:  # Reasonable range
                        statistics_found.append({
                            "statistic_type": "UNIVERSITY_INSTITUTIONS",
                            "metric_name": "university_institutions",
                            "value": value,
                            "unit": "count",
                            "source_section": "page_text",
                            "academic_year": academic_year,
                        })
                        break
                except ValueError:
                    continue
        
        # Pattern 2: Look for programme counts
        programme_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*academic\s+programmes?',
            r'(\d{1,3}(?:,\d{3})*)\s*programmes?',
            r'(\d{1,3}(?:,\d{3})*)\s*degree\s+programmes?',
            r'total\s+(?:of\s+)?(\d{1,3}(?:,\d{3})*)\s+programmes?',
        ]
        
        for pattern in programme_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    value = int(match.replace(',', ''))
                    if 1 <= value <= 10000:  # Reasonable range
                        statistics_found.append({
                            "statistic_type": "ACADEMIC_PROGRAMMES",
                            "metric_name": "academic_programmes",
                            "value": value,
                            "unit": "count",
                            "source_section": "page_text",
                            "academic_year": academic_year,
                        })
                        break
                except ValueError:
                    continue
        
        # Pattern 3: Look for tables with statistics
        if soup:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    cell_texts = [cell.get_text(strip=True).lower() for cell in cells]
                    
                    # Check if row contains university institution count
                    row_text = ' '.join(cell_texts)
                    if any(keyword in row_text for keyword in ['university institution', 'university count', 'total university']):
                        for cell_text in cell_texts:
                            numbers = re.findall(r'\d{1,3}(?:,\d{3})*', cell_text)
                            for num_str in numbers:
                                try:
                                    value = int(num_str.replace(',', ''))
                                    if 1 <= value <= 1000:
                                        statistics_found.append({
                                            "statistic_type": "UNIVERSITY_INSTITUTIONS",
                                            "metric_name": "university_institutions",
                                            "value": value,
                                            "unit": "count",
                                            "source_section": "table",
                                            "academic_year": academic_year,
                                        })
                                        break
                                except ValueError:
                                    continue
                    
                    # Check for programme count
                    if any(keyword in row_text for keyword in ['academic programme', 'programme count', 'total programme']):
                        for cell_text in cell_texts:
                            numbers = re.findall(r'\d{1,3}(?:,\d{3})*', cell_text)
                            for num_str in numbers:
                                try:
                                    value = int(num_str.replace(',', ''))
                                    if 1 <= value <= 10000:
                                        statistics_found.append({
                                            "statistic_type": "ACADEMIC_PROGRAMMES",
                                            "metric_name": "academic_programmes",
                                            "value": value,
                                            "unit": "count",
                                            "source_section": "table",
                                            "academic_year": academic_year,
                                        })
                                        break
                                except ValueError:
                                    continue
        
        # Store statistics in metadata for ingestion pipeline
        if statistics_found:
            result.metadata["tcu_statistics"] = statistics_found
            logger.info(f"Extracted {len(statistics_found)} TCU statistics from {result.url}")


class UniversityCrawler(BaseCrawler):
    """Crawler for individual university websites."""
    
    def __init__(self, job: IngestionJob, db_session, university_website: str):
        super().__init__(job, db_session)
        parsed = urlparse(university_website)
        self.allowed_domains = [parsed.netloc]
        self.start_urls = [university_website]
        self.request_delay = 2.0
    
    async def crawl(self, max_pages: int = 100) -> List[CrawlResult]:
        """Crawl university site."""
        results = await super().crawl(max_pages)
        
        for result in results:
            result.metadata["source_type"] = "UNIVERSITY_OFFICIAL"
            result.metadata["authority_level"] = "LEVEL_2"
        
        return results


class PDFDownloader:
    """Download and process PDF documents."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={"User-Agent": "ChuoAI Bot/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def download_pdf(self, url: str) -> Optional[Dict[str, Any]]:
        """Download PDF and extract text."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                content = await response.read()
                content_hash = hashlib.sha256(content).hexdigest()
                
                # Save to temp file for processing
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                    f.write(content)
                    temp_path = f.name
                
                try:
                    # Extract text using PyPDF2
                    import PyPDF2
                    text_parts = []
                    with open(temp_path, 'rb') as pf:
                        reader = PyPDF2.PdfReader(pf)
                        for page_num, page in enumerate(reader.pages):
                            text = page.extract_text()
                            if text:
                                text_parts.append(f"[Page {page_num + 1}]\n{text}")
                    
                    full_text = "\n\n".join(text_parts)
                    
                    return {
                        "content": full_text,
                        "content_hash": content_hash,
                        "page_count": len(reader.pages),
                        "file_size": len(content),
                        "metadata": {
                            "source_url": url,
                            "downloaded_at": datetime.utcnow().isoformat(),
                            "file_type": "PDF"
                        }
                    }
                finally:
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Failed to download/process PDF {url}: {e}")
            return None