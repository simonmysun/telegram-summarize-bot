import logging
logger = logging.getLogger(__name__)

import typing
if typing.TYPE_CHECKING:
    import telegram
    
import re
import os

from telegram import constants

from .process_url import process_url
from .fetch_content import fetch_content
from .llm_api import complete
from .render_html import render
from .throttle import Throttle

MAX_INPUT_LENGTH = int(os.getenv('MAX_INPUT_LENGTH'))

def get_url_from_message(messages: 'telegram.Message[]') -> str:
  all_text = ''
  url = ''
  for message in messages:
    if message is None:
      continue
    if message.entities:
      for entity in message.entities:
        if entity.type == 'text_link':
          all_text += f'{entity.url}\n'
          logger.info(f'URL found in entity: {entity.url}')
    if message.caption_entities:
      for entity in message.caption_entities:
        if entity.type == 'text_link':
          all_text += f'{entity.url}\n'
          logger.info(f'URL found in caption entity: {entity.url}')
    if message.caption:
      all_text += f'{message.caption}\n'
    all_text += f'{message.text}\n'
  logger.info(f'All text: {all_text}')
  urls = re.findall(r'(([Hh][Tt]{2}[Pp][Ss]?:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.([a-zA-Z()]{2,}|[xX][nN]--[a-zA-Z()]{2,})\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*))', all_text) # this is still not a complete URL matching regex
  if urls:
    url = urls[0][0]
  else:
    logger.info(f'No URL found.')
  return url

throttle = Throttle()

prompt_template_summarize_content = ''
with open('prompts/summarize_content.txt', 'r') as f_prompt_template_summarize_content:
  prompt_template_summarize_content = f_prompt_template_summarize_content.read()

prompt_template_summarize_discussion = ''
with open('prompts/summarize_discussion.txt', 'r') as f_prompt_template_summarize_discussion:
  prompt_template_summarize_discussion = f_prompt_template_summarize_discussion.read()

prompt_template_summarize_comment = ''
with open('prompts/summarize_comment.txt', 'r') as f_prompt_template_summarize_comment:
  prompt_template_summarize_comment = f_prompt_template_summarize_comment.read()

async def handle_general_message(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  throttle.call()
  replyMessage = await update.message.reply_text(render('_Processing..._'), parse_mode=constants.ParseMode.HTML)
  url = get_url_from_message([update.message.reply_to_message, update.message])
  if url == '':
    throttle.call()
    await replyMessage.edit_text(render('**ERROR**: No URL found in the message.'), parse_mode=constants.ParseMode.HTML)
    return
  logger.info(f'Processing: {url}')
  uri, discussion_uri = process_url(url)
  message = ''
  (final_url, content) = await fetch_content(uri.geturl())
  message += f'URL: {final_url}\n'
  if discussion_uri:
    message += f'Discussion: {discussion_uri.geturl()}\n\n'
  message += f'<b><a href="{final_url}">Content</a></b>\n'
  if len([line for line in content.split('\n') if line.strip()]) == 0:
    logger.error(f'No content or discussion is fetched. ')
    message += render(f'**ERROR**: No content or discussion is fetched. \n')
    content = f'{final_url}.'
  if uri.netloc in ['news.ycombinator.com'] and not discussion_uri:
    logger.info('This is a comment on HN')
    prompt = prompt_template_summarize_comment.format(**{
      'content': content
    })
  else:
    prompt = prompt_template_summarize_content.format(**{
      'content': content
    })
  if len(prompt) > MAX_INPUT_LENGTH:
    message += render(f'_Content is truncated._\n')
    # throttle.call()
    # await update.message.reply_text(render(message), parse_mode=constants.ParseMode.HTML)
    logger.info(f'Prompt length is ({len(prompt)} characters). Truncating to {MAX_INPUT_LENGTH} characters.')
    prompt = prompt[:MAX_INPUT_LENGTH]
    prompt += 'TRUNCATED'
  result = []
  # logger.info(f'prompt: {prompt}')
  try:
    async for token in complete(prompt):
      result.append(token)
  except Exception as e:
    logger.error(f'ERROR: {repr(e)}')
    message += f'{''.join(result)}\n{render('**ERROR**: LLM API request failed')}\n'
  if len(result) == 0:
    logger.error('No result returned from LLM.')
    message += render(f'**ERROR**: No result returned from LLM.\n')
  else:
    message += f'<blockquote expandable>{render(''.join(result))}</blockquote>'
  logger.info(f'Message: {message[:50].encode("unicode_escape").decode("utf-8")}')
  logger.info(f'Message: {message}')
  logger.info(f'length: {len(message)}')
  await replyMessage.edit_text(message, parse_mode=constants.ParseMode.HTML)
  throttle.call()
  discussion = ''
  if discussion_uri:
    message += f'<b><a href="{discussion_uri.geturl()}">Discussion</a></b>\n'
    (final_url, discussion) = await fetch_content(discussion_uri.geturl())
    if len([line for line in discussion.split('\n') if line.strip()]) == 0:
      logger.error(f'No discussion is fetched. Task aborted.')
      message += f'{render('**ERROR**: No discussion is fetched. Task aborted.')}\n'
    prompt = prompt_template_summarize_discussion.format(**{
      'content': ''.join(result),
      'discussion': discussion
    })
    if len(prompt) > MAX_INPUT_LENGTH:
      logger.info(f'Prompt length is ({len(prompt)} characters). Truncating to {MAX_INPUT_LENGTH} characters.')
      message += f'{render('_discussion is truncated_')}\n'
      prompt = prompt[:MAX_INPUT_LENGTH]
      prompt += '\nTRUNCATED\n'
    # logger.info(f'Messages: {prompt}')
    result = []
    # logger.info(f'prompt: {prompt}')
    try:
      async for token in complete(prompt):
        result.append(token)
    except Exception as e:
      logger.error(f'ERROR: {repr(e)}')
      message += f'{''.join(result)}\n{render('**ERROR**: LLM API request failed')}\n'
    if len(result) == 0:
      logger.error('No result returned.')
      message += f'**ERROR**: No result returned.\n'
    else:
      message += f'<blockquote expandable>{render(''.join(result))}</blockquote>'
    throttle.call()
    logger.info(f'Message: {message[:50].encode("unicode_escape").decode("utf-8")}')
    # logger.info(f'Message: {message}')
    logger.info(f'length: {len(message)}')
    await replyMessage.edit_text(message, parse_mode=constants.ParseMode.HTML)
    