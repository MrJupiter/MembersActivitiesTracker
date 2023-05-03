import discord
import os
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from keep_alive import keep_alive

SUPPORTED_ROLES = ["Apex Legends", "VALORANT", "Among Us", "PICO PARK", "Call of Duty", "League Of Legends", "Call of War", "Fifa"]

supported_roles_list = list(map(lambda x: x.title(), SUPPORTED_ROLES))

COMMAND_CHOICES = []

# Used to get the index of a list element contained in a string
def getIndexOfElementContainedInString(str_list, str):
  str1 = str.title()
  str_list1 = list(map(lambda x: x.title(), str_list))
  for item in str_list1:
    if item in str1:
      return str_list1.index(item)
  return -1

# Used to create app_commands.choices list -> COMMAND_CHOICES
def addCommandChoice():
  for role in supported_roles_list:
    COMMAND_CHOICES.append(discord.app_commands.Choice(name=str(role), value=supported_roles_list.index(role)))

# Used to add a role from supported_roles_list
async def add_role(rolestr, member):
  if rolestr.title() in supported_roles_list and get(member.guild.roles, name="Now " + rolestr.title()):
    await member.add_roles(get(member.guild.roles, name="Now " + rolestr.title()))
    
# Used to remove a role from supported_roles_list
async def remove_role(rolestr, member):
  if rolestr.title() in supported_roles_list and get(member.guild.roles, name="Now " + rolestr.title()):
    await member.remove_roles(get(member.guild.roles, name="Now " + rolestr.title()))

# Used to run the bot in main.py
def run_discord_bot():
  intents = discord.Intents.all()
  intents.message_content = True
  intents.members = True 
  bot = commands.Bot(command_prefix='/', intents=intents)

  # When the discord bot is up sync the new tree command and create COMMAND_CHOICES
  @bot.event
  async def on_ready():
    print("Bot is Up")
    addCommandChoice()
    try:
      synced = await bot.tree.sync()
      print(f"Synced {len(synced)} command(s)")
    except Exception as e:
      print(e)

  # Bot Slash Command lfg using games' roles
  @bot.tree.command(name="lfg", description = "Send DM to all members playing a given game")
  @app_commands.describe(game = "Choose a game")
  @app_commands.choices(game = COMMAND_CHOICES)
  async def lfg(ctx: discord.Interaction, game: discord.app_commands.Choice[int]):
    role = discord.utils.get(ctx.guild.roles,name="Now " + game.name)
    # Check if author is in a voice channel
    if ctx.user.voice is None:
      await ctx.response.send_message("Join a voice channel and retry!", ephemeral = True)
      return
    counter = 0
    # Iterate on all members with a given role
    for member in role.members:
      # Never send a message to the author
      if member.id != ctx.user.id:
        await member.send(f"{ctx.user.mention} is looking for a team to play **{str(role.name).replace('Now ', '')}** on **{str(ctx.guild.name)}** Server. You can join him here: <#{ctx.user.voice.channel.id}>")
        counter = counter + 1
    if counter > 0:
      await ctx.response.send_message(f"I've just sent a DM to all server's members that are playing **{str(role.name).replace('Now ', '')}** : {counter} member(s)", ephemeral = True)
    else: 
      await ctx.response.send_message(f"Sorry to tell you that no one is actually playing **{str(role.name).replace('Now ', '')}**...", ephemeral = True)

  # Update roles due to actual activity (Games only)
  @bot.event
  async def on_presence_update(before, after):
    # When a member logged out
    if str(after.status) == discord.Status.offline:
      for game in supported_roles_list:
        role = get(after.guild.roles, name="Now " + game)
        if role in after.roles:
          await after.remove_roles(role)
    
    # When a member had no activity but just launched a game
    if len(before.activities) == 0 and len(after.activities) > 0 and str(after.activities[-1].type) == "ActivityType.playing":
      #print(f"{after.name} started playing {after.activities[-1].name}")
      current_rolestr = str(after.activities[-1].name)
      index = getIndexOfElementContainedInString(supported_roles_list, current_rolestr)
      if index >= 0:
        await add_role(supported_roles_list[index], after)
    
    # When a member switched from a game to another
    if len(before.activities) > 0 and len(after.activities) > 0 and str(before.activities[-1].type) == "ActivityType.playing" and str(after.activities[-1].type) == "ActivityType.playing":
      before_rolestr = str(before.activities[-1].name)
      after_rolestr = str(after.activities[-1].name)
      #print(f"{after.name} switched from  {before.activities[-1].name} to {after.activities[-1].name}")
      index_before = getIndexOfElementContainedInString(supported_roles_list, before_rolestr)
      if index_before >= 0:
        await remove_role(supported_roles_list[index_before], after)
      index_after = getIndexOfElementContainedInString(supported_roles_list, after_rolestr)
      if index_after >= 0:
        await add_role(supported_roles_list[index_after], after)
    
    # When a member stopped playing games (he has no more activity)
    if len(before.activities) > 0 and len(after.activities) == 0 and str(before.activities[-1].type) == "ActivityType.playing":  
      #print(f"{after.name} stopped playing {before.activities[-1].name}")
      before_rolestr = str(before.activities[-1].name)
      index_before = getIndexOfElementContainedInString(supported_roles_list, before_rolestr)
      if index_before >= 0:
        await remove_role(supported_roles_list[index_before], after)

  # HTTP Server persistent
  keep_alive()
  
  # Discord Application Bot Token
  bot.run(os.environ['TOKEN']) 