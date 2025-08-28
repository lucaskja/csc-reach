# Quick Start Guide

## Get Started in 5 Minutes

### Prerequisites
- ✅ CSC-Reach installed
- ✅ Microsoft Outlook configured
- ✅ Customer data file ready

### Step 1: Launch Application
**Windows**: Double-click desktop icon  
**macOS**: Open from Applications folder

### Step 2: Import Customer Data
1. Click **Import Data**
2. Select your file (CSV, Excel, JSON)
3. Review automatic column mapping
4. Confirm import

### Step 3: Choose Template
1. Click **Template Library**
2. Browse categories or search
3. Select template
4. Click **Use Template**

### Step 4: Customize Message
- Edit subject and content
- Use variables: `{name}`, `{company}`
- Preview with sample data
- Save changes

### Step 5: Test Campaign
1. Select 1-2 customers
2. Click **Create Draft** (email) or **Preview** (WhatsApp)
3. Review in Outlook or preview window
4. Send test manually

### Step 6: Execute Campaign
1. Select target recipients
2. Choose channel (Email/WhatsApp)
3. Click **Send Messages**
4. Monitor progress in real-time

## Data File Format

Your file must include these columns:

```csv
name,company,email,phone
John Smith,ABC Corp,john@abc.com,+1-555-0123
Maria Garcia,XYZ Ltd,maria@xyz.com,+1-555-0456
```

## Template Example

```
Subject: Welcome to {company}, {name}!

Dear {name},

Thank you for your interest in our services. 
We're excited to work with {company}.

Best regards,
Your Team
```

## Pro Tips

- **Always test first** with small batches
- **Use meaningful variables** for personalization
- **Preview before sending** to catch errors
- **Monitor progress** during campaigns
- **Keep Outlook open** while sending emails

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "No data loaded" | Import your customer file first |
| "Email not ready" | Check Outlook is open and configured |
| "Variables not working" | Use exact syntax: `{name}` not `{Name}` |
| "Import failed" | Verify file format and column headers |

## Next Steps

- Explore [Template Library](user_manual.md#template-management)
- Learn about [Multi-Channel Messaging](user_manual.md#multi-channel-messaging)
- Review [Best Practices](user_manual.md#best-practices)
- Check [Troubleshooting Guide](troubleshooting_guide.md)

Need help? See the complete [User Manual](user_manual.md)
