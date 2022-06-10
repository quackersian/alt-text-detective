import logging, disnake, config, tokens
from disnake.ext import commands

#TODO: Replace this with the one below once your code is live. Once live, changes to commands can take up to 1 hour to sync.
bot = commands.Bot(test_guilds = [config.test_guild_id])
#bot = commands.Bot()


#sets up logging using the standard logging library. Configure the level in the config.py file.
def setup_logging():
    try:
        logging.basicConfig(
            format = "%(asctime)s %(levelname)-8s %(message)s",
            filename='bot.log',
            encoding='utf-8',
            filemode='w',
            level = config.logging_level,
            datefmt="%Y-%m-%d %H:%M:%S")
        logging.info("-----------")
        print('Setup logging correctly.')

    except Exception as e:
        print(f"ERROR - failed to setup logging - {e}") 

#Alerts once the bot is ready to receive commands
@bot.event
async def on_ready():
    print(f"{config.bot_name} ready")

#An example slash command, will respond World when you use /hello
@bot.slash_command(description="Responds with 'World'")
async def hello(inter):

    await inter.send("World")
    
    

if __name__ == "__main__":
    setup_logging()
    bot.run(tokens.live_token)
