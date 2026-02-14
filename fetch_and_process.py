import os
import json
import re
import html.parser
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

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
        if tag in ['script', 'style', 'header', 'aside', 'footer', 'nav']:
            self.in_script = True
        elif tag == 'main' or (tag == 'div' and any(attr[0] == 'role' and attr[1] == 'main' for attr in attrs)):
            self.in_main = True
            self.main_depth = self.depth
            self.main_found = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style', 'header', 'aside', 'footer', 'nav']:
            self.in_script = False
        elif tag == 'main' or (self.in_main and self.depth == self.main_depth):
            self.in_main = False
        self.depth -= 1
        self.current_tag = ""

    def handle_data(self, data):
        if self.in_script:
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

# --- Browser Logic ---

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
    urls = [
        "https://aws.amazon.com/what-is/saas/",
        "https://en.wikipedia.org/wiki/Software_as_a_service",
        "https://www.teamtweaks.com/blog/saas-companies-in-india/",
        "https://www.naukri.com/saas-software-jobs",
        "https://azure.microsoft.com/en-in/resources/cloud-computing-dictionary/what-is-saas",
        "https://razorpay.com/blog/saas-india/",
        "https://www.ambitionbox.com/profile/saas-developer-salary",
        "https://saasboomi.org/india-saas-unicorn-tracker/",
        "https://yourstory.com/saas-india",
        "https://nasscom.in/knowledge-center/publications/india-saas-report-2026"
    ]

    source_dir = 'pagesource'
    data_dir = 'data.json'

    if not os.path.exists(source_dir): os.makedirs(source_dir)
    if not os.path.exists(data_dir): os.makedirs(data_dir)

    start_index = get_next_index(data_dir)
    stealth_applier = Stealth()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        
        for i, url in enumerate(urls, start=start_index):
            file_base = f"link{i:02d}"
            try:
                print(f"Fetching: {url}...")
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                stealth_applier.apply_stealth_sync(page)

                try:
                    response = page.goto(url, wait_until="load", timeout=90000)
                    if not response or response.status >= 400:
                        status = response.status if response else "No Response"
                        print(f"  [!] Received status {status}. skipping.")
                        context.close()
                        continue

                    time.sleep(5)
                    html_content = page.content()
                    source_path = os.path.join(source_dir, f"{file_base}.js")
                    with open(source_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)

                    structured_data = process_html(html_content)
                    json_path = os.path.join(data_dir, f"{file_base}.json")
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump([structured_data], f, indent=4)
                    
                    print(f"  Success: Saved processed data to {json_path}")
                    if os.path.exists(source_path): os.remove(source_path)

                except Exception as e:
                    print(f"  Error processing {url}: {e}")
                
                context.close()
                time.sleep(random.uniform(5, 10))

            except Exception as e:
                print(f"  Context error for {url}: {e}")

        browser.close()

if __name__ == "__main__":
    main()


# not working properly