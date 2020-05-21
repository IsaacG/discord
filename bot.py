#!/bin/python

import dotenv
import logging
import os
import sys

import discussion_queue
import inactive
import prompts
import quote_quiz
from discord.ext import commands


Prompts = prompts.Prompts
Pruner = inactive.Pruner
TalkQueue = discussion_queue.TalkQueue
QuoteQuiz = quote_quiz.QuoteQuiz

PROMPTS = {
  'creative-writing': 'prompts/prompts_writing.txt',
  'testing': 'prompts/prompts_discuss.txt',
  'conversation-prompts': 'prompts/prompts_discuss.txt',
}
QUOTES = 'quote_quiz/quotes.txt'


def main():
  if sys.stdout.isatty():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  else:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

  dotenv.load_dotenv()
  token = os.getenv('DISCORD_TOKEN')
  if not token:
    raise RuntimeError('Missing DISCORD_TOKEN')

  bot = commands.Bot(command_prefix='!')
  bot.add_cog(prompts.Prompts(PROMPTS))
  bot.add_cog(inactive.Pruner())
  bot.add_cog(discussion_queue.TalkQueue())
  bot.add_cog(quote_quiz.QuoteQuiz(QUOTES))
  bot.run(token)


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
