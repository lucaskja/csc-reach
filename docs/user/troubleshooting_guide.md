# Troubleshooting Guide

## Installation Issues

### Windows Security Warning
**Issue**: "Windows protected your PC" message  
**Cause**: Unsigned application  
**Solution**:
1. Click **More info**
2. Click **Run anyway**
3. This only appears on first run

### macOS Security Block
**Issue**: "Cannot be opened because it's from an unidentified developer"  
**Cause**: macOS Gatekeeper protection  
**Solution**:
1. Right-click CSC-Reach in Applications
2. Select **Open**
3. Click **Open** in dialog
4. Grant permissions when prompted

### Missing Outlook
**Issue**: "Microsoft Outlook is not installed"  
**Cause**: Outlook not found or not configured  
**Solution**:
1. Install Microsoft Outlook
2. Configure email account
3. Test sending email manually
4. Restart CSC-Reach

## Email Integration Issues

### Outlook Connection Failed
**Issue**: "Email: Not ready" status  
**Symptoms**: Cannot send emails, connection errors  
**Solutions**:
1. **Verify Outlook is running** and responsive
2. **Test manual email** from Outlook
3. **Check internet connection**
4. **Restart both applications**
5. **Update Outlook** to latest version

### macOS Automation Permissions
**Issue**: "Not authorized to send Apple events"  
**Cause**: Missing automation permissions  
**Solution**:
1. Open **System Preferences**
2. Go to **Security & Privacy** → **Privacy**
3. Select **Automation**
4. Find CSC-Reach
5. Check **Microsoft Outlook**
6. Restart CSC-Reach

### Email Sending Failures
**Issue**: Some emails fail to send  
**Causes**: Invalid addresses, rate limits, network issues  
**Solutions**:
1. **Validate email addresses** - remove invalid ones
2. **Reduce batch size** - send 10-20 at a time
3. **Check rate limits** - wait between batches
4. **Verify internet connection**
5. **Review Outlook sent items**

## Data Import Issues

### File Format Not Supported
**Issue**: "Cannot read file" error  
**Cause**: Unsupported format or corrupted file  
**Solution**:
1. **Verify file format**: CSV, Excel (.xlsx/.xls), JSON
2. **Check file integrity** - open in Excel/text editor
3. **Save as CSV** if using Excel
4. **Use UTF-8 encoding** for special characters

### Column Mapping Problems
**Issue**: Data not importing correctly  
**Cause**: Column headers don't match expected format  
**Solution**:
1. **Check required columns**: name, company, email, phone
2. **Use exact column names** (case-sensitive)
3. **Remove extra spaces** in headers
4. **Use column mapping dialog** to adjust

### Encoding Issues
**Issue**: Special characters appear as symbols  
**Cause**: File encoding mismatch  
**Solution**:
1. **Save file as UTF-8** in Excel or text editor
2. **Use "Save As" → "CSV UTF-8"** in Excel
3. **Check character encoding** in import dialog

## Template Issues

### Variables Not Working
**Issue**: `{name}` appears literally in messages  
**Cause**: Incorrect variable syntax or missing data  
**Solution**:
1. **Use exact syntax**: `{name}` not `{Name}` or `{NAME}`
2. **Verify data contains** required fields
3. **Check template preview** before sending
4. **Test with sample data**

### Template Not Saving
**Issue**: Changes lost when closing template editor  
**Cause**: Save operation failed  
**Solution**:
1. **Click Save button** explicitly
2. **Check disk space** availability
3. **Verify write permissions** to config directory
4. **Try different template name**

## WhatsApp Issues

### Cannot Connect to WhatsApp Web
**Issue**: Browser fails to load WhatsApp Web  
**Cause**: Network issues, browser problems  
**Solution**:
1. **Check internet connection**
2. **Update browser** to latest version
3. **Clear browser cache** and cookies
4. **Disable browser extensions**
5. **Try different browser**

### QR Code Login Problems
**Issue**: Cannot scan QR code or login fails  
**Cause**: Session expired, phone not connected  
**Solution**:
1. **Ensure phone has internet** connection
2. **Open WhatsApp on phone**
3. **Scan QR code quickly** before expiration
4. **Keep phone nearby** during session
5. **Refresh browser** if QR code expires

### Message Sending Failures
**Issue**: WhatsApp messages fail to send  
**Cause**: Rate limiting, connection issues, invalid numbers  
**Solution**:
1. **Verify phone numbers** are valid WhatsApp numbers
2. **Send slower** - reduce sending speed
3. **Check WhatsApp Web** is still logged in
4. **Restart browser session**

## Performance Issues

### Slow File Processing
**Issue**: Large files take too long to import  
**Cause**: File size, system resources  
**Solution**:
1. **Split large files** into smaller batches
2. **Close other applications** to free memory
3. **Use SSD storage** for better I/O performance
4. **Increase virtual memory** if needed

### Application Freezing
**Issue**: CSC-Reach becomes unresponsive  
**Cause**: Heavy processing, memory issues  
**Solution**:
1. **Wait for operation** to complete
2. **Check system resources** (Task Manager/Activity Monitor)
3. **Restart application** if necessary
4. **Process smaller batches**

## Configuration Issues

### Settings Not Saving
**Issue**: Preferences reset after restart  
**Cause**: Permission issues, corrupted config  
**Solution**:
1. **Run as administrator** (Windows)
2. **Check config directory** permissions
3. **Reset configuration** to defaults
4. **Reinstall application** if necessary

### Language Not Changing
**Issue**: Interface remains in wrong language  
**Cause**: Translation files missing, cache issues  
**Solution**:
1. **Restart application** after language change
2. **Clear application cache**
3. **Reinstall language pack**
4. **Check system locale** settings

## Getting Help

### Diagnostic Information
When reporting issues, include:
- **Application version**
- **Operating system** and version
- **Error messages** (exact text)
- **Steps to reproduce** the problem
- **Log files** (if requested)

### Log Files Location
- **Windows**: `%APPDATA%\CSC-Reach\logs\`
- **macOS**: `~/Library/Application Support/CSC-Reach/logs/`

### Debug Mode
Enable detailed logging:
```bash
# macOS/Linux
export CSC_REACH_DEBUG=1

# Windows
set CSC_REACH_DEBUG=1
```

### Support Channels
1. **Built-in Help** - Press F1 in application
2. **User Manual** - Complete documentation
3. **Community Forum** - User discussions
4. **Technical Support** - For complex issues

### Before Contacting Support
1. **Check this guide** for common solutions
2. **Try basic troubleshooting** steps
3. **Gather diagnostic information**
4. **Test with minimal data** to isolate issue
