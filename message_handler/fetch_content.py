import logging
logger = logging.getLogger(__name__)

import requests

from html2text import HTML2Text
h2t = HTML2Text()
h2t.ignore_tables = True
h2t.ignore_links = True
h2t.images_to_alt = True

import os
BROWSERLESS_API_URL = os.getenv('BROWSERLESS_API_URL')
BROWSERLESS_API_TOKEN = os.getenv('BROWSERLESS_API_TOKEN')
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

import urllib
browserless_query_params = urllib.parse.urlencode({
  "blockAds": "true",
  "timeout": "55000",
  "token": BROWSERLESS_API_TOKEN,
  "headless": False,
  "stealth": True
})

async def fetch_content(url: str) -> tuple[str, str]:
  logger.info(f'Fetching content from {url}')
  content = ''
  try:
    response = None
    if BROWSERLESS_API_URL is not None and len(BROWSERLESS_API_URL) > 0:
      logger.info(f'Using browserless API')
      browserless_url = f'{BROWSERLESS_API_URL}/content?{browserless_query_params}'
      response = requests.post(browserless_url, json={
        "bestAttempt": True,
        "gotoOptions": {
          "timeout": 30000,
          "waitUntil": "domcontentloaded"
        },
        "setJavaScriptEnabled": True,
        "url": url,
        "waitForTimeout": 1000
      }, timeout=60)
      try:
        probe_redirection = requests.get(url, allow_redirects=True, headers={
          'User-Agent': USER_AGENT
        }, timeout=3)
        if probe_redirection.history:
          logger.info(f'Redirected to {probe_redirection.url}')
          url = probe_redirection.url
      except requests.RequestException as e:
        logger.info(f'Failed to probe redirection: {repr(e)}')
    else:
      response = requests.get(url, allow_redirects=True, headers={
        'User-Agent': USER_AGENT
      }, timeout=60)
    if response.status_code == 200:
      if response.history:
        logger.info(f'Redirected to {response.url}')
        url = response.url
      content = response.text
      logger.info(f'Fetched {len(content)}')
    else:
      logger.info(f'Failed to retrieve content from {url}. Error: {response.status_code}')
    try:
      logger.info(f'Converting HTML to text...')
      content_text = h2t.handle(content)
      logger.info(f'Converted {len(content)} to {len(content_text)}')
      if len([line for line in content_text.split('\n') if line.strip()]) > 0:
        content = content_text
      else:
        logger.error(f'Converted text has no content. {content_text}')
        raise Exception('Converted text has no content. ')
    except Exception as e:
      logger.debug(f'Failed to convert HTML to text., {repr(e)}')
      pass
  except Exception as e:
    logger.info(f'Error: {repr(e)}')
    pass
  logger.info(f'Content length: {len(content)}')
  return (url, content)
