import os
import html
import re

from werkzeug.utils import secure_filename
import textract
from pdfminer.high_level import extract_text
import requests
from bs4 import BeautifulSoup

from agents.virtual_assistant import VirtualAssistantAgent

def process_uploaded_file(file):
    """Extract text from uploaded file."""
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower()

    # Save file temporarily for processing
    temp_path = f"/tmp/{filename}"
    file.save(temp_path)

    if extension in {'doc', 'docx', 'pdf'}:
        try:
            text = textract.process(temp_path).decode("utf-8")
        except Exception:
            text = extract_text(temp_path)  # Fallback for PDFs
    elif extension == 'txt':
        with open(temp_path, 'r', encoding='utf-8') as f:
            text = f.read()

    os.remove(temp_path)  # Clean up temporary file
    return text

def process_link(link):
    """Handle link input to extract text."""

    if "linkedin" in link:
        return "Sorry, LinkedIn job descriptions not yet supported."
    response = requests.get(link)
    if 'Content-Type' in response.headers and response.headers['Content-Type'] == 'application/pdf':
        temp_path = "/tmp/temp.pdf"
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        text = extract_text(temp_path)
        os.remove(temp_path)
    elif 'Content-Type' in response.headers and response.headers['Content-Type'] == 'text/html':
        # Assume HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
    else:
        return "Please input a URL that leads to a valid job description"
    
    VA = VirtualAssistantAgent()
    job_description = VA.send_message("user", f"Please extract the job description from this webpage: \n {text}")
    return job_description


class TextCleaneriser:
    def __init__(self, text):

        self.clean_text = self.extract_readable_text(text)



    def remove_json_and_placeholders(self, text):
        # Regex patterns for malformed and valid JSON-like data
        json_like_pattern = r'({.*?}|[.*?]|\bnull\b|".*?")'  # Matches JSON-like objects, arrays, and "null" or quoted values
        placeholder_pattern = r'%[A-Z_]+%|{{.*?}}|\*'  # Matches %PLACEHOLDER%, {{ templates }}, or *
        malformed_json_pattern = r'[:,]\s*[^{}\[\],]*[:,}]'  # Matches malformed key-value pairs (e.g., `:,"key":`)

        # Remove JSON-like data
        text = re.sub(json_like_pattern, '', text)

        # Remove placeholders
        text = re.sub(placeholder_pattern, '', text)

        # Remove malformed JSON fragments
        # text = re.sub(malformed_json_pattern, '', text)

        # Clean up extra spaces or newlines from removal
        text = re.sub(r'\n\s*\n', '\n', text)  # Remove extra blank lines
        text = text.strip()  # Remove leading/trailing whitespace

        return text

    def remove_long_words(self, text, max_length=50):
        # Split the text by spaces into words
        words = text.split()
        # Filter out words longer than max_length
        filtered_words = [word for word in words if len(word) <= max_length]
        # Join the filtered words back into a string
        cleaned_text = ' '.join(filtered_words)
        return cleaned_text

    def extract_readable_text(self, html_content):
        html_content = html.unescape(html_content)
        # Parse the HTML content
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        
        # Get text
        text = soup.get_text(separator="\n")
        
        # Break into lines and remove leading/trailing whitespace
        lines = (line.strip() for line in text.splitlines())
        
        # Remove empty lines and join
        readable_text = "\n".join(line for line in lines if line)
        
        readable_text = self.remove_long_words(readable_text)
        readable_text = self.remove_json_and_placeholders(readable_text)
        return readable_text