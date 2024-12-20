import os
import requests
from dotenv import load_dotenv
import json



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