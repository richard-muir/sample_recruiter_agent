import langroid as lr
import langroid.language_models as lm

# set up LLM
llm_cfg = lm.OpenAIGPTConfig( # or OpenAIAssistant to use Assistant API 
  # any model served via an OpenAI-compatible API
  chat_model=lm.OpenAIChatModel.GPT4o, # or, e.g., "ollama/mistral"
)
# use LLM directly
mdl = lm.OpenAIGPT(llm_cfg)
response = mdl.chat("What is the capital of Ontario?", max_tokens=10)

# use LLM in an Agent
agent_cfg = lr.ChatAgentConfig(llm=llm_cfg)
agent = lr.ChatAgent(agent_cfg)
agent.llm_response("What is the capital of China?") 
response = agent.llm_response("And India?") # maintains conversation state 

# wrap Agent in a Task to run interactive loop with user (or other agents)
task = lr.Task(agent, name="Bot", system_message="You are a helpful assistant")
task.run("Hello") # kick off with user saying "Hello"

# 2-Agent chat loop: Teacher Agent asks questions to Student Agent
teacher_agent = lr.ChatAgent(agent_cfg)
teacher_task = lr.Task(
  teacher_agent, name="Teacher",
  system_message="""
    Ask your student concise numbers questions, and give feedback. 
    Start with a question.
    """
)
student_agent = lr.ChatAgent(agent_cfg)
student_task = lr.Task(
  student_agent, name="Student",
  system_message="Concisely answer the teacher's questions.",
  single_round=True,
)

teacher_task.add_sub_task(student_task)
teacher_task.run()