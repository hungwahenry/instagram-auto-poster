# 🚀 Instagram AutoPoster - Server Deployment Guide

Complete guide for deploying your Instagram AutoPoster to a Vultr server with full Telegram bot control.

## 📋 Prerequisites

### 1. Server Setup (Vultr/DigitalOcean/AWS)
- **OS**: Ubuntu 20.04 LTS or newer (recommended)
- **RAM**: Minimum 1GB (2GB recommended for multiple accounts)
- **Storage**: 20GB minimum
- **Network**: Stable internet connection with good uptime
- **Provider**: Vultr, DigitalOcean, AWS EC2, Linode, or similar

### 2. Telegram Bot Setup
1. **Create Bot with BotFather**:
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot`
   - Choose a name and username for your bot
   - Save the **Bot Token** (e.g., `123456789:ABCdef...`)

2. **Get Your Chat ID**:
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - Save your **Chat ID** (e.g., `123456789`)

## 🔧 Deployment Steps

### Step 1: Connect to Your Server
```bash
ssh root@your-server-ip
```

### Step 2: Upload AutoPoster Files
```bash
# Create directory
mkdir -p /opt/autoposter
cd /opt/autoposter

# Upload all files from your local autoposter directory
# Use scp, rsync, or git clone
```

### Step 3: Run Deployment Script
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment (will install everything)
./deploy.sh
```

### Step 4: Configure During Setup
The deployment script will run `setup.py` interactively:

1. **Main Accounts**: Enter Instagram usernames to monitor
2. **Sub Accounts**: Enter commenting account credentials
3. **Media Types**: Choose content types to comment on
4. **Comments**: Add your predefined comments
5. **Telegram Bot**: Enter your bot token and chat ID

### Step 5: Verify Installation
```bash
# Check service status
sudo systemctl status autoposter
sudo systemctl status autoposter-bot

# View logs
sudo journalctl -u autoposter -f
sudo journalctl -u autoposter-bot -f
```

## 🤖 Telegram Bot Commands

Once deployed, message your bot with these commands:

### **Basic Commands**
- `/start` - Welcome message and command list
- `/help` - Show available commands
- `/status` - Check autoposter and server status

### **Bot Control**
- `/start_bot` - Start the autoposter
- `/stop_bot` - Stop the autoposter  
- `/restart_bot` - Restart the autoposter

### **Monitoring**
- `/config` - View current configuration
- `/stats` - View comment statistics
- `/logs` - Download recent log files

## 📊 Service Management

### **Systemd Services**
Your deployment creates two services:

1. **autoposter.service** - Main Instagram bot
2. **autoposter-bot.service** - Telegram controller

### **Service Commands**
```bash
# Start services
sudo systemctl start autoposter
sudo systemctl start autoposter-bot

# Stop services
sudo systemctl stop autoposter
sudo systemctl stop autoposter-bot

# Restart services
sudo systemctl restart autoposter
sudo systemctl restart autoposter-bot

# Check status
sudo systemctl status autoposter
sudo systemctl status autoposter-bot

# View logs
sudo journalctl -u autoposter -f
sudo journalctl -u autoposter-bot -f

# Enable auto-start on boot
sudo systemctl enable autoposter
sudo systemctl enable autoposter-bot
```

## 📁 File Structure on Server
```
/opt/autoposter/
├── autoposter.py              # Main bot
├── telegram_bot_controller.py # Remote controller
├── telegram_notifier.py       # Notification system
├── config.py                  # Configuration manager
├── setup.py                   # Interactive setup
├── service_manager.py         # Service management
├── requirements.txt           # Dependencies
├── config.json               # Your configuration
├── sessions/                 # Login sessions
├── commented_posts/          # Comment tracking
├── autoposter.log           # Main bot logs
├── bot_controller.log       # Controller logs
└── deploy.sh               # Deployment script
```

## 🔐 Security Considerations

### **1. File Permissions**
```bash
# Secure configuration file
chmod 600 config.json

# Secure session directory
chmod 700 sessions/
```

### **2. Firewall Setup**
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Block unnecessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### **3. Telegram Bot Security**
- Only you (authorized chat ID) can control the bot
- Bot token is stored securely in config.json
- All commands require authorization

## 📱 Telegram Notifications

Your bot will automatically send notifications for:

- ✅ **Successful comments** with post details
- ❌ **Failed comments** with error information
- 🚀 **Startup/shutdown** status updates
- 📊 **Monitoring cycle summaries** 
- 🚨 **Error alerts** for critical issues
- 🔐 **Login problems** for sub accounts

## 🔍 Troubleshooting

### **Common Issues**

1. **Services won't start**:
   ```bash
   # Check logs for errors
   sudo journalctl -u autoposter -n 50
   
   # Verify Python path
   which python3
   ```

2. **Telegram bot not responding**:
   ```bash
   # Check bot controller logs
   sudo journalctl -u autoposter-bot -n 50
   
   # Verify bot token and chat ID in config.json
   ```

3. **Instagram login failures**:
   ```bash
   # Check autoposter logs
   sudo journalctl -u autoposter -n 50
   
   # Verify account credentials
   # Check for 2FA requirements
   ```

4. **Permission errors**:
   ```bash
   # Fix file ownership
   sudo chown -R $USER:$USER /opt/autoposter
   
   # Fix permissions
   chmod 755 /opt/autoposter
   chmod 600 /opt/autoposter/config.json
   ```

### **Log Locations**
- **System logs**: `sudo journalctl -u autoposter`
- **Application logs**: `/opt/autoposter/autoposter.log`
- **Bot controller logs**: `/opt/autoposter/bot_controller.log`

## 🔄 Updates and Maintenance

### **Updating the Bot**
1. Stop services: `sudo systemctl stop autoposter autoposter-bot`
2. Upload new files to `/opt/autoposter/`
3. Restart services: `sudo systemctl start autoposter autoposter-bot`

### **Backup Important Data**
```bash
# Backup configuration and data
tar -czf autoposter-backup.tar.gz config.json sessions/ commented_posts/
```

### **Monitoring Resources**
```bash
# Check system resources
htop
df -h
free -h

# Monitor service logs in real-time
sudo journalctl -u autoposter -f
```

## 📞 Support

If you encounter issues:

1. Check the logs first: `sudo journalctl -u autoposter -n 100`
2. Verify configuration: `/config` command in Telegram
3. Check service status: `/status` command in Telegram
4. Review this deployment guide

Your Instagram AutoPoster is now ready for 24/7 operation with full remote control via Telegram! 🎉