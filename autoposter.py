"""Instagram autoposter - Main automation script."""

import time
import random
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict
from instagrapi import Client
from config import ConfigManager, MainAccount
from telegram_notifier import TelegramNotifier


class InstagramAutoPoster:
    """Main class for Instagram automation."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.sub_clients: dict = {}  # Store logged-in sub account clients
        self.monitoring_client = None  # Will use a sub account for monitoring
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)  # Create sessions directory
        self.commented_posts_dir = Path("commented_posts")
        self.commented_posts_dir.mkdir(exist_ok=True)  # Create commented posts tracking
        self.setup_logging()
        
        # Initialize Telegram notifier
        self.telegram = TelegramNotifier(
            bot_token=self.config.config.telegram_bot_token,
            chat_id=self.config.config.telegram_chat_id,
            enabled=self.config.config.telegram_enabled
        )
        
        # Statistics tracking
        self.cycle_stats = {
            'successful_comments': 0,
            'failed_comments': 0,
            'accounts_checked': 0,
            'new_posts_found': 0
        }
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('autoposter.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_session_file(self, username: str) -> Path:
        """Get session file path for a username."""
        return self.sessions_dir / f"{username}_session.json"
    
    def login_sub_accounts(self):
        """Login to all enabled sub accounts with session persistence."""
        self.logger.info("Logging in to sub accounts...")
        
        for sub_account in self.config.config.sub_accounts:
            if not sub_account.enabled:
                continue
                
            try:
                client = Client()
                session_file = self.get_session_file(sub_account.username)
                
                # Try to load existing session first
                if session_file.exists():
                    try:
                        client.load_settings(session_file)
                        client.login(sub_account.username, sub_account.password)
                        
                        # Test if session is still valid using timeline feed (as per docs)
                        client.get_timeline_feed()
                        self.logger.info(f"Restored session for {sub_account.username}")
                        
                    except Exception as session_error:
                        self.logger.warning(f"Session invalid for {sub_account.username}: {session_error}")
                        # Fresh login if session restoration fails, preserve UUIDs for consistency
                        try:
                            old_session = client.get_settings()
                            client.set_settings({})
                            client.set_uuids(old_session["uuids"])
                        except:
                            pass
                        
                        client.login(sub_account.username, sub_account.password)
                        client.dump_settings(session_file)
                        self.logger.info(f"Fresh login and saved session for {sub_account.username}")
                else:
                    # Fresh login for new account
                    client.login(sub_account.username, sub_account.password)
                    client.dump_settings(session_file)
                    self.logger.info(f"New login and saved session for {sub_account.username}")
                
                # Set delay range for human-like behavior (as per best practices)
                client.delay_range = [1, 3]
                
                self.sub_clients[sub_account.username] = client
                
                # Use first logged-in account for monitoring
                if self.monitoring_client is None:
                    self.monitoring_client = client
                    self.logger.info(f"Using {sub_account.username} for monitoring")
                
                # Add delay between logins to avoid rate limiting
                time.sleep(random.randint(3, 8))
                
            except Exception as e:
                self.logger.error(f"Failed to login to {sub_account.username}: {e}")
        
        # Send login status notification
        failed_accounts = []
        for sub_account in self.config.config.sub_accounts:
            if sub_account.enabled and sub_account.username not in self.sub_clients:
                failed_accounts.append(sub_account.username)
        
        if failed_accounts:
            self.telegram.send_login_issues(failed_accounts)
    
    def cleanup_invalid_sessions(self):
        """Remove invalid session files."""
        for session_file in self.sessions_dir.glob("*_session.json"):
            try:
                # Test if we can load the session
                test_client = Client()
                test_client.load_settings(session_file)
                # If we get here, session file is valid
            except Exception:
                # Remove invalid session file
                session_file.unlink()
                self.logger.info(f"Removed invalid session file: {session_file.name}")
    
    def get_commented_posts_file(self, username: str) -> Path:
        """Get commented posts file path for a username."""
        return self.commented_posts_dir / f"{username}_commented.json"
    
    def load_commented_posts(self, username: str) -> Dict:
        """Load commented posts data for a username."""
        file_path = self.get_commented_posts_file(username)
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading commented posts for {username}: {e}")
        
        # Return default structure
        return {
            "last_commented_post_id": None,
            "last_commented_timestamp": 0,
            "commented_post_ids": []
        }
    
    def save_commented_posts(self, username: str, data: Dict):
        """Save commented posts data for a username."""
        file_path = self.get_commented_posts_file(username)
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving commented posts for {username}: {e}")
    
    def mark_post_commented(self, username: str, post_id: str, post_timestamp: int):
        """Mark a post as commented on."""
        data = self.load_commented_posts(username)
        data["last_commented_post_id"] = post_id
        data["last_commented_timestamp"] = post_timestamp
        if post_id not in data["commented_post_ids"]:
            data["commented_post_ids"].append(post_id)
        
        # Keep only last 100 commented posts to prevent file from growing too large
        if len(data["commented_post_ids"]) > 100:
            data["commented_post_ids"] = data["commented_post_ids"][-100:]
        
        self.save_commented_posts(username, data)
        self.logger.info(f"Marked post {post_id} as commented for {username}")
    
    def get_media_type_name(self, media) -> str:
        """Get human-readable media type name."""
        if media.media_type == 1:
            return "photo"
        elif media.media_type == 2:
            if media.product_type == "igtv":
                return "igtv"
            elif media.product_type == "clips":
                return "reel"
            else:
                return "video"
        elif media.media_type == 8:
            return "album"
        else:
            return "unknown"
    
    def should_comment_on_media(self, media) -> bool:
        """Check if we should comment on this media type."""
        media_type = self.get_media_type_name(media)
        return media_type in self.config.config.allowed_media_types
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username using private API."""
        if not self.monitoring_client:
            self.logger.error("No monitoring client available")
            return None
            
        try:
            # Use direct user_id_from_username method to avoid public API attempts
            user_id = self.monitoring_client.user_id_from_username(username)
            return str(user_id)
        except Exception as e:
            self.logger.error(f"Failed to get user ID for {username}: {e}")
            return None
    
    def get_recent_posts(self, user_id: str, amount: int = 5) -> List:
        """Get recent posts from a user using private API."""
        if not self.monitoring_client:
            self.logger.error("No monitoring client available")
            return []
            
        try:
            # Use private API method for better reliability
            medias = self.monitoring_client.user_medias_v1(user_id, amount=amount)
            return medias
        except Exception as e:
            self.logger.error(f"Failed to get posts for user ID {user_id}: {e}")
            return []
    
    def check_new_posts(self, main_account: MainAccount) -> List:
        """Check for new posts from a main account that we haven't commented on."""
        if not main_account.user_id:
            user_id = self.get_user_id(main_account.username)
            if user_id:
                main_account.user_id = user_id
                self.config.save_config()
            else:
                return []
        
        recent_posts = self.get_recent_posts(main_account.user_id)
        commented_data = self.load_commented_posts(main_account.username)
        posts_to_comment = []
        
        # If this is the first time monitoring this account
        if commented_data["last_commented_post_id"] is None:
            # Comment only on the latest post that matches our media type criteria
            if recent_posts:
                for post in recent_posts:
                    if self.should_comment_on_media(post):
                        posts_to_comment = [post]
                        media_type = self.get_media_type_name(post)
                        self.logger.info(f"First time monitoring {main_account.username}, targeting latest {media_type} post")
                        break
                else:
                    self.logger.info(f"No allowed media types found for {main_account.username}")
        else:
            # Find posts newer than the last one we commented on
            last_commented_timestamp = commented_data["last_commented_timestamp"]
            
            for post in recent_posts:
                post_timestamp = int(post.taken_at.timestamp())
                post_id = str(post.pk)
                media_type = self.get_media_type_name(post)
                
                # Skip if we've already commented on this post
                if post_id in commented_data["commented_post_ids"]:
                    continue
                
                # Skip if this media type is not allowed
                if not self.should_comment_on_media(post):
                    self.logger.info(f"Skipping {media_type} post {post.code} - not in allowed media types")
                    continue
                    
                # Only include posts newer than our last commented post
                if post_timestamp > last_commented_timestamp:
                    posts_to_comment.append(post)
        
        if posts_to_comment:
            self.logger.info(f"Found {len(posts_to_comment)} new posts to comment on from {main_account.username}")
        
        return posts_to_comment
    
    def select_random_comment(self) -> str:
        """Select a random comment from predefined comments."""
        return random.choice(self.config.config.predefined_comments)
    
    def comment_on_post(self, media_id: str, username: str) -> bool:
        """Comment on a post using a sub account."""
        if username not in self.sub_clients:
            self.logger.error(f"Sub account {username} not logged in")
            return False
        
        try:
            client = self.sub_clients[username]
            comment_text = self.select_random_comment()
            
            # Add the comment
            client.media_comment(media_id, comment_text)
            self.logger.info(f"Successfully commented '{comment_text}' on post {media_id} using {username}")
            self.cycle_stats['successful_comments'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to comment on post {media_id} using {username}: {e}")
            self.cycle_stats['failed_comments'] += 1
            return False
    
    def process_new_post(self, post, main_account_username: str):
        """Process a new post by commenting with sub accounts."""
        media_id = post.id
        post_timestamp = int(post.taken_at.timestamp())
        media_type = self.get_media_type_name(post)
        self.logger.info(f"Processing new {media_type} post {post.code} from {main_account_username}")
        
        # Select random sub accounts to comment
        available_sub_accounts = [
            username for username in self.sub_clients.keys()
            if any(sub.username == username and sub.enabled 
                  for sub in self.config.config.sub_accounts)
        ]
        
        if not available_sub_accounts:
            self.logger.warning("No available sub accounts for commenting")
            return
        
        # Randomly select up to max_comments_per_post sub accounts
        max_comments = min(
            len(available_sub_accounts), 
            self.config.config.max_comments_per_post
        )
        selected_accounts = random.sample(available_sub_accounts, max_comments)
        
        commented_successfully = False
        
        for username in selected_accounts:
            # Add random delay between comments
            delay = random.randint(*self.config.config.comment_delay_range)
            self.logger.info(f"Waiting {delay} seconds before commenting with {username}")
            time.sleep(delay)
            
            comment_result = self.comment_on_post(media_id, username)
            if comment_result:
                commented_successfully = True
                # Send success notification
                self.telegram.send_comment_success(
                    main_account=main_account_username,
                    post_code=post.code,
                    media_type=media_type,
                    comment=self.select_random_comment(),
                    sub_account=username
                )
            else:
                # Send failure notification
                self.telegram.send_comment_failure(
                    main_account=main_account_username,
                    post_code=post.code,
                    media_type=media_type,
                    error="Comment posting failed",
                    sub_account=username
                )
        
        # Mark post as commented if at least one comment was successful
        if commented_successfully:
            self.mark_post_commented(main_account_username, str(post.pk), post_timestamp)
    
    def monitor_accounts(self):
        """Monitor all main accounts for new posts."""
        self.logger.info("Starting account monitoring...")
        
        # Reset cycle stats
        self.cycle_stats = {
            'successful_comments': 0,
            'failed_comments': 0,
            'accounts_checked': 0,
            'new_posts_found': 0
        }
        
        for main_account in self.config.config.main_accounts:
            if not main_account.enabled:
                continue
                
            self.cycle_stats['accounts_checked'] += 1
                
            try:
                new_posts = self.check_new_posts(main_account)
                self.cycle_stats['new_posts_found'] += len(new_posts)
                
                for post in new_posts:
                    self.process_new_post(post, main_account.username)
                    
            except Exception as e:
                error_msg = f"Error monitoring {main_account.username}: {e}"
                self.logger.error(error_msg)
                self.telegram.send_error_notification(
                    error_type="Monitoring Error",
                    error_message=str(e),
                    context=f"Account: {main_account.username}"
                )
        
        self.logger.info("Account monitoring cycle completed")
        
        # Send cycle summary
        self.telegram.send_monitoring_cycle_summary(self.cycle_stats)
    
    def run(self):
        """Main run loop."""
        self.logger.info("Starting Instagram AutoPoster...")
        
        try:
            # Login to sub accounts
            self.login_sub_accounts()
            
            if not self.sub_clients:
                self.logger.error("No sub accounts logged in. Exiting.")
                self.telegram.send_error_notification(
                    error_type="Startup Error",
                    error_message="No sub accounts logged in successfully",
                    context="Initial login phase"
                )
                return
                
            if not self.monitoring_client:
                self.logger.error("No monitoring client available. Exiting.")
                self.telegram.send_error_notification(
                    error_type="Startup Error", 
                    error_message="No monitoring client available",
                    context="Initial login phase"
                )
                return
            
            # Send startup notification
            self.telegram.send_startup_notification(
                sub_accounts_count=len(self.sub_clients),
                main_accounts_count=len([acc for acc in self.config.config.main_accounts if acc.enabled])
            )
            
            self.logger.info(f"Monitoring will run every {self.config.config.check_interval} seconds")
            
            while True:
                self.monitor_accounts()
                
                # Wait for next check
                self.logger.info(f"Sleeping for {self.config.config.check_interval} seconds...")
                time.sleep(self.config.config.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Stopping Instagram AutoPoster...")
            self.telegram.send_shutdown_notification("Manual stop (Ctrl+C)")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(error_msg)
            self.telegram.send_error_notification(
                error_type="Critical Error",
                error_message=str(e),
                context="Main run loop"
            )
            self.telegram.send_shutdown_notification(f"Critical error: {str(e)[:100]}")


def main():
    """Main entry point."""
    # Initialize configuration
    config_manager = ConfigManager()
    
    # Create and run autoposter
    autoposter = InstagramAutoPoster(config_manager)
    autoposter.run()


if __name__ == "__main__":
    main()