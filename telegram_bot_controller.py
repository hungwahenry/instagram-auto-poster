"""Telegram bot controller for managing Instagram AutoPoster remotely."""

import os
import json
import subprocess
import time
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import requests
from dataclasses import asdict

from config import ConfigManager


class TelegramBotController:
    """Full-featured Telegram bot for remote autoposter management."""
    
    def __init__(self, bot_token: str, authorized_chat_ids: list):
        self.bot_token = bot_token
        self.authorized_chat_ids = [str(chat_id) for chat_id in authorized_chat_ids]
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.config_manager = ConfigManager()
        self.autoposter_process = None
        self.running = True
        self.offset = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot_controller.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def is_authorized(self, chat_id: str) -> bool:
        """Check if chat_id is authorized to use the bot."""
        return str(chat_id) in self.authorized_chat_ids
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram chat."""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    def send_document(self, chat_id: str, file_path: str, caption: str = "") -> bool:
        """Send document to Telegram chat."""
        try:
            url = f"{self.base_url}/sendDocument"
            
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': chat_id,
                    'caption': caption
                }
                response = requests.post(url, files=files, data=data, timeout=30)
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Failed to send document: {e}")
            return False
    
    def get_updates(self) -> list:
        """Get updates from Telegram."""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.offset,
                "timeout": 30
            }
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                data = response.json()
                if data["ok"]:
                    return data["result"]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get updates: {e}")
            return []
    
    def handle_start(self, chat_id: str):
        """Handle /start command."""
        if not self.is_authorized(chat_id):
            self.send_message(chat_id, "❌ Unauthorized access")
            return
        
        welcome_msg = """
🤖 <b>Instagram AutoPoster Controller</b>

Welcome to the remote control panel!

<b>Bot Control:</b>
/status - Check autoposter status
/start_bot - Start the autoposter
/stop_bot - Stop the autoposter
/restart_bot - Restart the autoposter

<b>Configuration:</b>
/config - View current configuration
/edit_config - Download config JSON for editing
/backup_config - Download config backup

<b>Monitoring:</b>
/logs - Download latest logs
/stats - View session statistics

<b>Config Editing:</b>
Send edited JSON with caption 'update_config'

/help - Show this help message

You can control your Instagram automation remotely!
        """
        self.send_message(chat_id, welcome_msg.strip())
    
    def handle_status(self, chat_id: str):
        """Handle /status command."""
        if not self.is_authorized(chat_id):
            return
        
        # Check if autoposter is running
        is_running = self.check_autoposter_running()
        
        status_emoji = "🟢" if is_running else "🔴"
        status_text = "Running" if is_running else "Stopped"
        
        # Get system info
        try:
            disk_usage = subprocess.check_output(['df', '-h', '.'], text=True).split('\n')[1].split()
            disk_info = f"{disk_usage[4]} used"
        except:
            disk_info = "N/A"
        
        try:
            uptime = subprocess.check_output(['uptime'], text=True).strip()
        except:
            uptime = "N/A"
        
        config = self.config_manager.config
        
        status_msg = f"""
{status_emoji} <b>AutoPoster Status: {status_text}</b>

📊 <b>Configuration:</b>
• Main accounts: {len([acc for acc in config.main_accounts if acc.enabled])}
• Sub accounts: {len([acc for acc in config.sub_accounts if acc.enabled])}
• Check interval: {config.check_interval}s
• Media types: {', '.join(config.allowed_media_types)}

💾 <b>System Info:</b>
• Disk usage: {disk_info}
• Server uptime: {uptime}
• Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(chat_id, status_msg.strip())
    
    def handle_start_bot(self, chat_id: str):
        """Handle /start_bot command."""
        if not self.is_authorized(chat_id):
            return
        
        if self.check_autoposter_running():
            self.send_message(chat_id, "⚠️ AutoPoster is already running!")
            return
        
        try:
            # Start autoposter as background process
            self.autoposter_process = subprocess.Popen(
                ['python', 'autoposter.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            time.sleep(2)  # Give it time to start
            
            if self.autoposter_process.poll() is None:
                self.send_message(chat_id, "✅ AutoPoster started successfully!")
                self.logger.info("AutoPoster started via Telegram command")
            else:
                self.send_message(chat_id, "❌ Failed to start AutoPoster. Check logs for details.")
        except Exception as e:
            self.send_message(chat_id, f"❌ Error starting AutoPoster: {str(e)}")
            self.logger.error(f"Error starting autoposter: {e}")
    
    def handle_stop_bot(self, chat_id: str):
        """Handle /stop_bot command."""
        if not self.is_authorized(chat_id):
            return
        
        if not self.check_autoposter_running():
            self.send_message(chat_id, "⚠️ AutoPoster is not running!")
            return
        
        try:
            # Find and kill autoposter process
            result = subprocess.run(['pkill', '-f', 'autoposter.py'], capture_output=True)
            
            time.sleep(2)  # Give it time to stop
            
            if not self.check_autoposter_running():
                self.send_message(chat_id, "🛑 AutoPoster stopped successfully!")
                self.logger.info("AutoPoster stopped via Telegram command")
            else:
                self.send_message(chat_id, "❌ Failed to stop AutoPoster completely")
        except Exception as e:
            self.send_message(chat_id, f"❌ Error stopping AutoPoster: {str(e)}")
            self.logger.error(f"Error stopping autoposter: {e}")
    
    def handle_restart_bot(self, chat_id: str):
        """Handle /restart_bot command."""
        if not self.is_authorized(chat_id):
            return
        
        self.send_message(chat_id, "🔄 Restarting AutoPoster...")
        
        # Stop first
        if self.check_autoposter_running():
            subprocess.run(['pkill', '-f', 'autoposter.py'])
            time.sleep(3)
        
        # Then start
        try:
            self.autoposter_process = subprocess.Popen(
                ['python', 'autoposter.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            time.sleep(3)
            
            if self.autoposter_process.poll() is None:
                self.send_message(chat_id, "✅ AutoPoster restarted successfully!")
                self.logger.info("AutoPoster restarted via Telegram command")
            else:
                self.send_message(chat_id, "❌ Failed to restart AutoPoster")
        except Exception as e:
            self.send_message(chat_id, f"❌ Error restarting AutoPoster: {str(e)}")
    
    def handle_config(self, chat_id: str):
        """Handle /config command."""
        if not self.is_authorized(chat_id):
            return
        
        config = self.config_manager.config
        
        # Mask sensitive data
        masked_sub_accounts = []
        for acc in config.sub_accounts:
            masked_acc = {
                "username": acc.username,
                "password": "*" * len(acc.password),
                "enabled": acc.enabled
            }
            masked_sub_accounts.append(masked_acc)
        
        config_data = {
            "main_accounts": [asdict(acc) for acc in config.main_accounts],
            "sub_accounts": masked_sub_accounts,
            "predefined_comments": config.predefined_comments,
            "check_interval": config.check_interval,
            "comment_delay_range": list(config.comment_delay_range),
            "max_comments_per_post": config.max_comments_per_post,
            "allowed_media_types": config.allowed_media_types,
            "telegram_enabled": config.telegram_enabled
        }
        
        config_msg = f"""
⚙️ <b>Current Configuration</b>

📱 <b>Main Accounts ({len(config.main_accounts)}):</b>
{chr(10).join([f"• @{acc.username} {'✅' if acc.enabled else '❌'}" for acc in config.main_accounts])}

👥 <b>Sub Accounts ({len(config.sub_accounts)}):</b>
{chr(10).join([f"• @{acc.username} {'✅' if acc.enabled else '❌'}" for acc in config.sub_accounts])}

💬 <b>Comments ({len(config.predefined_comments)}):</b>
{chr(10).join([f"• {comment[:50]}{'...' if len(comment) > 50 else ''}" for comment in config.predefined_comments[:3]])}
{'...' if len(config.predefined_comments) > 3 else ''}

⚙️ <b>Settings:</b>
• Check interval: {config.check_interval}s
• Comment delay: {config.comment_delay_range[0]}-{config.comment_delay_range[1]}s
• Max comments per post: {config.max_comments_per_post}
• Media types: {', '.join(config.allowed_media_types)}
        """
        
        self.send_message(chat_id, config_msg.strip())
    
    def handle_logs(self, chat_id: str):
        """Handle /logs command."""
        if not self.is_authorized(chat_id):
            return
        
        log_files = ['autoposter.log', 'bot_controller.log']
        
        for log_file in log_files:
            if Path(log_file).exists():
                try:
                    # Get last 100 lines of log
                    result = subprocess.run(['tail', '-100', log_file], capture_output=True, text=True)
                    
                    if result.stdout:
                        # Create temporary file with recent logs
                        temp_file = f"recent_{log_file}"
                        with open(temp_file, 'w') as f:
                            f.write(result.stdout)
                        
                        # Send as document
                        caption = f"📄 Last 100 lines from {log_file}"
                        if self.send_document(chat_id, temp_file, caption):
                            self.send_message(chat_id, f"✅ Sent {log_file}")
                        else:
                            self.send_message(chat_id, f"❌ Failed to send {log_file}")
                        
                        # Clean up temp file
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    else:
                        self.send_message(chat_id, f"⚠️ {log_file} is empty")
                except Exception as e:
                    self.send_message(chat_id, f"❌ Error reading {log_file}: {str(e)}")
            else:
                self.send_message(chat_id, f"⚠️ {log_file} not found")
    
    def handle_stats(self, chat_id: str):
        """Handle /stats command."""
        if not self.is_authorized(chat_id):
            return
        
        try:
            # Get statistics from commented posts files
            commented_posts_dir = Path("commented_posts")
            total_comments = 0
            account_stats = {}
            
            if commented_posts_dir.exists():
                for file_path in commented_posts_dir.glob("*_commented.json"):
                    account_name = file_path.stem.replace("_commented", "")
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            comment_count = len(data.get("commented_post_ids", []))
                            account_stats[account_name] = comment_count
                            total_comments += comment_count
                    except:
                        continue
            
            # Get session files count
            sessions_dir = Path("sessions")
            session_count = len(list(sessions_dir.glob("*_session.json"))) if sessions_dir.exists() else 0
            
            stats_msg = f"""
📊 <b>Session Statistics</b>

💬 <b>Total Comments Posted:</b> {total_comments}

📱 <b>Comments by Account:</b>
{chr(10).join([f"• @{acc}: {count} comments" for acc, count in account_stats.items()]) if account_stats else "• No comment data available"}

🔐 <b>Active Sessions:</b> {session_count}

⏰ <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.send_message(chat_id, stats_msg.strip())
            
        except Exception as e:
            self.send_message(chat_id, f"❌ Error generating stats: {str(e)}")
    
    def handle_edit_config(self, chat_id: str):
        """Handle /edit_config command - send current JSON for editing."""
        if not self.is_authorized(chat_id):
            return
        
        try:
            # Read current config
            with open('config.json', 'r') as f:
                config_json = f.read()
            
            # Send as text file for easy editing
            temp_file = "current_config.json"
            with open(temp_file, 'w') as f:
                f.write(config_json)
            
            caption = """📝 <b>Current Configuration</b>

To edit:
1. Download this file
2. Edit the JSON 
3. Send back with caption: <code>update_config</code>

⚠️ <b>Important:</b>
• Keep JSON format valid
• Don't change structure
• Passwords will be visible"""
            
            if self.send_document(chat_id, temp_file, caption):
                self.send_message(chat_id, "✅ Config sent! Edit and send back with caption 'update_config'")
            
            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass
                
        except Exception as e:
            self.send_message(chat_id, f"❌ Error reading config: {str(e)}")
    
    def handle_update_config(self, chat_id: str, document: dict):
        """Handle config update from uploaded JSON file."""
        if not self.is_authorized(chat_id):
            return
        
        try:
            # Get file info
            file_id = document['file_id']
            file_name = document.get('file_name', 'unknown')
            
            # Download file from Telegram
            file_info_url = f"{self.base_url}/getFile?file_id={file_id}"
            response = requests.get(file_info_url)
            
            if response.status_code != 200:
                self.send_message(chat_id, "❌ Failed to get file info")
                return
            
            file_path = response.json()['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            
            # Download the file
            file_response = requests.get(file_url)
            if file_response.status_code != 200:
                self.send_message(chat_id, "❌ Failed to download file")
                return
            
            # Parse and validate JSON
            try:
                new_config_data = json.loads(file_response.text)
            except json.JSONDecodeError as e:
                self.send_message(chat_id, f"❌ Invalid JSON format: {str(e)}")
                return
            
            # Backup current config
            shutil.copy('config.json', 'config.json.backup')
            
            # Write new config
            with open('config.json', 'w') as f:
                json.dump(new_config_data, f, indent=2)
            
            # Reload config manager
            self.config_manager = ConfigManager()
            
            self.send_message(chat_id, """✅ <b>Configuration Updated!</b>

📄 Backup saved as: config.json.backup
🔄 Config reloaded successfully

⚠️ <b>To apply changes:</b>
Use /restart_bot to restart with new settings""")
            
            self.logger.info(f"Configuration updated via Telegram by {chat_id}")
            
        except Exception as e:
            self.send_message(chat_id, f"❌ Error updating config: {str(e)}")
            # Restore backup if something went wrong
            try:
                shutil.copy('config.json.backup', 'config.json')
                self.send_message(chat_id, "🔄 Restored previous config due to error")
            except:
                pass
    
    def handle_backup_config(self, chat_id: str):
        """Handle /backup_config command."""
        if not self.is_authorized(chat_id):
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"config_backup_{timestamp}.json"
            
            # Create timestamped backup
            shutil.copy('config.json', backup_name)
            
            caption = f"💾 Configuration Backup\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            if self.send_document(chat_id, backup_name, caption):
                self.send_message(chat_id, "✅ Config backup sent!")
            
            # Clean up
            try:
                os.remove(backup_name)
            except:
                pass
                
        except Exception as e:
            self.send_message(chat_id, f"❌ Error creating backup: {str(e)}")
    
    def handle_document(self, message: Dict[str, Any]):
        """Handle document uploads."""
        chat_id = str(message['chat']['id'])
        
        if not self.is_authorized(chat_id):
            return
        
        caption = message.get('caption', '').strip().lower()
        
        if caption == 'update_config':
            self.handle_update_config(chat_id, message['document'])
        else:
            self.send_message(chat_id, "❓ Send JSON files with caption 'update_config' to update configuration")
    
    def check_autoposter_running(self) -> bool:
        """Check if autoposter process is running."""
        try:
            result = subprocess.run(['pgrep', '-f', 'autoposter.py'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def handle_message(self, message: Dict[str, Any]):
        """Handle incoming Telegram message."""
        try:
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            
            if not self.is_authorized(chat_id):
                self.send_message(chat_id, "❌ Unauthorized access")
                return
            
            # Handle commands
            if text == '/start' or text == '/help':
                self.handle_start(chat_id)
            elif text == '/status':
                self.handle_status(chat_id)
            elif text == '/start_bot':
                self.handle_start_bot(chat_id)
            elif text == '/stop_bot':
                self.handle_stop_bot(chat_id)
            elif text == '/restart_bot':
                self.handle_restart_bot(chat_id)
            elif text == '/config':
                self.handle_config(chat_id)
            elif text == '/logs':
                self.handle_logs(chat_id)
            elif text == '/stats':
                self.handle_stats(chat_id)
            elif text == '/edit_config':
                self.handle_edit_config(chat_id)
            elif text == '/backup_config':
                self.handle_backup_config(chat_id)
            else:
                self.send_message(chat_id, "❓ Unknown command. Use /help to see available commands.")
        
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def run(self):
        """Main bot loop."""
        self.logger.info("Starting Telegram Bot Controller...")
        
        while self.running:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.offset = update['update_id'] + 1
                    
                    if 'message' in update:
                        if 'document' in update['message']:
                            self.handle_document(update['message'])
                        else:
                            self.handle_message(update['message'])
                
                time.sleep(1)  # Prevent excessive API calls
                
            except KeyboardInterrupt:
                self.logger.info("Bot controller stopped by user")
                self.running = False
            except Exception as e:
                self.logger.error(f"Error in bot loop: {e}")
                time.sleep(5)  # Wait before retrying


def main():
    """Main entry point."""
    # Load configuration to get bot token and authorized users
    config_manager = ConfigManager()
    
    if not config_manager.config.telegram_bot_token:
        print("❌ No Telegram bot token found in config.json")
        print("Please run setup.py first to configure Telegram notifications")
        return
    
    # For now, use the same chat_id as authorized user
    # In production, you might want a separate config for authorized users
    authorized_chat_ids = [config_manager.config.telegram_chat_id]
    
    bot = TelegramBotController(
        bot_token=config_manager.config.telegram_bot_token,
        authorized_chat_ids=authorized_chat_ids
    )
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot controller stopped")


if __name__ == "__main__":
    main()