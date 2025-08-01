"""Service manager for Instagram AutoPoster deployment."""

import os
import sys
import subprocess
import argparse
from pathlib import Path


SYSTEMD_SERVICE_TEMPLATE = """[Unit]
Description=Instagram AutoPoster
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}
Environment=PATH={python_path}
ExecStart={python_executable} {script_path}
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=autoposter

[Install]
WantedBy=multi-user.target
"""

SYSTEMD_BOT_SERVICE_TEMPLATE = """[Unit]
Description=Instagram AutoPoster Telegram Bot Controller
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}
Environment=PATH={python_path}
ExecStart={python_executable} {script_path}
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=autoposter-bot

[Install]
WantedBy=multi-user.target
"""


class ServiceManager:
    """Manages systemd services for the autoposter."""
    
    def __init__(self):
        self.current_dir = Path.cwd()
        self.user = os.getenv('USER', 'root')
        self.python_executable = sys.executable
        self.python_path = os.path.dirname(self.python_executable)
    
    def create_service_file(self, service_name: str, script_name: str, template: str) -> bool:
        """Create systemd service file."""
        try:
            service_content = template.format(
                user=self.user,
                working_dir=self.current_dir,
                python_path=self.python_path,
                python_executable=self.python_executable,
                script_path=self.current_dir / script_name
            )
            
            service_file = f"/etc/systemd/system/{service_name}.service"
            
            # Write service file (requires sudo)
            with open(f"{service_name}.service", 'w') as f:
                f.write(service_content)
            
            # Move to systemd directory
            result = subprocess.run([
                'sudo', 'mv', f"{service_name}.service", service_file
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to create service file: {result.stderr}")
                return False
            
            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
            print(f"✅ Service file created: {service_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating service file: {e}")
            return False
    
    def install_services(self):
        """Install both autoposter and bot controller services."""
        print("🔧 Installing AutoPoster services...")
        
        # Create autoposter service
        if self.create_service_file('autoposter', 'autoposter.py', SYSTEMD_SERVICE_TEMPLATE):
            print("✅ AutoPoster service installed")
        else:
            print("❌ Failed to install AutoPoster service")
            return False
        
        # Create bot controller service
        if self.create_service_file('autoposter-bot', 'telegram_bot_controller.py', SYSTEMD_BOT_SERVICE_TEMPLATE):
            print("✅ Bot Controller service installed")
        else:
            print("❌ Failed to install Bot Controller service")
            return False
        
        # Enable services
        try:
            subprocess.run(['sudo', 'systemctl', 'enable', 'autoposter'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'autoposter-bot'], check=True)
            print("✅ Services enabled for auto-start")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to enable services: {e}")
            return False
        
        print("\n🚀 Installation complete!")
        print("\nService Management Commands:")
        print("  sudo systemctl start autoposter        # Start main bot")
        print("  sudo systemctl start autoposter-bot    # Start controller")
        print("  sudo systemctl stop autoposter         # Stop main bot")
        print("  sudo systemctl stop autoposter-bot     # Stop controller")
        print("  sudo systemctl status autoposter       # Check main bot status")
        print("  sudo systemctl status autoposter-bot   # Check controller status")
        print("  sudo journalctl -u autoposter -f       # View main bot logs")
        print("  sudo journalctl -u autoposter-bot -f   # View controller logs")
        
        return True
    
    def uninstall_services(self):
        """Uninstall services."""
        print("🗑️ Uninstalling AutoPoster services...")
        
        services = ['autoposter', 'autoposter-bot']
        
        for service in services:
            try:
                # Stop service
                subprocess.run(['sudo', 'systemctl', 'stop', service], capture_output=True)
                
                # Disable service
                subprocess.run(['sudo', 'systemctl', 'disable', service], capture_output=True)
                
                # Remove service file
                service_file = f"/etc/systemd/system/{service}.service"
                subprocess.run(['sudo', 'rm', '-f', service_file], capture_output=True)
                
                print(f"✅ Removed {service} service")
            except Exception as e:
                print(f"❌ Error removing {service}: {e}")
        
        # Reload systemd
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], capture_output=True)
        print("✅ Services uninstalled")
    
    def show_status(self):
        """Show status of all services."""
        services = ['autoposter', 'autoposter-bot']
        
        print("📊 Service Status:")
        print("=" * 50)
        
        for service in services:
            try:
                result = subprocess.run([
                    'systemctl', 'is-active', service
                ], capture_output=True, text=True)
                
                status = result.stdout.strip()
                emoji = "🟢" if status == "active" else "🔴"
                
                print(f"{emoji} {service}: {status}")
                
                # Get brief status info
                result = subprocess.run([
                    'systemctl', 'status', service, '--no-pager', '-l'
                ], capture_output=True, text=True)
                
                # Extract key info from status
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Active:' in line or 'Main PID:' in line:
                        print(f"   {line.strip()}")
                
            except Exception as e:
                print(f"❌ Error checking {service}: {e}")
            
            print()
    
    def create_deployment_script(self):
        """Create deployment script for server."""
        script_content = '''#!/bin/bash

# Instagram AutoPoster Deployment Script
echo "🚀 Deploying Instagram AutoPoster..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not present
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv autoposter_env
source autoposter_env/bin/activate

# Install requirements
echo "📋 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up configuration
echo "⚙️ Running setup..."
python setup.py

# Install services
echo "🔧 Installing systemd services..."
python service_manager.py install

# Start services
echo "🚀 Starting services..."
sudo systemctl start autoposter-bot
sudo systemctl start autoposter

echo "✅ Deployment complete!"
echo ""
echo "📱 Your Telegram bot controller is now running!"
echo "💬 Send /start to your bot to begin remote management"
echo ""
echo "📊 Check status with: sudo systemctl status autoposter"
echo "📋 View logs with: sudo journalctl -u autoposter -f"
'''
        
        with open('deploy.sh', 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod('deploy.sh', 0o755)
        
        print("✅ Created deploy.sh script")
        print("📤 Upload this entire directory to your server and run: ./deploy.sh")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Instagram AutoPoster Service Manager')
    parser.add_argument('action', choices=['install', 'uninstall', 'status', 'deploy-script'],
                       help='Action to perform')
    
    args = parser.parse_args()
    manager = ServiceManager()
    
    if args.action == 'install':
        manager.install_services()
    elif args.action == 'uninstall':
        manager.uninstall_services()
    elif args.action == 'status':
        manager.show_status()
    elif args.action == 'deploy-script':
        manager.create_deployment_script()


if __name__ == "__main__":
    main()