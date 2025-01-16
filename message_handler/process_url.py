import logging
logger = logging.getLogger(__name__)

import requests
import re
from urllib.parse import urlparse

def get_hn_story_url(story_id: str):
  base_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
  response = requests.get(base_url)
  if response.status_code == 200:
    story_info = response.json()
    return story_info
  else:
    logger.error(f'Failed to retrieve story with ID {story_id}. Error: {response.status_code}')
    return None

def process_url(url: str) -> tuple[urlparse, urlparse]:
  uri = urlparse(url)
  if not uri.scheme:
    uri = urlparse(f'http://{url}')
  discussion_uri = None
  if uri.netloc == 'news.ycombinator.com':
    logger.info('HN URL detected')
    story_id = url.split('=')[-1]
    story_info = get_hn_story_url(story_id)
    if story_info.get('type') == 'story':
      discussion_uri = uri
      uri = urlparse(story_info.get('url'))
      logger.info(f'HN post URL: {uri.geturl()}')
      logger.info(f'HN discussion URL: {discussion_uri.geturl()}')
  elif uri.netloc == 'readhacker.news':
    logger.info('ReadHN URL detected')
    if uri.path.startswith('/s/'):
      story_id = uri.path.split('/')[-1]
      discussion_uri = urlparse(f'https://readhacker.news/c/{story_id}')
    elif uri.path.startswith('/c/'):
      story_id = uri.path.split('/')[-1]
      discussion_uri = uri
      uri = urlparse(f'https://readhacker.news/s/{story_id}')
  elif re.match(r'(.*\.)?arxiv\.org$', uri.netloc):
    logger.info('Arxiv URL detected')
    if uri.path.startswith('/abs/') or uri.path.startswith('/pdf/'):
      uri_html = urlparse(uri.geturl())
      uri_html = uri_html._replace(path=uri_html.path.replace('/abs', '/html'))
      uri_html = uri_html._replace(path=uri_html.path.replace('/pdf', '/html'))
      logger.info(f'Trying arxiv HTML link: {uri_html.geturl()}')
      if requests.get(uri_html.geturl()).status_code == 404:
        logger.info(f'404: {uri_html.geturl()}')
        uri_html = uri_html._replace(netloc='ar5iv.labs.arxiv.org')
        if requests.get(uri_html.geturl()).status_code == 404:
          logger.info(f'404: {uri_html.geturl()}')
          logger.info('Arxiv HTML link not found, using abstract instead.')
        else:
          logger.info(f'Fallback to abstract')
          uri = uri_html._replace(path=uri_html.path.replace('/pdf', '/abs'))
      else:
        logger.info(f'Fallback to abstract')
        uri = uri_html._replace(path=uri_html.path.replace('/pdf', '/abs'))
  logger.info(f'Final URL: {uri.geturl()}')
  if discussion_uri:
    logger.info(f'Final Discussion URL: {discussion_uri.geturl()}')
  else:
    logger.info('No discussion URL found.')
  return uri, discussion_uri