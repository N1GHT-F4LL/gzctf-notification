# GZCTF Discord Notification Bot

A Discord bot that monitors GZCTF (GZCTF) platform for notifications and events, then pushes them to a Discord channel in real-time.

## Features

- **Real-time Notifications**: Monitors GZCTF platform for new notices and events
- **Rich Discord Embeds**: Beautiful formatted messages with colors and emojis
- **Multiple Notification Types**:
  - 🥇 First Blood notifications
  - 🥈 Second Blood notifications  
  - 🥉 Third Blood notifications
  - 💡 New hint releases
  - 🎯 New challenge releases
  - 🚩 Flag submissions
  - 🚀 Container start/stop events
  - ⚠️ Cheat detection alerts
- **Duplicate Prevention**: Tracks seen notifications to avoid spam
- **Persistent State**: Remembers last notification ID across restarts
- **Configurable**: Easy configuration via environment variables

## Supported Notification Types

### Game Notices (Public)
- **FirstBlood**: First team to solve a challenge
- **SecondBlood**: Second team to solve a challenge  
- **ThirdBlood**: Third team to solve a challenge
- **NewHint**: New hint released for a challenge
- **NewChallenge**: New challenge released
- **Normal**: General game announcements

### Game Events (Internal)
- **FlagSubmit**: Flag submission attempts and results
- **ContainerStart**: Challenge container started
- **ContainerDestroy**: Challenge container destroyed
- **CheatDetected**: Cheating detection alerts
- **Normal**: General game events

## Installation

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- GZCTF platform access (API token or username/password)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gzctf-notification
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create Discord Bot**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the bot token
   - Enable "Message Content Intent" under Privileged Gateway Intents

4. **Invite Bot to Server**
   - Go to "OAuth2" > "URL Generator"
   - Select "bot" scope
   - Select the following permissions:
     - **Send Messages** (Required for sending notifications)
     - **Use Slash Commands** (Required for slash commands)
     - **Embed Links** (For rich message formatting)
     - **Attach Files** (For potential file attachments)
     - **Use External Emojis** (For better message formatting)
   - Use the generated URL to invite the bot to your server
   - **Important**: Make sure the bot has access to the specific channel where you want notifications sent

5. **Configure Environment**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # GZCTF Configuration
   GZCTF_BASE_URL=http://your-gzctf-instance.com
   GZCTF_API_TOKEN=your_api_token_here
   # OR use username/password authentication
   GZCTF_USERNAME=your_username
   GZCTF_PASSWORD=your_password

   # Discord Bot Configuration
   DISCORD_TOKEN=your_discord_bot_token_here
   DISCORD_CHANNEL_ID=1234567890123456789
   DISCORD_GUILD_ID=1234567890123456789

   # Bot Configuration
   GAME_ID=1
   POLL_INTERVAL=30
   ENABLE_NOTICES=true
   ENABLE_EVENTS=true
   ```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GZCTF_BASE_URL` | GZCTF platform URL | Yes | `http://localhost:8080` |
| `GZCTF_API_TOKEN` | API token for authentication | No* | - |
| `GZCTF_USERNAME` | Username for authentication | No* | - |
| `GZCTF_PASSWORD` | Password for authentication | No* | - |
| `DISCORD_TOKEN` | Discord bot token | Yes | - |
| `DISCORD_CHANNEL_ID` | Discord channel ID for notifications | Yes | - |
| `DISCORD_GUILD_ID` | Discord guild ID (optional) | No | - |
| `GAME_ID` | GZCTF game ID to monitor | Yes | - |
| `POLL_INTERVAL` | Polling interval in seconds | No | `30` |
| `ENABLE_NOTICES` | Enable game notices | No | `true` |
| `ENABLE_EVENTS` | Enable game events | No | `true` |
| `DEBUG` | Enable debug logging | No | `false` |

*Either API token or username/password is required for authentication.

### Finding Discord Channel ID

1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on the channel you want to use
3. Click "Copy ID"

### Finding GZCTF Game ID

1. Navigate to your GZCTF platform
2. Go to the game you want to monitor
3. The game ID is usually in the URL: `https://your-gzctf.com/game/{GAME_ID}`

## Usage

### Running the Bot

```bash
python main.py
```

The bot will:
1. Authenticate with GZCTF platform
2. Connect to Discord
3. Start polling for notifications every 30 seconds (configurable)
4. Send formatted notifications to the specified Discord channel



### Debugging

If you encounter issues, you can:

1. **Enable debug mode** by setting `DEBUG=true` in your `.env` file
2. **Test API connectivity** using the debug script:
   ```bash
   python debug_api.py
   ```
3. **Test configuration** using the test script:
   ```bash
   python test_config.py
   ```
4. **Check Discord permissions** using the permission checker:
   ```bash
   python check_discord_permissions.py
   ```


## Example Notifications

### First Blood Notification
```
🥇 First Blood! 🩸
**Web Challenge** has been solved by **Team Alpha**!
Notice ID: 123
```

### New Hint Notification
```
💡 New Hint Available
New hint for **Crypto Challenge**: Check the file headers
Notice ID: 124
```

### Flag Submission
```
🚩 Flag Submission
✅ Flag submitted for **Pwn Challenge** - **ACCEPTED!**
User: hacker123
Team: Team Beta
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your GZCTF credentials
   - Ensure the API token is valid or username/password are correct
   - Verify the GZCTF base URL is accessible

2. **Discord Bot Permission Errors (403 Forbidden)**
   - Ensure the bot has been invited to your Discord server
   - Check that the bot has the following permissions in the target channel:
     - **Send Messages**
     - **Embed Links**
     - **Use External Emojis**
   - Verify the `DISCORD_CHANNEL_ID` is correct
   - Make sure the bot can see and access the specified channel
   - Check channel permissions - the bot role must have permission to send messages

3. **Bot Cannot Send Messages**
   - Right-click on the target channel → Edit Channel → Permissions
   - Add the bot role and ensure it has "Send Messages" permission
   - Check if the channel has any permission overwrites that might block the bot

2. **Discord Bot Not Responding**
   - Check the bot token is correct
   - Ensure the bot has proper permissions in the channel
   - Verify the channel ID is correct

3. **No Notifications Received**
   - Check if the game ID is correct
   - Verify the game has active notifications
   - Check the bot logs for errors

4. **Duplicate Notifications**
   - The bot tracks seen notifications to prevent duplicates
   - If you restart the bot, it may send recent notifications again

### Logs

The bot creates a log file `gzctf_bot.log` with detailed information about:
- Authentication status
- API requests and responses
- Discord message sending
- Errors and exceptions

## Development

### Project Structure

```
gzctf-notification/
├── main.py                 # Main entry point
├── config.py              # Configuration management
├── gzctf_client.py        # GZCTF API client
├── discord_bot.py         # Discord bot implementation
├── notification_formatter.py # Notification formatting
├── requirements.txt       # Python dependencies
├── env.example           # Example environment file
└── README.md             # This file
```

### Adding New Notification Types

1. Update the `NotificationFormatter` class in `notification_formatter.py`
2. Add new colors and emojis to the mapping dictionaries
3. Implement formatting logic in the appropriate methods

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Open an issue on the repository

## Acknowledgments

- GZCTF platform for providing the API
- Discord.py library for Discord integration
- Python community for excellent async libraries 