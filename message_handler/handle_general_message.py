import typing
if typing.TYPE_CHECKING:
    import telegram
    
import logging, re, os

from telegram import constants

from .process_url import process_url
from .fetch_content import fetch_content
from .llm_api import complete

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
          logging.info(f'URL found in entity: {entity.url}')
    all_text += f'{message.text}\n'
  urls = re.findall(r'(https?://[^\s]+)', all_text)
  if urls:
    url = urls[0]
  else:
    logging.info(f'No URL found.')
  return url

prompt_template = ''
with open('prompt_template.txt', 'r') as f_prompt_template:
  prompt_template = f_prompt_template.read()

async def handle_general_message(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  replyMessage = await update.message.reply_text('_Processing..._', parse_mode='Markdown')
  url = get_url_from_message([update.message.reply_to_message, update.message])
  if url == '':
    await replyMessage.edit_text('*ERROR*: No URL found in the message.', parse_mode='Markdown')
    return
  logging.info(f'Processing: {url}')
  uri, discussion_uri = process_url(url)
  content = await fetch_content(uri.geturl())
  discussion = ''
  if discussion_uri:
    discussion = await fetch_content(discussion_uri.geturl())
  if len([line for line in (content + discussion).split('\n') if line.strip()]) == 0:
    logging.error(f'No content or discussion is fetched. Task aborted.')
    await replyMessage.edit_text('*ERROR*: No content or discussion is fetched. Task aborted.', parse_mode='Markdown')
    return
  if discussion_uri and len(content) > MAX_INPUT_LENGTH * 0.75:
    logging.info(f'Content length is {len(content)}. Truncating to {int(MAX_INPUT_LENGTH * 0.75)} characters.')
    content = content[:int(MAX_INPUT_LENGTH * 0.75)]
    content += 'TRUNCATED'
  prompt = prompt_template.format(**{
    'content': content,
    'discussion': discussion
  })
  if(len(prompt) > MAX_INPUT_LENGTH):
    await update.message.edit_text('_Processing..._ (content is truncated)', parse_mode='Markdown')
    logging.info(f'Prompt length is ({len(prompt)} characters). Truncating to {MAX_INPUT_LENGTH} characters.')
    prompt = prompt[:MAX_INPUT_LENGTH]
    prompt += 'TRUNCATED'
  if prompt.endswith('TRUNCATED'):
    await update.message.edit_text('_Processing..._ (prompt is truncated)', parse_mode='Markdown')
  # logging.info(f'Messages: {prompt}')
  result = []
  counter = 0
  try:
    async for token in complete(prompt):
      counter += 1
      result.append(token)
      if(counter >= 50):
        counter = 0
        try:
          await update.message.reply_chat_action(constants.ChatAction.TYPING)
          await replyMessage.edit_text(''.join(result), parse_mode='Markdown')
        except:
          pass
  except Exception as e:
    logging.error(f'ERROR: {repr(e)}')
    await replyMessage.edit_text(f'*ERROR*: LLM API request failed: {repr(e)}', parse_mode='Markdown')
  if len(result) == 0:
    logging.error('No result returned.')
    await replyMessage.edit_text('*ERROR*: No result returned.', parse_mode='Markdown')
  if counter > 0:
    await replyMessage.edit_text(''.join(result), parse_mode='Markdown')