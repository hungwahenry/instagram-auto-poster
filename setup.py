"""Setup script for Instagram AutoPoster."""

from config import ConfigManager


def setup_configuration():
    """Interactive setup for the autoposter configuration."""
    print("🤖 Instagram AutoPoster Setup")
    print("=" * 40)
    
    config_manager = ConfigManager()
    
    # Setup main accounts
    print("\n📱 Main Accounts Setup")
    print("These are the accounts you want to monitor for new posts.")
    
    main_accounts = []
    while True:
        username = input("Enter main account username (or 'done' to finish): ").strip()
        if username.lower() == 'done':
            break
        if username:
            main_accounts.append(username)
            print(f"✅ Added {username}")
    
    # Setup sub accounts
    print("\n👥 Sub Accounts Setup")
    print("These are the accounts that will comment on your main account posts.")
    
    sub_accounts = []
    while True:
        username = input("Enter sub account username (or 'done' to finish): ").strip()
        if username.lower() == 'done':
            break
        if username:
            password = input(f"Enter password for {username}: ").strip()
            if password:
                sub_accounts.append((username, password))
                print(f"✅ Added {username}")
    
    # Setup media types
    print("\n📷 Media Types Setup")
    print("Choose which Instagram content types to comment on:")
    print("  1. photo   - Regular photo posts")
    print("  2. video   - Feed video posts") 
    print("  3. reel    - Reels/clips")
    print("  4. album   - Carousel posts (multiple photos/videos)")
    print("  5. igtv    - IGTV videos")
    
    available_types = ["photo", "video", "reel", "album", "igtv"]
    default_types = ["photo", "video", "reel", "album"]  # All except IGTV
    
    print(f"\nDefault selection: {', '.join(default_types)}")
    use_default = input("Use default media types? (y/n): ").strip().lower()
    
    if use_default == 'y':
        allowed_media_types = default_types
    else:
        allowed_media_types = []
        print("\nSelect media types to comment on (enter numbers separated by spaces):")
        for i, media_type in enumerate(available_types, 1):
            print(f"  {i}. {media_type}")
        
        while True:
            selection = input("Enter selection (e.g., '1 2 3' or 'done'): ").strip()
            if selection.lower() == 'done':
                break
            
            try:
                indices = [int(x) - 1 for x in selection.split()]
                for idx in indices:
                    if 0 <= idx < len(available_types):
                        media_type = available_types[idx]
                        if media_type not in allowed_media_types:
                            allowed_media_types.append(media_type)
                            print(f"✅ Added {media_type}")
                break
            except ValueError:
                print("Please enter valid numbers or 'done'")
    
    print(f"Selected media types: {', '.join(allowed_media_types)}")
    
    # Setup comments
    print("\n💬 Predefined Comments Setup")
    print("Enter comments that will be randomly selected for posts.")
    
    comments = []
    default_comments = [
        "Great post! 🔥",
        "Amazing content! ❤️",
        "Love this! 😍"
    ]
    
    print("Default comments will be added. You can add more:")
    for comment in default_comments:
        print(f"  • {comment}")
    
    comments.extend(default_comments)
    
    while True:
        comment = input("Enter additional comment (or 'done' to finish): ").strip()
        if comment.lower() == 'done':
            break
        if comment:
            comments.append(comment)
            print(f"✅ Added '{comment}'")
    
    # Update configuration
    config_manager.config.main_accounts = []
    for username in main_accounts:
        config_manager.add_main_account(username)
    
    config_manager.config.sub_accounts = []
    for username, password in sub_accounts:
        config_manager.add_sub_account(username, password)
    
    config_manager.config.predefined_comments = comments
    config_manager.config.allowed_media_types = allowed_media_types
    
    # Setup Telegram notifications (optional)
    print("\n📱 Telegram Notifications Setup (Optional)")
    print("Get notified about comments, errors, and bot status via Telegram.")
    
    enable_telegram = input("Enable Telegram notifications? (y/n): ").strip().lower()
    if enable_telegram == 'y':
        print("\n🤖 To set up Telegram notifications:")
        print("1. Create a bot: https://t.me/BotFather")
        print("2. Get your chat ID: https://t.me/userinfobot")
        
        bot_token = input("Enter your Telegram bot token: ").strip()
        chat_id = input("Enter your Telegram chat ID: ").strip()
        
        if bot_token and chat_id:
            config_manager.config.telegram_bot_token = bot_token
            config_manager.config.telegram_chat_id = chat_id
            config_manager.config.telegram_enabled = True
            print("✅ Telegram notifications enabled")
            
            # Test connection
            from telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier(bot_token, chat_id, True)
            if notifier.test_connection():
                print("✅ Telegram connection successful!")
            else:
                print("⚠️ Telegram connection failed. Please check your settings.")
        else:
            print("⚠️ Telegram setup skipped - missing bot token or chat ID")
    else:
        print("📱 Telegram notifications disabled")
    
    config_manager.save_config()
    
    print("\n✅ Configuration saved to config.json")
    print("\n🚀 Setup complete! You can now run:")
    print("    python autoposter.py")
    
    # Display summary
    print("\n📋 Configuration Summary:")
    print(f"  • Main accounts to monitor: {len(main_accounts)}")
    print(f"  • Sub accounts for commenting: {len(sub_accounts)}")
    print(f"  • Predefined comments: {len(comments)}")
    print(f"  • Allowed media types: {', '.join(allowed_media_types)}")
    print(f"  • Check interval: {config_manager.config.check_interval} seconds")
    print(f"  • Max comments per post: {config_manager.config.max_comments_per_post}")
    
    # Additional setup tips
    print("\n💡 Tips:")
    print("  • First run will comment on latest posts only")
    print("  • Subsequent runs comment on posts newer than last commented")
    print("  • Sessions are saved to avoid repeated logins")
    print("  • Post tracking prevents duplicate comments")


if __name__ == "__main__":
    setup_configuration()