import logging
logger = logging.getLogger(__name__)

import requests

from html2text import HTML2Text
h2t = HTML2Text()
h2t.ignore_tables = True
h2t.ignore_links = True
h2t.ignore_images = True
h2t.google_doc = True

async def fetch_content(url: str) -> (str, str):
  logger.info(f'Fetching content from {url}')
  content = ''
  try:
    response = requests.get(url, allow_redirects=True, headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
  }, timeout=60)
    if response.status_code == 200:
      if response.history:
        logger.info(f'Redirected to {response.url}')
        url = response.url
      logger.info(f'Fetched {len(response.text)}')
      content = response.text
    else:
      logger.info(f'Failed to retrieve content from {url}. Error: {response.status_code}')
    try:
      content_text = h2t.handle(content)
      if len([line for line in content_text.split('\n') if line.strip()]) > 0:
        content = content_text
      else:
        raise Exception('Converted text has no content.')
    except:
      logger.debug(f'Failed to convert HTML to text.')
      pass
  except Exception as e:
    logger.info(f'Error: {repr(e)}')
    pass
  logger.info(f'Content length: {len(content)}')
  return (url, content)