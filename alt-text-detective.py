import logging, disnake, config, tokens, sqlite3, sys
from disnake.ext import commands

req_intents = disnake.Intents.default()
req_intents.members = True
req_intents.message_content = True
bot = commands.InteractionBot(intents=req_intents, test_guilds=[config.test_guild_id])


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


    #If we failed to set up the logger then we can't record any information, so we need to quit.
    except Exception as e:
        print(f"Failed to setup logging. {e}.") 
        sys.exit()



#connects to the db file and creates the guild table if it doesn't already exist.
def setup_db():    
    try:
        #creates the db if it doesn't already exist.
        con = sqlite3.connect(config.db) 
        cur = con.cursor()
        #creates the guild config table if it doesn't already exist.
        cur.execute("CREATE TABLE IF NOT EXISTS guilds (gi INTEGER PRIMARY KEY, dim TEXT, alc INTEGER, nu TEXT, ns TEXT)")
        con.commit()
        #creates the user logging table if it doesn't already exist.
        cur.execute("CREATE TABLE IF NOT EXISTS users (uid INTEGER PRIMARY KEY, msg INTEGER, gid INTEGER)")
        con.commit()

        con.close()
        logging.info(f"Connected to {config.db} OK.")            

    #if we can't connect then we can't do the main job of the bot, so stop running.
    except Exception as e:
        logging.exception(f"Failed to connect to {config.db}. {e}.")
        sys.exit()


def increase_count(
    user_id: int=None,
    guild_id: int=None,
    amount_to_increase: int=1
    ):
    """Updates the total invalid messages sent by a user
    
    Parameters
    ----------
    user_id: :class:`int`
        the discord id of the user to increase
    guild_id: :class:`int`
        the guild id the user is in
    amount_to_increase: :class:`int`
        the amount to increase the user's count by. Default is 1.
    
    Returns
    ----------
    None

    """
    #catch if no parameters were passed.
    if user_id is None or guild_id is None:
        logging.warning(f"Tried to increase count without parameters.")
        return

    try:
        con = sqlite3.connect(config.db) 
        cur = con.cursor()
        
        cur.execute("SELECT msg FROM users where uid=? AND gid=?", (user_id,guild_id))
        current_count = cur.fetchone()
            

        #the user didn't exist in the table, so we need to add them.    
        if current_count is None:      
            logging.info(f"{user_id} not found, adding in.")      
            cur.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, amount_to_increase, guild_id))
            con.commit()
            con.close()            
                  
        else:
            new_count = amount_to_increase + int(current_count[0])

            cur.execute("UPDATE users SET msg=? WHERE uid=? AND gid=?", (new_count, user_id, guild_id))
            con.commit()
            con.close()

            logging.info(f"Successfully increased count for {user_id} to {new_count}.")


    except Exception as e:
        logging.exception(f"Failed to increase count for {user_id}. {e}")
        try:
            #try to gracefully close the connection to db on exception, might not work depending on where the exception was.
            #TODO: can we handle this more gracefully?
            con.close()
        finally:
            pass

        return
       
       
def get_guild_naughty_list(
    guild_id: int=None
    ):
    """Gets the list of bad users for the given guild.
    
    Parameters
    ----------
    guild_id: :class:`int`
        the guild id to check
    
    Returns
    ----------
    list_of_users :class:`list`
        A list of users by id, and their associated number of bad messages

    """    
    try:
        con = sqlite3.connect(config.db) 
        cur = con.cursor()

        cur.execute("SELECT * FROM users where gid=?",(guild_id,))
        list_of_users = []
        list_of_users = cur.fetchall()
        con.close()

        return list_of_users

    except Exception as e:
        logging.exception(f"Failed to get list of users for {guild_id}. {e}")
        return None



#Alerts once the bot is ready to receive commands
@bot.event
async def on_ready():
    game = disnake.Game("with images")#status is always "playing x" where x is game
    await bot.change_presence(status=disnake.Status.online, activity=game)
    logging.info(f"{config.bot_name} ready")
    print(f"{config.bot_name} ready")
     

#creates the admin role when joining a server
@bot.event
async def on_guild_join(
    guild: disnake.Guild
    ):

    logging.info(f"Joined {guild.name}.")


#called when the bot leaves/is kicked/is banned from a guild.
@bot.event
async def on_guild_remove(
    guild: disnake.Guild
    ):

    logging.info(f"Left {guild.name}.")



@bot.slash_command(description="Gets the list of users and bad messages for the guild.", dm_permission=False)
async def naughty(
    inter: disnake.ApplicationCommandInteraction
    ):

    logging.info(f"{inter.author} got the naughty list")

    naughty_users = get_guild_naughty_list(inter.guild.id)

    if naughty_users is None:
        #something went wrong getting the list
        logging.warning(f"None returned from get_guild_naughty_list.")
        await inter.send("Failed to get list, try again later.", ephemeral=True)
        return
    
    elif len(naughty_users) == 0:
        #there were no entries for the guild
        logging.info(f"No entries found for {inter.guild_id}")
        await inter.send(f"No entries for your guild. Well done!", ephemeral=True)
    
    else:
        #sort the naughty list by most naughty messages 
        naughty_users.sort(key = lambda tup: tup[1], reverse=True)

        #create an embed with the info on it
        naughty_embed = disnake.Embed(title="Naughty User Rankings")
        
        for user in naughty_users:

            member = await inter.guild.getch_member(user[0])            
            if user[1] == 1:
                naughty_embed.add_field(name=member.name, value=f"{user[1]} naughty message", inline=False)
            else:
                naughty_embed.add_field(name=member.name, value=f"{user[1]} naughty messages", inline=False)

        await inter.send(embed=naughty_embed)


#clears any stats from users in the guild 
@commands.has_role(config.bot_admin_role)
@bot.slash_command(description="Resets the stats for your server.", dm_permission=False)
async def reset(
    inter: disnake.ApplicationCommandInteraction,
    ):
    logging.debug(f"Attempting to delete records for {inter.guild_id} by {inter.author}")
    try:
        con = sqlite3.connect(config.db)
        cur = con.cursor()

        cur.execute("DELETE FROM users WHERE gid=?", (inter.guild_id,))
        con.commit()
        con.close()
        logging.info(f"Deleted records for {inter.guild_id}")
        await inter.send("Successfully reset the stats for your server.", ephemeral=True)

    except Exception as e:
        con.close()
        logging.exception(f"Failed to reset stats for {inter.guild_id}. {e}")
        await inter.send("Failed to reset stats. Try again later.", ephemeral=True)


@reset.error
async def reset_error(
    inter: disnake.ApplicationCommandInteraction,
    error
    ):
    logging.info(f"{inter.author} tried to reset {inter.guild_id} but didn't have permissions.")
    await inter.send("You don't have permission to do that.", ephemeral=True)




#command to set up the bot on how to respond to images sent.
@commands.has_role(config.bot_admin_role)#checks that the user has the bot admin role.
@bot.slash_command(description="Configures the settings for your guild", dm_permission=False)#can't be used in a DM
async def setup(
    inter: disnake.ApplicationCommandInteraction,
    delete_invalid_messages: bool = commands.Param(default = False, description="True = delete invalid messages, False = don't delete invalid messages. False by default."),
    action_log_channel: disnake.TextChannel = commands.Param(default=0, description="What channel to log any deleted message info to. Leave blank if you don't want this."),
    notify_user: bool = commands.Param(default=True, description="Whether to notify the user if they upload an image without a description. True by default."),
    notify_silently: bool = commands.Param(default=True, description="Whether to notify the user silently, or let everyone see. True by default.")
    ):

    #convert the parameters to accepted db types
    delete_invalid_messages = str(delete_invalid_messages)
    action_log_channel = int(action_log_channel.id)
    notify_user = str(notify_user)
    notify_silently = str(notify_silently)

    #could take a while to sort db response out, so defer the update - shows as "botname is thinking..."
    await inter.response.defer(ephemeral=True)

    #check we can actually connect to the db
    try:
        con = sqlite3.connect(config.db)     
        cur = con.cursor()    
    except Exception as e:
        logging.exception(f"Cannot connect to db. {e}.")
        await inter.edit_original_message(content="Failed to save config, try again later.")
    
    

    #check if the guild already exists in the database
    gi = int(inter.guild_id)
    cur.execute("SELECT * FROM guilds WHERE gi = ?", (gi,))#parameters need to be sent as a tuple, so we need the trailing ',' to make a 1 element tuple
    
    guild_exists = cur.fetchone()

    if guild_exists:
        #guild is already in db, so just update with new parameters from the slash command
        logging.info(f"Trying to update config for {inter.guild_id}.")
        
        try:
            #update the db with the parameters            
            cur.execute("UPDATE guilds SET dim=?, alc=?, nu=?, ns=? WHERE gi=?", (delete_invalid_messages, action_log_channel, notify_user, notify_silently, inter.guild_id))        
            con.commit()
            con.close()
            logging.info(f"Updated config for {inter.guild_id}.")
            await inter.edit_original_message(content="Successfully saved config!")


        except Exception as e:
            #if something goes wrong then inform the user
            logging.exception(f"Failed to update db. {e}")
            await inter.edit_original_message(content="Failed to save config, try again later.")


    else:
        #guild doesn't exist in the db, so insert new data
        logging.info(f"Saving config for new guild {inter.guild_id}")
        
        try:
            #insert the data into the db using the parameters from the slash command
            cur.execute("INSERT INTO guilds(gi, dim, alc, nu, ns) VALUES (?,?,?,?,?)", (inter.guild_id, delete_invalid_messages, action_log_channel, notify_user, notify_silently))
            con.commit()
            con.close()
            logging.info(f"Saved new config for {inter.guild_id}")
            await inter.edit_original_message(content="Successfully saved config!")


        except Exception as e:
            con.close()
            logging.exception(f"Failed to save config for new guild. {e}.")
            await inter.edit_original_message(content="Failed to save config, try again later.")
            

@setup.error
async def setup_error(ctx: disnake.ApplicationCommandInteraction, error):
    if isinstance(error, commands.CheckFailure):
        logging.info(f"{ctx.author} tried to use the 'setup' command, but didn't have the '{config.bot_admin_role}' role.")
        await ctx.send(f"You don't have permission to do that.", ephemeral=True)
    


#Checking messages sent for images with no alt-text/description
@bot.event
async def on_message(
    ctx: disnake.Message
    ):

    #only care about messages with attachments, from users not bots, and sent in a guild
    if ctx.guild is not None and not ctx.author.bot and len(ctx.attachments) != 0: 

        #connect to the db to check server config        
        con = sqlite3.connect(config.db)     
        cur = con.cursor() 

        #get the info on the guild the message was sent in
        cur.execute("SELECT * FROM guilds WHERE gi=?", (ctx.guild.id,))
        server_config = cur.fetchone()
        con.close()
        if server_config is not None:

            delete_invalid_messages = server_config[1]
            action_log_channel = server_config[2]
            notify_user = server_config[3]
            notify_silently = server_config[4]

            for att in ctx.attachments:

                #only care about image attachments
                if "image" in att.content_type:

                    logging.info(f"Checking images from {ctx.author} in {ctx.guild.name}.")

                    if att.description is None:
                        logging.info(f"Found images with no alt text in {ctx.guild.name}.")

                        increase_count(user_id = ctx.author.id, guild_id = ctx.guild.id, amount_to_increase=len(ctx.attachments))

                        #depending on config, we might notify the user, delete the message, record the action in a separate channel.
                        if notify_user == "True":
                            if notify_silently == "True":
                                await ctx.channel.send(f"Hey {ctx.author.mention}, please add descriptions to your images!", delete_after=5)
                            else:
                                await ctx.channel.send(f"Hey {ctx.author.mention}, please add descriptions to your images!")

                        if delete_invalid_messages == "True":
                            await ctx.delete()
                        
                        if action_log_channel != 0:
                            #log the user and channel that the invalid image was sent in.
                            log_channel = await ctx.guild.fetch_channel(action_log_channel)
                            try:
                                if delete_invalid_messages == "True":
                                    await log_channel.send(f"Deleted an image from {ctx.author.mention}  in {ctx.channel.mention} with no alt-text.")
                                else:
                                    await log_channel.send(f"Found an image from {ctx.author.mention}  in {ctx.channel.mention} with no alt-text. \n {ctx.jump_url}")
                            
                            except disnake.errors.Forbidden:
                                #if the bot doesn't have access to the channel
                                logging.warning(f"Couldn't log message in {log_channel}.")

                    else:
                        logging.debug("Image had description, well done!")

        else:
            #the server hasn't got a config.
            logging.warning(f"{ctx.guild.id} doesn't have a config setup.")


@bot.slash_command(description="Info about the bot.")
async def info(
    inter: disnake.ApplicationCommandInteraction
    ):

        logging.info(f"{inter.author} checked bot info.")  

        info_embed = disnake.Embed(title="Space Bot Info")
        info_embed.add_field(name="Version", value=config.script_version + " - " + config.script_date, inline=True)
        info_embed.add_field(name="Joined servers", value=len(bot.guilds), inline=True)
        info_embed.add_field(name="Discord Support Server", value=config.discord_server, inline=False)
        info_embed.add_field(name="Bot Invite Link", value=config.invite_link, inline=False)
        info_embed.add_field(name="Bot Code on Github", value=config.github_link, inline=False)
               
        await inter.send(embed=info_embed)






@commands.is_owner()
@bot.slash_command(description="Secret")
async def secret(
    inter: disnake.ApplicationCommandInteraction,
    short: bool = commands.Param(default=True, description="Show only the latest 10 joined servers, or the full info.")
    ):

        logging.info(f"{inter.author} checked secret bot info.")
     
        joined_guilds = []
        guild_count = len(bot.guilds)

        for guild in bot.guilds:
            #gather guild info in a tuple in a list(?) so we can sort by joined date in the embed.
            join_date = guild.me.joined_at
            join_date = join_date.strftime("%Y-%m-%d %H:%M:%S")
            joined_guilds.append((join_date, guild.name, guild.member_count))            
        
        #sorting the guilds by join date newest to oldest
        joined_guilds.sort(key = lambda tup: tup[0], reverse=True) # from https://stackoverflow.com/questions/3121979/

        if short == True:
        #only show the 10 most recently joined guilds
            guild_embed = disnake.Embed(title="Joined Server Info")

            for i in range(min(10, guild_count)):
                guild_embed.add_field(name=joined_guilds[i][1], value=f"Joined on {joined_guilds[i][0]}. {joined_guilds[i][2]} members.", inline=False)
            
            guild_embed.set_footer(text=f"{config.bot_name} is in {guild_count} servers.")
            await inter.send(embed=guild_embed, ephemeral=True)

        else:
        #show all the guild info in one big message. 2,000 character limit
          
            guild_message = f"**__{config.bot_name} is in {guild_count} servers__** \n\n"
            for guild in joined_guilds:
                guild_message += f"__{guild[1]}__ \n"
                guild_message += f"*Joined on {guild[0]}. {guild[2]} members.* \n\n"
           
            try:
                await inter.send(guild_message, ephemeral=True)
          
            except disnake.HTTPException as e:
                if e.code == 50035:
                    with open("guild_message.txt", "w")as f:
                        f.write(guild_message)
                    guild_file = disnake.File(filename="guild_message.txt")
                    #the message we tried to send was more than 2000 characters, so blocked by the API.
                    logging.warning(f"{config.bot_name} is in {guild_count} servers, message length was {len(guild_message)}. Sent file instead.")
                    await inter.send("I'm so popular, I'm in too many guilds to mention!", ephemeral=True, file=guild_file)

                else:
                    #some other HTTP exception
                    logging.exception(e)
                    await inter.send("Something went wrong, sorry!", ephemeral=True)
            
            except Exception as e:
                #some other exception
                logging.exception(e)
                await inter.send("Something went wrong, sorry!", ephemeral=True)


@secret.error
async def secret_error(inter: disnake.ApplicationCommandInteraction, error):
    logging.info(f"{inter.author.name} tried to use the secret command.")
    await inter.send("You don't have permission to use that.", ephemeral=True)


if __name__ == "__main__":
    setup_logging()
    setup_db()
    bot.run(tokens.test_bot_token)
