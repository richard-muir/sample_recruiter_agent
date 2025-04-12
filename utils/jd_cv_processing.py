import os
import html
import re
import uuid

from werkzeug.utils import secure_filename
import textract
from pdfminer.high_level import extract_text as pdfminer_extract_text
import requests
from bs4 import BeautifulSoup

from agents.virtual_assistant import VirtualAssistantAgent

def process_file(file, filename=None):
    """
    Extract text from either an uploaded file or fetched PDF content.
    
    :param file: Either an uploaded file-like object or binary content of a fetched file.
    :param filename: (Optional) Filename if processing fetched content.
    :return: Extracted text from the file.
    """
    if hasattr(file, "filename"):  # Uploaded file-like object
        filename = secure_filename(file.filename)
        file_content = file.read()
    elif isinstance(file, bytes) and filename:  # Fetched binary content
        filename = secure_filename(filename)
        file_content = file
    else:
        raise ValueError("Invalid input. Provide an uploaded file or binary content with a filename.")

    # Determine file extension
    extension = filename.rsplit('.', 1)[-1].lower()

    # Generate a unique temporary file path
    unique_filename = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join("/tmp", unique_filename)

    try:
        # Save the binary content to a temporary file
        with open(temp_path, 'wb') as f:
            f.write(file_content)

        # Process the file based on its extension
        if extension in {'doc', 'docx', 'pdf'}:
            try:
                text = textract.process(temp_path).decode("utf-8")
            except Exception:
                if extension == 'pdf':
                    # Fallback for PDFs using pdfminer
                    text = pdfminer_extract_text(temp_path)
                else:
                    raise ValueError("Error processing document.")
        elif extension == 'txt':
            with open(temp_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return text



def fetch_pdf_content_from_link(url):
    """
    Validate the URL and fetch the PDF file content if valid.
    Raises ValueError if the link does not point to a valid PDF file.
    """
    try:
        # Fetch the URL with a GET request to download the content
        response = requests.get(url, allow_redirects=True, timeout=10)

        # Check if the Content-Type is a PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type != 'application/pdf':
            raise ValueError("The provided link does not point to a valid PDF file.")

        pdf_content = response.content
        filename = url.split('/')[-1]  # Extract filename from URL
        text = process_file(pdf_content, filename=filename)
        # Return the content of the PDF
        return text
    except requests.RequestException as e:
        raise ValueError(f"Error validating or fetching the PDF: {e}")


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
        text = text.replace('{', '').replace('}', '')
        text = ' '.join(text.split()) # Remove extra whitlespaces

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