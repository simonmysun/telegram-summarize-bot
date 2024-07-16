import logging, requests

from html2text import HTML2Text
h2t = HTML2Text()
h2t.ignore_tables = True
h2t.ignore_links = True
h2t.ignore_images = True
h2t.google_doc = True

async def fetch_content(url: str) -> str:
  logging.info(f'Fetching content from {url}')
  content = ''
  try:
    response = requests.get(url, allow_redirects=True, headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
  })
    if response.status_code == 200:
      if response.history:
        logging.info(f'Redirected to {response.url}')
      logging.info(f'Fetched {len(response.text)}')
      content = response.text
    else:
      logging.info(f'Failed to retrieve content from {url}. Error: {response.status_code}')
    try:
      content_text = h2t.handle(content)
      if len([line for line in content_text.split('\n') if line.strip()]) > 0:
        content = content_text
      else:
        raise Exception('Converted text has no content.')
    except:
      logging.debug(f'Failed to convert HTML to text.')
      pass
  except Exception as e:
    logging.info(f'Error: {repr(e)}')
    pass
  return content