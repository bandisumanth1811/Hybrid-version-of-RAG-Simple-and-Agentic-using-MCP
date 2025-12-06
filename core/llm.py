import os
from typing import List
from google import genai
from dotenv import load_dotenv
import chromadb.utils.embedding_functions as ef

load_dotenv()

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            # We don't raise immediately to allow app to start, but methods will fail
            print("WARNING: GEMINI_API_KEY not set.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash-lite"
        self.embedding_model = "models/text-embedding-004"

    def ask(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating content: {e}"

class GeminiEmbeddingFunction(ef.EmbeddingFunction):
    def __init__(self, client: GeminiClient):
        self.client = client

    def __call__(self, input: List[str]) -> List[List[float]]:
        # Google GenAI SDK supports batch embedding
        try:
            # The SDK might differ slightly, but usually supports list of contents
            # If strict 0.3.0: client.models.embed_content(model=..., contents=[...])
            result = self.client.client.models.embed_content(
                model=self.client.embedding_model,
                contents=input
            )
            
            # The result structure typically has an 'embeddings' list
            # Each item has 'values'
            return [e.values for e in result.embeddings]
        except Exception as e:
            print(f"Embedding error: {e}")
            # Return dummy embeddings or re-raise? 
            # Re-raising is better to catch config errors
            raise e
