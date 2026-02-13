import html.parser
import json
import os
import sys

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
    input_dir = 'pagesource'
    output_dir = 'data.json'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define range or specific files to process
    if len(sys.argv) > 1:
        files_to_process = sys.argv[1:]
    else:
        # Default to processing link11-link20 if no args provided
        files_to_process = [f'link{i:02d}.js' for i in range(11, 21)]
    
    for filename in files_to_process:
        input_path = os.path.join(input_dir, filename)
        output_filename = filename.replace('.js', '.json')
        output_path = os.path.join(output_dir, output_filename)
        
        if not os.path.exists(input_path):
            print(f"Skipping {input_path}, file not found.")
            continue

        print(f"Processing {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        result = process_html(content)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([result], f, indent=4)
        print(f"Created {output_path}")

if __name__ == "__main__":
    main()
