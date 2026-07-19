"""Fabric Notebook: Test OpenAI API Key

Quick test to verify your OpenAI API key works.
"""

# %% Cell 1: Install
%pip install openai

# %% Cell 2: Test your key
import openai

OPENAI_API_KEY = "REPLACE_WITH_YOUR_KEY"

client = openai.OpenAI(api_key=OPENAI_API_KEY)
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=5,
    )
    print(f"Working! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error: {e}")
