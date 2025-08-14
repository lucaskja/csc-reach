# CSC-Reach Product Overview

CSC-Reach is a cross-platform desktop application for bulk email communication through Microsoft Outlook integration. It processes customer data from CSV files and utilizes Outlook's native functionality for professional email campaigns.

## Core Purpose
- Streamline bulk email communication for businesses
- Professional template management with variable substitution
- Cross-platform Outlook integration (macOS + Windows)
- Real-time progress tracking and comprehensive logging

## Key Features
- CSV import with automatic column detection and encoding support
- Email template system with variables (`{name}`, `{company}`, etc.)
- Cross-platform Outlook integration (AppleScript for macOS, COM for Windows)
- Template library with categories and import/export functionality
- Multi-language support (English, Spanish, Portuguese)
- Professional GUI with real-time progress tracking
- Draft email creation for testing before bulk sending

## Target Users
- Businesses needing streamlined email communication
- Marketing teams managing email campaigns
- Customer service teams with bulk messaging needs
- Organizations requiring professional email automation

## Current Status
### Completed Features
- ✅ Email MVP with Outlook integration
- ✅ Cross-platform support (macOS + Windows)
- ✅ CSV import with automatic column detection
- ✅ Template Management System with library
- ✅ Complete internationalization (en/pt/es)
- ✅ Professional build system

## Internationalization Requirements
- **Everything must be internationalized**
- Support English (en), Portuguese (pt), and Spanish (es)
- Use the existing i18n system: `from ..core.i18n_manager import get_i18n_manager`
- All user-facing text must use `i18n.tr("key")` or `self.i18n_manager.tr("key")`
- Add translations to all three language files in `src/multichannel_messaging/localization/`