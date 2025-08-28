# BrickLink Storage Location Auto-Populator

Automatically assign storage locations to new LEGO parts by matching them with your existing BrickLink inventory.

## Quick Start

**Double-click `start_app.bat` to launch the application!**

## How to Use

### 1. First Time Setup
- Launch the app by double-clicking `start_app.bat`
- Go to the **"2. API Setup"** tab
- Enter your BrickLink API credentials:
  - Consumer Key
  - Consumer Secret  
  - Token
  - Token Secret
- Click **"Save Config"** and then **"Connect & Test"**

### 2. Processing BSX Files
- Go to **"1. Select File"** tab
- Click **"Browse BSX Files"** and select your BrickStore export file
- Choose output options (create new file recommended)
- Go to **"3. Process"** tab  
- Click **"Start Processing"** when both requirements are green ✓
- View results in **"4. Results"** tab
- Click **"Save Updated File"** to save with locations

## Features

- **100% Automated** - Assigns locations based on your existing inventory
- **Smart Matching** - Uses most frequently used location per item ID
- **BrickStore Compatible** - Preserves all original file formatting
- **Preview Mode** - See changes before applying
- **Detailed Logging** - Track every assignment and issue

## Getting BrickLink API Credentials

1. Visit [BrickLink Developer Console](https://www.bricklink.com/v3/api/register_consumer.page)
2. Create a new OAuth application
3. Copy the Consumer Key, Consumer Secret, Token, and Token Secret
4. Enter them in the app's API Setup tab

## Files Explained

- `start_app.bat` - Double-click this to launch the application
- `main_app.py` - Main application file
- `config.json` - Stores your API credentials (created after first save)
- `bricklink_app.log` - Application log file

## Troubleshooting

**App won't start?**
- Ensure Python is installed
- Run: `pip install customtkinter requests requests-oauthlib`

**No matches found?**
- Ensure your BrickLink store has inventory with location data in "Remarks" field
- Check that item IDs match between BSX file and your inventory

**BrickStore won't open the file?**
- The app preserves original BSX structure - this should not happen
- Check the log file for any errors during processing

## Success!

Your processed BSX file will have storage locations automatically assigned based on your existing BrickLink inventory patterns. Import it back into BrickStore and your items will be perfectly organized!

---
*Generated with BrickLink Storage Location Auto-Populator*