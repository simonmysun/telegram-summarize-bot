import requests, feedparser, logging
from urllib.parse import urlparse

def get_hn_story_url(story_id: str) -> str:
  base_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
  response = requests.get(base_url)
  if response.status_code == 200:
    story_info = response.json()
    return story_info.get('url')
  else:
    logging.error(f'Failed to retrieve story with ID {story_id}. Error: {response.status_code}')
    return ''

def get_reddit_post_url_from_rss(subreddit: str, post_id: str) -> str: # never tested
  rss_url = f'https://www.reddit.com/r/{subreddit}/comments/{post_id}.rss'
  feed = feedparser.parse(rss_url)
  if feed.entries:
    post = feed.entries[0]  # Assuming there's only one entry for the given post ID
    return post.link
  else:
    logging.error(f'No post found with ID {post_id} in subreddit {subreddit}.')
    return ''

def process_url(url: str) -> tuple[urlparse, urlparse]:
  uri = urlparse(url)
  if not uri.scheme:
    uri = urlparse(f'http://{url}')
  discussion_uri = None
  if uri.netloc == 'news.ycombinator.com':
    logging.info('HN URL detected')
    story_id = url.split('=')[-1]
    discussion_uri = uri
    uri = urlparse(get_hn_story_url(story_id))
    logging.info(f'HN post URL: {uri.geturl()}')
    logging.info(f'HN discussion URL: {discussion_uri.geturl()}')
  elif uri.netloc == 'readhacker.news':
    logging.info('ReadHN URL detected')
    if uri.path.startswith('/s/'):
      story_id = uri.path.split('/')[-1]
      discussion_uri = urlparse(f'https://readhacker.news/c/{story_id}')
    elif uri.path.startswith('/c/'):
      story_id = uri.path.split('/')[-1]
      discussion_uri = uri
      uri = urlparse(f'https://readhacker.news/s/{story_id}')
  elif 'reddit.com' in uri.netloc:
    logging.info('Reddit URL detected')
    post_id = uri.path.split('/')[-2]
    subreddit = uri.path.split('/')[-3]
    discussion_uri = uri
    uri = urlparse(get_reddit_post_url_from_rss(subreddit, post_id))
    logging.info(f'Reddit post URL: {uri.geturl()}')
    logging.info(f'Reddit discussion URL: {discussion_uri.geturl()}')
  elif uri.netloc in ['arxiv.org', 'www.arxiv.org']:
    logging.info('Arxiv URL detected')
    if uri.path.startswith('/abs/') or uri.path.startswith('/pdf/'):
      uri_html = urlparse(uri.geturl())
      uri_html = uri_html._replace(path=uri_html.path.replace('/abs', '/html'))
      uri_html = uri_html._replace(path=uri_html.path.replace('/pdf', '/html'))
      logging.info(f'Trying arxiv HTML link: {uri_html.geturl()}')
      if requests.get(uri_html.geturl()).status_code == 404:
        logging.info(f'404: {uri_html.geturl()}')
        uri_html = uri_html._replace(netloc='ar5iv.labs.arxiv.org')
        if requests.get(uri_html.geturl()).status_code == 404:
          logging.info(f'404: {uri_html.geturl()}')
          logging.info('Arxiv HTML link not found, using abstract instead.')
        else:
          logging.info(f'Fallback to abstract')
          uri = uri_html._replace(path=uri_html.path.replace('/pdf', '/abs'))
      else:
        logging.info(f'Fallback to abstract')
        uri = uri_html._replace(path=uri_html.path.replace('/pdf', '/abs'))
  elif 'twitter.com' in uri.netloc:
    uri = uri._replace(netloc='fxtwitter.com')
  elif 'x.com' in uri.netloc:
    uri= uri._replace(netloc='fixupx.com')
  logging.info(f'Final URL: {uri.geturl()}')
  if discussion_uri:
    logging.info(f'Final Discussion URL: {discussion_uri.geturl()}')
  else:
    logging.info('No discussion URL found.')
  return uri, discussion_uri