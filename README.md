# 🤖 Instagram AutoPoster

An enterprise-grade Instagram automation system that monitors your main accounts and automatically comments using sub accounts when new posts are detected. Features full remote control via Telegram bot and production-ready server deployment.

![GitHub](https://img.shields.io/github/license/hungwahenry/instagram-auto-poster)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macOS-green.svg)

## ✨ Features

### 🔥 **Core Automation**
- **Smart Post Monitoring**: Tracks main accounts without login requirements
- **Intelligent Commenting**: Sub accounts automatically comment on new posts
- **Media Type Filtering**: Target specific content types (photos, videos, reels, albums)
- **Duplicate Prevention**: Advanced tracking prevents commenting twice
- **Sequential Processing**: Comments only on posts newer than last processed

### 📱 **Full Telegram Control**
- **Remote Management**: Complete bot control via Telegram commands
- **Real-time Notifications**: Instant alerts for comments, errors, and status
- **Live Configuration Editing**: Download, edit, and upload JSON config files
- **Log File Access**: Download recent logs directly to your phone
- **System Monitoring**: Server status, statistics, and performance metrics

### 🛡️ **Enterprise Features** 
- **Session Persistence**: Automatic login session management with UUID preservation
- **Rate Limiting Protection**: Human-like delays and randomization
- **Private API Usage**: Direct Instagram private API calls for maximum reliability
- **Service Management**: Systemd integration with auto-restart and boot startup
- **Comprehensive Logging**: Detailed application and system logs

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/hungwahenry/instagram-auto-poster.git
cd instagram-auto-poster

# Install dependencies
pip install -r requirements.txt

# Run interactive setup
python setup.py

# Start autoposter
python autoposter.py
```

### Server Deployment
```bash
# Upload files to server
scp -r . root@your-server:/opt/autoposter/

# Run one-command deployment
cd /opt/autoposter
./deploy.sh
```

## 📱 Telegram Bot Commands

Once deployed, control everything via Telegram:

### **Bot Control**
- `/start` - Welcome message and help
- `/status` - Check system status
- `/start_bot` - Start the autoposter
- `/stop_bot` - Stop the autoposter
- `/restart_bot` - Restart the autoposter

### **Configuration Management**
- `/config` - View current configuration
- `/edit_config` - Download config JSON for editing
- `/backup_config` - Create configuration backup
- **Upload JSON** with caption `update_config` to update settings

### **Monitoring & Logs**
- `/logs` - Download recent log files
- `/stats` - View commenting statistics

## ⚙️ Configuration

### Interactive Setup
Run `python setup.py` for guided configuration:

1. **Main Accounts** - Instagram accounts to monitor
2. **Sub Accounts** - Accounts that will post comments  
3. **Media Types** - Choose content types to target
4. **Comments** - Predefined comment pool
5. **Telegram Bot** - Remote control setup

### Configuration File Structure
```json
{
  "main_accounts": [
    {
      "username": "account_to_monitor",
      "user_id": "123456789",
      "enabled": true
    }
  ],
  "sub_accounts": [
    {
      "username": "commenting_account",
      "password": "secure_password",
      "enabled": true
    }
  ],
  "predefined_comments": [
    "Great post! 🔥",
    "Amazing content! ❤️",
    "Love this! 😍"
  ],
  "allowed_media_types": ["photo", "video", "reel", "album"],
  "check_interval": 300,
  "comment_delay_range": [30, 120],
  "max_comments_per_post": 2,
  "telegram_bot_token": "your_bot_token",
  "telegram_chat_id": "your_chat_id",
  "telegram_enabled": true
}
```

## 🏗️ Architecture

### System Components
- **autoposter.py** - Main automation engine
- **telegram_bot_controller.py** - Remote control interface
- **telegram_notifier.py** - Real-time notifications
- **config.py** - Configuration management
- **service_manager.py** - Production deployment tools

### Data Flow
1. **Monitor** → Fetch recent posts from main accounts
2. **Filter** → Apply media type and timestamp filters  
3. **Comment** → Select random sub accounts and comments
4. **Track** → Store processed post IDs to prevent duplicates
5. **Notify** → Send Telegram alerts for all activities

## 🛠️ Production Deployment

### Server Requirements
- **OS**: Ubuntu 20.04+ (recommended)
- **RAM**: 1GB minimum, 2GB recommended
- **Storage**: 20GB minimum
- **Python**: 3.7+

### Deployment Steps
1. **Server Setup**: Create Vultr/DigitalOcean server
2. **File Upload**: Transfer all files to `/opt/autoposter/`
3. **Run Deployment**: Execute `./deploy.sh`
4. **Configure**: Follow interactive setup prompts
5. **Test Bot**: Message your Telegram bot with `/start`

### Service Management
```bash
# Service status
sudo systemctl status autoposter
sudo systemctl status autoposter-bot

# Start/stop services
sudo systemctl start autoposter
sudo systemctl stop autoposter

# View logs
sudo journalctl -u autoposter -f
sudo journalctl -u autoposter-bot -f
```

## 📊 Smart Features

### **Intelligent Post Detection**
- **First Run**: Comments only on latest posts
- **Subsequent Runs**: Comments on posts newer than last processed
- **Media Filtering**: Skip unwanted content types
- **Duplicate Protection**: Never comment twice on same post

### **Human-like Behavior**
- **Random Delays**: 30-120 second intervals between comments
- **Comment Variation**: Randomly selected from your predefined list
- **Session Persistence**: Maintains login sessions to avoid repeated authentication
- **Private API**: Uses Instagram's mobile API for better reliability

### **Real-time Monitoring**
- **Telegram Notifications**: Instant alerts for all activities
- **Success/Failure Tracking**: Detailed reporting of comment attempts
- **Error Handling**: Automatic recovery from failures
- **Statistics**: Track total comments and performance metrics

## 🔒 Security & Best Practices

### **Account Security**
- Use strong, unique passwords for sub accounts
- Enable 2FA on main accounts (monitoring only, no login required)
- Regularly rotate sub account passwords
- Monitor for unusual Instagram security alerts

### **Rate Limiting**
- Built-in delays prevent Instagram rate limiting
- Configurable intervals between checks and comments
- Smart session management reduces authentication requests
- Human-like behavior patterns

### **Data Protection**
- Sensitive data excluded from version control
- Session files stored locally with restricted permissions
- Configuration backups created automatically
- Telegram bot access limited to authorized users

## 📈 Use Cases

### **Content Creators**
- Boost engagement on new posts immediately
- Maintain consistent interaction across multiple accounts
- Support network growth through cross-promotion

### **Marketing Agencies**
- Automate client engagement strategies
- Manage multiple brand accounts efficiently
- Provide detailed reporting and analytics

### **Social Media Managers**
- Scale engagement across client portfolios
- Ensure timely responses to new content
- Maintain brand presence 24/7

## 🔍 Troubleshooting

### **Common Issues**

**Services won't start:**
```bash
sudo journalctl -u autoposter -n 50
sudo systemctl status autoposter
```

**Instagram login failures:**
- Check account credentials
- Verify 2FA settings
- Review Instagram security notifications

**Telegram bot not responding:**
```bash
sudo journalctl -u autoposter-bot -n 50
```

**Comments not appearing:**
- Instagram may be shadow-filtering comments
- Try more natural, varied comments
- Check if accounts need to follow each other first

### **Log Locations**
- **Application logs**: `autoposter.log`
- **Bot controller logs**: `bot_controller.log`  
- **System logs**: `sudo journalctl -u autoposter`

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and legitimate business purposes only. Users are responsible for:
- Complying with Instagram's Terms of Service
- Following applicable laws and regulations
- Using the tool ethically and responsibly
- Managing their own account security

The authors are not responsible for any account restrictions, violations, or misuse of this software.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review application logs
3. Open an issue on GitHub

---

**Built with ❤️ for the Instagram automation community**