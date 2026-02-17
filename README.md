# Instagram Reels Reposter Bot

**⚠️ Android Only**: This bot works exclusively with Android devices/emulators and cannot run on iOS devices.

Automated Instagram bot that monitors DMs for reels and automatically reposts them with captions.

## Features

- **Automatic DM Monitoring**: Checks for new reels in DMs every 5-6 minutes
- **Smart Duplicate Detection**: Prevents reposting the same reel using unique ID tracking
- **Automatic Reposting**: Downloads and reposts reels with captions
- **Cross-Platform Host Support**: Launcher works on Windows, macOS, and Linux (but requires Android device/emulator)
- **Auto Appium Management**: Automatically starts/stops Appium server
- **Error Handling**: Comprehensive error handling and recovery mechanisms with Appium crash recovery
- **Emulator Integration**: Designed for Android emulator

## Important Limitations

⚠️ **Download Button Requirement**: This bot only works with reels that have the "Download" button available. Many users restrict downloads on their content, which will prevent the bot from saving and reposting those reels. The bot will skip reels without download access.

## Prerequisites

**⚠️ Android Device/Emulator Required**: This bot requires an Android device or emulator. iOS devices are not supported.

- Android Emulator or physical Android device
- Instagram app installed and logged in
- Node.js and npm installed
- Android SDK configured

## Quick Start

### 1. Install Dependencies

```bash
pip install Appium-Python-Client selenium
npm install -g appium
appium driver install uiautomator2
```

### 2. Run the Executable Launcher

**Windows:** Double-click `run_bot.bat` or run:
```bash
run_bot.bat
```

**macOS/Linux:**
```bash
./run_bot.sh
```

**Or directly with Python:**
```bash
python3 run_bot.py
```

The launcher will:
1. Check all dependencies (Appium, ADB, Python packages)
2. Show available devices and prompt for device ID
3. Ask for Instagram username to monitor
4. Automatically configure the bot
5. Start the Instagram bot

### What Happens

1. **Appium Server**: Automatically starts in background
2. **Device Connection**: Connects to Instagram app on emulator
3. **Login Check**: Verifies Instagram login status
4. **DM Monitoring**: Checks for new reels from specified user
5. **Processing**: Downloads and reposts new reels with AI captions
6. **Loop**: Repeats every 5-6 minutes

### Stop the Bot

Press `Ctrl+C` to gracefully stop the bot and cleanup resources.

## Technical Details

### File Structure

- `bot.py` - Main bot implementation
- `run_bot.py` - Interactive launcher (asks for device ID & username)
- `run_bot.bat` - Windows executable (double-click to run)
- `run_bot.sh` - macOS/Linux executable
- `processed_reels.txt` - Tracks processed reel IDs

### Key Methods

- `start_appium_server()` - Auto-starts Appium with OS-specific handling
- `check_for_reels()` - Monitors DMs for new reel content
- `download_reel()` - Saves reels to device storage
- `repost_reel()` - Creates new posts with AI-generated captions
- `load_processed_reels()` - Prevents duplicate processing

### Error Handling

- Automatic popup dismissal
- App restart on connection failures
- Graceful Appium server management
- Comprehensive logging and debugging

## Troubleshooting

### Common Issues

1. **Appium not starting**: Ensure Node.js and Appium are properly installed
2. **Device not found**: Check emulator is running and device ID is correct
3. **Instagram login issues**: Manually log in on emulator before starting bot
4. **Reel processing fails**: Check Instagram app permissions and storage access
5. **Download button missing**: Some users restrict downloads on their reels. The bot will skip these reels automatically
6. **UiAutomator2 crashes**: The bot will automatically restart Appium and reconnect when instrumentation crashes occur

## Security Notes

- Stores processed reel IDs locally to prevent duplicates
- Uses device clipboard for URL extraction
- Requires Instagram login credentials on device
- No external API calls or data transmission

## Requirements

- Python 3.7+
- Android Emulator
- Instagram App
- Appium Server
- Android SDK