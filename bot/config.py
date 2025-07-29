import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class GZCTFConfig:
    """GZCTF API Configuration"""
    base_url: str
    username: str
    password: str

@dataclass
class DiscordConfig:
    """Discord Bot Configuration"""
    token: str
    guild_id: Optional[int] = None

@dataclass
class BotConfig:
    """Main Bot Configuration"""
    gzctf: GZCTFConfig
    discord: DiscordConfig
    poll_interval: int = 30  # seconds
    game_id: Optional[int] = None
    enable_notices: bool = True
    enable_events: bool = True
    notice_types: list = None
    event_types: list = None
    debug: bool = False

    def __post_init__(self):
        if self.notice_types is None:
            self.notice_types = [
                "FirstBlood", "SecondBlood", "ThirdBlood", 
                "NewHint", "NewChallenge", "Normal"
            ]
        if self.event_types is None:
            self.event_types = [
                "FlagSubmit", "ContainerStart", "ContainerDestroy", 
                "CheatDetected", "Normal"
            ]

def load_config() -> BotConfig:
    """Load configuration from environment variables"""
    
    # GZCTF Configuration
    gzctf_config = GZCTFConfig(
        base_url=os.getenv("GZCTF_BASE_URL", "http://localhost:8080"),
        username=os.getenv("GZCTF_USERNAME", ""),
        password=os.getenv("GZCTF_PASSWORD", "")
    )
    
    # Discord Configuration
    discord_config = DiscordConfig(
        token=os.getenv("DISCORD_TOKEN", ""),
        guild_id=int(os.getenv("DISCORD_GUILD_ID")) if os.getenv("DISCORD_GUILD_ID") else None
    )
    
    # Bot Configuration
    config = BotConfig(
        gzctf=gzctf_config,
        discord=discord_config,
        poll_interval=int(os.getenv("POLL_INTERVAL", "30")),
        game_id=int(os.getenv("GAME_ID")) if os.getenv("GAME_ID") else None,
        enable_notices=os.getenv("ENABLE_NOTICES", "true").lower() == "true",
        enable_events=os.getenv("ENABLE_EVENTS", "true").lower() == "true",
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )
    
    return config 