import discord
import os
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from keep_alive import keep_alive

SUPPORTED_ROLES = ["Apex Legends", "Valorant", "Among Us", "Pico Park", "Call Of Duty", "League Of Legends", "Counter-Strike", "Fifa", "Fortnite", "Rainbow Six Siege", "Grand Theft Auto", "Red Dead Redemption"]

supported_roles_list = list(map(lambda x: x.title(), SUPPORTED_ROLES))

GAMES_CHOICES = []

RANKED_GAMES = list(map(lambda x: x.title(), ["Apex Legends", 
                                              "Valorant", 
                                              "Call Of Duty"]))

RANKED_MATRIX = {
  "Apex Legends" : [
    discord.app_commands.Choice(name="Rookie", value=1),
    discord.app_commands.Choice(name="Bronze", value=2), 
    discord.app_commands.Choice(name="Silver", value=3), 
    discord.app_commands.Choice(name="Gold", value=4), 
    discord.app_commands.Choice(name="Platinium", value=5), 
    discord.app_commands.Choice(name="Diamond", value=6), 
    discord.app_commands.Choice(name="Master", value=7), 
    discord.app_commands.Choice(name="Predator", value=8)
  ],
  "Valorant" : [
    discord.app_commands.Choice(name="Iron", value=1),
    discord.app_commands.Choice(name="Bronze", value=2), 
    discord.app_commands.Choice(name="Silver", value=3), 
    discord.app_commands.Choice(name="Gold", value=4), 
    discord.app_commands.Choice(name="Platinium", value=5), 
    discord.app_commands.Choice(name="Diamond", value=6), 
    discord.app_commands.Choice(name="Ascendant", value=7), 
    discord.app_commands.Choice(name="Immortal", value=8), 
    discord.app_commands.Choice(name="Radiant", value=9)
  ],
  "Call Of Duty" : [
    discord.app_commands.Choice(name="Bronze", value=1), 
    discord.app_commands.Choice(name="Silver", value=2), 
    discord.app_commands.Choice(name="Gold", value=3), 
    discord.app_commands.Choice(name="Platinium", value=4), 
    discord.app_commands.Choice(name="Diamond", value=5), 
    discord.app_commands.Choice(name="Crimson", value=6), 
    discord.app_commands.Choice(name="Iridescent", value=7),
    discord.app_commands.Choice(name="Top 250", value=8)
  ]
}
LEGIT_ID = {
  #server_id: [commands_channel_id, logs_channel_id]
  828417721745014784: [1103065600735051797, 1103821924418728046],
  1092836175405928478: [1103784396634472528, 1103822302572974190]
}

def getGameActivity(activities):
  game_activity = ""
  for activity in activities:
    if activity is not None:
      activity_name = activity
      if activity.name is not None:
        activity_name.name
      index = getIndexOfElementContainedInString(supported_roles_list, str(activity_name).title())
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
    GAMES_CHOICES.append(discord.app_commands.Choice(name=str(role), value=supported_roles_list.index(role)))

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
    if before.guild.id in list(LEGIT_ID.keys()):
      # When a member logged out
      if str(after.status) == discord.Status.offline:
        for game in supported_roles_list:
          role = get(after.guild.roles, name="Now " + game)
          if role in after.roles:
            await after.remove_roles(role)
      
      before_activities = getGameActivity(before.activities)
      after_activities = getGameActivity(after.activities)
      #print(f"{before.name} from {before.guild.name} switched from {before.activities} to {after.activities}")
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
  # Creating an app_commands.check
  class NotLegitServer(app_commands.CheckFailure):
    pass
  def legit_guilds():
    async def predicate(ctx):
        if ctx.guild_id not in list(LEGIT_ID.keys()):
            raise NotLegitServer("Sorry to tell that you need to be in the legit servers' list to use this bot... Please, contact <@583461272046141585> to add your discord server in the legit list")
        return True
    return app_commands.check(predicate)

  @bot.tree.error
  async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    await interaction.response.send_message(str(error), ephemeral=True)
    
  # Bot Slash Command lfg using games' roles
  @bot.tree.command(name="lfg", description = "Send DM to all members playing a given game")
  @app_commands.describe(
    game = "Choose a game",
    mode = "Choose a mode"
  )
  @app_commands.choices(
    game = GAMES_CHOICES,
    mode = [
    discord.app_commands.Choice(name='Ranked', value=1),
    discord.app_commands.Choice(name='Casual', value=2),
    ]
  )
  @legit_guilds()
  async def lfg(ctx: discord.Interaction, game: discord.app_commands.Choice[int], mode: discord.app_commands.Choice[int] = None):
      # Check if author is in a voice channel
      if ctx.user.voice is None:
        await ctx.response.send_message("Join a voice channel and retry!", ephemeral = True)
        return
      elif ctx.channel_id == LEGIT_ID.get(ctx.guild_id)[0]:
        legit_cmd_mode = True
        mode_name = "Casual"
        if mode != None:
          mode_name = mode.name
          if (mode.value == 1 and game.name not in RANKED_GAMES):
            legit_cmd_mode = False
          
        if legit_cmd_mode:
          role = discord.utils.get(ctx.guild.roles,name="Now " + game.name)
          if role:
            counter = 0
            # Iterate on all members with a given role
            for member in role.members:
              # Never send a message to the author
              if member.id != ctx.user.id:
                await member.send(f"{ctx.user.mention} is looking for a team to play **{mode_name}** in **{game.name} ** on **{str(ctx.guild.name)}** Server. You can join him here: <#{ctx.user.voice.channel.id}>")  
                counter = counter + 1
            if counter > 0:
              await ctx.response.send_message(f"I've just sent a DM to all server's members that are playing **{game.name}** : {counter} member(s)", ephemeral = True)
            else:
              await ctx.response.send_message(f"Sorry to tell you that no one is actually playing **{str(role.name).replace('Now ', '')}**...", ephemeral = True)
            # Send log message to the appropriate text channel
            logs_channel = bot.get_channel(LEGIT_ID.get(ctx.guild_id)[1])
            await logs_channel.send(f"{ctx.user.mention} used '/lfg **{game.name}** **{mode_name}**' - DM {counter} member(s)")
          else:
            await ctx.response.send_message("This game isn't supported in this server: No role found...", ephemeral = True)
        else:
          await ctx.response.send_message("This game doesn't support ranked", ephemeral = True)
      else:
        await ctx.response.send_message(f"You must execute the command in <#{LEGIT_ID.get(ctx.guild_id)[0]}>", ephemeral = True)
  
  #----------------------------------------------------------------------------------------------------------------------------
  
  @bot.tree.command(name="remove_now_roles_from_member", 
                    description = "Remove Now Game roles from all members")
  @app_commands.checks.has_permissions(administrator = True)
  @legit_guilds()
  async def remove_now_roles_from_member(ctx: discord.Interaction):
      response_txt = ""
      for rolestr in supported_roles_list:
        role = discord.utils.get(ctx.guild.roles, name="Now " + rolestr)
        if role is not None:
          counter = 0
          for member in role.members:
            await member.remove_roles(role)
            counter = counter + 1
          response_txt = response_txt + "> Removed " + str(role.name) + " from " + str(counter) + " members\n"
      logs_channel = bot.get_channel(LEGIT_ID.get(ctx.guild_id)[1])
      await logs_channel.send(f"{ctx.user.mention} used /remove_all_roles\n{response_txt}")
      await ctx.response.send_message(f"Check <#{LEGIT_ID.get(ctx.guild_id)[1]}>", ephemeral = True)

  
  @bot.tree.command(name="add_now_roles", 
                    description = "Add Now Game roles to the server")
  @app_commands.checks.has_permissions(administrator = True)
  @legit_guilds()
  async def add_now_roles(ctx: discord.Interaction):
    for srole in supported_roles_list:
      role = get(ctx.guild.roles, name="Now " + srole)
      if not role:
        await ctx.guild.create_role(name="Now " + srole, colour=discord.Colour(0x511229))
    await ctx.response.send("Added successfully all the Now roles", ephemeral = True)
    
  @bot.tree.command(name="delete_now_roles", 
                      description = "Delete Now Game roles to the server")
  @app_commands.checks.has_permissions(administrator = True)
  @legit_guilds()
  async def delete_now_roles(ctx: discord.Interaction):
    for rolestr in supported_roles_list:
      role = discord.utils.get(ctx.guild.roles, name="Now " + rolestr)
      if role is not None:
        await role.delete()
    await ctx.response.send("Removed successfully all the Now roles", ephemeral = True)  
  
  # HTTP Server persistent
  keep_alive()
  
  # Discord Application Bot Token
  bot.run(os.environ['TOKEN'])
