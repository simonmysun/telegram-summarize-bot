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
      # logger.info(line)
      if line: 
        parts = line.decode('utf-8').split('data: ')
        if parts[1] == '[DONE]':
          continue
        data = None
        try:
          data = json.loads(parts[1])
        except Exception as e:
          logger.error(f'Error: {e}')
          logger.error(line)
          raise e
        if 'choices' not in data:
          logger.error(f'Unexpected response: {data}')
          raise Exception(f'Unexpected response: {data}')
        if len(data['choices']) != 1:
          logger.error(f'Unexpected number of choices: {len(data["choices"])}, {data}')
          if len(data['choices']) == 0:
            raise Exception(f'Unexpected number of choices: {len(data["choices"])}, {data}')
        try:
          if 'finish_reason' in data['choices'][0]:
            if data['choices'][0]['finish_reason'] != 'stop':
              if data['choices'][0]['finish_reason'] != None:
                logger.error(f'Unexpected finish_reason: {data["choices"][0]["finish_reason"]}')
                raise Exception(f'finish_reason={ data["choices"][0]["finish_reason"] }')
            else:
              break
          if 'delta' not in data['choices'][0] or 'content' not in data['choices'][0]['delta']:
            logger.error(f'Unexpected response: {data}')
            raise Exception(f'Unexpected response: {data}')
          yield data['choices'][0]['delta']['content']
        except Exception as e:
          logger.error(line)
          logger.error(f'Error: {e}')
          raise