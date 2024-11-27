 
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model

from openai import OpenAI
client = OpenAI()

with open('my_cv.txt', 'r', encoding='utf-8') as file:
    cv_content = file.read()

system_content = f"""You are a digital twin of me, Rich Muir.
You have access to my entire job history, and answer questions in a clear and professional way.
For your reference, here is my CV: {cv_content}.

You are waiting and ready to receive questions for different recruiters about jobs.

You address the recruiter directly, giving the best information you can, but you don't lie, and you say when you don't have experience."""



def create_chat_gpt_message(question_from_recruiter):
    return [
        {"role": "system", "content": system_content},
        {
            "role": "user",
            "content": question_from_recruiter
        }
    ]


 
class Message(Model):
    message: str

    
 
my_ai = Agent(
    name="rich_job_seeker",
    port=8000,
    seed="the quick brown fox",
    endpoint=["http://127.0.0.1:8000/submit"],
)
 
fund_agent_if_low(my_ai.wallet.address())
 
@my_ai.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}, with context: {msg.message}")

    gpt_message = create_chat_gpt_message(msg.message)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=gpt_message
    )
    msg = completion.choices[0].message.content
    await ctx.send(sender, Message(message=msg))
 
if __name__ == "__main__":
    my_ai.run()
 