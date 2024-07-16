import typing
if typing.TYPE_CHECKING:
    import telegram

import os, logging

ADMIN_USER_IDS = list(map(int, os.getenv('ADMIN_USER_IDS').split(',')))
ALLOWED_TELEGRAM_USER_IDS = list(map(int, os.getenv('ALLOWED_TELEGRAM_USER_IDS').split(',')))

async def handle_help_message(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  userId = update.message.from_user.id
  logging.info(f'user<{userId}>: {update.message.text}')
  await context.bot.set_my_commands([
    ('start', 'Start the bot'),
    ('help', 'Show this help message')
  ])
  logging.info(await context.bot.get_my_commands())
  if userId in ADMIN_USER_IDS or userId in ALLOWED_TELEGRAM_USER_IDS:
    await update.message.reply_text('I summarize the first link in the message')
  if userId in ADMIN_USER_IDS:
    await update.message.reply_text('Admin commands are available.')
  else:
    await update.message.reply_text('Permission denied')