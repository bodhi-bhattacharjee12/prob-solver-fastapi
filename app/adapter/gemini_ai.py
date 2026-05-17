import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

class Gemini_AIModelAdapter:
    def __init__(self, temperature=0.8, max_tokens=2048):
        load_dotenv()
        self.google_api_key = os.getenv("GEMINI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        if not self.google_api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

        # Initialize the Gemini chat model instance here so get_llm() can return it
        try:
            # You can switch the model to "gemini-pro" or "gemini-1.5-pro" as needed
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",  
                google_api_key=self.google_api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            # Raise a clearer error if the model cannot be initialized
            raise RuntimeError(f"Failed to initialize Gemini Chat model: {e}") from e

    def chat(self, llm_message):
        """Invoke the Gemini model with the provided message."""
        response = self.llm.invoke(llm_message)
        return response
    
    def get_llm(self):
        """Return the Gemini model instance."""
        return self.llm