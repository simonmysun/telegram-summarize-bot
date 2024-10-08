import typing
if typing.TYPE_CHECKING:
    import telegram
    
import logging, re, os, time

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
    if message.caption_entities:
      for entity in message.caption_entities:
        if entity.type == 'text_link':
          all_text += f'{entity.url}\n'
          logging.info(f'URL found in caption entity: {entity.url}')
    if message.caption:
      all_text += f'{message.caption}\n'
    all_text += f'{message.text}\n'
  logging.info(f'All text: {all_text}')
  urls = re.findall(r'(([Hh][Tt]{2}[Pp][Ss]?:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.([a-zA-Z()]{2,}|[xX][nN]--[a-zA-Z()]{2,})\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*))', all_text) # this is still not a complete URL matching regex
  if urls:
    url = urls[0][0]
  else:
    logging.info(f'No URL found.')
  return url

prompt_template_summarize_content = ''
with open('prompt_template_summarize_content.txt', 'r') as f_prompt_template_summarize_content:
  prompt_template_summarize_content = f_prompt_template_summarize_content.read()

prompt_template_summarize_discussion = ''
with open('prompt_template_summarize_discussion.txt', 'r') as f_prompt_template_summarize_discussion:
  prompt_template_summarize_discussion = f_prompt_template_summarize_discussion.read()

async def handle_general_message(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  message_interval = 0.500
  replyMessage = await update.message.reply_text('_Processing..._', parse_mode='Markdown')
  url = get_url_from_message([update.message.reply_to_message, update.message])
  if url == '':
    time.sleep(message_interval)
    message_interval += 0.250
    await replyMessage.edit_text('*ERROR*: No URL found in the message.', parse_mode='Markdown')
    return
  logging.info(f'Processing: {url}')
  uri, discussion_uri = process_url(url)
  (final_url, content) = await fetch_content(uri.geturl())
  if len([line for line in content.split('\n') if line.strip()]) == 0:
    logging.error(f'No content or discussion is fetched. Task aborted.')
    time.sleep(message_interval)
    message_interval += 0.250
    await replyMessage.edit_text('*ERROR*: No content or discussion is fetched. Task aborted.', parse_mode='Markdown')
    content = f'Error fetching content, please output this URL and summarize the words appearing in the URL instead: {final_url}.'
  prompt = prompt_template_summarize_content.format(**{
    'content': content
  })
  if len(prompt) > MAX_INPUT_LENGTH:
    time.sleep(message_interval)
    message_interval += 0.250
    await replyMessage.edit_text('_Processing..._ (content is truncated)', parse_mode='Markdown')
    await update.message.reply_text('_content is truncated_', parse_mode='Markdown')
    logging.info(f'Prompt length is ({len(prompt)} characters). Truncating to {MAX_INPUT_LENGTH} characters.')
    prompt = prompt[:MAX_INPUT_LENGTH]
    prompt += 'TRUNCATED'
  # logging.info(f'Messages: {prompt}')
  result = []
  last_sent = time.time()
  try:
    async for token in complete(prompt):
      result.append(token)
      if last_sent + message_interval < time.time():
        last_sent = time.time()
        message_interval += 0.250
        try:
          await update.message.reply_chat_action(constants.ChatAction.TYPING)
          await replyMessage.edit_text(''.join(result), parse_mode='Markdown')
        except:
          pass
  except Exception as e:
    logging.error(f'ERROR: {repr(e)}')
    time.sleep(message_interval)
    message_interval += 0.250
    await replyMessage.edit_text(f'{''.join(result)}\n*ERROR*: LLM API request failed: {repr(e)}', parse_mode='Markdown')
    return
  time.sleep(message_interval)
  message_interval += 0.250
  if len(result) == 0:
    logging.error('No result returned.')
    await replyMessage.edit_text('*ERROR*: No result returned.', parse_mode='Markdown')
  else:
    await replyMessage.edit_text(''.join(result), parse_mode='Markdown')
  
  
  discussion = ''
  if discussion_uri:
    time.sleep(message_interval)
    message_interval += 0.250
    replyMessage = await update.message.reply_text('_Processing discussion_... ', parse_mode='Markdown')
    (final_url, discussion) = await fetch_content(discussion_uri.geturl())
    if len([line for line in discussion.split('\n') if line.strip()]) == 0:
      logging.error(f'No discussion is fetched. Task aborted.')
      time.sleep(message_interval)
      message_interval += 0.250
      await replyMessage.edit_text('*ERROR*: No discussion is fetched. Task aborted.', parse_mode='Markdown')
      return
    prompt = prompt_template_summarize_discussion.format(**{
      'content': ''.join(result),
      'discussion': discussion
    })
    if len(prompt) > MAX_INPUT_LENGTH:
      logging.info(f'Prompt length is ({len(prompt)} characters). Truncating to {MAX_INPUT_LENGTH} characters.')
      await replyMessage.edit_text('_Processing..._ (discussion is truncated)', parse_mode='Markdown')
      await update.message.reply_text('_discussion is truncated_', parse_mode='Markdown')
      prompt = prompt[:MAX_INPUT_LENGTH]
      prompt += 'TRUNCATED'
    # logging.info(f'Messages: {prompt}')
    result = []
    last_sent = time.time()
    try:
      async for token in complete(prompt):
        result.append(token)
        if last_sent + message_interval < time.time():
          last_sent = time.time()
          message_interval += 0.250
          try:
            await update.message.reply_chat_action(constants.ChatAction.TYPING)
            await replyMessage.edit_text(''.join(result), parse_mode='Markdown')
          except:
            pass
    except Exception as e:
      logging.error(f'ERROR: {repr(e)}')
      time.sleep(message_interval)
      message_interval += 0.250
      await replyMessage.edit_text(f'{''.join(result)}\n*ERROR*: LLM API request failed: {repr(e)}', parse_mode='Markdown')
      return
    time.sleep(message_interval)
    if len(result) == 0:
      logging.error('No result returned.')
      await replyMessage.edit_text('*ERROR*: No result returned.', parse_mode='Markdown')
    else:
      await replyMessage.edit_text(''.join(result), parse_mode='Markdown')