#!/bin/bash

# Instagram AutoPoster Deployment Script
echo "🚀 Deploying Instagram AutoPoster..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Running as root. Consider creating a dedicated user for security."
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python and pip if not present
echo "🐍 Installing Python dependencies..."
apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv autoposter_env
source autoposter_env/bin/activate

# Install requirements
echo "📋 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set proper permissions
echo "🔒 Setting file permissions..."
chmod +x service_manager.py
chmod 600 config.json 2>/dev/null || true

# Set up configuration
echo "⚙️ Running setup..."
python setup.py

# Install services
echo "🔧 Installing systemd services..."
python service_manager.py install

# Start services
echo "🚀 Starting services..."
systemctl start autoposter-bot
systemctl start autoposter

# Check service status
echo "📊 Checking service status..."
sleep 3
systemctl is-active --quiet autoposter && echo "✅ AutoPoster service is running" || echo "❌ AutoPoster service failed to start"
systemctl is-active --quiet autoposter-bot && echo "✅ Bot Controller service is running" || echo "❌ Bot Controller service failed to start"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📱 Your Telegram bot controller is now running!"
echo "💬 Send /start to your bot to begin remote management"
echo ""
echo "📊 Service Management Commands:"
echo "  systemctl status autoposter        # Check main bot status"
echo "  systemctl status autoposter-bot    # Check controller status"
echo "  journalctl -u autoposter -f        # View main bot logs"
echo "  journalctl -u autoposter-bot -f    # View controller logs"
echo ""
echo "🔧 To manage services:"
echo "  systemctl start|stop|restart autoposter"
echo "  systemctl start|stop|restart autoposter-bot"
echo ""
echo "🎯 Next steps:"
echo "1. Message your Telegram bot with /start"
echo "2. Use /status to check system status"
echo "3. Monitor logs with /logs command"
echo ""
echo "🚀 Your Instagram AutoPoster is now live!"