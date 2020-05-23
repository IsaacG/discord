#!/bin/python

import collections
import datetime
import discord
import enum
import json
import logging
import more_itertools
import os
import sys
import time

from discord.ext import commands

DEBUG = False
if DEBUG: import conf


async def is_owner(ctx):
  return ctx.guild and ctx.guild.owner == ctx.author


class Pruner(commands.Cog):
  """Member management to remove inactive and grant access on activity."""

  qualified_name = 'Prune Inactive Accounts'

  # How many days since last activity before being deemed inactive.
  PRUNE_INACTIVE_TIMEOUT = 21
  PRUNE_KICK_TIMEOUT = 30

  def __init__(self, bot, config):
    super(Pruner, self).__init__()
    self.bot = bot
    self.config = config

    self._role = {}
    self._welcome_channel = {}

    self.load_history()
    self.next_save = int(time.time()) + 60 * 60

  def cog_unload(self):
    self.save_history()

  def history_file(self):
    return os.getenv('PRUNER_HISTFILE')

  def load_history(self):
    if not os.path.exists(self.history_file()):
      self.history = {}
      return
    with open(self.history_file(), 'rt') as f:
      try:
        self.history = {int(k): v for k, v in json.load(f).items()}
      except Exception:
        self.history = {}

  def save_history(self):
    with open(self.history_file(), 'wt') as f:
      json.dump(self.history, f)
    self.next_save = int(time.time()) + 60 * 60

  def get_nonmembers(self, guild):
    r = self._role[guild]
    return [m for m in guild.members if r not in m.roles]

  def ignore_guild(self, g_obj):
    return g_obj.guild not in self._welcome_channel

  def member_role(self, g_obj):
    return self._role[g_obj.guild]

  async def welcome(self, g_obj, msg):
    """Send a message to the guild welcome channel, if configured."""
    guild = g_obj.guild
    if self.ignore_guild(g_obj):
      return
    await self._welcome_channel[guild].send(msg)

  @commands.Cog.listener()
  async def on_ready(self):
    """On ready, find the welcome channels and member roles for all the connected guilds."""
    self._welcome_channel = {}
    for g in self.bot.guilds:
      if g.name not in self.config: continue

      c_name, r_name = self.config[g.name]

      cs = [c for c in g.text_channels if c.name == c_name]
      if not cs: continue
      c = cs[0]
      if not c.permissions_for(g.me).manage_roles: continue

      roles = [r for r in g.roles if r.name == r_name]
      if not roles: continue
      r = roles[0]

      self._welcome_channel[g] = c
      self._role[g] = r

  @commands.Cog.listener()
  async def on_member_join(self, member):
    print('on_member_join: %s' % member.mention)
    if self.ignore_guild(member): return
    print('welcome member')
    msg = 'Welcome, %s. Please introduce yourself to gain access to the rest of the server.' % member.mention
    await self.welcome(member, msg)

  @commands.Cog.listener()
  async def on_message(self, message):
    if self.ignore_guild(message): return
    role = self.member_role(message)

    if (not message.guild  # Direct message.
        or message.is_system()
        or isinstance(message.author, discord.User)):
      return

    m_id = message.author.id
    now = int(time.time())
    first = m_id not in self.history
    self.history[m_id] = now

    if role not in message.author.roles:
      await message.author.add_roles(role)

    if first or now > self.next_save:
      self.save_history()

  @commands.command()
  @commands.check(is_owner)
  async def list_nonmembers(self, ctx, *args):
    if self.ignore_guild(ctx): return
    nonmembers = self.get_nonmembers(ctx.guild)
    await ctx.send('%d non-members: %s' % (
        len(nonmembers), ', '.join(m.display_name for m in nonmembers)))

  @commands.command()
  @commands.check(is_owner)
  async def ping_nonmembers(self, ctx, *args):
    if self.ignore_guild(ctx): return
    msg = ctx.message.content[len(ctx.prefix + ctx.invoked_with):].strip()
    if len(msg) >= 2000:
      await ctx.send('Message len is too big. %d > 2000. Fail.' % len(msg))
      return

    nonmembers = self.get_nonmembers(ctx.guild)
    out = '%s: %s' % (', '.join(m.mention for m in nonmembers), msg)
    if len(out) < 2000:
      await self.welcome(ctx, out)
      return

    await ctx.send('Message len is too big. %d > 2000. Chunking.' % len(out))
    people = ', '.join(m.mention for m in nonmembers)
    if len(people) < 2000:
      await self.welcome(ctx, people)
      await self.welcome(ctx, msg)
      return

    people = [', '.join(m.mention for m in subset) for subset in more_itertools.chunked(nonmembers, 50)]
    if any(len(p) > 2000 for p in people):
      await ctx.send('People list too big even in chunks. Fail.')
    for p in people:
      await self.welcome(ctx, p)
    await self.welcome(ctx, msg)

  @commands.command()
  @commands.check(is_owner)
  async def prune(self, ctx, *args):
    if self.ignore_guild(ctx): return
    role = self.member_role(ctx)
    inactive_timeout = self.PRUNE_INACTIVE_TIMEOUT * 60 * 60 * 24
    now = int(time.time())
    dt_now = datetime.datetime.now()
    cutoff = now - inactive_timeout

    active = lambda m: (self.history.get(m.id, 0) > cutoff)

    never_spoke = [m for m in ctx.guild.members if m.id not in self.history]
    active      = [m for m in ctx.guild.members if active(m)]
    inactive    = list(set(ctx.guild.members) - set(never_spoke) - set(active))

    inactive_w_role = [m for m in inactive if role in m.roles]
    never_spoke_wr = [m for m in never_spoke if role in m.roles]
    drops = inactive_w_role + never_spoke_wr

    # People that joined a while ago and never spoke. Stale accounts. Kick?
    stale_cutoff = dt_now - datetime.timedelta(days=self.PRUNE_KICK_TIMEOUT)
    stale = [m for m in never_spoke if m.joined_at < stale_cutoff]

    await ctx.send('%d members, %d never spoke, %d inactive, %d active' % (len(ctx.guild.members), len(never_spoke), len(inactive), len(active)))
    await ctx.send('role_remove: Drop member from %d never spoke and %d inactive' % (len(never_spoke_wr), len(inactive_w_role)))
    await ctx.send(' '.join(m.display_name for m in drops))
    await ctx.send('kick_stale: Kick %d people that are stale (been here %d days and never spoke): %s' % (
        len(stale), self.PRUNE_KICK_TIMEOUT, ' '.join(m.display_name for m in stale)))

    if 'role_remove' in ctx.message.content.split():
      for member in drops:
        await member.remove_roles(role)
    if 'kick_stale' in ctx.message.content.split():
      for member in stale:
        await member.kick()
    await ctx.send('Done')

  @commands.command()
  @commands.check(is_owner)
  async def build_hist(self, ctx, *args):
    if self.ignore_guild(ctx): return
    role = self.member_role(message)
    last_spoke = collections.defaultdict(lambda: datetime.datetime(1990, 1, 1))
    for channel in ctx.guild.text_channels:
      if not channel.permissions_for(ctx.guild.me).read_message_history:
        continue
      async for message in channel.history(limit=10000, oldest_first=False):
        if message.is_system() or isinstance(message.author, discord.User):
          continue
        last_spoke[message.author] = max(
            last_spoke[message.author], message.created_at)
    history = {}
    for m, dt in last_spoke.items():
      dt = dt.replace(tzinfo=datetime.timezone(datetime.timedelta()))
      history[m.id] = int(dt.timestamp())
    self.history = history
    self.save_history()
    await ctx.send('Done. Built history with %d members.' % len(self.history))

    # Grant the "member" role to any active users.
    if False:
      for member in active:
        if role not in member.roles:
          await member.add_roles(role)


def main():
  # guild => (welcome channel, member role)
  CONFIG = {'Server Name': ('welcome', 'member')}

  if DEBUG:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    CONFIG = conf.PRUNE_CONF

  bot = commands.Bot(command_prefix='!')
  bot.add_cog(Pruner(bot, CONFIG))
  bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
