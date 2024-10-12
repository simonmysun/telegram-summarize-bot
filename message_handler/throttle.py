import logging
logger = logging.getLogger(__name__)

import time

class Throttle:
  # https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
  # When sending messages inside a particular chat, avoid sending more than one message per second. We may allow short bursts that go over this limit, but eventually you'll begin receiving 429 errors.
  # If you're sending bulk notifications to multiple users, the API will not allow more than 30 messages per second or so. Consider spreading out notifications over large intervals of 8—12 hours for best results.
  # Also note that your bot will not be able to send more than 20 messages per minute to the same group.
  
  # --> 1 message per second, 20 messages per minute
  
  def __init__(self):
    self.queue = list()
  
  def call(self):
    self.__wait()
    self.queue.append(time.time())
    
  def busy(self):
    return len(self.queue) >= 19 or len(self.queue) > 0 and time.time() - self.queue[-1] < 1
  
  def __update(self):
    now = time.time()
    self.queue = [timestamp for timestamp in self.queue if timestamp > now - 60]
  
  def __wait(self):
    self.__update()
    now = time.time()
    if len(self.queue) >= 19:
      logger.info(f'lenth of queue = {len(self.queue)}, waiting {(now - self.queue[0])} seconds to dequeue. Throttling...')
      time.sleep(60.5 - (now - self.queue[0]))
      self.__wait()
    elif len(self.queue) > 0 and now - self.queue[-1] < 1:
      logger.info(f'last sent {(now - self.queue[-1])} second ago. Throttling...')
      time.sleep(1.5 - (now - self.queue[-1]))
      self.__wait()