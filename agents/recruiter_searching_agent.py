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


class SearchingAgent(ChatGPTContextManager):
    def __init__(self, 
                 job_description, 
                 cvs, 
                 n_candidates=3, 
                 min_suitability_score=8, 
                 suitability_threshold=0.7,
                 most_important_skills='auto'):
        super().__init__()
        self.interviewing_agent_address = ''
        self.cvs = cvs
        self.min_suitability_score = min_suitability_score
        self.suitability_threshold = suitability_threshold
        # self.cvs = []

        self.candidates = []
        self.selected_canidates = []

        # self.searching_agent = Agent(
        #     name="searcher",
        #     port=8002,
        #     seed="jumps over the lazy dog",
        #     endpoint=["http://127.0.0.1:8002/submit"],
        # )
        # fund_agent_if_low(self.searching_agent.wallet.address())

        self.initial_content = f"""You are a professional recruiter, specialised in reviewing CVs.
            You are looking for the perfect candidate for the job, and will select {n_candidates} from the pool of available CVs.
            For your reference, here is the job description: {job_description}.

            When reading the job description, will identify the top five skills needed for the job, and appraise
            each candidate in the list of candidates for each of those skills.

            When asked, you will return the candidate's score for each of the important skills.

            When you have found up to {n_candidates} suitable candidates, you will return their names, and the contents of their CVs."""
        
        # Initilse the searcher
        _ = self.send_message('system', self.initial_content)
        if most_important_skills == 'auto':
            self.most_important_skills = self.get_most_important_skills()
        else:
            self.most_important_skills = most_important_skills

    
    def get_most_important_skills(self):
        # Get the list of top five skills for the job
        skill_message = self.send_message('user',
                          "What are the five most important skills needed for this job?", 
                          response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "most_important_skills",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "most_important_skills": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                            # "minItems": 5,
                                            # "maxItems": 5
                                        }
                                    },
                                    "required": ["most_important_skills"],
                                    "additionalProperties": False
                                },
                                "strict": True
                            }
                        })
        skill_message_json = json.loads(skill_message)
        return skill_message_json["most_important_skills"]


    
    def appraise_candidates(self):
        self.cv_appraisal_response_format = self._generate_cv_appraisal_response_format()

        for cv_text in self.cvs:
            appraised_cv = self._appraise_cv(cv_text)
            appraised_cv['cv_text'] = cv_text

            # Add the new appraisal to self.candidates
            self.candidates.append(appraised_cv)


    def _appraise_cv(self, cv_text):
        
        instruction = f"""Please appraise this CV for the following skills: {self.most_important_skills}.
        You should give a score of 0-10 for how well the candidate does at each of the skills and justify 
        your reasoning for doing so by extracting relevant information from the CV. You should also give an overall overall suitability
        score. You should also extract the candidate's name and email.

        Here is the CV: {cv_text}"""

        response = self.send_message('user', instruction, response_format=self.cv_appraisal_response_format)
        
        appraised_cv = json.loads(response)
        
        return appraised_cv


    def select_candidates(self):
        # selected_candidates = []
        # unselected_candidates = []
        for candidate in self.candidates:
            candidate_scores = [
                candidate['skills'][sc] for sc in self.most_important_skills
                ]
            candidate_scores.append(candidate['overall_score'])
            score_thresholds = [sc >= self.min_suitability_score for sc in candidate_scores]
            pc_scores_ge_threshold = sum(score_thresholds) / len(score_thresholds)
            candidate['scores_ge_threshold'] = pc_scores_ge_threshold
            if pc_scores_ge_threshold >= self.suitability_threshold:
                candidate['selected'] = True
            else:
                candidate['selected'] = False



    def _generate_cv_appraisal_response_format(self):
        # Create dynamic properties for each skill's score
        properties = {}
        required_fields = ["name", "email", "overall_score", "skills"]  # Include 'name' in the required fields
        properties["name"] = {
            "type": "string",
            "description": "The candidate's name"
        }
        properties["email"] = {
            "type": "string",
            "description": "The candidate's enail address"
        }
        properties["overall_score"] = {
            "type": "integer",
            "description": "Overall score for the candidate based on skill appraisal (0-10)."
        }
        
        skill_properties = {}
        skill_required = []
        
        # Loop through the list of skills and create dynamic keys
        for i, skill in enumerate(self.most_important_skills, 1):
            # skill_key = f"skill{i}_score"
            skill_properties[skill] = {
                "type": "integer",
                "description": f"Score (0-10) for {skill}."
            }
            skill_required.append(skill)
            
            skill_justify = f'{skill}_JUSTIFICATION'
            skill_properties[skill_justify] = {
                "type": "string",
                "description": f"Justification for the score given to {skill} for the candidate."
            }
            skill_required.append(skill_justify)

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
                "name": "cv_appraisal_response",
                "schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required_fields,
                    "additionalProperties": False
                },
                "strict": True
            }
        }