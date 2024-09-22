# !/usr/bin/env python
# -*- coding: utf-8 -*

import logging, os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from dotenv import load_dotenv
os.environ.clear()
load_dotenv()

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

from message_handler.handle_permission_check import handle_permission_check
from message_handler.handle_general_message import handle_general_message
from message_handler.handle_help_message import handle_help_message

if __name__ == '__main__':
  application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
  application.add_handler(CommandHandler('start', handle_help_message))
  application.add_handler(CommandHandler('help', handle_help_message))
  application.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & (~filters.COMMAND), handle_general_message), group=100)
  application.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & (~filters.COMMAND), handle_permission_check), group=1)
  application.run_polling()