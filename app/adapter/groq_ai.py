import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq


class Groq_AIModelAdapter:
    def __init__(self, temperature=0.8, max_tokens=2048):
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment variables.")

        # Initialize the Groq chat model instance here so get_llm() can return it
        try:
            #self.llm = ChatGroq(model="qwen/qwen3-32b", api_key=self.groq_api_key, # openai/gpt-oss-120b
            self.llm = ChatGroq(model="openai/gpt-oss-120b", api_key=self.groq_api_key,
                                temperature=self.temperature,
                                max_tokens=self.max_tokens)
        except Exception as e:
            # Raise a clearer error if the model cannot be initialized
            raise RuntimeError(f"Failed to initialize Groq Chat model: {e}") from e


    def chat(self,llm_message):
        """Invoke the Groq model with the provided message."""
        #llm = self.model()
        response = self.llm.invoke(llm_message)
        return response
    
    def get_llm(self):
        """Return the Groq model instance."""
        return self.llm