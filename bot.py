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

TOKEN = os.getenv('DISCORD_TOKEN')
PROMPTS = {
  'creative-writing': 'prompts/prompts_writing.txt',
  'conversation-prompts': 'prompts/prompts_discuss.txt',
}
QUOTES = 'quote_quiz/quotes.txt'


def main():
  if sys.stdout.isatty():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  else:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

  token = os.getenv('DISCORD_TOKEN')
  if not token:
    raise RuntimeError('Missing DISCORD_TOKEN')

  dotenv.load_dotenv()

  bot = commands.Bot(command_prefix='!')
  bot.add_cog(prompts.Prompts(PROMPTS))
  bot.add_cog(inactive.Pruner())
  bot.add_cog(discussion_queue.TalkQueue())
  bot.add_cog(quote_quiz.QuoteQuiz(QUOTES))
  bot.run(token)


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
