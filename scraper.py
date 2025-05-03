from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter

from config import CHUNK_SIZE, CHUNK_OVERLAP
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    # Remove extra newlines and whitespace
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common unwanted patterns
    text = re.sub(r'\[.*?\]', '', text)  # Remove [something]
    text = re.sub(r'\b\d+\b', '', text)  # Remove standalone numbers
    return text


def get_all_links(url: str, domain: str) -> List[str]:
    """Get all links from a page that belong to the same domain"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()

        for link in soup.find_all('a', href=True):
            href = link['href']
            # Handle relative URLs
            full_url = urljoin(url, href)
            # Filter for same-domain links
            if urlparse(full_url).netloc == domain:
                links.add(full_url)

        return list(links)
    except Exception as e:
        logger.error(f"Error getting links from {url}: {str(e)}")
        return []


def scrape_website(url: str, max_pages: int = 2) -> List[dict]:
    """
    Scrape all pages of a website with improved content cleaning
    Args:
        url: The starting URL to scrape
        max_pages: Maximum number of pages to scrape (default: 10)
    Returns:
        List of cleaned documents with metadata
    """
    try:
        # Validate and parse URL
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")

        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        base_url = f"{parsed_url.scheme}://{domain}"

        # Get all pages to scrape
        all_pages = get_all_links(url, domain)
        if url not in all_pages:
            all_pages.append(url)

        # Limit number of pages to scrape
        pages_to_scrape = all_pages[:max_pages]
        logger.info(f"Found {len(all_pages)} pages. Scraping {len(pages_to_scrape)} pages.")

        # Scrape each page
        documents = []
        for page_url in pages_to_scrape:
            try:
                loader = WebBaseLoader(page_url)
                docs = loader.load()

                for doc in docs:
                    # Clean the content
                    # cleaned_content = clean_text(doc.page_content)
                    cleaned_content = doc.page_content



                    # Add metadata
                    doc.page_content = cleaned_content
                    doc.metadata['source'] = page_url
                    doc.metadata['domain'] = domain
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Error scraping {page_url}: {str(e)}")
                continue

        if not documents:
            raise ValueError("No valid content found on any pages")

        # Split the content into chunks
        text_splitter = CharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        splits = text_splitter.split_documents(documents)

        logger.info(f"Successfully scraped {len(splits)} chunks from {len(pages_to_scrape)} pages")
        return splits

    except Exception as e:
        logger.error(f"Error scraping website: {str(e)}")
        raise