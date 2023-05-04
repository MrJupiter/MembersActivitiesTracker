import discord
import os
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from keep_alive import keep_alive

SUPPORTED_ROLES = ["Apex Legends", "Valorant", "Among Us", "Pico Park", "Call Of Duty", "League Of Legends", "Counter-Strike", "Fifa", "Fortnite", "Rainbow Six Siege", "Grand Theft Auto", "Red Dead Redemption"]

supported_roles_list = list(map(lambda x: x.title(), SUPPORTED_ROLES))

COMMAND_CHOICES = []

LEGIT_SERVERS_ID = [828417721745014784, 1092836175405928478]
LEGIT_CHANNELS_ID = [1103065600735051797, 1103784396634472528]

def getGameActivity(activities):
  game_activity = ""
  for activity in activities:
    index = getIndexOfElementContainedInString(supported_roles_list, str(activity.name.title()))
    if index >= 0 and str(activity.type) == "ActivityType.playing":
      #print(activity.name)
      game_activity = supported_roles_list[index]
  return game_activity
        
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
  intents.presences = True
  bot = commands.Bot(command_prefix='/', intents=intents)

  #----------------------------------------------------------------------------------------------------------------------------
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
  #----------------------------------------------------------------------------------------------------------------------------
  
  # Update roles due to actual activity (Games only)
  @bot.event
  async def on_presence_update(before, after):
    if before.guild.id in LEGIT_SERVERS_ID:
      # When a member logged out
      if str(after.status) == discord.Status.offline:
        for game in supported_roles_list:
          role = get(after.guild.roles, name="Now " + game)
          if role in after.roles:
            await after.remove_roles(role)
      
      before_activities = getGameActivity(before.activities)
      after_activities = getGameActivity(after.activities)
      print(f"{before.name} from {before.guild.name} switched from {before.activities} to {after.activities}")
      # When a member had no activity but just launched a game
      if before_activities == "" and after_activities != "":
        await add_role(after_activities, after)
      
      # When a member switched from a game to another
      if before_activities != "" and after_activities != "":
        await remove_role(before_activities, after)
        await add_role(after_activities, after)
      
      # When a member stopped playing games (he has no more activity)
      if before_activities != "" and after_activities == "":  
        await remove_role(before_activities, after)
  
  #----------------------------------------------------------------------------------------------------------------------------
  async def isnt_legit_message(ctx: discord.Interaction):
    index = LEGIT_SERVERS_ID.index(ctx.guild_id)
    if index >= 0:
      if ctx.channel_id != LEGIT_CHANNELS_ID[index]:
        await ctx.response.send_message(f"You must execute the command in <#{LEGIT_CHANNELS_ID[index]}>", ephemeral = True) 
    
  # Bot Slash Command lfg using games' roles
  @bot.tree.command(name="lfg", description = "Send DM to all members playing a given game")
  @app_commands.describe(game = "Choose a game")
  @app_commands.choices(game = COMMAND_CHOICES)
  async def lfg(ctx: discord.Interaction, game: discord.app_commands.Choice[int]):
    if ctx.guild_id in LEGIT_SERVERS_ID:
      if ctx.channel_id in LEGIT_CHANNELS_ID:
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
      else:
        await isnt_legit_message(ctx)
    else:
      await ctx.response.send_message("Sorry to tell that you need to be in the legit servers' list to use this bot... Please, contact <@583461272046141585> to add your discord server in the legit list", ephemeral = True)
  #----------------------------------------------------------------------------------------------------------------------------
  def check_if_it_is_me(interaction: discord.Interaction) -> bool:
    return interaction.user.id == 583461272046141585
  @bot.tree.command(name="remove_all_roles", description = "Remove Now Game roles from all members")
  @app_commands.check(check_if_it_is_me)
  async def remove_all_roles(ctx: discord.Interaction):
    if ctx.guild_id in LEGIT_SERVERS_ID:
      for rolestr in supported_roles_list:
        role = discord.utils.get(ctx.guild.roles, name="Now " + rolestr)
        for member in role.members:
          await remove_role(rolestr, member)
      await ctx.response.send_message("Removed the role 'Now Game' roles from all members", ephemeral = True)
    else:
      await ctx.response.send_message("Sorry to tell that you need to be in the legit servers' list to use this bot... Please, contact <@583461272046141585> to add your discord server in the legit list", ephemeral = True)
      
  # HTTP Server persistent
  keep_alive()
  
  # Discord Application Bot Token
  bot.run(os.environ['TOKEN'])
