# GZCTF Discord Notification Bot - Design Specification

## 1. Project Overview

### 1.1 Purpose
GZCTF Discord Notification Bot is a Python application designed to monitor and forward notifications from the GZCTF platform (a CTF - Capture The Flag system) to Discord servers in real-time.

### 1.2 Main Objectives
- **Real-time Monitoring**: Continuously monitor notifications and events from GZCTF
- **Discord Integration**: Send beautifully formatted notifications to Discord channels
- **Notification Classification**: Support multiple notification types (First Blood, hints, challenges, etc.)
- **Security**: Manage private channels for sensitive information
- **Reliability**: Robust error handling and automatic recovery

### 1.3 Scope
- Support GZCTF platform with cookie-based authentication
- Discord integration with rich embeds and slash commands
- Containerization with Docker
- Persistent state management
- Comprehensive logging and monitoring

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GZCTF API     │◄───┤  Discord Bot    │───►│  Discord Server │
│   Platform      │    │   Application   │    │   Channels      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Persistent     │
                       │  Storage        │
                       │  (State/Logs)   │
                       └─────────────────┘
```

### 2.2 Module Architecture

```
gzctf-notification/
├── bot/                          # Core application modules
│   ├── main.py                   # Entry point & orchestration
│   ├── config.py                 # Configuration management
│   ├── gzctf_client.py          # GZCTF API client
│   ├── discord_bot.py           # Discord bot implementation
│   ├── notification_formatter.py # Message formatting
│   └── __init__.py
├── scripts/                      # Utility & debugging scripts
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
└── env.example                  # Configuration template
```

### 2.3 Data Flow

```
1. Authentication Flow:
   GZCTF Login API → Cookie-based Session → Token Storage

2. Notification Flow:
   GZCTF API Polling → Data Processing → Discord Formatting → Channel Delivery

3. State Management:
   Runtime State ↔ JSON Persistence ↔ File System
```

## 3. Detailed Design

### 3.1 Core Components

#### 3.1.1 Main Application (`main.py`)
**Primary Functions:**
- Application entry point and lifecycle management
- Configuration loading and validation
- Logging setup with rotation
- Error handling and exit codes
- Async context management

**Design:**
```python
class ApplicationLifecycle:
    - load_config() → BotConfig
    - configure_logging() → None
    - validate_config() → Optional[str]
    - main() → int  # Exit code
```

#### 3.1.2 Configuration Management (`config.py`)
**Primary Functions:**
- Environment variable parsing
- Type-safe configuration with dataclasses
- Default value management
- Configuration validation

**Design:**
```python
@dataclass
class GZCTFConfig:
    base_url: str
    username: str
    password: str

@dataclass
class DiscordConfig:
    token: str
    guild_id: Optional[int]

@dataclass
class BotConfig:
    gzctf: GZCTFConfig
    discord: DiscordConfig
    poll_interval: int = 30
    game_id: Optional[int] = None
    enable_notices: bool = True
    enable_events: bool = True
    # ... other fields
```

#### 3.1.3 GZCTF API Client (`gzctf_client.py`)
**Primary Functions:**
- Cookie-based authentication with GZCTF
- API endpoint management
- Session management with connection pooling
- Automatic token refresh
- Error handling and retry logic

**Design:**
```python
class GZCTFClient:
    - authenticate() → bool
    - is_authenticated() → bool
    - get_game_notices(game_id, count, skip) → List[Dict]
    - get_game_events(game_id, count, skip) → List[Dict]
    - get_game_info(game_id) → Optional[Dict]
    - _make_authenticated_request() → Optional[Response]
    - _set_auth_cookie() → None
```

**Authentication Flow:**
1. POST `/api/account/login` with username/password
2. Extract `GZCTF_Token` from response cookies
3. Set cookie in session for subsequent requests
4. Automatic refresh when token expires

#### 3.1.4 Discord Bot (`discord_bot.py`)
**Primary Functions:**
- Discord.py bot implementation
- Channel management (public/private)
- Slash command support
- Polling loop for notifications
- State persistence
- Permission management

**Design:**
```python
class GZCTFNotificationBot(commands.Bot):
    - setup_hook() → None
    - on_ready() → None
    - setup_channels() → None
    - start_polling() → None
    - process_notifications() → None
    - send_notification() → None
    - load_state() / save_state() → None
```

**Channel Management:**
- **Notification Channel**: Public channel for general notices
- **Event Channel**: Private channel for sensitive events
- Auto-creation with proper permissions
- Permission verification and setup

#### 3.1.5 Notification Formatter (`notification_formatter.py`)
**Primary Functions:**
- Convert GZCTF data to Discord embeds
- Color coding by notification type
- Emoji mapping
- Timestamp formatting
- Content truncation and sanitization

**Design:**
```python
class NotificationFormatter:
    - format_notice(notice) → Optional[discord.Embed]
    - format_event(event) → Optional[discord.Embed]
    - _format_notice_title() → str
    - _format_event_title() → str
    - _get_event_color() → int
```

### 3.2 Data Models

#### 3.2.1 GZCTF Notice Structure
```json
{
    "id": "integer",
    "type": "FirstBlood|SecondBlood|ThirdBlood|NewHint|NewChallenge|Normal",
    "values": ["string array"],
    "time": "unix_timestamp",
    "timestamp": "iso_string"
}
```

#### 3.2.2 GZCTF Event Structure
```json
{
    "type": "FlagSubmit|ContainerStart|ContainerDestroy|CheatDetected|Normal",
    "values": ["string array"],
    "time": "unix_timestamp",
    "user": "string",
    "team": "string"
}
```

#### 3.2.3 Bot State Structure
```json
{
    "last_notice_id": "integer|null",
    "last_event_time": "iso_string|null",
    "events_disabled_due_to_auth": "boolean",
    "events_failure_count": "integer",
    "last_auth_refresh": "iso_string",
    "poll_count": "integer"
}
```

### 3.3 Security Design

#### 3.3.1 Authentication Security
- **Cookie-based auth**: Use GZCTF_Token cookie instead of Bearer tokens
- **Session management**: Proper cookie domain and path settings
- **Auto-refresh**: Refresh tokens based on time-based and poll-count-based triggers
- **Credential protection**: Environment variables for sensitive data

#### 3.3.2 Discord Security
- **Private channels**: Event channel only accessible by admins
- **Permission verification**: Auto-check and setup proper permissions
- **Rate limiting**: Respect Discord API rate limits
- **Input sanitization**: Clean user input before display

#### 3.3.3 Container Security
- **Non-root user**: Container runs as user `bot` (UID 1000)
- **Minimal base image**: Python 3.11-slim
- **Volume isolation**: Persistent data in isolated volumes
- **Resource limits**: CPU and memory constraints

## 4. Deployment Architecture

### 4.1 Container Design

#### 4.1.1 Dockerfile Strategy
```dockerfile
FROM python:3.11-slim
# Multi-stage build not needed for this project
# Single-stage with optimization for size and security
```

**Optimization Features:**
- Minimal base image
- Layer caching with requirements.txt copy first
- Non-root user execution
- Clean package cache
- UTF-8 encoding setup

#### 4.1.2 Docker Compose Architecture
```yaml
services:
  gzctf-bot:
    # Single service architecture
    # Volume mounting cho persistence
    # Environment file integration
    # Resource limits
    # Logging configuration
```

**Volume Strategy:**
- Single volume `gzctf-bot-volume` for all persistent data
- Logs and state files in the same volume
- Easy backup and migration

### 4.2 Configuration Management

#### 4.2.1 Environment Variables
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

#### 4.2.2 Configuration Validation
- Required field checking
- Type conversion with error handling
- Default value application
- Environment-specific overrides

## 5. Error Handling & Resilience

### 5.1 Error Categories

#### 5.1.1 Authentication Errors
- **401 Unauthorized**: Auto-retry with re-authentication
- **403 Forbidden**: Disable affected endpoints (events)
- **Credential errors**: Fail fast with clear error messages

#### 5.1.2 Network Errors
- **Connection timeouts**: Retry with exponential backoff
- **SSL errors**: Session recreation
- **Rate limiting**: Respect Discord rate limits

#### 5.1.3 Data Errors
- **JSON parsing**: Graceful fallback with logging
- **Invalid timestamps**: Use current time as fallback
- **Missing fields**: Use default values

### 5.2 Recovery Strategies

#### 5.2.1 Authentication Recovery
```python
# Auto-refresh triggers:
1. Every 30 polling cycles (~15 minutes default)
2. After 1 hour regardless of poll count
3. On 401 response from API
4. On token validation failure
```

#### 5.2.2 Session Recovery
```python
# Session recreation on:
1. "Session is closed" errors
2. SSL connection errors
3. Connector closed states
```

#### 5.2.3 State Recovery
- Persistent state in JSON files
- Graceful degradation when state file corrupted
- State validation and migration

## 6. Monitoring & Logging

### 6.1 Logging Strategy

#### 6.1.1 Log Levels
- **DEBUG**: Detailed API requests/responses, authentication flows
- **INFO**: Startup info, successful operations, notifications sent
- **WARNING**: Recoverable errors, authentication retries
- **ERROR**: Failed operations, configuration errors

#### 6.1.2 Log Rotation
```python
RotatingFileHandler(
    maxBytes=5_000_000,  # 5MB per file
    backupCount=3,       # Keep 3 backup files
    encoding='utf-8'
)
```

#### 6.1.3 Log Locations
- **Local**: `./logs/gzctf_bot.log`
- **Container**: `/app/logs/gzctf_bot.log`
- **Override**: `LOG_DIR` environment variable

### 6.2 Monitoring Points

#### 6.2.1 Health Metrics
- Authentication status
- API response times
- Discord connection status
- Notification delivery success rate
- Error frequency

#### 6.2.2 Business Metrics
- Notifications processed per hour
- Event types distribution
- Channel activity
- User engagement

## 7. Performance Considerations

### 7.1 Polling Optimization

#### 7.1.1 Adaptive Polling
- Default 30-second interval
- Configurable via `POLL_INTERVAL`
- Efficient timestamp-based filtering
- Duplicate prevention

#### 7.1.2 API Efficiency
- Batch requests with count/skip parameters
- Timestamp sorting to optimize processing
- Connection pooling with aiohttp
- Session reuse

### 7.1.3 Memory Management
- Async context managers
- Proper session cleanup
- Limited state retention
- Log rotation

### 7.2 Discord Optimization

#### 7.2.1 Rate Limiting
- Built-in discord.py rate limiting
- Batch message sending when possible
- Embed optimization for rich content

#### 7.2.2 Channel Management
- Lazy channel creation
- Permission caching
- Efficient channel lookups

## 8. Testing Strategy

### 8.1 Utility Scripts

#### 8.1.1 Debug Scripts
- **`debug_api.py`**: Test GZCTF API connectivity
- **`test_config.py`**: Validate configuration loading
- **`test_simple.py`**: End-to-end authentication test
- **`verify_permissions.py`**: Discord permission verification

#### 8.1.2 Management Scripts
- **`generate_invite_link.py`**: Bot invitation URL generation
- **`clear_slash_commands.py`**: Clean up Discord commands

### 8.2 Testing Approach

#### 8.2.1 Unit Testing
- Configuration parsing
- Notification formatting
- State management
- Error handling

#### 8.2.2 Integration Testing
- GZCTF API integration
- Discord API integration
- End-to-end notification flow

#### 8.2.3 Manual Testing
- Permission verification
- Channel creation
- Notification delivery
- Error recovery

## 9. Deployment Guide

### 9.1 Prerequisites

#### 9.1.1 GZCTF Requirements
- GZCTF platform access
- User account with monitor permissions or admin permissions for event notifications
- Game ID identification

#### 9.1.2 Discord Requirements
- Discord application creation
- Bot token generation
- Server invitation with proper permissions
- Channel ID identification

### 9.2 Deployment Steps

#### 9.2.1 Environment Setup
```bash
1. Clone repository
2. Copy env.example to .env
3. Configure environment variables
4. Verify configuration with test scripts
```

#### 9.2.2 Docker Deployment
```bash
1. docker-compose up -d
2. Monitor logs: docker-compose logs -f
3. Verify channel creation
4. Test notification delivery
```

#### 9.2.3 Local Development
```bash
1. pip install -r requirements.txt
2. python bot/main.py
3. Monitor console output
4. Use debug scripts for troubleshooting
```

## 10. Maintenance & Operations

### 10.1 Regular Maintenance

#### 10.1.1 Log Management
- Monitor log file sizes
- Archive old logs
- Check for error patterns
- Performance monitoring

#### 10.1.2 Configuration Updates
- Environment variable updates
- Channel permission reviews
- Game ID updates
- Polling interval optimization

### 10.2 Troubleshooting

#### 10.2.1 Common Issues
- Authentication failures
- Permission errors
- Network connectivity
- Configuration errors

#### 10.2.2 Diagnostic Tools
- Debug scripts
- Log analysis
- Permission verification
- API connectivity tests

## 11. Future Enhancements

### 11.1 Potential Features

#### 11.1.1 Advanced Notifications
- Custom notification filters
- User mention systems
- Notification scheduling
- Multi-game support

#### 11.1.2 Analytics
- Notification statistics
- Performance metrics
- User engagement tracking
- Historical data analysis

#### 11.1.3 Integration Expansions
- Webhook support
- Multiple Discord servers
- Slack integration
- Email notifications

### 11.2 Scalability Considerations

#### 11.2.1 Multi-Instance Support
- Database backend for state
- Message queue for notifications
- Load balancing
- High availability

#### 11.2.2 Performance Optimization
- Caching layers
- Database optimization
- Async processing improvements
- Resource usage optimization

## 12. Conclusion

GZCTF Discord Notification Bot is a well-designed application with modular architecture, robust error handling, and flexible deployment strategy. This project demonstrates best practices in:

- **Clean Architecture**: Separation of concerns with clear module boundaries
- **Reliability**: Comprehensive error handling and recovery mechanisms
- **Security**: Proper authentication and permission management
- **Maintainability**: Clear code structure and extensive documentation
- **Operability**: Docker deployment and monitoring capabilities

This design provides a solid foundation for monitoring GZCTF platforms and integration with Discord, with scalability for future requirements.
