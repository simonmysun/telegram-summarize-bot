import logging
logger = logging.getLogger(__name__)

import os

from openai import OpenAI

LLM_MODEL = os.getenv('LLM_MODEL')
SYSTEM_PROMPT = 'You are a helpful assitant. '

client = OpenAI(
  api_key=os.getenv('OPENAI_API_KEY'),
  base_url=os.getenv('OPENAI_API_URL') if os.getenv('OPENAI_API_URL') else 'https://api.openai.com/v1/',
  )

async def complete(prompt: str) -> None:
  completion = client.chat.completions.create(
    model=LLM_MODEL,
    messages=[
      {"role": "developer", "content": SYSTEM_PROMPT},
      {"role": "user", "content": prompt}
    ],
    stream=True
  )
  for chunk in completion:
    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
      if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
        if chunk.choices[0].delta.content:
          yield chunk.choices[0].delta.content
          continue
    logger.error(f"Unexpected response format: {chunk}")