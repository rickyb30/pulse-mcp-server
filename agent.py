#!/usr/bin/env python3
"""
Intelligent MCP Agent - AI Assistant with Tool Access

This agent connects to your MCP server and acts as an intelligent assistant
that can leverage various tools (AWS, Snowflake, Stock Market, etc.) to answer
your questions and perform tasks.
"""

import asyncio
import json
import sys
import re
from typing import Dict, List, Any, Optional
from fastmcp import Client
from datetime import datetime
import argparse

class MCPAgent:
    def __init__(self):
        self.client = None
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self.conversation_history = []
        self.snowflake_session = None
        self.aws_session = None
        self.session_expiry = None
        
    async def connect(self):
        """Connect to the MCP server"""
        try:
            # Import the server from your advanced_mcp_server.py
            from advanced_mcp_server import mcp
            self.client = Client(mcp)
            await self.client.__aenter__()
            
            # Discover available tools, resources, and prompts
            await self.discover_capabilities()
            
            print("🤖 AI Agent connected to MCP server successfully!")
            print(f"📊 Discovered {len(self.tools)} tools, {len(self.resources)} resources, {len(self.prompts)} prompts")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False
    
    async def discover_capabilities(self):
        """Discover all available tools, resources, and prompts"""
        try:
            # Get tools from the client
            if hasattr(self.client, 'list_tools'):
                tools_response = await self.client.list_tools()
                if hasattr(tools_response, 'tools'):
                    for tool in tools_response.tools:
                        self.tools[tool.name] = {
                            'description': tool.description,
                            'schema': tool.inputSchema if hasattr(tool, 'inputSchema') else None
                        }
            
            # Try to get available tools by inspecting the server
            # This is a fallback method to discover tools
            if not self.tools:
                self.tools = {
                    'calculate': {'description': 'Perform mathematical calculations', 'category': 'utility'},
                    'get_weather': {'description': 'Get weather information for a city', 'category': 'info'},
                    'web_search': {'description': 'Search the web for information', 'category': 'search'},
                    'discover_aws_profiles': {'description': 'Discover available AWS profiles', 'category': 'aws'},
                    'analyze_aws_costs': {'description': 'Analyze AWS costs for a given period', 'category': 'aws'},
                    'get_aws_cost_report': {'description': 'Generate AWS cost report', 'category': 'aws'},
                    'get_stock_info': {'description': 'Get stock information for a symbol', 'category': 'finance'},
                    'get_historical_stock_data': {'description': 'Get historical stock data', 'category': 'finance'},
                    'get_technical_indicators': {'description': 'Get technical indicators for a stock', 'category': 'finance'},
                    'screen_stocks': {'description': 'Screen stocks based on criteria', 'category': 'finance'},
                    'get_market_indices': {'description': 'Get major market indices', 'category': 'finance'},
                    'analyze_portfolio': {'description': 'Analyze a portfolio of holdings', 'category': 'finance'},
                    'get_crypto_data': {'description': 'Get cryptocurrency data', 'category': 'finance'},
                    'get_stock_report': {'description': 'Generate comprehensive stock report', 'category': 'finance'},
                    'connect_snowflake_sso': {'description': 'Connect to Snowflake using SSO', 'category': 'snowflake'},
                    'connect_snowflake_credentials': {'description': 'Connect to Snowflake using credentials', 'category': 'snowflake'},
                    'get_snowflake_overall_costs': {'description': 'Get overall Snowflake costs', 'category': 'snowflake'},
                    'get_snowflake_top_warehouses': {'description': 'Get top Snowflake warehouses by cost', 'category': 'snowflake'},
                    'get_snowflake_cost_summary': {'description': 'Get Snowflake cost summary', 'category': 'snowflake'},
                    'get_snowflake_cost_report': {'description': 'Generate Snowflake cost report', 'category': 'snowflake'},
                    'connect_snowflake_auto': {'description': 'Auto-connect to Snowflake', 'category': 'snowflake'},
                    'connect_databricks_sso': {'description': 'Connect to Databricks using SSO', 'category': 'databricks'},
                    'get_databricks_overall_costs': {'description': 'Get overall Databricks costs', 'category': 'databricks'},
                    'get_databricks_top_clusters': {'description': 'Get top Databricks clusters by cost', 'category': 'databricks'},
                    'get_databricks_workspace_summary': {'description': 'Get Databricks workspace summary', 'category': 'databricks'},
                    'get_databricks_cost_report': {'description': 'Generate Databricks cost report', 'category': 'databricks'}
                }
                
        except Exception as e:
            print(f"⚠️  Could not fully discover capabilities: {e}")
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze user question to determine intent and required tools"""
        question_lower = question.lower()
        
        # Define keywords for different categories
        keywords = {
            'snowflake': ['snowflake', 'warehouse', 'credits', 'compute', 'sf cost'],
            'databricks': ['databricks', 'cluster', 'workspace', 'spark', 'dbx', 'db cost'],
            'aws': ['aws', 'amazon', 'ec2', 'rds', 's3', 'lambda', 'cloud cost'],
            'stock': ['stock', 'ticker', 'share', 'equity', 'portfolio', 'nasdaq', 'dow', 'sp500'],
            'crypto': ['crypto', 'bitcoin', 'ethereum', 'cryptocurrency', 'btc', 'eth'],
            'weather': ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy'],
            'math': ['calculate', 'compute', 'sum', 'average', 'math', 'multiply', 'divide'],
            'search': ['search', 'find', 'look up', 'information about', 'tell me about']
        }
        
        # Analyze intent
        intents = []
        for category, words in keywords.items():
            if any(word in question_lower for word in words):
                intents.append(category)
        
        # Determine specific actions
        actions = []
        if 'cost' in question_lower or 'expense' in question_lower or 'spending' in question_lower:
            actions.append('cost_analysis')
        if 'report' in question_lower or 'summary' in question_lower:
            actions.append('generate_report')
        if 'connect' in question_lower or 'login' in question_lower:
            actions.append('connect')
        if 'list' in question_lower or 'show' in question_lower:
            actions.append('list')
        
        return {
            'intents': intents,
            'actions': actions,
            'question': question
        }
    
    def suggest_tools(self, analysis: Dict[str, Any]) -> List[str]:
        """Suggest appropriate tools based on question analysis"""
        intents = analysis['intents']
        actions = analysis['actions']
        suggested_tools = []
        
        # Snowflake-related tools
        if 'snowflake' in intents:
            if 'connect' in actions:
                suggested_tools.extend(['connect_snowflake_auto', 'connect_snowflake_sso'])
            elif 'cost_analysis' in actions:
                suggested_tools.extend(['get_snowflake_overall_costs', 'get_snowflake_cost_summary'])
            elif 'generate_report' in actions:
                suggested_tools.append('get_snowflake_cost_report')
            elif 'list' in actions:
                suggested_tools.append('get_snowflake_top_warehouses')
            else:
                suggested_tools.extend(['get_snowflake_overall_costs', 'get_snowflake_cost_summary'])
        
        # Databricks-related tools
        if 'databricks' in intents:
            if 'connect' in actions:
                suggested_tools.append('connect_databricks_sso')
            elif 'cost_analysis' in actions:
                suggested_tools.extend(['get_databricks_overall_costs', 'get_databricks_workspace_summary'])
            elif 'generate_report' in actions:
                suggested_tools.append('get_databricks_cost_report')
            elif 'list' in actions:
                suggested_tools.append('get_databricks_top_clusters')
            else:
                suggested_tools.extend(['get_databricks_overall_costs', 'get_databricks_workspace_summary'])
        
        # AWS-related tools
        if 'aws' in intents:
            if 'connect' in actions or 'list' in actions:
                suggested_tools.append('discover_aws_profiles')
            elif 'cost_analysis' in actions:
                suggested_tools.append('analyze_aws_costs')
            elif 'generate_report' in actions:
                suggested_tools.append('get_aws_cost_report')
            else:
                suggested_tools.extend(['discover_aws_profiles', 'analyze_aws_costs'])
        
        # Stock/Finance-related tools
        if 'stock' in intents:
            if 'list' in actions:
                suggested_tools.append('get_market_indices')
            else:
                suggested_tools.extend(['get_stock_info', 'get_market_indices'])
        
        # Crypto-related tools
        if 'crypto' in intents:
            suggested_tools.append('get_crypto_data')
        
        # Weather-related tools
        if 'weather' in intents:
            suggested_tools.append('get_weather')
        
        # Math-related tools
        if 'math' in intents:
            suggested_tools.append('calculate')
        
        # Search-related tools
        if 'search' in intents:
            suggested_tools.append('web_search')
        
        return suggested_tools
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Any:
        """Execute a specific tool with parameters"""
        try:
            if params is None:
                params = {}
                
            print(f"🔧 Executing tool: {tool_name} with params: {params}")
            result = await self.client.call_tool(tool_name, params)
            
            # Handle TextContent wrapped results from MCP server
            if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                # If result is a list/iterable of TextContent objects
                for item in result:
                    if hasattr(item, 'text'):
                        try:
                            # Try to parse the text as JSON
                            parsed = json.loads(item.text)
                            return parsed
                        except json.JSONDecodeError:
                            # If not JSON, return the text directly
                            return item.text
            
            return result
            
        except Exception as e:
            return f"❌ Error executing {tool_name}: {e}"
    
    def extract_parameters(self, question: str, tool_name: str) -> Dict[str, Any]:
        """Extract parameters for tools from the user question"""
        params = {}
        question_lower = question.lower()
        
        # Extract common parameters
        if tool_name in ['get_weather']:
            # Try to extract city name
            city_patterns = [
                r'weather in ([\w\s]+?)(?:\s|$|[.,?!])',
                r'weather for ([\w\s]+?)(?:\s|$|[.,?!])',
                r'temperature in ([\w\s]+?)(?:\s|$|[.,?!])'
            ]
            for pattern in city_patterns:
                match = re.search(pattern, question_lower)
                if match:
                    params['city'] = match.group(1).strip()
                    break
        
        elif tool_name in ['get_stock_info', 'get_historical_stock_data', 'get_technical_indicators']:
            # Extract stock symbol
            symbol_patterns = [
                r'\b([A-Z]{1,5})\b',  # Stock symbols are usually 1-5 uppercase letters
                r'stock\s+(\w+)',
                r'ticker\s+(\w+)'
            ]
            for pattern in symbol_patterns:
                match = re.search(pattern, question.upper())
                if match:
                    params['symbol'] = match.group(1)
                    break
        
        elif tool_name.startswith('snowflake') or tool_name.startswith('aws') or tool_name.startswith('databricks'):
            # Extract days for cost analysis
            days_patterns = [
                r'(\d+)\s*days?',
                r'last\s*(\d+)\s*days?',
                r'past\s*(\d+)\s*days?'
            ]
            for pattern in days_patterns:
                match = re.search(pattern, question_lower)
                if match:
                    params['days'] = int(match.group(1))
                    break
            
            if 'days' not in params:
                params['days'] = 30  # Default to 30 days
        
        elif tool_name == 'web_search':
            # For web search, use the entire question as query
            params['query'] = question
            params['limit'] = 5
        
        elif tool_name == 'calculate':
            # Extract numbers for calculation
            numbers = re.findall(r'\d+(?:\.\d+)?', question)
            if numbers:
                params['numbers'] = [float(n) for n in numbers]
                
                # Determine operation
                if any(word in question_lower for word in ['sum', 'add', 'total', '+']):
                    params['operation'] = 'sum'
                elif any(word in question_lower for word in ['average', 'mean', 'avg']):
                    params['operation'] = 'avg'
                elif any(word in question_lower for word in ['max', 'maximum', 'highest']):
                    params['operation'] = 'max'
                elif any(word in question_lower for word in ['min', 'minimum', 'lowest']):
                    params['operation'] = 'min'
                else:
                    params['operation'] = 'sum'  # Default
        
        return params
    
    def detect_connection_preference(self, question: str) -> Optional[str]:
        """Detect user's preferred connection method from their question"""
        question_lower = question.lower()
        
        # SSO keywords
        sso_keywords = ['sso', 'single sign-on', 'single sign on', 'saml', 'oauth', 'browser auth']
        if any(keyword in question_lower for keyword in sso_keywords):
            return 'sso'
        
        # Credential keywords
        credential_keywords = ['password', 'username', 'credentials', 'login', 'user pass']
        if any(keyword in question_lower for keyword in credential_keywords):
            return 'credentials'
        
        # Connect keywords with method specification
        if 'connect with sso' in question_lower or 'use sso' in question_lower:
            return 'sso'
        if 'connect with password' in question_lower or 'use password' in question_lower:
            return 'credentials'
        
        return None
    
    def is_session_valid(self) -> bool:
        """Check if current Snowflake session is still valid"""
        if not self.snowflake_session:
            return False
        
        # Check if session has expiry information
        if self.session_expiry:
            from datetime import datetime
            try:
                expiry_time = datetime.fromisoformat(self.session_expiry)
                if datetime.now() > expiry_time:
                    print("⏰ Session expired, need to re-authenticate")
                    return False
            except:
                pass
        
        return True
    
    async def ensure_snowflake_connection(self, original_question: str) -> Dict[str, Any]:
        """Ensure Snowflake is connected, ask for details if needed"""
        try:
            # Check if we have a valid existing session
            if self.is_session_valid():
                print("✅ Using existing Snowflake session")
                return self.snowflake_session
            
            # First try auto-connect
            print("🔍 Checking Snowflake connection...")
            auto_result = await self.execute_tool('connect_snowflake_auto', {})
            
            if isinstance(auto_result, dict) and auto_result.get('success'):
                print("✅ Auto-connected to Snowflake successfully!")
                self.store_snowflake_session(auto_result)
                return auto_result
            
            # Detect user's preferred connection method from their question
            preferred_method = self.detect_connection_preference(original_question)
            
            if preferred_method == 'sso':
                print("🔐 Detected SSO preference in your question. Setting up SSO connection...")
                result = await self.setup_snowflake_sso()
                if result.get('success'):
                    self.store_snowflake_session(result)
                return result
            elif preferred_method == 'credentials':
                print("🔑 Detected credential preference in your question. Setting up credential connection...")
                result = await self.setup_snowflake_credentials()
                if result.get('success'):
                    self.store_snowflake_session(result)
                return result
            else:
                # If no preference detected, ask user for connection details
                print("\n❗ Snowflake connection required.")
                print("🔗 Available connection methods:")
                print("  1. SSO (Single Sign-On)")
                print("  2. Username/Password")
                print("  3. Skip (will use mock data)")
                
                while True:
                    choice = input("\n🤔 Choose connection method (1/2/3): ").strip()
                    
                    if choice == '1':
                        result = await self.setup_snowflake_sso()
                        if result.get('success'):
                            self.store_snowflake_session(result)
                        return result
                    elif choice == '2':
                        result = await self.setup_snowflake_credentials()
                        if result.get('success'):
                            self.store_snowflake_session(result)
                        return result
                    elif choice == '3':
                        print("⚠️  Skipping Snowflake connection. Results may be limited.")
                        return {'success': True, 'method': 'skipped'}
                    else:
                        print("❌ Please choose 1, 2, or 3")
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def parse_snowflake_account(self, account_input: str) -> str:
        """Parse account identifier from various input formats including full URLs"""
        account_input = account_input.strip()
        
        # If it's a full URL, parse it
        if account_input.startswith('https://') or account_input.startswith('http://'):
            # Extract hostname from URL
            # Examples:
            # https://abc123.us-east-1.privatelink.snowflakecomputing.com/
            # https://abc123.snowflakecomputing.com/
            # https://myorg-myaccount.snowflakecomputing.com/
            import re
            url_pattern = r'https?://([^/]+)'
            match = re.match(url_pattern, account_input)
            if match:
                hostname = match.group(1)
                # Remove .snowflakecomputing.com suffix if present
                if hostname.endswith('.snowflakecomputing.com'):
                    account = hostname.replace('.snowflakecomputing.com', '')
                else:
                    account = hostname
                print(f"🔗 Parsed account from URL: {account}")
                return account
        
        # If it's already an account identifier, return as-is
        # Handle cases like:
        # abc123.us-east-1
        # abc123.us-east-1.privatelink
        # myorg-myaccount
        return account_input
    
    def store_snowflake_session(self, connection_result: Dict[str, Any]):
        """Store Snowflake session information for reuse"""
        if connection_result.get('success'):
            self.snowflake_session = connection_result
            
            # Set session expiry (default to 4 hours if not provided)
            if 'expires_at' in connection_result:
                self.session_expiry = connection_result['expires_at']
            else:
                from datetime import datetime, timedelta
                # Default session expiry of 4 hours
                expiry = datetime.now() + timedelta(hours=4)
                self.session_expiry = expiry.isoformat()
            
            print(f"💾 Session stored and will expire at {self.session_expiry[:19]}")
    
    def clear_snowflake_session(self):
        """Clear stored Snowflake session"""
        self.snowflake_session = None
        self.session_expiry = None
        print("🧹 Snowflake session cleared")
    
    async def setup_snowflake_sso(self) -> Dict[str, Any]:
        """Setup Snowflake SSO connection"""
        try:
            print("\n🔐 Setting up Snowflake SSO connection...")
            
            # Get account details - accept full URL or account identifier
            print("💡 You can provide either:")
            print("   • Full Snowflake URL (e.g., https://abc123.us-east-1.privatelink.snowflakecomputing.com/)")
            print("   • Account identifier (e.g., abc123.us-east-1 or myorg-myaccount)")
            
            account_input = input("\n🏢 Snowflake URL or Account: ").strip()
            if not account_input:
                return {'success': False, 'error': 'Account/URL is required'}
            
            # Parse the account identifier
            account = self.parse_snowflake_account(account_input)
            
            user = input("👤 Snowflake Username: ").strip()
            if not user:
                return {'success': False, 'error': 'Username is required'}
            
            print(f"\n🚀 Launching SSO session for {user}@{account}...")
            print("🌐 Your browser will open for authentication...")
            
            # Execute SSO connection
            result = await self.execute_tool('connect_snowflake_sso', {
                'account': account,
                'user': user
            })
            
            if isinstance(result, dict):
                if result.get('success'):
                    print("✅ SSO connection successful!")
                    if result.get('message'):
                        print(f"📝 {result['message']}")
                    return result
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ SSO connection failed: {error_msg}")
                    return result
            elif isinstance(result, str):
                # Try to parse string results as JSON
                try:
                    parsed_result = json.loads(result)
                    if isinstance(parsed_result, dict) and parsed_result.get('success'):
                        print("✅ SSO connection successful!")
                        if parsed_result.get('message'):
                            print(f"📝 {parsed_result['message']}")
                        return parsed_result
                    else:
                        print(f"❌ Connection result: {result}")
                        return {'success': False, 'error': result}
                except json.JSONDecodeError:
                    print(f"❌ Unexpected result: {result}")
                    return {'success': False, 'error': str(result)}
            else:
                print(f"❌ Unexpected result type: {type(result)} - {result}")
                return {'success': False, 'error': str(result)}
                
        except Exception as e:
            return {'success': False, 'error': f'SSO setup failed: {str(e)}'}
    
    async def setup_snowflake_credentials(self) -> Dict[str, Any]:
        """Setup Snowflake credential-based connection"""
        try:
            print("\n🔑 Setting up Snowflake credential connection...")
            
            # Get account details - accept full URL or account identifier
            print("💡 You can provide either:")
            print("   • Full Snowflake URL (e.g., https://abc123.us-east-1.privatelink.snowflakecomputing.com/)")
            print("   • Account identifier (e.g., abc123.us-east-1 or myorg-myaccount)")
            
            account_input = input("\n🏢 Snowflake URL or Account: ").strip()
            if not account_input:
                return {'success': False, 'error': 'Account/URL is required'}
            
            # Parse the account identifier
            account = self.parse_snowflake_account(account_input)
            
            user = input("👤 Snowflake Username: ").strip()
            if not user:
                return {'success': False, 'error': 'Username is required'}
            
            import getpass
            password = getpass.getpass("🔒 Snowflake Password: ")
            if not password:
                return {'success': False, 'error': 'Password is required'}
            
            role = input("🎭 Role (optional, press Enter to skip): ").strip()
            warehouse = input("🏭 Warehouse (optional, press Enter to skip): ").strip()
            
            print(f"\n🔗 Connecting to Snowflake as {user}@{account}...")
            
            # Execute credential connection
            params = {
                'account': account,
                'user': user,
                'password': password
            }
            
            if role:
                params['role'] = role
            if warehouse:
                params['warehouse'] = warehouse
            
            result = await self.execute_tool('connect_snowflake_credentials', params)
            
            if isinstance(result, dict):
                if result.get('success'):
                    print("✅ Credential connection successful!")
                    if result.get('message'):
                        print(f"📝 {result['message']}")
                    return result
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ Credential connection failed: {error_msg}")
                    return result
            elif isinstance(result, str):
                # Try to parse string results as JSON
                try:
                    parsed_result = json.loads(result)
                    if isinstance(parsed_result, dict) and parsed_result.get('success'):
                        print("✅ Credential connection successful!")
                        if parsed_result.get('message'):
                            print(f"📝 {parsed_result['message']}")
                        return parsed_result
                    else:
                        print(f"❌ Connection result: {result}")
                        return {'success': False, 'error': result}
                except json.JSONDecodeError:
                    print(f"❌ Unexpected result: {result}")
                    return {'success': False, 'error': str(result)}
            else:
                print(f"❌ Unexpected result type: {type(result)} - {result}")
                return {'success': False, 'error': str(result)}
                
        except Exception as e:
            return {'success': False, 'error': f'Credential setup failed: {str(e)}'}
    
    async def ensure_databricks_connection(self, original_question: str) -> Dict[str, Any]:
        """Ensure Databricks is connected, ask for details if needed"""
        try:
            # Detect user's preferred connection method from their question
            preferred_method = self.detect_connection_preference(original_question)
            
            if preferred_method == 'sso':
                print("🔐 Detected SSO preference in your question. Setting up Databricks SSO connection...")
                result = await self.setup_databricks_sso()
                return result
            else:
                # Default to SSO setup for Databricks
                print("🧱 Databricks connection required.")
                print("🔗 Databricks uses SSO authentication with Personal Access Tokens")
                result = await self.setup_databricks_sso()
                return result
                
        except Exception as e:
            return {'success': False, 'error': f'Databricks connection failed: {str(e)}'}
    
    def extract_workspace_url(self, url_input: str) -> str:
        """Extract and normalize Databricks workspace URL"""
        # Remove any extra whitespace
        url_input = url_input.strip()
        
        # If it doesn't start with https://, add it
        if not url_input.startswith('https://'):
            url_input = f'https://{url_input}'
        
        # Common Databricks URL patterns
        if 'databricks.com' in url_input:
            return url_input
        elif 'cloud.databricks.com' in url_input:
            return url_input
        elif 'azuredatabricks.net' in url_input:
            return url_input
        else:
            # Assume it's a custom domain or partial URL
            return url_input
    
    async def setup_databricks_sso(self) -> Dict[str, Any]:
        """Setup Databricks SSO connection"""
        try:
            print("\n🧱 Setting up Databricks SSO connection...")
            print("💡 You'll need:")
            print("   • Your Databricks workspace URL")
            print("   • A Personal Access Token")
            print()
            
            # Get workspace URL
            workspace_url = input("🔗 Enter your Databricks workspace URL: ").strip()
            if not workspace_url:
                return {'success': False, 'error': 'Workspace URL is required'}
            
            # Normalize the URL
            workspace_url = self.extract_workspace_url(workspace_url)
            print(f"📝 Using workspace URL: {workspace_url}")
            
            # Get Personal Access Token
            print("\n🔑 Personal Access Token Setup:")
            print("   1. Go to your Databricks workspace")
            print("   2. Click on your user icon → User Settings")
            print("   3. Go to 'Access tokens' tab")
            print("   4. Click 'Generate new token'")
            print("   5. Copy the generated token")
            print()
            
            token = input("🔐 Enter your Personal Access Token (or press Enter to continue without it): ").strip()
            
            # Try to connect
            print("\n🔌 Attempting to connect to Databricks...")
            
            # Call the connection tool
            if token:
                result = await self.execute_tool('connect_databricks_sso', {
                    'workspace_url': workspace_url,
                    'personal_access_token': token
                })
            else:
                result = await self.execute_tool('connect_databricks_sso', {
                    'workspace_url': workspace_url
                })
            
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                    if isinstance(parsed_result, dict):
                        if parsed_result.get('success'):
                            print("✅ SSO connection successful!")
                            if parsed_result.get('message'):
                                print(f"📝 {parsed_result['message']}")
                        elif parsed_result.get('requires_token'):
                            print("⚠️  Personal Access Token required for API access")
                            if parsed_result.get('instructions'):
                                print("\n📋 Instructions:")
                                for instruction in parsed_result['instructions']:
                                    print(f"   {instruction}")
                        return parsed_result
                    else:
                        print(f"❌ Connection result: {result}")
                        return {'success': False, 'error': result}
                except json.JSONDecodeError:
                    print(f"❌ Unexpected result: {result}")
                    return {'success': False, 'error': str(result)}
            elif isinstance(result, dict):
                if result.get('success'):
                    print("✅ SSO connection successful!")
                    if result.get('message'):
                        print(f"📝 {result['message']}")
                elif result.get('requires_token'):
                    print("⚠️  Personal Access Token required for API access")
                    if result.get('instructions'):
                        print("\n📋 Instructions:")
                        for instruction in result['instructions']:
                            print(f"   {instruction}")
                return result
            else:
                print(f"❌ Unexpected result type: {type(result)} - {result}")
                return {'success': False, 'error': str(result)}
                
        except Exception as e:
            return {'success': False, 'error': f'SSO setup failed: {str(e)}'}
    
    async def handle_question(self, question: str) -> str:
        """Handle a user question by analyzing it and executing appropriate tools"""
        print(f"\n🤔 Analyzing question: {question}")
        
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'question',
            'content': question
        })
        
        # Analyze the question
        analysis = self.analyze_question(question)
        print(f"📝 Intent analysis: {analysis['intents']}, Actions: {analysis['actions']}")
        
        # Check if Snowflake connection is needed
        if 'snowflake' in analysis['intents']:
            connection_result = await self.ensure_snowflake_connection(question)
            if connection_result and 'error' in connection_result:
                return f"❌ Snowflake connection failed: {connection_result['error']}"
            
            # If connection was successful, show connection status
            if connection_result and connection_result.get('success'):
                if connection_result.get('method') != 'skipped':
                    print("🎯 Connection established! Proceeding with your request...")
        
        # Check if Databricks connection is needed
        if 'databricks' in analysis['intents']:
            connection_result = await self.ensure_databricks_connection(question)
            if connection_result and 'error' in connection_result:
                return f"❌ Databricks connection failed: {connection_result['error']}"
            
            # If connection was successful, show connection status
            if connection_result and connection_result.get('success'):
                print("🎯 Databricks connection established! Proceeding with your request...")
        
        # Suggest and execute tools
        suggested_tools = self.suggest_tools(analysis)
        
        if not suggested_tools:
            return "🤷 I'm not sure which tools to use for this question. Could you be more specific? Available categories: AWS, Snowflake, Databricks, Stocks, Weather, Math, Search"
        
        print(f"🛠️  Suggested tools: {suggested_tools}")
        
        results = []
        for tool_name in suggested_tools[:3]:  # Limit to 3 tools to avoid overwhelming
            if tool_name in self.tools:
                # Extract parameters for this tool
                params = self.extract_parameters(question, tool_name)
                
                # Execute the tool
                result = await self.execute_tool(tool_name, params)
                results.append({
                    'tool': tool_name,
                    'params': params,
                    'result': result
                })
        
        # Format response
        response = self.format_response(question, results)
        
        # Add response to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'response',
            'content': response,
            'tools_used': [r['tool'] for r in results]
        })
        
        return response
    
    def format_response(self, question: str, results: List[Dict[str, Any]]) -> str:
        """Format the response based on tool results"""
        if not results:
            return "❌ No results were obtained from the tools."
        
        response_parts = []
        
        for result in results:
            tool_name = result['tool']
            tool_result = result['result']
            
            response_parts.append(f"\n🔧 **{tool_name}**:")
            
            if isinstance(tool_result, dict):
                if 'error' in tool_result:
                    response_parts.append(f"   ❌ Error: {tool_result['error']}")
                else:
                    # Format based on tool type
                    if 'snowflake' in tool_name.lower():
                        response_parts.append(self.format_snowflake_result(tool_result))
                    elif 'databricks' in tool_name.lower():
                        response_parts.append(self.format_databricks_result(tool_result))
                    elif 'aws' in tool_name.lower():
                        response_parts.append(self.format_aws_result(tool_result))
                    elif 'stock' in tool_name.lower() or 'market' in tool_name.lower():
                        response_parts.append(self.format_stock_result(tool_result))
                    else:
                        response_parts.append(f"   📊 {json.dumps(tool_result, indent=2)}")
            else:
                response_parts.append(f"   📊 {tool_result}")
        
        return "\n".join(response_parts)
    
    def format_snowflake_result(self, result: Dict[str, Any]) -> str:
        """Format Snowflake-specific results"""
        if 'total_cost' in result:
            return f"   💰 Total cost: ${result.get('total_cost', 0):.2f}"
        elif 'warehouses' in result:
            warehouses = result['warehouses'][:5]  # Top 5
            formatted = "   🏭 Top warehouses by cost:\n"
            for wh in warehouses:
                formatted += f"      • {wh.get('name', 'Unknown')}: ${wh.get('cost', 0):.2f}\n"
            return formatted
        else:
            return f"   📊 {json.dumps(result, indent=6)}"
    
    def format_databricks_result(self, result: Dict[str, Any]) -> str:
        """Format Databricks-specific results"""
        if 'cost_summary' in result or 'summary' in result:
            summary = result.get('cost_summary', result.get('summary', {}))
            total_cost = summary.get('estimated_total_cost', 0)
            total_clusters = summary.get('total_clusters', 0)
            active_clusters = summary.get('active_clusters', 0)
            return f"   💰 Total estimated cost: ${total_cost:.2f}\n   🖥️  Clusters: {active_clusters}/{total_clusters} active"
        elif 'top_clusters' in result:
            clusters = result['top_clusters'][:3]  # Top 3
            formatted = "   🏆 Top clusters by cost:\n"
            for cluster in clusters:
                formatted += f"      • {cluster.get('cluster_name', 'Unnamed')}: ${cluster.get('estimated_period_cost', 0):.2f}\n"
            return formatted
        elif 'workspace_url' in result:
            return f"   🧱 Workspace: {result.get('workspace_url')}\n   📊 {json.dumps(result, indent=6)}"
        else:
            return f"   📊 {json.dumps(result, indent=6)}"
    
    def format_aws_result(self, result: Dict[str, Any]) -> str:
        """Format AWS-specific results"""
        if 'total_cost' in result:
            return f"   💰 Total AWS cost: ${result.get('total_cost', 0):.2f}"
        elif 'profiles' in result:
            profiles = result['profiles']
            return f"   🔧 Found {len(profiles)} AWS profiles: {', '.join(profiles)}"
        else:
            return f"   📊 {json.dumps(result, indent=6)}"
    
    def format_stock_result(self, result: Dict[str, Any]) -> str:
        """Format stock-specific results"""
        if 'price' in result:
            return f"   📈 Price: ${result.get('price', 0):.2f}, Change: {result.get('change', 0):.2f}%"
        elif 'indices' in result:
            indices = result['indices']
            formatted = "   📊 Market indices:\n"
            for name, data in indices.items():
                formatted += f"      • {name}: {data.get('value', 'N/A')}\n"
            return formatted
        else:
            return f"   📊 {json.dumps(result, indent=6)}"
    
    def show_help(self):
        """Show available commands and tool categories"""
        help_text = """
🤖 **AI Agent Help**

**Available Categories:**
• 📊 **Snowflake**: Cost analysis, warehouse usage, billing reports
• 🧱 **Databricks**: Cost analysis, cluster usage, workspace monitoring
• ☁️  **AWS**: Cost analysis, profile discovery, billing reports  
• 📈 **Finance**: Stock info, market data, portfolio analysis
• 🌤️  **Weather**: Current weather for any city
• 🧮 **Math**: Calculations (sum, average, min, max)
• 🔍 **Search**: Web search for information

**Example Questions:**
• "What's my Snowflake cost for the last 30 days?"
• "Show me Databricks cluster costs using SSO"
• "Show me AWS costs for the past week"
• "What's the weather in New York?"
• "Get stock info for AAPL"
• "Calculate the sum of 10, 20, 30"
• "Search for information about Python"

**Commands:**
• `help` - Show this help
• `tools` - List all available tools
• `history` - Show conversation history
• `session` - Show current session status
• `clear` - Clear stored sessions
• `quit` - Exit the agent
"""
        return help_text
    
    def show_tools(self):
        """Show all available tools organized by category"""
        categories = {}
        for tool_name, tool_info in self.tools.items():
            category = tool_info.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append((tool_name, tool_info.get('description', 'No description')))
        
        tools_text = "\n🛠️  **Available Tools by Category:**\n"
        for category, tools in categories.items():
            tools_text += f"\n**{category.upper()}:**\n"
            for tool_name, description in tools:
                tools_text += f"  • {tool_name}: {description}\n"
        
        return tools_text
    
    def show_history(self):
        """Show conversation history"""
        if not self.conversation_history:
            return "📝 No conversation history yet."
        
        history_text = "\n📝 **Conversation History:**\n"
        for entry in self.conversation_history[-10:]:  # Last 10 entries
            timestamp = entry['timestamp'][:19]  # Remove microseconds
            entry_type = entry['type']
            content = entry['content'][:100] + "..." if len(entry['content']) > 100 else entry['content']
            
            if entry_type == 'question':
                history_text += f"\n🤔 [{timestamp}] Q: {content}"
            else:
                tools_used = entry.get('tools_used', [])
                history_text += f"\n🤖 [{timestamp}] A: Used tools {tools_used}"
        
        return history_text
    
    def show_session_status(self):
        """Show current session status"""
        status_text = "\n🔐 **Session Status:**\n"
        
        # Snowflake session
        if self.snowflake_session:
            status_text += "\n✅ **Snowflake**: Connected"
            if self.session_expiry:
                status_text += f"\n   📅 Expires: {self.session_expiry[:19]}"
            if self.snowflake_session.get('account'):
                status_text += f"\n   🏢 Account: {self.snowflake_session['account']}"
            if self.snowflake_session.get('user'):
                status_text += f"\n   👤 User: {self.snowflake_session['user']}"
        else:
            status_text += "\n❌ **Snowflake**: Not connected"
        
        # AWS session (placeholder for future)
        if self.aws_session:
            status_text += "\n✅ **AWS**: Connected"
        else:
            status_text += "\n❌ **AWS**: Not connected"
        
        status_text += "\n\n💡 Use `clear` to clear all sessions"
        return status_text
    
    async def run_interactive(self):
        """Run the agent in interactive mode"""
        print("\n" + "="*60)
        print("🤖 **AI Agent with MCP Tools** 🛠️")
        print("="*60)
        print("I can help you with AWS costs, Snowflake analysis, stock data, weather, and more!")
        print("Type 'help' for available commands, or ask me a question.")
        print("Type 'quit' to exit.")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye! Thanks for using the AI Agent!")
                    break
                elif user_input.lower() == 'help':
                    print(self.show_help())
                elif user_input.lower() == 'tools':
                    print(self.show_tools())
                elif user_input.lower() == 'history':
                    print(self.show_history())
                elif user_input.lower() in ['session', 'status']:
                    print(self.show_session_status())
                elif user_input.lower() in ['clear', 'clear session']:
                    self.clear_snowflake_session()
                    print("✅ Session cleared successfully")
                else:
                    print("\n🤖 Agent: Processing your question...")
                    response = await self.handle_question(user_input)
                    print(f"\n🤖 Agent: {response}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using the AI Agent!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.__aexit__(None, None, None)

async def main():
    parser = argparse.ArgumentParser(description='AI Agent with MCP Tools')
    parser.add_argument('--question', '-q', help='Ask a single question and exit')
    parser.add_argument('--list-tools', action='store_true', help='List all available tools and exit')
    args = parser.parse_args()
    
    # Create and connect the agent
    agent = MCPAgent()
    
    if not await agent.connect():
        sys.exit(1)
    
    try:
        if args.list_tools:
            print(agent.show_tools())
        elif args.question:
            response = await agent.handle_question(args.question)
            print(f"\n🤖 Agent: {response}")
        else:
            await agent.run_interactive()
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 