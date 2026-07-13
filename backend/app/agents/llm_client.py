import os
import requests
from google import genai
from google.genai import types
from app.config import settings

def generate_llm_response(prompt: str, response_json: bool = False) -> str:
    """Tries to call Gemini first; automatically fails over to Groq Llama 3.3 if rate-limited."""
    # 1. Try Gemini
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            if response_json:
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            else:
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
            
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Gemini API failed or rate-limited: {str(e)}. Attempting Groq failover...")

    # 2. Try Groq (Failover)
    groq_key = settings.GROQ_API_KEY
    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.3-70b-versatile",  # Correct standard model ID
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            
            if response_json:
                data["response_format"] = {"type": "json_object"}
                
            res = requests.post(url, json=data, headers=headers, timeout=12)
            res.raise_for_status()
            
            content = res.json()["choices"][0]["message"]["content"]
            if content:
                return content.strip()
        except Exception as groq_err:
            print(f"Groq API call also failed: {str(groq_err)}")

    # If both fail or keys are missing, raise an error to trigger RAG fallback
    raise Exception("All active LLM providers (Gemini & Groq) failed or are unconfigured.")