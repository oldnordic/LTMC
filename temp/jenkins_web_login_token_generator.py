#!/usr/bin/env python3
"""
Jenkins API Token Generation - Web Login Approach
=================================================

Professional solution that performs web-based login first, then generates API tokens.
Handles Jenkins security properly with session management.
"""

import sys
import requests
import json
import re
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup

@dataclass
class JenkinsTokenResult:
    """Professional Jenkins token generation result"""
    success: bool
    token: Optional[str]
    token_name: Optional[str]
    error_details: str
    next_steps: list

class JenkinsWebLoginTokenGenerator:
    """
    Professional Jenkins API token generator using web login approach.
    
    Handles full web authentication, CSRF protection, and session management.
    """
    
    def __init__(self, jenkins_url: str, username: str, password: str):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LTMC-Jenkins-MCP-Integration/1.0'
        })
        
    def generate_api_token(self, token_name: str = "LTMC-MCP-Integration") -> JenkinsTokenResult:
        """
        Generate Jenkins API token using complete web login approach.
        
        NON-NEGOTIABLE: Must handle complete authentication flow properly.
        """
        print(f"🔐 JENKINS API TOKEN - WEB LOGIN APPROACH")
        print(f"=========================================")
        print(f"Jenkins URL: {self.jenkins_url}")
        print(f"Username: {self.username}")
        print(f"Token Name: {token_name}")
        print()
        
        try:
            # Step 1: Perform web-based login
            print("📋 STEP 1: Web-based authentication")
            print("-----------------------------------")
            
            login_result = self._perform_web_login()
            if not login_result[0]:
                return JenkinsTokenResult(
                    success=False,
                    token=None,
                    token_name=token_name,
                    error_details=f"Web login failed: {login_result[1]}",
                    next_steps=[
                        "Verify Jenkins credentials are correct",
                        "Check if user 'feanor' exists and is enabled",
                        "Verify Jenkins allows form-based authentication",
                        "Check Jenkins security configuration"
                    ]
                )
            
            print(f"  ✅ Web login successful: {login_result[1]}")
            
            # Step 2: Navigate to user configuration
            print("\\n📋 STEP 2: Navigate to user configuration")
            print("-----------------------------------------")
            
            user_config_result = self._access_user_configuration()
            if not user_config_result[0]:
                return JenkinsTokenResult(
                    success=False,
                    token=None,
                    token_name=token_name,
                    error_details=f"User configuration access failed: {user_config_result[1]}",
                    next_steps=[
                        "Check if user has permission to configure profile",
                        "Verify Jenkins version supports API tokens (2.129+)",
                        "Check security settings for user self-configuration"
                    ]
                )
            
            print(f"  ✅ User configuration accessible")
            
            # Step 3: Generate API token
            print("\\n📋 STEP 3: Generate API token")
            print("------------------------------")
            
            token_result = self._generate_token_via_web_interface(token_name)
            if token_result[0]:
                token_value = token_result[1]
                print(f"  ✅ API token generated successfully!")
                print(f"  🔑 Token name: {token_name}")
                print(f"  🔑 Token value: {token_value[:10]}...{token_value[-10:]}")
                
                # Step 4: Verify token works
                print("\\n📋 STEP 4: Verify generated token works")
                print("---------------------------------------")
                
                verification = self._verify_token(token_value)
                if verification[0]:
                    print("  ✅ Token verification successful!")
                    print(f"  👤 Token authenticates as: {verification[1]}")
                    
                    return JenkinsTokenResult(
                        success=True,
                        token=token_value,
                        token_name=token_name,
                        error_details="",
                        next_steps=[
                            "Update MCP configuration with generated token",
                            "Test Jenkins MCP integration",
                            "Store token securely for future use"
                        ]
                    )
                else:
                    print(f"  ⚠️ Token verification failed: {verification[1]}")
                    # Return token anyway if generation succeeded
                    return JenkinsTokenResult(
                        success=True,
                        token=token_value,
                        token_name=token_name,
                        error_details=f"Token generated but verification unclear: {verification[1]}",
                        next_steps=[
                            "Update MCP configuration with generated token",
                            "Test Jenkins MCP integration manually"
                        ]
                    )
            else:
                return JenkinsTokenResult(
                    success=False,
                    token=None,
                    token_name=token_name,
                    error_details=f"Token generation failed: {token_result[1]}",
                    next_steps=[
                        "Check Jenkins version (requires 2.129+)",
                        "Verify API token feature is enabled",
                        "Check user permissions for token generation",
                        "Try manual token generation through Jenkins UI"
                    ]
                )
                
        except Exception as e:
            return JenkinsTokenResult(
                success=False,
                token=None,
                token_name=token_name,
                error_details=f"Unexpected error: {str(e)}",
                next_steps=[
                    "Check network connectivity to Jenkins",
                    "Verify Jenkins server is running properly",
                    "Check for any Jenkins plugin conflicts"
                ]
            )
    
    def _perform_web_login(self) -> Tuple[bool, str]:
        """Perform complete web-based login to Jenkins"""
        try:
            # Get login page
            login_response = self.session.get(f"{self.jenkins_url}/login", timeout=15)
            if login_response.status_code != 200:
                return False, f"Login page HTTP {login_response.status_code}"
            
            print("  🔍 Login page retrieved")
            
            # Parse login form
            soup = BeautifulSoup(login_response.text, 'html.parser')
            login_form = soup.find('form', {'name': 'login'})
            if not login_form:
                return False, "Login form not found on page"
            
            # Prepare login data
            login_data = {
                'j_username': self.username,
                'j_password': self.password,
                'Submit': 'Sign in'
            }
            
            # Add hidden fields
            for hidden_input in login_form.find_all('input', type='hidden'):
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    login_data[name] = value
            
            print(f"  🔍 Submitting login for user: {self.username}")
            
            # Submit login
            login_url = urljoin(self.jenkins_url, login_form.get('action', '/j_spring_security_check'))
            
            response = self.session.post(
                login_url,
                data=login_data,
                timeout=15,
                allow_redirects=True
            )
            
            # Check if login was successful
            if response.status_code == 200:
                # Check for successful login indicators
                if '/login' in response.url:
                    return False, "Login failed - redirected back to login page"
                
                # Verify authentication by checking who we are
                whoami_response = self.session.get(f"{self.jenkins_url}/whoAmI/api/json", timeout=10)
                if whoami_response.status_code == 200:
                    data = whoami_response.json()
                    if data.get('name') != 'anonymous':
                        return True, f"Authenticated as {data.get('name')}"
                
                return False, "Login appeared successful but still anonymous"
            else:
                return False, f"Login HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def _access_user_configuration(self) -> Tuple[bool, str]:
        """Access user configuration page"""
        try:
            # Try multiple possible paths for user configuration
            paths = [
                f"/user/{self.username}/configure",
                f"/user/{self.username}",
                "/me/configure",
                "/me"
            ]
            
            for path in paths:
                url = f"{self.jenkins_url}{path}"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200 and 'configure' in path.lower():
                    # Check if this looks like a configuration page
                    if 'api' in response.text.lower() and 'token' in response.text.lower():
                        return True, f"Configuration page accessible at {path}"
                elif response.status_code == 200:
                    # Check if there's a configure link
                    soup = BeautifulSoup(response.text, 'html.parser')
                    config_link = soup.find('a', href=re.compile(r'.*/configure$'))
                    if config_link:
                        return True, f"Configuration link found from {path}"
            
            return False, "User configuration page not accessible"
            
        except Exception as e:
            return False, f"Configuration access error: {str(e)}"
    
    def _generate_token_via_web_interface(self, token_name: str) -> Tuple[bool, str]:
        """Generate token via web interface"""
        try:
            # Navigate to user configuration page
            config_url = f"{self.jenkins_url}/user/{self.username}/configure"
            response = self.session.get(config_url, timeout=15)
            
            if response.status_code != 200:
                # Try alternative path
                config_url = f"{self.jenkins_url}/me/configure" 
                response = self.session.get(config_url, timeout=15)
            
            if response.status_code == 200:
                print("  🔍 Configuration page loaded")
                
                # Look for API token section and generation endpoint
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find token generation endpoint
                token_scripts = soup.find_all('script', string=re.compile(r'generateNewToken|ApiTokenProperty'))
                
                # Try the REST API approach with proper session
                endpoints_to_try = [
                    f"{self.jenkins_url}/user/{self.username}/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken",
                    f"{self.jenkins_url}/me/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken"
                ]
                
                # Get CSRF crumb if available
                crumb = self._get_csrf_crumb_from_session()
                
                for endpoint in endpoints_to_try:
                    print(f"  🔍 Trying endpoint: {endpoint.split('/')[-1]}...")
                    
                    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                    if crumb:
                        headers.update(crumb)
                    
                    data = {'newTokenName': token_name}
                    
                    token_response = self.session.post(endpoint, data=data, headers=headers, timeout=15)
                    
                    if token_response.status_code == 200:
                        # Try to extract token from response
                        token_value = self._extract_token_from_response(token_response.text)
                        if token_value:
                            return True, token_value
                
                return False, "Token generation endpoints not responsive"
            else:
                return False, f"Configuration page HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Web interface generation error: {str(e)}"
    
    def _get_csrf_crumb_from_session(self) -> Dict[str, str]:
        """Get CSRF crumb using authenticated session"""
        try:
            response = self.session.get(f"{self.jenkins_url}/crumbIssuer/api/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                field = data.get('crumbRequestField', 'Jenkins-Crumb')
                crumb = data.get('crumb')
                if crumb:
                    return {field: crumb}
            return {}
        except Exception:
            return {}
    
    def _extract_token_from_response(self, response_text: str) -> Optional[str]:
        """Extract token value from various response formats"""
        # Try JSON response
        try:
            data = json.loads(response_text)
            if 'tokenValue' in data:
                return data['tokenValue']
            if 'data' in data and 'tokenValue' in data['data']:
                return data['data']['tokenValue']
        except json.JSONDecodeError:
            pass
        
        # Try HTML data attribute
        token_match = re.search(r'data-new-token-value="([^"]+)"', response_text)
        if token_match:
            return token_match.group(1)
        
        # Try various token patterns
        patterns = [
            r'"tokenValue"\s*:\s*"([^"]+)"',
            r'token["\s]*:["\s]*"([a-f0-9]{32,})"',
            r'value="([a-f0-9]{32,})"[^>]*name="tokenValue"',
            r'<code[^>]*>([a-f0-9]{32,})</code>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _verify_token(self, token: str) -> Tuple[bool, str]:
        """Verify the generated token works"""
        try:
            # Test token with basic auth
            verify_session = requests.Session()
            verify_session.auth = (self.username, token)
            
            response = verify_session.get(f"{self.jenkins_url}/whoAmI/api/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                username = data.get('name', 'unknown')
                if username != 'anonymous':
                    return True, username
            
            return False, f"Token verification returned HTTP {response.status_code}"
        except Exception as e:
            return False, f"Token verification error: {str(e)}"


def main():
    """Professional Jenkins web login token generation execution"""
    print("🚀 JENKINS WEB LOGIN TOKEN GENERATION")
    print("=====================================")
    print()
    
    # Configuration 
    jenkins_url = "http://192.168.1.119:8080"
    username = "feanor"
    password = "2113"
    token_name = "LTMC-MCP-Integration"
    
    print(f"Target Jenkins: {jenkins_url}")
    print(f"Username: {username}")
    print(f"Token name: {token_name}")
    print()
    
    generator = JenkinsWebLoginTokenGenerator(jenkins_url, username, password)
    result = generator.generate_api_token(token_name)
    
    print(f"\\n🎯 TOKEN GENERATION RESULTS")
    print(f"============================")
    print(f"Success: {'✅ YES' if result.success else '❌ NO'}")
    print(f"Token Name: {result.token_name}")
    
    if result.success and result.token:
        print(f"Token Generated: ✅ YES")
        print(f"Token Value: {result.token}")
        print()
        print("🔧 MCP CONFIGURATION UPDATE")
        print("===========================")
        print("Use these credentials for Jenkins MCP:")
        print(f"Username: {username}")
        print(f"API Token: {result.token}")
        print()
        print("Complete MCP Configuration:")
        print(json.dumps({
            "mcpServers": {
                "jenkins": {
                    "command": "mcp-jenkins",
                    "args": [
                        "--jenkins-url", jenkins_url,
                        "--jenkins-username", username,
                        "--jenkins-password", result.token
                    ]
                }
            }
        }, indent=2))
    else:
        print(f"Token Generated: ❌ NO")
        print(f"Error: {result.error_details}")
        print()
        print("🔧 TROUBLESHOOTING STEPS")
        print("========================")
        for i, step in enumerate(result.next_steps, 1):
            print(f"{i}. {step}")
    
    print(f"\\n📋 Process completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\n⚠️ Process interrupted by user")
        sys.exit(1)