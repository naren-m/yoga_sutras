import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re

BASE_URL = "https://shlokam.org/yogasutra"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

OUTPUT_FILE = "data/yoga_sutras.json"

class YogaSutraScraper:
    def __init__(self):
        self.data = {
            "slug": "yoga-sutras",
            "title": "Yoga Sutras of Patanjali",
            "description": "The foundational text of Yoga philosophy.",
            "sections": []
        }
        self.padas = [
            {"slug": "samadhi-pada", "title": "Samadhi Pada", "order": 1, "count": 51},
            {"slug": "sadhana-pada", "title": "Sadhana Pada", "order": 2, "count": 55},
            {"slug": "vibhuti-pada", "title": "Vibhuti Pada", "order": 3, "count": 56},
            {"slug": "kaivalya-pada", "title": "Kaivalya Pada", "order": 4, "count": 34}
        ]

    def fetch_url(self, url):
        try:
            print(f"Fetching {url}...")
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def scrape(self):
        for pada in self.padas:
            section_data = {
                "slug": pada["slug"],
                "title": pada["title"],
                "order": pada["order"],
                "blocks": []
            }
            
            print(f"Scraping {pada['title']}...")
            
            for i in range(1, pada["count"] + 1):
                sutra_slug = f"{pada['order']}-{i}"
                url = f"{BASE_URL}/{sutra_slug}/" # URL pattern: https://shlokam.org/yogasutra/1-1/
                
                html = self.fetch_url(url)
                if not html:
                    continue

                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract Content
                # Note: Selectors might need adjustment based on actual page structure.
                # Assuming standard shlokam.org structure based on common WP themes or similar sites.
                
                # Try to find Sanskrit (Devanagari)
                sanskrit_elem = soup.find('div', class_='entry-content') # fallback
                # Heuristic: look for Devanagari block or specific classes if known?
                # On shlokam.org/yogasutra/1-1 :
                # Often in a blockquote or specific div.
                
                content = ""
                transliteration = ""
                meaning = ""
                
                # Refined extraction logic based on typical content
                main_content = soup.find('main', id='main') or soup.find('div', class_='entry-content')
                
                if main_content:
                    texts = main_content.get_text(separator="\n").split("\n")
                    # This is rough; a real robust scraper needs precise selectors.
                    # For now, we store the raw text or try to identify parts.
                    # Let's try to grab the first Devanagari text as content.
                    
                    # Better approach: Look for specific elements often used.
                    # Usually: <p><strong>...sanskrit...</strong></p>
                    pass
                
                # Since I can't inspect interactively, I'll save a raw dump fields for now
                # and refining later if needed, or rely on a simpler structure if found.
                # Let's try to extract minimally useful info to prove the concept.
                
                block_data = {
                    "slug": f"{pada['order']}.{i}",
                    "order": i,
                    "content": "To be extracted", # Placeholder if scraping fails
                    "transliteration": "",
                    "meaning": "",
                    "url": url
                }
                
                # Basic parsing attempt
                if main_content:
                   # Simplistic extraction
                   block_data["content"] = main_content.get_text().strip()[:100] + "..." # Truncate for now

                section_data["blocks"].append(block_data)
                time.sleep(1) # Be polite

            self.data["sections"].append(section_data)

    def save(self):
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Saved data to {OUTPUT_FILE}")

if __name__ == "__main__":
    scraper = YogaSutraScraper()
    scraper.scrape()
    scraper.save()
