#!/bin/python

import discord
import os
import random

from discord.ext import commands


RESPONSES = [
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes - definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
]


class EightBall(commands.Cog):
  """Provide Maigic 8-Ball responses."""

  qualified_name = 'Magic 8-Ball'

  def response(self):
    return random.choice(RESPONSES)

  @commands.Cog.listener()
  async def on_message(self, message):
    # Ignore DMs. Only respond when mentioned.
    # Only respond to what might be a question.
    if (
        message.guild
        and message.guild.me in message.mentions
        and '?' in message.content[1:]
    ):
      await message.channel.send(self.response())

  @commands.command()
  async def eightball(self, ctx):
    await ctx.send(self.response())


def main():
  bot = commands.Bot(command_prefix='!')
  bot.add_cog(EightBall())
  bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
