import json
from pathlib import Path 
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

from openai_context import ChatGPTContextManager

from openai import OpenAI

 
class Message(Model):
    message: str
 
RECIPIENT_ADDRESS = "agent1qvwum0ystzx7djjh09lw529yajk7rznnvlutfrmv44v445hsp5x3zxr9f8x"


class SearchingAgent(ChatGPTContextManager):
    def __init__(self, job_description, cv_dir, n_candidates=3):
        super().__init__()
        self.interviewing_agent_address = ''
        self.cv_dir = cv_dir

        self.candidates = []

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

        # Get the list of top five skills for the job
        message = self.send_message('user',
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
                                            "minItems": 5,
                                            "maxItems": 5
                                        }
                                    },
                                    "required": ["most_important_skills"],
                                    "additionalProperties": False
                                },
                                "strict": True
                            }
                        })
        self.most_important_skills = message["most_important_skills"]
        self.cv_appraisal_response_format = self._generate_cv_appraisal_response_format()

        self.find_candidates(self.cv_dir)


    @classmethod
    def create_from_jd_and_cv_dir(cls, jd_file_path, cv_dir):
        with open(jd_file_path, 'r', encoding='utf-8') as file:
            job_content = file.read()

        return cls(job_content, cv_dir)
    
    def find_candidates(self, cv_dir):
        
        
        # Directory containing text files
        folder_path = Path(self.cv_dir)

        # Iterate through .txt files in the directory
        for file_path in folder_path.glob("*.txt"):
            with file_path.open("r", encoding="utf-8") as file:
                cv_contents = file.read()
                self._appraise_cv(cv_contents)


    def _appraise_cv(self, cv_text):
        instruction = f"""Please appraise this CV for the following skills: {self.most_important_skills}.
        You should give a score of 0-10 for how well the candidate does at each of the skills, as well as an overall suitability
        score. You should also extract the candidate's name.

        Here is the CV: {cv_text}"""

        response = self.send_message('user', instruction, response_format=self.cv_appraisal_response_format)
        response_content = response['choices'][0]['message']['content']
        
        appraised_cv = json.loads(response_content)
        appraised_cv['cv_text'] = cv_text
        self.candidates.append(appraised_cv)



    def _generate_cv_appraisal_response_format(self):
        # Create dynamic properties for each skill's score
        properties = {}
        required_fields = ["name", "overall_score"]  # Include 'name' in the required fields

        properties["overall_score"] = {
            "type": "integer",
            "description": "Overall score for the candidate based on skill appraisal (0-10)."
        }
        
        # Loop through the list of skills and create dynamic keys
        for i, skill in enumerate(self.most_important_skills, 1):
            skill_key = f"skill{i}_score"
            properties[skill_key] = {
                "type": "integer",
                "description": f"Score (0-10) for {skill}."
            }
            required_fields.append(skill_key)

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

        

searcher = SearchingAgent.create_from_jd_and_cv_dir("jobs/job1.txt", "cvs")


class InterviewAgent(ChatGPTContextManager):

    def __init__(self, job_description):
        super().__init__(self)
        self.suitability_score = 0

        self.interviewing_agent = Agent(
            name="interviewer",
            port=8001,
            seed="jumps over the lazy dog",
            endpoint=["http://127.0.0.1:8001/submit"],
        )
        fund_agent_if_low(self.interviewing_agent.wallet.address())


        self.initial_content = f"""You are a professional recruiter named Bilbo Bobbins, specialising in interviewing candidates.
            You are looking for the perfect candidate for the job, and will ask questions to find that candidate.
            For your reference, here is the job description: {job_description}.

            You are proactive in finding the best candidate, but you are very happy to dismiss a candidate if they don't fit.

            You address the candidate directly, asking one direct question at a time.

            You can ask a maximum of ten questions to the candidate, 
            and you need to keep track of the candidate's suitability for the role. 
            When asked for the candidate's suitability, you retrun a score between 0 and 10, with 10 being the most suitable."""
        
        self.send_message('system', self.initial_content)

    @classmethod
    def job_description_from_text_file(cls, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            job_content = file.read()

        return cls(job_content)


    
    def get_suitability_score(self):
        message = "What is the candidate's suitability score for this job?"
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "suitability_score_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "suitability_score": {
                            "type": "integer",
                            "description": "A score representing the suitability of the application."
                        }
                    },
                    "required": ["suitability_score"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
        message = self.send_message('user', message, response_format=response_format)
        self.suitability_score = message["suitability_score"]
        








 
# @recruiter.on_event("startup")
# async def send_opening_message(ctx: Context):
#     ctx.logger.info(f"Recruiter bot initialised")
#     gpt_message = [
#         {"role": "system", "content": system_content},
#         {
#             "role": "user",
#             "content": "Using the information from the CV you have been provided, please begin the recruitment process."
#         }
#     ]

#     ctx.logger.info(f"Generating response from ChatGPT")
#     completion = client.chat.completions.create(
#         model="gpt-4o",
#         messages=gpt_message
#     )
#     msg = completion.choices[0].message.content
#     ctx.logger.info(f"Generated first contact message: {msg}")


#     await ctx.send(RECIPIENT_ADDRESS, Message(message=msg))
 
# @recruiter.on_message(model=Message)
# async def message_handler(ctx: Context, sender: str, msg: Message):
#     ctx.logger.info(f"Received message from {sender}: {msg.message}")

#     gpt_message = create_chat_gpt_message(msg.message)
#     completion = client.chat.completions.create(
#         model="gpt-4o",
#         messages=gpt_message
#     )
#     msg = completion.choices[0].message.content
#     ctx.logger.info(f"Generated response: {msg}")

#     await ctx.send(sender, Message(message=msg))


 
# if __name__ == "__main__":
#     recruiter.run()
 