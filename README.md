# Multi-Channel Bulk Messaging System

## Overview

The Multi-Channel Bulk Messaging System is a cross-platform desktop application designed to facilitate bulk messaging through email and WhatsApp channels. It processes customer data from CSV files, utilizes Outlook's mail merge functionality for emails, and integrates with WhatsApp Business API for instant messaging. The application runs locally on users' machines, available for both Windows and macOS platforms.

This system caters to a multilingual user base in Brazil and Latin America, supporting Portuguese, Spanish, and English. It's designed to streamline communication processes for businesses needing to send mass communications efficiently and effectively.

## Key Features

- CSV file processing (customer name, company name, telephone number, email)
- Email composition and sending via Outlook mail merge
- WhatsApp message composition and sending via WhatsApp Business API
- Default and customizable message templates for both email and WhatsApp
- Multi-language support (Portuguese, Spanish, English)
- Cross-platform compatibility (Windows and macOS)
- Daily messaging quota management (100 per day per user)
- User-friendly interface for CSV file input and template customization

## Technologies Used

- Python
- Microsoft Outlook (for email integration)
- WhatsApp Business API
- PyQt/PySide6 for GUI development
- CSV file handling libraries
- py2exe/PyInstaller for executable creation

## System Requirements

### Windows
- Windows 10 or later (primary supported platform)
- Microsoft Outlook installed and configured
- 4GB RAM minimum
- 2GHz processor or better
- 500MB free disk space

### macOS
- macOS 10.14 or later
- Microsoft Outlook for Mac installed and configured
- 4GB RAM minimum
- 2GHz processor or better
- 500MB free disk space

## Installation

### Windows

1. Download the latest release `MultiChannelMessaging-win.exe` from the releases page.
2. Double-click the executable to start the installation process.
3. Follow the on-screen instructions to complete the installation.

### macOS

1. Download the latest release `MultiChannelMessaging-mac.dmg` from the releases page.
2. Open the DMG file and drag the application to your Applications folder.
3. Right-click on the application and select "Open" to bypass macOS security restrictions on the first run.

## Configuration

### WhatsApp Business API Setup

1. Obtain WhatsApp Business API credentials from the WhatsApp Business Platform.
2. In the application settings, navigate to "WhatsApp Configuration".
3. Enter your API key, phone number ID, and other required credentials.

### Outlook Configuration

1. Ensure Microsoft Outlook is installed and set up with your email account.
2. The application will automatically detect your Outlook installation.
3. If prompted, grant the necessary permissions for the application to interact with Outlook.

## Usage

1. Launch the Multi-Channel Bulk Messaging System application.
2. Click on "Import CSV" and select your customer data file.
3. Choose or customize your message template for email and WhatsApp.
4. Select the desired language for your messages.
5. Review the list of recipients and message content.
6. Click "Send" to initiate the bulk messaging process.
7. Monitor the progress and review the sending report upon completion.

## Development Approach

When working with this project, the agent should ensure it is working within a git repo. If one is not configured yet, the agent should create one.

The agent should update and extend this README.md file with additional information about the project as development progresses, and commit changes to this file and the other planning files below as they are updated.

Working with the user, the agent will implement the project step by step, first by working out the requirements, then the desktop application design, followed by the list of tasks needed to:
1. Implement the project source code
2. Create platform-specific builds
3. Run integration tests on both Windows and macOS platforms

Once all planning steps are completed and documented, and the user is ready to proceed, the agent will begin implementing the tasks one at a time until the project is completed.

## Project Layout

The project includes the following core files:

* `requirements.md`: Defines the requirements for this project
* `design.md`: Defines the desktop application design and architecture
* `tasks.md`: Lists the discrete tasks that need to be executed in order to successfully implement the project. Each task has a check box [ ] that is checked off when the task has been successfully completed. A git commit should be performed after any task is successfully completed.

Additional files that may be included based on project needs:

* `test-plan.md`: Describes unit test, integration, and performance test plans
* `packaging.md`: Details the build and packaging process for both Windows and macOS
* `a11y.md`: Describes the accessibility goals for the project and accessibility testing plan

## Limitations

- Daily limit of 100 messages per user
- Adheres to WhatsApp Business API usage policies
- Complies with email anti-spam regulations
- Requires local installation of Microsoft Outlook