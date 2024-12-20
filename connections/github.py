import os
import requests
from dotenv import load_dotenv


from utils import TextCleaneriser

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
        return TextCleaneriser(resp.text).clean_text