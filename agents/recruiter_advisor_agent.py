import json
from pathlib import Path 
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

# if __name__ == '__main__':
#     from openai_context import ChatGPTContextManager
# else:
#     from .openai_context import ChatGPTContextManager

from .openai_context import ChatGPTContextManager


from openai import OpenAI

 
class Message(Model):
    message: str
 
RECIPIENT_ADDRESS = "agent1qvwum0ystzx7djjh09lw529yajk7rznnvlutfrmv44v445hsp5x3zxr9f8x"


class AdvisorAgent(ChatGPTContextManager):
    def __init__(self, 
                 job_description, 
                 cv,
                 most_important_skills,
                 recruiter_appraisal_data
                 ):
        super().__init__()
        self.interviewing_agent_address = ''
        self.cv = cv
        self.job_description = job_description
        self.most_important_skills = most_important_skills
        self.recruiter_appraisal_data = recruiter_appraisal_data


        self.initial_content = f"""You are a professional recruiter, specialised in giving advice to candidates.
            You want to help this candidate hone their CV and do the best they can to get the job they're looking for.
            However, you're honest and you don't ever fool the candidate into applying for a job that they can't get.
            You offer advice for how to improve the CV, but for roles that are too different from the candidate's skillset,
            or too advanced for the candidate's experience, you are not afraid to tell them that it might be better to look elsewhere.
            For your reference, here is the job description: {job_description}.

            You will also receieve some data from another recruiter who has reviewed the job description, identified the top
            5 skills for this job, and has appraised this CV for how well it matches the job.

            Your task here is to provide advice for the candidate on how to improve their CV.

            Some ideas for the kinds of advice that you can provide are:
            - The candidate should better represent their existing experience by rewriting their experience to focus on 
            the skills listed
            - The candidate should consider if they need to do a training course or certification to imrpove their CV
            - The candidate might consider to do a personal project to improve their CV in a specific area

            But don't limit yourself to just these kinds of advice.

            All you need to do now is acknowledge this message, I'll ask you for your assessment later.
            
            """
        
        # Initilse the searcher
        _ = self.send_message('system', self.initial_content)
        self.skill_advice_response_format = self._generate_skill_advice_response_format()
        


    def advise_candidate(self):
        message = self.send_message(
            'user', f"""Here is the recruiter's opinion of what are the top 5 
            skills for this job:\n {self.most_important_skills}\n

            Here is the recruiter's assessment of the candidate's CV: \n {self.recruiter_appraisal_data}\n

            And here is the candidate's CV: \n {self.cv}

            For each of the skills listed, please can you provide information to the candidate as to how
            they can improve the way they demonstrate knowledge/experience of these skills. If the skill score is very
            high then you can also say that no improvement is needed.""",
            response_format = self.skill_advice_response_format)
        message_json = json.loads(message)
        return message_json



    @classmethod
    def create_from_jd_and_cv_dir(cls, jd_file_path, cv_dir):
        with open(jd_file_path, 'r', encoding='utf-8') as file:
            job_content = file.read()

        return cls(job_content, cv_dir)
    


    def _generate_skill_advice_response_format(self):
        # Create dynamic properties for each skill's score
        properties = {}
        required_fields = ["skills"]  # Include 'name' in the required fields
        
        skill_properties = {}
        skill_required = []
        
        # Loop through the list of skills and create dynamic keys
        for i, skill in enumerate(self.most_important_skills, 1):
            
            skill_advice = f'{skill}_ADVICE'
            skill_properties[skill_advice] = {
                "type": "string",
                "description": f"Advice for how the candidate can improve their CV with regards to this specific skill"
            }
            skill_required.append(skill_advice)

        properties['skills'] = {
            'type': 'object',
            'description': "The list of skills and associated data",
            'properties': skill_properties,
            'required': skill_required,
            "additionalProperties": False
        }

        # Return the dynamic response_format
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "cv_advice_response",
                "schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required_fields,
                    "additionalProperties": False
                },
                "strict": True
            }
        }

