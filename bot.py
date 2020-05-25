#!/bin/python

import conf
import dotenv
import logging
import os
import sys

import discussion_queue
import eight_ball
import inactive
import prompts
import quote_quiz

from discord.ext import commands


PROMPTS = {
  'creative-writing': 'prompts/prompts_writing.txt',
  'testing': 'prompts/prompts_discuss.txt',
  'conversation-prompts': 'prompts/prompts_discuss.txt',
}
QUOTES = 'quote_quiz/quotes.txt'
PRUNE_CONF = {'Some Server Name': ('welcome', 'member')}
PRUNE_CONF = conf.PRUNE_CONF  # Private config


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
  bot.add_cog(inactive.Pruner(bot, PRUNE_CONF))
  bot.add_cog(discussion_queue.TalkQueue())
  bot.add_cog(quote_quiz.QuoteQuiz(QUOTES))
  bot.add_cog(eight_ball.EightBall())
  bot.run(token)


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
