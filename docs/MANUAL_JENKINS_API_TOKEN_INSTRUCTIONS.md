# Manual Jenkins API Token Generation - Step-by-Step Instructions

## 🔧 **SITUATION STATUS**

The automated token generation failed due to authentication issues. Here's the **MANUAL APPROACH** to complete the Jenkins MCP integration:

## 📋 **STEP 1: Access Jenkins Web Interface**

1. **Open your web browser**
2. **Navigate to**: `http://192.168.1.119:8080`
3. **You should see the Jenkins login page**

## 📋 **STEP 2: Login to Jenkins**

1. **Enter credentials**:
   - **Username**: `feanor`
   - **Password**: `2113`
2. **Click "Sign in"**

### ⚠️ **If Login Fails**:
- **Check if user exists**: User may need to be created properly
- **Try different credentials**: Check if admin/admin or admin/password works
- **Security settings**: Jenkins might have different security configuration

## 📋 **STEP 3: Navigate to User Configuration**

**Once logged in successfully**:

### Method A: Through Username Menu
1. **Click on "feanor"** (your username) in the top-right corner
2. **Select "Configure"** from the dropdown menu

### Method B: Direct URL
1. **Navigate directly to**: `http://192.168.1.119:8080/user/feanor/configure`

### Method C: Through People Menu
1. **Click "People"** in the main Jenkins menu
2. **Click on "feanor"** user
3. **Click "Configure"** on the user page

## 📋 **STEP 4: Generate API Token**

**On the user configuration page**:

1. **Scroll down** to find the **"API Token"** section
2. **Click "Add new Token"** button
3. **Enter token name**: `LTMC-MCP-Integration`
4. **Click "Generate"** button
5. **⚠️ IMPORTANT**: **Copy the token immediately** - it won't be shown again!

### **Expected Token Format**:
- Length: ~40 characters
- Format: Mix of letters and numbers (e.g., `11a1b2c3d4e5f6789012345678901234567890ab`)

## 📋 **STEP 5: Update MCP Configuration**

**Once you have the API token**:

1. **Save the token securely**
2. **Update the MCP configuration** with these values:
   ```json
   {
     "mcpServers": {
       "jenkins": {
         "command": "mcp-jenkins",
         "args": [
           "--jenkins-url", "http://192.168.1.119:8080",
           "--jenkins-username", "feanor",
           "--jenkins-password", "YOUR_API_TOKEN_HERE"
         ]
       }
     }
   }
   ```

## 📋 **STEP 6: Test Jenkins MCP Integration**

**Run our existing test framework**:
```bash
cd /home/feanor/Projects/ltmc
python3 ltmc_jenkins_mcp_test.py --test-with-token YOUR_API_TOKEN_HERE
```

## 🔧 **TROUBLESHOOTING COMMON ISSUES**

### Issue 1: User Configuration Page Not Found
**Solution**: The user "feanor" might not exist or have proper permissions
- **Try creating the user through Jenkins admin interface**
- **Check user permissions for self-configuration**

### Issue 2: No "API Token" Section Visible
**Possible Causes**:
- **Jenkins version too old** (requires 2.129+)
- **API token feature disabled** by administrator
- **User lacks permissions** to generate tokens

**Solutions**:
- **Check Jenkins version**: We confirmed 2.504.3 (should work)
- **Contact admin** to enable API token feature
- **Check user permissions** in Jenkins security settings

### Issue 3: "Add new Token" Button Missing
**Known Issue**: In some Jenkins versions, the button doesn't appear until at least one token exists
**Solution**: 
- **Check if legacy token exists** and can be used
- **Ask admin to generate initial token**
- **Try through Jenkins script console** (admin access required)

## 🔒 **ALTERNATIVE APPROACHES**

### Option A: Use Jenkins Admin Account
If the "feanor" user doesn't work:
1. **Try admin credentials** (admin/admin, admin/password, admin/2113)
2. **Generate token for admin user**
3. **Use admin credentials in MCP configuration**

### Option B: Jenkins CLI Method
If web interface doesn't work:
```bash
# Download Jenkins CLI
wget http://192.168.1.119:8080/jnlpJars/jenkins-cli.jar

# Generate token via CLI (if credentials work)
java -jar jenkins-cli.jar -s http://192.168.1.119:8080 -auth feanor:2113 create-api-token LTMC-MCP-Integration
```

### Option C: Script Console (Admin Required)
**Navigate to**: `http://192.168.1.119:8080/script`
**Run Groovy script**:
```groovy
import jenkins.security.ApiTokenProperty
import hudson.model.User

def user = User.getById('feanor', false)
if (user != null) {
    def apiTokenProperty = user.getProperty(ApiTokenProperty.class)
    def tokenUuid = apiTokenProperty.generateNewToken('LTMC-MCP-Integration')
    def token = apiTokenProperty.getTokenStats().find { it.uuid == tokenUuid.uuid }
    println "Token: " + token.value
}
```

## ✅ **NEXT STEPS AFTER TOKEN GENERATION**

1. **✅ Token Generated**: Update MCP configuration 
2. **✅ Test Integration**: Run LTMC MCP test suite
3. **✅ Professional Migration**: Replace manual curl commands
4. **✅ Complete Setup**: Finalize Jenkins MCP integration

## 📞 **IF MANUAL APPROACH ALSO FAILS**

**Let me know**:
1. **What you see** when you access `http://192.168.1.119:8080`
2. **Login results** with feanor/2113 credentials
3. **Any error messages** you encounter
4. **Jenkins security configuration** if accessible

**We have backup solutions** including:
- Alternative MCP authentication approaches
- Direct Jenkins API usage with different auth methods
- Fallback to basic authentication for MCP integration

---
*Professional Jenkins MCP Integration Guide*  
*LTMC Project - Quality Over Speed Approach*