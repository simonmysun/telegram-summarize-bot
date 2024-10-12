import logging
logger = logging.getLogger(__name__)

import os

import typing
if typing.TYPE_CHECKING:
    import telegram

from telegram.ext import ApplicationHandlerStop

ADMIN_USER_IDS = list(map(int, os.getenv('ADMIN_USER_IDS').split(',')))
ALLOWED_TELEGRAM_USER_IDS = list(map(int, os.getenv('ALLOWED_TELEGRAM_USER_IDS').split(',')))

async def handle_permission_check(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  user_id = update.message.from_user.id
  logger.info(f'user<{user_id}>: {update.message.text}')
  if user_id not in ADMIN_USER_IDS and user_id not in ALLOWED_TELEGRAM_USER_IDS:
    logger.info(f'user<{user_id}>: Permission denied')
    await update.message.reply_text('Permission denied')
    raise ApplicationHandlerStop()
  else:
    logger.info(f'user<{user_id}>: Permission granted')