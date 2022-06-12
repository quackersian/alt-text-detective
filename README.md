# Alt Text Detective

![v0.2.1](https://img.shields.io/badge/version-v0.2.1-blue)

A discord bot for detecting images sent without alt text/descriptions.
Useful in servers that have users with screen readers, as without the alt text the screen readers cannot function.

[Invite Link](https://discord.com/api/oauth2/authorize?client_id=984816760500932699&permissions=274877917184&scope=bot%20applications.commands)

[Support Discord](https://discord.gg/x7CyFRA5s6)


## Features
- Warning members
- Deleting images without alt text
- Admin log when messages are detected/deleted
- List the users who sent images with no alt text
- Reset the stats for your server

## Permissions Needed
- Send Messages
- Send Messages in Threads
- Manage Messages (if you want the bot to delete images without alt text.)

## License
[MIT License - Free to use and modify](https://github.com/quackersian/alt-text-detective/blob/master/LICENSE)

## Setup
1. [Invite the bot](https://discord.com/api/oauth2/authorize?client_id=984816760500932699&permissions=274877917184&scope=bot%20applications.commands) (duh!).
2. Create a role called `AltTextAdmin`, with permissions to use slash commands.
3. Assign that role to you or anyone who will change the configuration of the bot in your server (usually admins/moderators).
4. Create a channel to use for bot notifications (if you want this, leave blank if you don't).
5. Use `/setup` to setup the bot in your server (repeat this if you want to change the setup).
