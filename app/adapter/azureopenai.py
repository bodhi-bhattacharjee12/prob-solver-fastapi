import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import AzureChatOpenAI


class Azure_AIModelAdapter:
    def __init__(self, temperature=0.8, max_tokens=2048):
        load_dotenv()
        self.azureopenai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.version=os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        self.temperature = temperature
        self.max_tokens = max_tokens
        if not self.azureopenai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is not set in the environment variables.")
        # Initialize the Groq chat model instance here so get_llm() can return it
        try:
            # Initialize the Azure OpenAI client
            self.llm = AzureChatOpenAI(
                azure_endpoint=self.azure_endpoint,  # must match your Azure endpoint
                api_key=self.azureopenai_api_key,
                deployment_name=self.deployment_name,    # must match your Azure deployment name
                api_version=self.version,                # use the latest supported version
                temperature=self.temperature
            )
        except Exception as e:
            # Raise a clearer error if the model cannot be initialized
            raise RuntimeError(f"Failed to initialize Azure openAI Chat model: {e}") from e


    def chat(self,llm_message):
        """Invoke the Azure openAI model with the provided message."""
        #llm = self.model()
        response = self.llm.invoke(llm_message)
        print("Azure OpenAI model response:", response)
        return response
    
    def get_llm(self):
        """Return the Azure openAI model instance."""
        return self.llm