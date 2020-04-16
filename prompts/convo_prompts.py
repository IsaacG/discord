#!/bin/python

import os
import random
from discord.ext import commands


PROMPTS = {
  'creative-writing': 'convo_prompts/prompts_writing.txt',
  'conversation-prompts': 'convo_prompts/prompts_discuss.txt',
}


class Prompts(commands.Cog):
  """Serve up conversation prompts."""

  qualified_name = 'Conversation Prompter'

  def __init__(self):
    super()
    self.prompts = {}
    for channel, filename in PROMPTS.items():
      with open(filename) as f:
        lines = f.read().split('\n')
        lines = [l.strip() for l in lines if l.strip()]
        self.prompts[channel] = lines


  @commands.command()
  async def prompt(self, ctx, *args):
    if ctx.channel.name not in self.prompts:
      await ctx.send('No prompts for channel %s' % ctx.channel.name)
    else:
      await ctx.send(random.choice(self.prompts[ctx.channel.name]))


def main():
  bot = commands.Bot(command_prefix='!')
  bot.add_cog(Prompts())
  bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
