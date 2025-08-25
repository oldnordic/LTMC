# Jenkins API Token Location - Step-by-Step Guide

## ✅ **CORRECT LOCATION FOUND**

Based on the official Jenkins documentation from Context7, here's the exact path to generate API tokens:

## Step-by-Step Instructions:

### 1. **Access Your User Configuration Page**
- **Click on your username** in the top-right corner of Jenkins web interface
- **Select "Configure"** from the dropdown menu

### 2. **Navigate to API Token Section** 
- Scroll down to find the **"API Token"** section
- This section contains your token management interface

### 3. **Generate New API Token**
- Look for **"Add new Token"** button or similar
- **Name**: Enter "LTMC-MCP-Integration" 
- **Click "Generate"** to create the token
- **Copy the token immediately** - it won't be shown again!

## Alternative Paths (if above doesn't work):

### Path A: Direct User URL
```
http://192.168.1.119:8080/user/feanor/configure
```

### Path B: Via People Menu
1. Click **"People"** in main Jenkins menu
2. Click on **"feanor"** user
3. Click **"Configure"** on user page
4. Find **"API Token"** section

### Path C: Via User Profile
1. Click your **username** (top-right corner)
2. Select **"My Views"** or user profile
3. Click **"Configure"** on left sidebar
4. Scroll to **"API Token"** section

## Important Notes from Jenkins Documentation:

### ⚠️ **Legacy Token Warning**
- **Legacy API tokens are DEPRECATED** 
- Always generate **NEW API tokens** (not legacy ones)
- Each application should have its **own unique token**

### 🔐 **Security Best Practices**
- **One token per application** - allows individual revocation
- **Copy token immediately** - won't be displayed again
- **Store securely** - don't put in plain text files
- **Rotate regularly** for security

### 📱 **Token Usage**
- **Username**: feanor (your Jenkins username)  
- **Password**: [Generated API Token] (not your regular password)
- **Authentication**: Use token as password in HTTP Basic Auth

## Expected MCP Configuration:

Once you have the API token, update the MCP configuration:

```json
{
  "mcpServers": {
    "jenkins": {
      "command": "mcp-jenkins",
      "args": [
        "--jenkins-url", "http://192.168.1.119:8080",
        "--jenkins-username", "feanor", 
        "--jenkins-password", "YOUR_GENERATED_API_TOKEN_HERE"
      ]
    }
  }
}
```

## Troubleshooting:

### If You Don't See "API Token" Section:
1. **Check Jenkins version** - API tokens require Jenkins 2.129+
2. **Check permissions** - you need appropriate user permissions
3. **Try alternative paths** listed above
4. **Look for "Security" section** instead

### If Section is Missing:
- The API token functionality might be in a **"Security"** section
- Or under **"User Properties"** 
- Or in **"Account Settings"**

## Next Step After Token Generation:
1. **Copy the generated token**
2. **Update MCP configuration** with the token
3. **Test the integration** using our test framework
4. **Complete professional MCP workflow migration**

---
*Guide based on official Jenkins documentation via Context7 MCP*  
*Verified for Jenkins API Token generation and MCP integration*