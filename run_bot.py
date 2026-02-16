#!/usr/bin/env python3
"""
Instagram Reels Bot - Simple Launcher
Interactive launcher that prompts for configuration and runs the bot
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required tools are available"""
    print("Checking dependencies...")
    
    # Check Python packages
    try:
        import appium
        import selenium
    except ImportError:
        print("❌ Missing Python packages")
        print("Install with: pip install Appium-Python-Client selenium")
        return False
    
    # Check Appium
    try:
        result = subprocess.run(['appium', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Appium {result.stdout.strip()}")
        else:
            print("❌ Appium not working")
            return False
    except FileNotFoundError:
        print("❌ Appium not found")
        print("Install with: npm install -g appium")
        return False
    
    # Check ADB
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ADB found")
        else:
            print("❌ ADB not working")
            return False
    except FileNotFoundError:
        print("❌ ADB not found")
        print("Make sure Android SDK is installed")
        return False
    
    return True

def get_device_id():
    """Get device ID from user"""
    print("\nAvailable devices:")
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            devices = [line.split('\t')[0] for line in lines if line.strip()]
            
            if not devices:
                print("No devices found. Make sure emulator is running.")
                return None
            
            for i, device in enumerate(devices, 1):
                print(f"{i}. {device}")
            
            choice = input("Enter device number (or device ID): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(devices):
                return devices[int(choice) - 1]
            elif choice in devices:
                return choice
            else:
                print("Invalid choice")
                return None
        else:
            print("Could not get device list")
            return None
    except:
        device_id = input("Enter device ID: ").strip()
        return device_id if device_id else None

def update_config(device_id, username):
    """Update bot configuration"""
    try:
        with open('bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace configuration
        content = content.replace('YOUR_USERNAME = ""', f'YOUR_USERNAME = "{username}"')
        content = content.replace('DEVICE_ID = ""', f'DEVICE_ID = "{device_id}"')
        
        with open('bot.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error updating config: {e}")
        return False

def main():
    """Main launcher"""
    print("🤖 Instagram Reels Bot")
    print("=" * 25)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Get configuration
    print("\nBot Configuration:")
    print("-" * 18)
    
    device_id = get_device_id()
    if not device_id:
        print("No device selected")
        return 1
    
    username = input("Enter Instagram username to monitor: @").strip()
    if not username:
        print("No username provided")
        return 1
    
    print(f"\nConfiguration:")
    print(f"  Device: {device_id}")
    print(f"  Monitor: @{username}")
    
    confirm = input("\nStart bot? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return 1
    
    # Update configuration
    print("Updating configuration...")
    if not update_config(device_id, username):
        return 1
    
    # Start bot
    print("\n🚀 Starting Instagram Reels Bot...")
    print("Press Ctrl+C to stop\n")
    
    try:
        from bot import InstagramReelsBot
        bot = InstagramReelsBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())