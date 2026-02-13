import html.parser
import json
import os

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
        if tag == 'script':
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
        if tag == 'script':
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
        
        # Only add to clean_text if we are in main OR if main hasn't been found yet
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

def main():
    file_path = 'react.pagesource.js'
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by <!DOCTYPE html> if there are multiple documents
    # Although we saw only 1, it's safer to handle multiple if they exist.
    pages = []
    # Use regex to find start of HTML documents
    import re
    doc_starts = [m.start() for m in re.finditer(r'<!DOCTYPE html>', content, re.IGNORECASE)]
    
    if not doc_starts:
        # Maybe no doctype but has html tag?
        doc_starts = [m.start() for m in re.finditer(r'<html', content, re.IGNORECASE)]

    if not doc_starts:
        # Treat entire file as one page
        pages.append(content)
    else:
        for i in range(len(doc_starts)):
            start = doc_starts[i]
            end = doc_starts[i+1] if i+1 < len(doc_starts) else len(content)
            pages.append(content[start:end])

    results = []
    for page_content in pages:
        results.append(process_html(page_content))

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
