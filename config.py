"""Configuration management for Instagram autoposter."""

import json
from typing import List
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class SubAccount:
    """Sub account configuration."""
    username: str
    password: str
    enabled: bool = True
    
    
@dataclass
class MainAccount:
    """Main account to monitor."""
    username: str
    user_id: str = ""  # Will be fetched automatically
    last_post_timestamp: int = 0
    enabled: bool = True


@dataclass
class Config:
    """Main configuration class."""
    main_accounts: List[MainAccount]
    sub_accounts: List[SubAccount]
    predefined_comments: List[str]
    check_interval: int = 300  # 5 minutes
    comment_delay_range: tuple = (30, 120)  # 30-120 seconds delay
    max_comments_per_post: int = 2  # Max sub accounts to comment per post
    allowed_media_types: List[str] = None  # Which media types to comment on
    telegram_bot_token: str = ""  # Telegram bot token
    telegram_chat_id: str = ""  # Telegram chat ID for notifications
    telegram_enabled: bool = False  # Enable/disable Telegram notifications
    
    def __post_init__(self):
        if self.allowed_media_types is None:
            self.allowed_media_types = ["photo", "video", "reel", "album"]  # Default: all except IGTV
    
    
class ConfigManager:
    """Manages configuration file operations."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config: Config = self._load_config()
    
    def _load_config(self) -> Config:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            config = Config(
                main_accounts=[MainAccount(**acc) for acc in data.get('main_accounts', [])],
                sub_accounts=[SubAccount(**acc) for acc in data.get('sub_accounts', [])],
                predefined_comments=data.get('predefined_comments', []),
                check_interval=data.get('check_interval', 300),
                comment_delay_range=tuple(data.get('comment_delay_range', [30, 120])),
                max_comments_per_post=data.get('max_comments_per_post', 2),
                allowed_media_types=data.get('allowed_media_types', ["photo", "video", "reel", "album"]),
                telegram_bot_token=data.get('telegram_bot_token', ""),
                telegram_chat_id=data.get('telegram_chat_id', ""),
                telegram_enabled=data.get('telegram_enabled', False)
            )
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Config:
        """Create default configuration."""
        return Config(
            main_accounts=[
                MainAccount(username="your_main_account_1"),
                MainAccount(username="your_main_account_2")
            ],
            sub_accounts=[
                SubAccount(username="sub_account_1", password="password1"),
                SubAccount(username="sub_account_2", password="password2")
            ],
            predefined_comments=[
                "Punters and sports analysts, we are building the biggest forum for bettors and gamblers, free to join, use the link in my bio to join now!",
                "Join the biggest forum for bettors and gamblers, free to join, use the link in my bio to join now!",
                "Free betting odds, promos, and tips, use the link in my bio to join now the biggest forum for bettors and gamblers!",
            ]
        )
    
    def save_config(self):
        """Save current configuration to file."""
        data = {
            'main_accounts': [asdict(acc) for acc in self.config.main_accounts],
            'sub_accounts': [asdict(acc) for acc in self.config.sub_accounts],
            'predefined_comments': self.config.predefined_comments,
            'check_interval': self.config.check_interval,
            'comment_delay_range': list(self.config.comment_delay_range),
            'max_comments_per_post': self.config.max_comments_per_post,
            'allowed_media_types': self.config.allowed_media_types,
            'telegram_bot_token': self.config.telegram_bot_token,
            'telegram_chat_id': self.config.telegram_chat_id,
            'telegram_enabled': self.config.telegram_enabled
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_main_account(self, username: str):
        """Add a main account to monitor."""
        self.config.main_accounts.append(MainAccount(username=username))
        self.save_config()
    
    def add_sub_account(self, username: str, password: str):
        """Add a sub account for commenting."""
        self.config.sub_accounts.append(SubAccount(username=username, password=password))
        self.save_config()
    
    def add_comment(self, comment: str):
        """Add a predefined comment."""
        if comment not in self.config.predefined_comments:
            self.config.predefined_comments.append(comment)
            self.save_config()
    
    def update_last_post_timestamp(self, username: str, timestamp: int):
        """Update last seen post timestamp for a main account."""
        for account in self.config.main_accounts:
            if account.username == username:
                account.last_post_timestamp = timestamp
                self.save_config()
                break