from openai import OpenAI
from dotenv import load_dotenv
import os

class ChatGPTContextManager:
    def __init__(self, model="gpt-4o-mini-2024-07-18"):
        """
        Initialize the context manager.
        
        :param api_key: Your OpenAI API key.
        :param model: The model to use, e.g., "gpt-4".
        """
        # Load environment variables from .env file
        load_dotenv()
        # Get the API key from the .env file
        self.api_key = os.getenv("OPENAI_API_KEY")

        # self.api_key = api_key
        self.model = model
        self.messages = []
        self.client = OpenAI(api_key=self.api_key)

        # Set the API key for the OpenAI library
        #  done using dotenv
        # openai.api_key = api_key

    def add_message(self, role, content):
        """
        Add a message to the context.

        :param role: The role of the message ('system', 'user', or 'assistant').
        :param content: The content of the message.
        """
        self.messages.append({"role": role, "content": content})

    def send_message(self, role, message, max_tokens=1000, response_format=None):
        """
        Send a message to the ChatGPT API and get a response.

        :param user_input: The user's input message.
        :param max_tokens: The maximum number of tokens in the response.
        :return: The assistant's response as a string.
        """
        # Add the user's message to the context
        self.add_message(role, message)
        
        if response_format is not None:
            # Call the API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                max_tokens=max_tokens,
                response_format=response_format
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                max_tokens=max_tokens
            )


        # Extract the assistant's message
        assistant_message = response.choices[0].message.content
        
        # Add the assistant's message to the context
        self.add_message("assistant", assistant_message)

        return assistant_message

    def clear_context(self):
        """
        Clear the conversation context.
        """
        self.messages = []