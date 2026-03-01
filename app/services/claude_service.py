import google.generativeai as genai
import os

genai.configure(api_key=os.getenv('gemini-1.5-flash-8b'))
model = genai.GenerativeModel('gemini-2.0-flash')

def call_claude(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text