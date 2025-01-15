import logging
logger = logging.getLogger(__name__)

import typing
if typing.TYPE_CHECKING:
    import telegram

import os

ADMIN_USER_IDS = list(map(int, os.getenv('ADMIN_USER_IDS').split(',')))

async def handle_help_message(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  user_id = update.message.from_user.id
  chat_id = update.message.chat.id
  logger.info(f'user<{user_id}>@chat<{chat_id}>: {update.message.text}')
  await context.bot.set_my_commands([
    ('start', 'Start the bot'),
    ('summarize', 'Summarize the first link in the message'),
    ('help', 'Show this help message')
  ])
  logger.info(await context.bot.get_my_commands())
  await update.message.reply_text('I summarize the first link in the message')
  if user_id in ADMIN_USER_IDS:
    await update.message.reply_text('Admin commands are available.')