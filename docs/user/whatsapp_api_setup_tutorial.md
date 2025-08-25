# WhatsApp Business API Setup Tutorial for CSC-Reach

## Overview

This comprehensive tutorial will guide you through setting up WhatsApp Business API credentials for use with CSC-Reach. You'll learn how to create a Meta developer account, set up a WhatsApp Business app, and obtain the necessary API credentials.

## Prerequisites

Before you begin, ensure you have:
- A valid WhatsApp Business account
- A Meta (Facebook) account
- A verified business phone number
- Administrative access to your business

## Step-by-Step Setup Guide

### Step 1: Create a Meta Developer Account

1. **Visit Meta for Developers**
   - Go to [developers.facebook.com](https://developers.facebook.com)
   - Click **"Get Started"** in the top right corner

2. **Register as a Developer**
   - Log in with your Meta (Facebook) account
   - Complete the developer registration process
   - Verify your account via email or phone if prompted
   - Accept the Meta Developer Terms and Policies

3. **Verify Your Account**
   - You may need to provide additional verification
   - This can include phone number verification or identity confirmation

### Step 2: Create a Business App

1. **Access My Apps**
   - From the Meta for Developers dashboard, click **"My Apps"**
   - Click **"Create App"**

2. **Select App Type**
   - Choose **"Business"** as your app type
   - If you don't see "Business", select **"Other"** → **"Next"** → **"Business"**

3. **Configure Your App**
   - **App Name**: Enter a descriptive name (e.g., "YourCompany WhatsApp Integration")
   - **App Contact Email**: Use your business email address
   - **Business Account**: Select or create a business account
   - Click **"Create App"**

### Step 3: Add WhatsApp Product to Your App

1. **Add WhatsApp Product**
   - In your app dashboard, scroll down to **"Add products to your app"**
   - Find **"WhatsApp"** and click **"Set up"**

2. **Business Portfolio Setup**
   - If you have an existing business portfolio, select it
   - If not, you'll be guided through creating one:
     - **Business Name**: Your official business name
     - **Business Description**: Brief description of your business
     - **Business Website**: Your company website URL
     - **Business Category**: Select the most appropriate category

3. **Automatic Setup**
   The system will automatically create:
   - A test WhatsApp Business Account (WABA)
   - A test business phone number
   - A pre-approved "hello_world" template

### Step 4: Generate Access Token

1. **Navigate to API Setup**
   - In the left sidebar, go to **"WhatsApp"** → **"API Setup"**

2. **Generate Access Token**
   - Click the blue **"Generate access token"** button
   - Complete the authentication flow
   - **Important**: Copy and securely store this token immediately
   - This is your **Access Token** for CSC-Reach

3. **Note Your Phone Number ID**
   - In the **"From"** field, you'll see your test phone number
   - Click on the phone number to see details
   - Copy the **Phone Number ID** (numeric value)
   - This is your **Phone Number ID** for CSC-Reach

### Step 5: Add Test Recipients (Development Phase)

1. **Add Recipient Numbers**
   - In the **"To"** field, click **"Manage phone number list"**
   - Click **"Add phone number"**
   - Enter a valid WhatsApp number (including country code)
   - The recipient will receive a verification code in WhatsApp

2. **Verify Recipients**
   - Ask the recipient to share the verification code
   - Enter the code to verify the number
   - Repeat for up to 5 test numbers

### Step 6: Test Your Setup

1. **Send Test Message**
   - Ensure your test phone number is selected in **"From"**
   - Select a verified recipient in **"To"**
   - Click **"Send message"** to send the hello_world template
   - Verify the message is received

2. **Test with cURL (Optional)**
   ```bash
   curl -X POST \
     https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages \
     -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
     -H 'Content-Type: application/json' \
     -d '{
       "messaging_product": "whatsapp",
       "to": "RECIPIENT_PHONE_NUMBER",
       "type": "template",
       "template": {
         "name": "hello_world",
         "language": {
           "code": "en_US"
         }
       }
     }'
   ```

### Step 7: Configure CSC-Reach

1. **Open CSC-Reach**
   - Launch the CSC-Reach application
   - Go to **"Settings"** → **"WhatsApp Business API Settings"**

2. **Enter Your Credentials**
   - **Access Token**: Paste the token from Step 4
   - **Phone Number ID**: Enter the Phone Number ID from Step 4
   - **Business Account ID**: (Optional) Found in your app dashboard
   - Click **"Test Connection"** to verify

3. **Configure Rate Limits**
   - **Rate Limit**: Start with 20 messages per minute (default)
   - **Daily Limit**: Set to 1000 messages per day (default)
   - **Delay Between Messages**: 3 seconds (recommended)

### Step 8: Set Up Webhooks (Optional but Recommended)

1. **Configure Webhook URL**
   - In WhatsApp → **"Configuration"**, find **"Webhook"**
   - Enter your webhook URL (if you have one)
   - Set **"Verify Token"** (create a secure random string)

2. **Subscribe to Events**
   - Check **"messages"** for message delivery status
   - Check **"message_deliveries"** for delivery confirmations
   - Check **"message_reads"** for read receipts

### Step 9: Production Setup (When Ready)

1. **Add Real Business Number**
   - In **"API Setup"**, click **"Add phone number"**
   - Follow the verification process for your business number
   - This may require business verification documents

2. **Business Verification**
   - Complete Meta Business Verification if required
   - Provide necessary business documents
   - Wait for approval (can take several days)

3. **Update Rate Limits**
   - Production accounts have higher rate limits
   - Adjust CSC-Reach settings accordingly

## Important Information for CSC-Reach Users

### Required Credentials

You need these three pieces of information for CSC-Reach:

1. **Access Token**: Long string starting with "EAA..." (keep secure!)
2. **Phone Number ID**: Numeric ID for your WhatsApp business number
3. **Business Account ID**: (Optional) Your WhatsApp Business Account ID

### Security Best Practices

1. **Protect Your Access Token**
   - Never share your access token publicly
   - Store it securely in CSC-Reach's encrypted settings
   - Regenerate if compromised

2. **Use Test Environment First**
   - Always test with the test phone number first
   - Verify all functionality before using production numbers
   - Test with small batches initially

3. **Monitor Usage**
   - Keep track of your message quotas
   - Monitor delivery rates and failures
   - Set up appropriate rate limiting

### Rate Limits and Quotas

**Test Account Limits:**
- 5 recipient phone numbers maximum
- 250 messages per day
- Standard rate limits apply

**Production Account Limits:**
- Unlimited verified recipients
- Higher daily message quotas (varies by account)
- Enhanced rate limits based on account status

### Troubleshooting Common Issues

#### "Invalid Access Token" Error
- Verify the token is copied correctly (no extra spaces)
- Check if the token has expired
- Ensure you're using a valid user or system token

#### "Phone Number Not Valid" Error
- Ensure phone numbers include country code (e.g., +1234567890)
- Remove any formatting characters (spaces, dashes, parentheses)
- Verify the number is a valid WhatsApp number

#### "Rate Limit Exceeded" Error
- Reduce sending frequency in CSC-Reach settings
- Increase delay between messages
- Check your account's current quota limits

#### "Template Not Found" Error
- Ensure you're using approved templates only
- Check template name spelling and language code
- Wait for template approval if recently submitted

### Getting Help

If you encounter issues:

1. **Check CSC-Reach Logs**
   - Enable debug logging in CSC-Reach
   - Check the application logs for detailed error messages

2. **Meta Developer Support**
   - Visit [developers.facebook.com/support](https://developers.facebook.com/support)
   - Check the WhatsApp Business API documentation
   - Use the Meta Developer Community forums

3. **CSC-Reach Support**
   - Check the application's built-in help system
   - Review error messages in the WhatsApp settings dialog
   - Use the connection test feature to diagnose issues

## Next Steps

Once your WhatsApp Business API is set up:

1. **Create Message Templates**
   - Design templates for your business communications
   - Submit templates for approval through Meta Business Manager
   - Test templates with CSC-Reach's template system

2. **Import Customer Data**
   - Use CSC-Reach's CSV import feature
   - Ensure phone numbers are in international format
   - Verify customer consent for WhatsApp messaging

3. **Start Messaging**
   - Begin with small test batches
   - Monitor delivery rates and customer responses
   - Scale up gradually as you gain confidence

## Conclusion

Setting up WhatsApp Business API for CSC-Reach involves several steps, but following this tutorial ensures you have a properly configured, secure, and compliant setup. Remember to always test thoroughly before sending messages to customers, and keep your credentials secure.

For the most up-to-date information, always refer to the official Meta for Developers documentation at [developers.facebook.com/docs/whatsapp](https://developers.facebook.com/docs/whatsapp).