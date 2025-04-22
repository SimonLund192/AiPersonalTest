import json  # ensure JSON is available before any use
import os
import requests
from bs4 import BeautifulSoup

from seo_scorer import SEOScorer

class WebScraper:
    """
    A simple web scraper to fetch product descriptions from competitor pages and score them using SEOScorer.
    Exclusing the keyword metric.
    """
    def __init__(self, headers=None, timeout=10):
        self.headers = headers or {"User-Agent": "Mozilla/5.0 (compatible)"}
        self.timeout = timeout
        self.scorer = SEOScorer()

    def fetch(self, url):
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def extract_description(self, html, selector):
        soup = BeautifulSoup(html, "html.parser")
        element = soup.select_one(selector)
        return element.get_text(separator=" ", strip=True) if element else ""

    def scrape_and_score(self, url, selector, keywords=None, all_descriptions=None):
        """
        Fetches the HTML, extracts the text via the CSS selector, then scores readability,
        length, structure and uniqueness - bt not keyword usage.
        """
        html = self.fetch(url)
        description = self.extract_description(html, selector)

        if not description:
            return {"url": url, "description": "", "score_data": None}
        
        # Pass an empty keyword list so calculate_keyword_score() = 0
        score_data = self.scorer.score_description(
            text=description, 
            keywords=[], 
            all_descriptions=all_descriptions or []
            )
        
        # Remove the keyword_score entry from the detailed breakdown
        score_data["detailed_scores"].pop("keyword_score", None)

        return {
            "url": url, 
            "description": description, 
            "score_data": score_data}

    def batch_scrape(self, url_selector_list, keywords=None, all_descriptions=None):
        """
        url_selector_list: list of (url, css_selector) tuples
        """
        results = []
        for url, selector in url_selector_list:
            try:
                results.append(self.scrape_and_score(url, selector, keywords, all_descriptions))
            except Exception as e:
                print(f"Error scraping {url}: {e}")
        return results

if __name__ == "__main__":
    # Prompt user for URL and CSS selector
    url = input("Enter the product page URL to scrape: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        exit(1)

    raw_selector = input(
        "Enter the CSS selector for the product description (e.g. div.description-block or div[lang=\"da-x-mtfrom-en\"]): "
    ).strip()
    # Automatically strip surrounding quotes if provided
    selector = raw_selector.strip('"').strip("'")
    if not selector:
        print("No CSS selector provided. Exiting.")
        exit(1)

    print(f"Scraping '{url}' using selector '{selector}'...")
    scraper = WebScraper()
    try:
        result = scraper.scrape_and_score(url, selector)
        # Ensure ExtractedData directory exists
        output_dir = os.path.join(os.getcwd(), 'ExtractedData')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'scraped_description.json')
        # Save scraped result to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Scraped data saved to {output_file}")
    except Exception as e:
        print(f"Error during scraping: {e}")


# Example Integration in description_generator.py
# ----------------------------------------------
# from web_scraper import WebScraper
#
# # Before generating your own descriptions, scrape competitor ones:
# scraper = WebScraper()
# # Suppose your products DataFrame has a 'CompetitorURL' column and you know the CSS selector:
# urls = [(row['CompetitorURL'], 'div.product-description') for _, row in products_df.iterrows() if row.get('CompetitorURL')]
# competitor_results = scraper.batch_scrape(urls, keywords, [d['generated_description'] for d in results])
#
# # You can inspect competitor_results for insights or include their descriptions in your all_descriptions pool
# for comp in competitor_results:
#     print(f"URL: {comp['url']} -> Score: {comp['score_data']['overall_score'] if comp['score_data'] else 'n/a'}")
