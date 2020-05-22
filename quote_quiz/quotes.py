#!/bin/python

import collections
import more_itertools
import os
import random
import re
import string
from dataclasses import dataclass
from discord.ext import commands


QUOTES = 'quotes.txt'

def SuperStrip(s):
  return ''.join(l for l in s.lower() if l in string.ascii_letters + string.digits)


@dataclass
class Quote:
  quote: str
  movie: str

  def __post_init__(self):
    self.quote = self.quote.strip()
    self.movie = self.movie.strip()

  def __str__(self):
    return '%s\n%s\n' % (self.quote, self.movie)


@dataclass
class ActiveQuote:
  quote: Quote
  guesses: int = 0
  hint_count: int = 0

  def GuessMatches(self, title) -> bool:
    self.guesses += 1
    return SuperStrip(title) == SuperStrip(self.quote.movie)

  def __post_init__(self):
    title = self.quote.movie
    self.hints = [
      '%d words' % len(title.split()),
      'starts with %s' % title[0],
    ]

    letters = list(l.upper() for l in set(SuperStrip(title)))
    random.shuffle(letters)
    vowels = [l for l in letters if l in 'AEIOU']
    consts = [l for l in letters if l not in 'AEIOU']
    letters = vowels + consts
    h = []
    clue = title.upper()
    while letters:
      l = letters.pop()
      clue = re.sub(l, '_', clue)
      h.append('`%s`' % ' '.join(a for a in clue))
    h.pop()
    h.reverse()
    self.hints.extend(h)

  def Answer(self) -> str:
    return '%s --%s' % (self.quote.quote, self.quote.movie)

  def Hint(self) -> str:
    self.hint_count += 1
    if self.hint_count > len(self.hints):
      return 'Out of hints :('
    return 'Hint: %s' % self.hints[self.hint_count - 1]

  def Result(self) -> str:
    return '(%d guesses, %d hints.) The movie is: %s' % (
        self.guesses, self.hint_count, self.quote.movie)

class Quotes:

  def __init__(self, filename: str):
    self._filename = filename
    self.quotes = []
    self.LoadQuotes()

  def LoadQuotes(self):
    self.cache = []
    with open(self._filename) as f:
      for i, lines in enumerate(more_itertools.chunked(f.readlines(), 2)):
        self.cache.append(Quote(quote=lines[0], movie=lines[1]))
        
  def GetQuote(self) -> ActiveQuote:
    if not self.quotes:
      self.quotes = list(self.cache)
      random.shuffle(self.quotes)
    return ActiveQuote(quote=self.quotes.pop())

  def AddQuote(self, quote, movie):
    self.cache.append(Quote(quote=quote, movie=movie))
    self.Persist()
    
  def DelQuote(self, quote):
    self.cache.remove(quote)
    self.Persist()

  def Persist(self):
    with open(self._filename, 'wt') as f:
      for q in self.cache:
        f.write(str(q))
    

class QuoteQuiz(commands.Cog):
  """Try to guess where a quote is from."""

  qualified_name = 'Quote Quiz'
  PROMPT = 'Try to `!guess` the movie for this quote: %s'
  ATTEMPTS = 4

  def __init__(self, filename=QUOTES):
    super()
    self.quotes = Quotes(filename)
    self.adding = collections.defaultdict(dict)
    self.current = collections.defaultdict(lambda: None)

  async def NextQuote(self, ctx):
    self.current[ctx.channel] = self.quotes.GetQuote()
    await ctx.send(self.PROMPT % self.CurQ(ctx).quote.quote)

  def FullQuote(self, ctx) -> str:
    return self.CurQ(ctx).Answer()

  def CommandContent(self, ctx):
    return ctx.message.content[len(ctx.invoked_with) + 2:]

  async def MaybeAddNew(self, ctx):
    entry = self.adding[ctx.author]
    if 'quote' in entry and 'movie' in entry:
      self.quotes.AddQuote(entry['quote'], entry['movie'])
      del self.adding[ctx.author]
      await ctx.send('%s added a new quote!' % ctx.author.display_name)
    elif 'quote' in entry and 'movie' not in entry:
      await ctx.send('Now tell me what movie that was from, %s, with `!addmovie The Movie Title`' % ctx.author.display_name)
    elif 'quote' not in entry and 'movie' in entry:
      await ctx.send('Now tell me the quote from that movie, %s, with `!addquote The Best Quote Ever`' % ctx.author.display_name)

  def CanMoveOn(self, ctx) -> bool:
    interactions = self.CurQ(ctx).guesses + self.CurQ(ctx).hint_count
    return interactions >= self.ATTEMPTS

  def CurQ(self, ctx) -> ActiveQuote:
    return self.current[ctx.channel]

  def IsActive(self, ctx) -> bool:
    return self.CurQ(ctx) is not None

  @commands.command()
  async def quote(self, ctx):
    if not self.IsActive(ctx):
      await self.NextQuote(ctx)
    else:
      if self.CanMoveOn(ctx):
        await ctx.send(self.FullQuote(ctx))
        await self.NextQuote(ctx)
      else:
        await ctx.send('Try a bit more or take a `!hint`. Quote: %s' % self.CurQ(ctx).quote.quote)

  @commands.command()
  async def guess(self, ctx):
    if not self.IsActive(ctx):
      return
    if self.CurQ(ctx).GuessMatches(self.CommandContent(ctx)):
      await ctx.send('%s got it! %s' % (
          ctx.author.display_name, self.CurQ(ctx).Result()))
      await self.NextQuote(ctx)
    else:
      await ctx.send('%s, that is not it.' % ctx.author.display_name)

  @commands.command()
  async def hint(self, ctx):
    if not self.IsActive(ctx):
      return
    await ctx.send(self.CurQ(ctx).Hint())

  @commands.command()
  async def delquote(self, ctx):
    if not self.IsActive(ctx):
      return
    self.quotes.DelQuote(self.CurQ(ctx).quote)
    await ctx.send('Deleted the last quote (%s)' % self.FullQuote(ctx))
    await self.NextQuote(ctx)

  @commands.command()
  async def addquote(self, ctx):
    self.adding[ctx.author]['quote'] = self.CommandContent(ctx)
    await self.MaybeAddNew(ctx)

  @commands.command()
  async def addmovie(self, ctx):
    self.adding[ctx.author]['movie'] = self.CommandContent(ctx)
    await self.MaybeAddNew(ctx)


def main():
  if False:
    q = Quote(quote='', movie='Mommie Dearest')
    a = ActiveQuote(quote=q)
    print('\n'.join(a.hints))
    return

  token = os.getenv('DISCORD_TOKEN')
  if token is None:
    raise Exception('Token not found')
  bot = commands.Bot(command_prefix='!')
  bot.add_cog(QuoteQuiz())
  bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
