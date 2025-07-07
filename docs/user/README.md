# CSC-Reach User Guide

## Overview

CSC-Reach is a professional cross-platform desktop application designed to facilitate bulk email communication through Microsoft Outlook integration. It processes customer data from CSV files and utilizes Outlook's native functionality for professional email campaigns.

## Quick Start

### Installation

#### macOS
1. Download `CSC-Reach-macOS.dmg` from the releases
2. Open the DMG file and drag the application to your Applications folder
3. Right-click on the application and select "Open" to bypass macOS security restrictions on the first run

#### Windows
1. Download `CSC-Reach-Windows.zip` from the releases
2. Extract the ZIP file to your desired location
3. Run `CSC-Reach.exe`

### Basic Usage

1. **Launch** the CSC-Reach application
2. **Import CSV**: Click "Import CSV" and select your customer data file
   - Required columns: name, company, phone, email
3. **Customize Template**: Edit the email subject and content
   - Use variables like `{name}` and `{company}` for personalization
4. **Preview**: Click "Preview Email" to see how emails will look
5. **Send**: Click "Send Emails" to start the bulk sending process

## Features

- **CSV file processing** with automatic column detection
- **Email composition and sending** via Outlook integration
- **Cross-platform Outlook integration** (macOS AppleScript + Windows COM)
- **Email preview functionality** before sending
- **Real-time progress tracking** and comprehensive logging
- **Professional GUI** with menu bar and toolbar
- **Multi-language support** framework (Portuguese, Spanish, English)

## System Requirements

### Windows
- Windows 10 or later
- Microsoft Outlook installed and configured
- 4GB RAM minimum
- 500MB free disk space

### macOS
- macOS 10.14 or later
- Microsoft Outlook for Mac installed and configured
- 4GB RAM minimum
- 500MB free disk space

## CSV File Format

Your CSV file should contain the following columns:
- `name` - Customer name
- `company` - Company name
- `phone` - Phone number (optional)
- `email` - Email address

Example:
```csv
name,company,phone,email
John Smith,Acme Corp,555-1234,john@acme.com
Jane Doe,Tech Inc,555-5678,jane@tech.com
```

## Email Templates

Use these variables in your email templates:
- `{name}` - Customer name
- `{company}` - Company name
- `{phone}` - Phone number
- `{email}` - Email address

## Troubleshooting

### Common Issues

1. **Outlook not detected**
   - Ensure Microsoft Outlook is installed and configured
   - Try restarting the application

2. **CSV import fails**
   - Check that your CSV file has the required columns
   - Ensure the file is not open in another application

3. **Emails not sending**
   - Verify Outlook is running and configured with your email account
   - Check your internet connection

### Getting Help

- Check the documentation in `docs/`
- Review the troubleshooting guides
- Contact support for additional assistance

## License

This project is licensed under the MIT License - see the LICENSE file for details.
