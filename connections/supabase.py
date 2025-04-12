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
        self.all_jobs = []
        self.all_jobs = self.get_all_jobs()
        self.allowed_fields = self.all_jobs[0].keys()
        

    def get_all_jobs(self):
        if not self.all_jobs:
            response = requests.get(self.active_jobs_endpoint, headers=self.headers)
            self.all_jobs = json.loads(response.text)

        return self.all_jobs
    
    def refresh_jobs(self):
        self.all_jobs = self.get_all_jobs()

    
    def get_job_by_field_value(self, field, value):
        if field not in self.allowed_fields:
            raise ValueError('Invalid field')
        else:
            selected_job = list([item for item in self.all_jobs if item.get(field) == value])[0]
            return selected_job
            
        