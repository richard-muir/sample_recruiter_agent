import json
from pathlib import Path 
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

# if __name__ == '__main__':
#     from openai_context import ChatGPTContextManager
# else:
#     from .openai_context import ChatGPTContextManager

from openai_context import ChatGPTContextManager


from openai import OpenAI

 
class Message(Model):
    message: str
 
RECIPIENT_ADDRESS = "agent1qvwum0ystzx7djjh09lw529yajk7rznnvlutfrmv44v445hsp5x3zxr9f8x"


class CVWriterAgent(ChatGPTContextManager):
    def __init__(self, 
                 job_description, 
                 cv,
                 most_important_skills,
                 ):
        super().__init__()
        self.cv = cv
        self.job_description = job_description
        self.most_important_skills = most_important_skills

        self.response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "profile_data",
                "schema": {
                "type": "object",
                "properties": {
                    "name": {
                    "type": "string"
                    },
                    "job_title": {
                    "type": "string"
                    },
                    "contact": {
                    "type": "object",
                    "properties": {
                        "email": {
                        "type": "string"
                        },
                        "phone": {
                        "type": "string"
                        },
                        "website": {
                        "type": "string"
                        }
                    },
                    "required": ["email", "phone", "website"],
                    "additionalProperties": False
                    },
                    "skills": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                    },
                    "jobs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "title": {
                            "type": "string"
                        },
                        "dates": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        }
                        },
                        "required": ["title", "dates", "description"],
                        "additionalProperties": False
                    }
                    },
                    "education": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "qualification": {
                            "type": "string"
                        },
                        "institution": {
                            "type": "string"
                        },
                        "dates": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        }
                        },
                        "required": ["qualification", "institution", "dates", "description"],
                        "additionalProperties": False
                    }
                    }
                },
                "required": ["name", "job_title", "contact", "skills", "jobs", "education"],
                "additionalProperties": False
                },
                "strict": True
            }
            }



        self.initial_content = f"""You are a professional recruiter, specialised in writing CVs to match the most important key skills in a job description.
            You want to help this candidate to write their CV in the best possible way by aligning it perfectly 
            to the job description. However, you won't invent information.

            For your reference, here is the job description: {job_description}.

            And here are the key skills: {most_important_skills}.

            Later, you will recieve the candiate's CV, and your task will be to rewrite it to a specific format to
            match the job description as best as possible. Candidate may also have provided additional information
            about their skills and experience, appended to the CV.

            All you need to do now is acknowledge this message, I'll ask you for your assessment later.
            
            """
        
        # Initilse the searcher
        _ = self.send_message('system', self.initial_content)
        
        
    def write_cv(self):
        message = self.send_message('user', f"""Your task is to rewrite the candidate's CV to match a given job description without inventing any information.
                                    Do not invent any information. Simply rewrite the existing CV to match the job description as best as possible.

                                    Here is the candidate's CV: {self.cv}

                                    You need to extract the following information points from the cv:
                                    - candidate name
                                    - email address
                                    - portfolio website (often github)
                                    - telephone number

                                    For each of the candidate's three most significant jobs, you need to get their:
                                    - Job title
                                    - Company name
                                    - Dates of employment
                                    - Description of duties, with key words

                                    You should also extract up to 6 skills, and record each with up to three words.

                                    For each of the candidate's three most significant education/certifications, you need to get their
                                    - certification name
                                    - The instution name
                                    - The dates they attended
                                    - The skills they learnt

                                    Please respond with the candidate's updated CV in the following format:""",
                                    response_format=self.response_format)
        
        message_json = json.loads(message)
        return message_json



    @classmethod
    def create_from_jd_and_cv_dir(cls, jd_file_path, cv_dir):
        with open(jd_file_path, 'r', encoding='utf-8') as file:
            job_content = file.read()

        return cls(job_content, cv_dir)
    

