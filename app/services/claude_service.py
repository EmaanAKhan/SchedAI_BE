import os
from google import genai

client_gemini = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def call_claude(prompt: str) -> str:
    provider = os.getenv('AI_PROVIDER', 'claude')

    if provider == 'gemini':
        response = client_gemini.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text

    else:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

