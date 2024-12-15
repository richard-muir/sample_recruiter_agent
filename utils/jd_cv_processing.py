import os

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
    print(99999999999999999999999999999)
    print(text)
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
    print(1111111111111111111111111111111111111)
    print(job_description)
    return job_description