#!/bin/python

import dotenv
import logging
import os
import sys

from . import discussion_queue
from . import inactive
from . import prompts
from . import quote_quiz
from discord.ext import commands


Prompts = prompts.Prompts
Pruner = inactive.Pruner
TalkQueue = discussion_queue.TalkQueue
QuoteQuiz = quote_quiz.QuoteQuiz


dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


def main():
  if sys.stdout.isatty():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  else:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
  dotenv.load_dotenv()
  prompts = {
    'creative-writing': 'convo_prompts/prompts_writing.txt',
    'conversation-prompts': 'convo_prompts/prompts_discuss.txt',
  }
  bot = commands.Bot(command_prefix='!')
  bot.add_cog(prompts.Prompts(prompts))
  bot.add_cog(inactive.Pruner())
  bot.add_cog(discussion_queue.TalkQueue())
  bot.add_cog(quote_quiz.QuoteQuiz('quotes/quotes.txt'))
  bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
