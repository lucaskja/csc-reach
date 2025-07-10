# CSC-Reach Troubleshooting Guide

## 🔧 Common Problems and Solutions

### 🚫 Installation Problems

#### Windows: "Windows protected your PC" message
**What it means**: Windows doesn't recognize CSC-Reach yet  
**Solution**:
1. Click **"More info"**
2. Click **"Run anyway"**
3. This only happens the first time

#### Mac: "Can't be opened because it's from an unidentified developer"
**What it means**: macOS security is protecting you  
**Solution**:
1. Right-click on CSC-Reach in Applications
2. Select **"Open"**
3. Click **"Open"** in the dialog
4. This only happens the first time

#### "Microsoft Outlook is not installed"
**What it means**: CSC-Reach can't find Outlook  
**Solution**:
1. Install Microsoft Outlook (from Office or Mac App Store)
2. Set up your email account in Outlook
3. Restart CSC-Reach

---

### 📧 Email Problems

#### "Email: Not ready" status
**What it means**: CSC-Reach can't connect to Outlook  
**Solutions**:
1. **Make sure Outlook is open** and working
2. **Send a test email** from Outlook to verify it works
3. **Restart both Outlook and CSC-Reach**
4. **Check your internet connection**

#### "Failed to send email" errors
**What it means**: Some emails couldn't be sent  
**Solutions**:
1. **Check email addresses** - remove invalid ones
2. **Send fewer emails at once** - try 10-20 instead of 100+
3. **Wait and try again** - you might have hit daily limits
4. **Check internet connection**

#### Emails are not personalized
**What it means**: {name} and {company} aren't being replaced  
**Solutions**:
1. **Check your CSV file** has columns named exactly: `name`, `company`, `phone`, `email`
2. **Use curly braces**: `{name}` not `(name)` or `[name]`
3. **Re-import your CSV file**

---

### 📊 Customer List Problems

#### "No recipients loaded"
**What it means**: You haven't imported customers yet  
**Solution**:
1. Click **"Import CSV"**
2. Select your customer file
3. Make sure it's in CSV format

#### CSV file won't import
**What it means**: The file format is wrong  
**Solutions**:
1. **Save as CSV format** in Excel:
   - File → Save As → CSV (Comma delimited)
2. **Check column names** are exactly: `name`, `company`, `phone`, `email`
3. **Remove empty rows** at the top or bottom
4. **Use English characters** - avoid special symbols in column names

#### Customer names look wrong
**What it means**: Character encoding problem  
**Solutions**:
1. **Open CSV in Notepad** (Windows) or TextEdit (Mac)
2. **Save with UTF-8 encoding**
3. **Re-import the file**

---

### 🎯 Template Problems

#### Templates don't save
**What it means**: Permission or storage problem  
**Solutions**:
1. **Run CSC-Reach as administrator** (Windows)
2. **Check available disk space** - need at least 100MB free
3. **Try a shorter template name**

#### Can't find saved templates
**What it means**: Templates are saved but not showing  
**Solutions**:
1. **Restart CSC-Reach**
2. **Check the correct category** in Template Library
3. **Use the search box** in Template Library

#### Template preview shows errors
**What it means**: Problem with template format  
**Solutions**:
1. **Check for unmatched braces**: use `{name}` not `{name`
2. **Remove special characters** from template
3. **Keep templates under 10,000 characters**

---

### 🐌 Performance Problems

#### CSC-Reach is very slow
**What it means**: Computer resources are low  
**Solutions**:
1. **Close other programs** to free memory
2. **Send fewer emails at once** (try 25-50 instead of 200+)
3. **Restart your computer**
4. **Check available disk space**

#### Sending emails takes forever
**What it means**: Network or Outlook performance issue  
**Solutions**:
1. **Check internet speed** - slow connection = slow sending
2. **Close other programs** using internet
3. **Send in smaller batches** (20-30 emails at a time)
4. **Wait for Outlook to finish** processing previous emails

---

### 🔒 Permission Problems

#### "Access denied" errors
**What it means**: CSC-Reach doesn't have necessary permissions  
**Solutions**:

**Windows**:
1. Right-click CSC-Reach icon
2. Select **"Run as administrator"**
3. Click **"Yes"** when prompted

**Mac**:
1. Go to System Preferences → Security & Privacy
2. Click **"Privacy"** tab
3. Find CSC-Reach and **check the box** next to it

#### Antivirus blocks CSC-Reach
**What it means**: Security software thinks CSC-Reach is suspicious  
**Solutions**:
1. **Add CSC-Reach to exceptions** in your antivirus
2. **Temporarily disable** antivirus during installation
3. **Download from official source** only

---

### 🌐 Language Problems

#### Interface is in wrong language
**What it means**: Language setting needs to be changed  
**Solution**:
1. Look for **"Settings"** or **"Configurações"** or **"Configuraciones"**
2. Find **"Language"** or **"Idioma"**
3. Select your preferred language
4. **Restart CSC-Reach**

#### Some text still in English
**What it means**: Not all features are translated yet  
**Solution**:
- This is normal - core features are translated
- Updates will include more translations

---

## 🆘 Emergency Solutions

### If Nothing Works
1. **Restart your computer**
2. **Reinstall CSC-Reach** (download fresh copy)
3. **Check Windows/macOS updates**
4. **Contact support** with error details

### Before Contacting Support
Gather this information:
- **What you were trying to do**
- **Exact error message** (take a screenshot)
- **Your operating system** (Windows 10, macOS Big Sur, etc.)
- **How many customers** you were trying to email
- **Size of your CSV file**

### Quick Diagnostic Steps
1. **Can you open CSC-Reach?** → If no, reinstall
2. **Can you import CSV?** → If no, check file format
3. **Can you see "Email: Ready"?** → If no, check Outlook
4. **Can you send one test email?** → If no, check internet
5. **Can you send to multiple customers?** → If no, reduce batch size

---

## 📞 Getting More Help

### Self-Help Resources
- [User Manual](user_manual.md) - Complete guide
- [Quick Start Guide](quick_start_guide.md) - 5-minute setup
- [Installation Guides](windows_installation_guide.md) - Step-by-step installation

### Contact Support
When contacting support, include:
- **Screenshot of the error**
- **Your CSV file** (remove sensitive data first)
- **Steps you tried** from this guide
- **Your computer details** (Windows/Mac version)

### Prevention Tips
- **Keep CSC-Reach updated** - download new versions when available
- **Backup your templates** - export them regularly
- **Test with small groups** - always start with 5-10 customers
- **Keep Outlook updated** - install Microsoft Office updates
- **Maintain your CSV file** - remove old/invalid email addresses

---

**Still having problems?** Contact your administrator or CSC-Reach support team with the information above.
