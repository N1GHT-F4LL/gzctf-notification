# GZCTF Discord Notification Bot

A Discord bot that monitors GZCTF platform for notifications and events, then pushes them to a Discord channel in real-time.

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
- **Smart Authentication**: Automatically refreshes authentication tokens to maintain connection
- **Robust Error Handling**: Gracefully handles connection issues and API errors

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
- GZCTF platform access (username/password)

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
     - **Use External Emojis** (For better message formatting)
   - Use the generated URL to invite the bot to your server
   - **If you want the bot to auto-create channels for notifications and events, grant it the `Manage Channels` permission.**
   - The bot will auto-create (or use) two channels:
     - **Notification channel** (public): For general notices like First Blood, New Challenges
     - **Event channel** (private): For sensitive data like flag submissions, user activities
   - You can customize these names via environment variables.

5. **Configure Environment**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # GZCTF Configuration
   GZCTF_BASE_URL=https://your-gzctf-instance.com
   GZCTF_USERNAME=your_username
   GZCTF_PASSWORD=your_password

   # Discord Bot Configuration
   DISCORD_TOKEN=your_discord_bot_token_here
   DISCORD_GUILD_ID=your_discord_server_id
   # Optional: Custom channel names (default: notification, event)
   NOTIFICATION_CHANNEL_NAME=notification
   EVENT_CHANNEL_NAME=event

   # Bot Configuration
   GAME_ID=1
   POLL_INTERVAL=30
   ENABLE_NOTICES=true
   ENABLE_EVENTS=true
   DEBUG=false
   TZ=Asia/Ho_Chi_Minh
   ```

## Configuration

### Environment Variables

| Category | Variable | Required | Default | Description |
|----------|----------|----------|---------|-------------|
| GZCTF | `GZCTF_BASE_URL` | Yes | - | GZCTF platform URL |
| GZCTF | `GZCTF_USERNAME` | Yes | - | Monitor user credentials |
| GZCTF | `GZCTF_PASSWORD` | Yes | - | Monitor user credentials |
| Discord | `DISCORD_TOKEN` | Yes | - | Bot token |
| Discord | `DISCORD_GUILD_ID` | Yes | - | Target server ID |
| Bot | `GAME_ID` | Yes | - | Target game ID |
| Bot | `POLL_INTERVAL` | No | 30 | Polling frequency (seconds) |
| Bot | `ENABLE_NOTICES` | No | true | Enable notice monitoring |
| Bot | `ENABLE_EVENTS` | No | true | Enable event monitoring |
| Channels | `NOTIFICATION_CHANNEL_NAME` | No | notification | Public channel name |
| Channels | `EVENT_CHANNEL_NAME` | No | event | Private channel name |
| System | `DEBUG` | No | false | Debug logging |
| System | `LOG_DIR` | No | /app/logs | Log directory |
| System | `TZ` | No | UTC | Timezone |

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

#### Using Python directly

```bash
python bot/main.py
```

#### Using Docker (recommended)

```bash
docker-compose up -d
```

The bot will:
1. Authenticate with GZCTF platform using cookie-based authentication
2. Connect to Discord
3. Create/setup channels based on configuration:
   - **Public notification channel**: Created only if ENABLE_NOTICES=true
   - **Private event channel**: Created only if ENABLE_EVENTS=true
4. Start polling for notifications every 30 seconds (configurable)
5. Send formatted notifications to the appropriate Discord channels
6. Write logs to `logs/gzctf_bot.log` locally or `/app/logs/gzctf_bot.log` in Docker.
7. Automatically refresh authentication when needed:
   - Every 30 polling cycles (approximately 15 minutes with default settings)
   - After 1 hour regardless of polling count
   - When token validation fails

### Private Event Channel Management

The bot automatically creates a private event channel that only administrators and the bot can access. This protects sensitive information like:
- Flag submission attempts and results
- User activity logs
- Container start/stop events
- Cheat detection alerts

#### Default Permissions:
- **@everyone**: No access (cannot see the channel)
- **Bot**: Full access (can send messages and embeds)
- **Admin/Moderator roles**: Full access (automatically detected)

### Debugging

If you encounter issues, you can:

1. **Enable debug mode** by setting `DEBUG=true` in your `.env` file
2. **Test API connectivity** using the debug script:
   ```bash
   python scripts/debug_api.py
   ```
3. **Test configuration** using the test script:
   ```bash
   python scripts/test_config.py
   ```
4. **Verify Discord permissions and private channel setup** using the verifier:
   ```bash
   python scripts/verify_permissions.py
   ```

### Utility Scripts

- **debug_api.py**: Debug GZCTF endpoints using the same cookie-based auth as the bot
  - Run: `python scripts/debug_api.py`
  - Logs auth status, game info, notices, events; detects 403 on events and warns
- **test_simple.py**: Quick end-to-end test for auth + notices/events via `GZCTFClient`
  - Run: `python scripts/test_simple.py`
- **test_config.py**: Print the configuration loaded from `.env`
  - Run: `python scripts/test_config.py`
- **verify_permissions.py**: Verify guild/channel permissions and ensure the event channel is private
  - Run: `python scripts/verify_permissions.py`
- **generate_invite_link.py**: Generate a bot invite link with recommended permissions
  - Run: `python scripts/generate_invite_link.py`

### Editor/IDE import hints

- Scripts under `scripts/` add the `bot/` folder to `sys.path` at runtime, so imports work when executing scripts.
- If your IDE (Pylance/Pyright) reports "reportMissingImports" for `config` or `gzctf_client`, add this to `.vscode/settings.json`:
  ```json
  {
    "python.analysis.extraPaths": ["./bot"]
  }
  ```
  Alternatively, set `PYTHONPATH` to the `bot` folder for your editor session.

## Example Notifications

### First Blood Notification
```
🥇 First Blood!
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
   - Ensure username/password are correct
   - Verify the GZCTF base URL is accessible
   - The bot now uses cookie-based authentication with GZCTF_Token
   - Authentication is refreshed automatically based on:
     - Every 30 polling cycles (configurable)
     - After 1 hour of operation (time-based refresh)
     - When token validation fails

2. **Discord Bot Permission Errors (403 Forbidden)**
   - Ensure the bot has been invited to your Discord server
   - Check that the bot has the following permissions in the target channel:
     - **Send Messages**
     - **Embed Links**
     - **Use External Emojis**
   - Verify `DISCORD_GUILD_ID` is correct
   - Make sure the bot can see and access the specified channel
   - Check channel permissions - the bot role must have permission to send messages

3. **Bot Cannot Send Messages**
   - Right-click on the target channel → Edit Channel → Permissions
   - Add the bot role and ensure it has "Send Messages" permission
   - Check if the channel has any permission overwrites that might block the bot

4. **Discord Bot Not Responding**
   - Check the bot token is correct
   - Ensure the bot has proper permissions in the channel
   - Verify the channel ID is correct

5. **No Notifications Received**
   - Check if the game ID is correct
   - Verify the game has active notifications
   - Check the bot logs for errors

6. **Duplicate Notifications**
   - The bot tracks seen notifications to prevent duplicates
   - If you restart the bot, it may send recent notifications again

### Logs

By default, logs are written to `./logs/gzctf_bot.log` (local runs) or `/app/logs/gzctf_bot.log` (Docker). You can override the folder with `LOG_DIR`.

Log file uses rotation (5 MB, 3 backups). It includes detailed information about:
- Authentication status
- API requests and responses
- Discord message sending
- Errors and exceptions

## System Architecture

The bot is organized with a clear modular structure:

1. **config.py**: Manages configuration from environment variables
2. **gzctf_client.py**: API client for communicating with GZCTF
   - Handles cookie-based authentication with GZCTF_Token
   - Manages session cookies with proper domain settings
   - Implements automatic token refresh mechanisms
3. **notification_formatter.py**: Formats notifications into Discord embeds
4. **discord_bot.py**: Handles Discord connection and sending notifications
   - Implements smart authentication refresh based on time and poll count
   - Provides robust error handling for API and connection issues
5. **main.py**: Entry point of the application

## Docker Deployment

The project is designed for easy deployment with Docker:

1. **Dockerfile**: Builds image from Python 3.11-slim
2. **docker-compose.yml**: Defines service with a single volume for all persistent data
3. **Volume**: Single volume stores both bot state and logs for simplicity
4. **Security**: Runs container as non-root user

## Project Structure

```
gzctf-notification/
├── bot/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── discord_bot.py         # Discord bot implementation
│   ├── gzctf_client.py        # GZCTF API client
│   ├── main.py                # Main entry point
│   └── notification_formatter.py # Notification formatting
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker configuration
├── env.example                # Example environment file
├── requirements.txt           # Python dependencies
└── README.md                  # This documentation
```

### Adding New Notification Types

1. Update the `NotificationFormatter` class in `notification_formatter.py`
2. Add new colors and emojis to the mapping dictionaries
3. Implement formatting logic in the appropriate methods

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