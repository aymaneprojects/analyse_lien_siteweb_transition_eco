import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

def fetch_page_content(url):
    """
    Fetches and parses the content of a single page.
    Simulates a real browser using headers to bypass potential scraping blocks.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.RequestException as e:
        print(f"Erreur réseau lors de la récupération de {url} : {e}")
        return None

def extract_text_from_page(soup):
    """
    Extracts text content (titles, paragraphs, lists) from a BeautifulSoup object.
    """
    content = []
    if not soup:
        return content

    for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
        text = tag.get_text(strip=True)
        if text:
            if tag.name.startswith('h'):
                content.append(f"{tag.name.upper()}: {text}\n")
            else:
                content.append(f"{text}\n")
    return content

def extract_page_title(soup, url):
    """
    Extract the title of a web page. If the title is not available, use the URL.
    """
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        return title_tag.string.strip()
    return url

def crawl_website(base_url, max_pages=20):
    """
    Crawls the website and collects content and titles from all reachable pages.
    """
    visited_urls = set()
    pages_to_visit = [base_url]
    scraped_data = {}
    page_titles = []

    while pages_to_visit and len(visited_urls) < max_pages:
        current_url = pages_to_visit.pop(0)

        # Skip already visited URLs
        if current_url in visited_urls:
            continue

        print(f"Scraping: {current_url}")
        soup = fetch_page_content(current_url)

        if soup:
            # Extract page content and title
            page_content = extract_text_from_page(soup)
            page_title = extract_page_title(soup, current_url)
            page_titles.append(page_title)

            if page_content:
                scraped_data[current_url] = page_content

            # Add new internal links to the queue
            for link in soup.find_all('a', href=True):
                full_url = urljoin(base_url, link['href'])

                if is_internal_link(base_url, full_url) and full_url not in visited_urls:
                    # Avoid duplicates in the queue
                    if full_url not in pages_to_visit:
                        pages_to_visit.append(full_url)

        visited_urls.add(current_url)

        # Optional delay to avoid overwhelming the server
        time.sleep(0.5)

    return scraped_data, page_titles

def is_internal_link(base_url, url):
    """
    Checks if a link is internal to the base website.
    """
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(url).netloc
    return base_domain == link_domain