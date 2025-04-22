import json
import os
import requests
from bs4 import BeautifulSoup
from readability import Document

from seo_scorer import SEOScorer

class WebScraper:
    """
    A simple web scraper to fetch product descriptions from competitor pages and
    score them using SEOScorer—excluding the keyword metric.
    Uses readability-lxml to automatically extract the main content block.
    """
    def __init__(self, headers=None, timeout=10):
        self.headers = headers or {"User-Agent": "Mozilla/5.0 (compatible)"}
        self.timeout = timeout
        self.scorer = SEOScorer()

    def fetch(self, url):
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def extract_description(self, html):
        # Use readability to isolate main content
        doc = Document(html)
        main_html = doc.summary()
        soup = BeautifulSoup(main_html, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    def scrape_and_score(self, url, all_descriptions=None):
        """
        Fetches the HTML, extracts the main content block via readability,
        then scores readability, length, structure, and uniqueness—but not keywords.
        Returns both raw and adjusted overall scores.
        """
        html = self.fetch(url)
        description = self.extract_description(html)

        if not description:
            return {"url": url, "description": "", "score_data": None}

        # Score without keyword usage (Keyword score still impacts the overall score)
        score_data = self.scorer.score_description(
            text=description,
            keywords=[],  # disable keyword metric
            all_descriptions=all_descriptions or []
        )

        # Normalize out the keyword weight so the other metrics fill to 100%
        kw_weight = self.scorer.keyword_weight
        if (1 - kw_weight) > 0:
            adjusted = round(score_data["overall_score"] / (1 - kw_weight), 2)
        else:
            adjusted = score_data["overall_score"]
        score_data["adjusted_overall_score"] = adjusted

        # Remove keyword score from details
        score_data["detailed_scores"].pop("keyword_score", None)

        return {
            "url": url, 
            "description": description, 
            "score_data": score_data}

if __name__ == "__main__":
    url = input("Enter the product page URL to scrape: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        exit(1)

    print(f"Scraping '{url}' and extracting main content...")
    scraper = WebScraper()
    try:
        result = scraper.scrape_and_score(url)

        # Ensure ExtractedData directory exists
        output_dir = os.path.join(os.getcwd(), 'ExtractedData')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'scraped_description.json')

        # Save scraped result
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Scraped data saved to {output_file}")
        if result["score_data"]:
            print("SEO Score (excluding keywords):", result["score_data"]["overall_score"])
    except Exception as e:
        print(f"Error during scraping: {e}")