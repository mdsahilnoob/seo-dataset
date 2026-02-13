import os
import json
import re
import html.parser
import requests
from urllib.parse import urlparse

# --- SEO Parser Logic ---
class SEOParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_nav = False
        self.in_footer = False
        self.in_main = False
        self.main_depth = 0
        self.current_tag = ""
        self.clean_text_parts = []
        self.h1_list = []
        self.h2_list = []
        self.h3_list = []
        self.depth = 0
        self.main_found = False

    def handle_starttag(self, tag, attrs):
        self.depth += 1
        self.current_tag = tag
        if tag == 'script' or tag == 'style':
            self.in_script = True
        elif tag == 'nav':
            self.in_nav = True
        elif tag == 'footer':
            self.in_footer = True
        elif tag == 'main' or (tag == 'div' and any(attr[0] == 'role' and attr[1] == 'main' for attr in attrs)):
            self.in_main = True
            self.main_depth = self.depth
            self.main_found = True

    def handle_endtag(self, tag):
        if tag == 'script' or tag == 'style':
            self.in_script = False
        elif tag == 'nav':
            self.in_nav = False
        elif tag == 'footer':
            self.in_footer = False
        elif tag == 'main' or (self.in_main and self.depth == self.main_depth):
            self.in_main = False
        self.depth -= 1
        self.current_tag = ""

    def handle_data(self, data):
        if self.in_script or self.in_nav or self.in_footer:
            return
        
        text = data.strip()
        if not text:
            return

        if self.current_tag == 'h1':
            self.h1_list.append(text)
        elif self.current_tag == 'h2':
            self.h2_list.append(text)
        elif self.current_tag == 'h3':
            self.h3_list.append(text)
        
        if self.in_main or not self.main_found:
            # Simple space normalization
            self.clean_text_parts.append(text)

def process_html(html_content):
    parser = SEOParser()
    parser.feed(html_content)
    
    return {
        "clean_text": " ".join(parser.clean_text_parts),
        "h1_list": parser.h1_list,
        "h2_list": parser.h2_list,
        "h3_list": parser.h3_list
    }

# --- Main Execution Logic ---

def get_next_index(data_dir):
    max_idx = 0
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            match = re.match(r'link(\d+)\.json', filename)
            if match:
                idx = int(match.group(1))
                if idx > max_idx:
                    max_idx = idx
    return max_idx + 1

def main():
    # Put your 10 links here
    urls = [
        "https://en.wikipedia.org/wiki/JavaScript",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Language_overview",
        "https://www.w3schools.com/js/",
        "https://www.geeksforgeeks.org/javascript-introduction-to-javascript/",
        "https://www.naukri.com/javascript-jobs",
        "https://roadmap.sh/javascript",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "https://www.ambitionbox.com/profile/javascript-developer-salary",
        "https://nodejs.org/",
        "https://www.npmjs.com/"
    ]

    source_dir = 'pagesource'
    data_dir = 'data.json'

    for d in [source_dir, data_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    start_index = get_next_index(data_dir)
    print(f"Starting numbering from: link{start_index:02d}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for i, url in enumerate(urls, start=start_index):
        try:
            print(f"Fetching: {url}...")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html_content = response.text

            # Generate filename base (e.g., link21, link22...)
            file_base = f"link{i:02d}"
            
            # 1. Save raw source to /pagesource folder
            source_path = os.path.join(source_dir, f"{file_base}.js")
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"  Saved raw source to {source_path}")

            # 2. Process and convert to structured JSON
            structured_data = process_html(html_content)
            
            # 3. Save to /data.json folder
            json_path = os.path.join(data_dir, f"{file_base}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([structured_data], f, indent=4)
            print(f"  Saved processed data to {json_path}")

        except Exception as e:
            print(f"  Error processing {url}: {e}")

if __name__ == "__main__":
    main()


[
  "https://en.wikipedia.org/wiki/JavaScript",
  "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Language_overview",
  "https://www.w3schools.com/js/",
  "https://www.geeksforgeeks.org/javascript-introduction-to-javascript/",
  "https://www.naukri.com/javascript-jobs",
  "https://roadmap.sh/javascript",
  "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
  "https://www.ambitionbox.com/profile/javascript-developer-salary",
  "https://nodejs.org/",
  "https://www.npmjs.com/"
]
