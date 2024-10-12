import logging
logger = logging.getLogger(__name__)

import os
import requests
import json

API_KEY = os.getenv('OPENAI_API_KEY')
API_URL = os.getenv('OPENAI_API_URL') if os.getenv('OPENAI_API_URL') else 'https://api.openai.com/v1/'
LLM_MODEL = os.getenv('LLM_MODEL')
SYSTEM_PROMPT = 'You are a helpful assitant. '

async def complete(prompt: str) -> None:
  with requests.post(f'{API_URL}chat/completions', headers={
    'Authorization': f'Bearer {API_KEY}'
  }, json={
    'model': LLM_MODEL, 
    'messages': [
        {
            'role': 'system',
            'content': SYSTEM_PROMPT
        },
        {
            'role': 'user',
            'content': prompt
        }
    ],
    'temperature': 0.7,
    'stream': True
  }, stream=True) as response:
    for line in response.iter_lines():
      if line:
        parts = line.decode('utf-8').split('data: ')
        if parts[1] == '[DONE]':
          continue
        data = json.loads(parts[1])
        if 'choices' not in data:
          logger.error(f'Unexpected response: {data}')
          raise
        if len(data['choices']) != 1:
          logger.error(f'Unexpected number of choices: {len(data["choices"])}, {data}')
        else:
          try:
            if data['choices'][0]['finish_reason'] != 'stop':
              if data['choices'][0]['finish_reason'] == None:
                if 'content' in data['choices'][0]['delta']:
                  yield data['choices'][0]['delta']['content']
              else:
                raise Exception(f'finish_reason={ data["choices"][0]["finish_reason"] }')
          except Exception as e:
            logger.error(line)
            logger.error(f'Error: {e}')
            raise