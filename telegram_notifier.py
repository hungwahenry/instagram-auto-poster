"""Telegram notification system for Instagram AutoPoster."""

import requests
import logging
from datetime import datetime
from typing import Dict, Any


class TelegramNotifier:
    """Handles Telegram notifications for the autoposter."""
    
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram chat."""
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_startup_notification(self, sub_accounts_count: int, main_accounts_count: int):
        """Send notification when autoposter starts."""
        message = f"""
🤖 <b>Instagram AutoPoster Started</b>

📊 <b>Configuration:</b>
• Sub accounts logged in: {sub_accounts_count}
• Main accounts monitored: {main_accounts_count}
• Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ Bot is now monitoring for new posts...
        """
        self.send_message(message.strip())
    
    def send_comment_success(self, main_account: str, post_code: str, media_type: str, 
                           comment: str, sub_account: str):
        """Send notification for successful comment."""
        message = f"""
✅ <b>Comment Posted Successfully</b>

📱 <b>Account:</b> @{main_account}
🎯 <b>Post:</b> {post_code} ({media_type})
💬 <b>Comment:</b> "{comment[:100]}{'...' if len(comment) > 100 else ''}"
👤 <b>By:</b> @{sub_account}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip())
    
    def send_comment_failure(self, main_account: str, post_code: str, media_type: str, 
                           error: str, sub_account: str):
        """Send notification for failed comment."""
        message = f"""
❌ <b>Comment Failed</b>

📱 <b>Account:</b> @{main_account}
🎯 <b>Post:</b> {post_code} ({media_type})
👤 <b>Sub Account:</b> @{sub_account}
⚠️ <b>Error:</b> {error[:200]}{'...' if len(error) > 200 else ''}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip())
    
    def send_monitoring_cycle_summary(self, cycle_stats: Dict[str, Any]):
        """Send summary after each monitoring cycle."""
        total_comments = cycle_stats.get('successful_comments', 0)
        total_failures = cycle_stats.get('failed_comments', 0)
        accounts_checked = cycle_stats.get('accounts_checked', 0)
        new_posts_found = cycle_stats.get('new_posts_found', 0)
        
        if total_comments == 0 and total_failures == 0 and new_posts_found == 0:
            return  # Skip notification if nothing happened
        
        status_emoji = "✅" if total_failures == 0 else "⚠️"
        
        message = f"""
{status_emoji} <b>Monitoring Cycle Complete</b>

📊 <b>Statistics:</b>
• Accounts checked: {accounts_checked}
• New posts found: {new_posts_found}
• Comments posted: {total_comments}
• Failed comments: {total_failures}
• Cycle time: {datetime.now().strftime('%H:%M:%S')}

Next check in 5 minutes...
        """
        self.send_message(message.strip())
    
    def send_error_notification(self, error_type: str, error_message: str, context: str = ""):
        """Send notification for critical errors."""
        message = f"""
🚨 <b>AutoPoster Error</b>

⚠️ <b>Type:</b> {error_type}
💥 <b>Error:</b> {error_message[:300]}{'...' if len(error_message) > 300 else ''}
📍 <b>Context:</b> {context}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the logs for more details.
        """
        self.send_message(message.strip())
    
    def send_login_issues(self, failed_accounts: list):
        """Send notification for login failures."""
        if not failed_accounts:
            return
            
        accounts_list = "\n".join([f"• @{acc}" for acc in failed_accounts])
        
        message = f"""
🔐 <b>Login Issues Detected</b>

❌ <b>Failed to login:</b>
{accounts_list}

⚠️ These accounts won't be able to comment until login issues are resolved.
        """
        self.send_message(message.strip())
    
    def send_shutdown_notification(self, reason: str = "Manual stop"):
        """Send notification when autoposter stops."""
        message = f"""
🛑 <b>Instagram AutoPoster Stopped</b>

📝 <b>Reason:</b> {reason}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Bot has been shut down.
        """
        self.send_message(message.strip())
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        try:
            test_message = f"🔧 Telegram connection test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return self.send_message(test_message)
        except Exception as e:
            self.logger.error(f"Telegram connection test failed: {e}")
            return False