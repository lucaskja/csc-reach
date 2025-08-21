# macOS Permissions Guide for CSC-Reach

CSC-Reach requires certain permissions on macOS to integrate with Microsoft Outlook and send emails. This guide will help you grant the necessary permissions.

## Required Permissions

### 1. Accessibility Permissions (Optional)
While CSC-Reach has been updated to work without System Events access, you may still want to grant accessibility permissions for the best experience.

**To grant accessibility permissions:**
1. Open **System Preferences** (or **System Settings** on macOS Ventura+)
2. Go to **Security & Privacy** → **Privacy** → **Accessibility**
3. Click the lock icon and enter your password
4. Click the **+** button and add CSC-Reach
5. Make sure CSC-Reach is checked in the list

### 2. Automation Permissions (Required)
CSC-Reach needs permission to control Microsoft Outlook via AppleScript.

**To grant automation permissions:**
1. Open **System Preferences** (or **System Settings** on macOS Ventura+)
2. Go to **Security & Privacy** → **Privacy** → **Automation**
3. Look for CSC-Reach in the list
4. Expand CSC-Reach and check **Microsoft Outlook**
5. If CSC-Reach doesn't appear, try running the app first - macOS will prompt you

### 3. Full Disk Access (Optional)
For enhanced logging and file operations, you may want to grant full disk access.

**To grant full disk access:**
1. Open **System Preferences** (or **System Settings** on macOS Ventura+)
2. Go to **Security & Privacy** → **Privacy** → **Full Disk Access**
3. Click the lock icon and enter your password
4. Click the **+** button and add CSC-Reach
5. Make sure CSC-Reach is checked in the list

## Troubleshooting Permission Issues

### Error: "Not authorized to send Apple events"
This error indicates that CSC-Reach doesn't have permission to control other applications.

**Solution:**
1. Follow the **Automation Permissions** steps above
2. Make sure Microsoft Outlook is checked under CSC-Reach
3. Restart CSC-Reach after granting permissions

### Error: "Cannot start Outlook"
This usually means Outlook isn't installed or CSC-Reach can't access it.

**Solutions:**
1. Make sure Microsoft Outlook is installed in `/Applications/Microsoft Outlook.app`
2. Try opening Outlook manually first
3. Grant automation permissions as described above
4. Restart both Outlook and CSC-Reach

### Permission Prompts Don't Appear
If macOS doesn't prompt you for permissions:

**Solutions:**
1. Reset permissions: `tccutil reset All com.yourcompany.csc-reach`
2. Manually add CSC-Reach to the privacy settings
3. Try running CSC-Reach from Terminal: `open /Applications/CSC-Reach.app`

## Verifying Permissions

After granting permissions, you can verify they're working:

1. Open CSC-Reach
2. Load a CSV file with test data
3. Create a draft email (don't send)
4. Check if the draft appears in Outlook

If the draft appears, permissions are working correctly!

## Security Notes

- CSC-Reach only accesses Outlook to create and send emails
- No personal data is transmitted outside your computer
- All email content is processed locally
- You can revoke permissions at any time through System Preferences

## Getting Help

If you continue to have permission issues:

1. Check the CSC-Reach logs in `~/Library/Logs/CSC-Reach/`
2. Try restarting your Mac
3. Ensure you're running the latest version of CSC-Reach
4. Contact support with your log files

## macOS Version Differences

### macOS Monterey and Earlier
- Use **System Preferences**
- Privacy settings are under **Security & Privacy**

### macOS Ventura and Later
- Use **System Settings**
- Privacy settings are under **Privacy & Security**
- Interface may look slightly different but steps are the same

---

*This guide was last updated for CSC-Reach v1.0.0*