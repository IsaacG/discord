#!/bin/python

import os
import random
from discord.ext import commands


PROMPTS = {
  'creative-writing': 'convo_prompts/prompts_writing.txt',
  'conversation-prompts': 'convo_prompts/prompts_discuss.txt',
}


def PromptGen(lines):
  while True:
    random.shuffle(lines)
    for l in lines:
      yield l


class Prompts(commands.Cog):
  """Serve up conversation prompts."""

  qualified_name = 'Conversation Prompter'

  def __init__(self, prompts=None):
    super()
    if prompts is None:
      prompts = PROMPTS
    self.prompts = {}
    self.generator = {}
    for channel, filename in prompts.items():
      with open(filename) as f:
        lines = f.read().split('\n')
        lines = [l.strip() for l in lines]
        lines = [l for l in lines if l and not l.startswith('#')]
        # Use item position over file line number to avoid gaps.
        # This does mean it can be offset from file line number.
        lines = ['%d. %s' % (i+1, j) for i, j in enumerate(lines)]
        self.prompts[channel] = PromptGen(lines)

  @commands.command()
  async def prompt(self, ctx, *args):
    words = ctx.message.content.split()
    if ctx.channel.name not in self.prompts:
      await ctx.send('No prompts for channel %s' % ctx.channel.name)
      return
    await ctx.send(next(self.prompts[ctx.channel.name]))


def main():
  bot = commands.Bot(command_prefix='!')
  bot.add_cog(Prompts())
  bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
