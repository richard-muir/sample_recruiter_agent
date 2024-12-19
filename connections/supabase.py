import re
import os
import html
import requests
from dotenv import load_dotenv
import json
from bs4 import BeautifulSoup



class SupabaseConnection:
    def __init__(self):
        load_dotenv()
        self.URL = os.getenv('SUPABASE_URL') # put project_url here
        self.API_KEY = os.getenv('SUPABASE_API_KEY') # put credential here

        self.active_jobs_endpoint = f'{self.URL}/rest/v1/active_jobs' # you will only receive the urls, which are still active
        self.headers = {
            'apikey': self.API_KEY,
            'Authorization': f'Bearer {self.API_KEY}',
            'Accept-Profile': 'api'
        }

    def get_all_jobs(self):
        # params = {
        #     'limit': -1
        # }
        
        response = requests.get(self.active_jobs_endpoint, headers=self.headers)
        return json.loads(response.text)
        

class GithubConnection:
    def __init__(self):
        load_dotenv()
        self.TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')

        self.owner = 'Bitvocation'
        self.repo = 'data'


    def get_job_description(self, jd_path):
        resp = requests.get(
            'https://api.github.com/repos/{owner}/{repo}/contents/{path}'.format(
            owner=self.owner, repo=self.repo, path=jd_path),
            headers={
                'accept': 'application/vnd.github.v3.raw',
                'authorization': 'token {}'.format(self.TOKEN)
                    }
            )
        return JobDescriptionExtractor(resp.text).job_description



class JobDescriptionExtractor:
    def __init__(self, text):

        self.job_description = self.extract_readable_text(text)



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