import os
import sys
import json
import requests
import asyncio
from fastmcp import FastMCP
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Import AWS cost analyzer
from aws_cost_analyzer import AWSCostAnalyzer, format_cost_analysis_report

# Import Stock Market analyzer
from stock_market_analyzer import StockMarketAnalyzer, format_stock_report

# Import Snowflake cost analyzer
from snowflake_cost_analyzer import SnowflakeCostAnalyzer, format_snowflake_report

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create a more advanced MCP server
mcp = FastMCP("Pulse")

# --- Tools ---

@mcp.tool
def calculate(operation: str, numbers: List[float]) -> float:
    """Perform a calculation on a list of numbers.
    
    Args:
        operation: The operation to perform ('sum', 'avg', 'min', 'max')
        numbers: A list of numbers to perform the operation on
        
    Returns:
        The result of the calculation
    """
    if operation == "sum":
        return sum(numbers)
    elif operation == "avg":
        return sum(numbers) / len(numbers)
    elif operation == "min":
        return min(numbers)
    elif operation == "max":
        return max(numbers)
    else:
        raise ValueError(f"Unknown operation: {operation}")

@mcp.tool
def get_weather(city: str, units: Optional[str] = "metric") -> Dict[str, Any]:
    """Get the current weather for a city using OpenWeather API.
    
    Args:
        city: The name of the city
        units: Unit system - 'metric' (Celsius) or 'imperial' (Fahrenheit)
        
    Returns:
        A dictionary containing weather information
    """
    if not OPENWEATHER_API_KEY:
        # Fallback if API key is not available
        return {
            "city": city,
            "temperature": 75.0 if units == "imperial" else 24.0,
            "conditions": "sunny",
            "humidity": 45,
            "wind_speed": 8.5,
            "description": "This is mock data as no OpenWeather API key was provided."
        }
    
    # Query the OpenWeather API
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": units
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        weather_data = response.json()
        
        # Extract relevant information
        result = {
            "city": city,
            "temperature": weather_data["main"]["temp"],
            "conditions": weather_data["weather"][0]["main"],
            "humidity": weather_data["main"]["humidity"],
            "wind_speed": weather_data["wind"]["speed"],
            "description": weather_data["weather"][0]["description"]
        }
        
        return result
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Error fetching weather data: {str(e)}",
            "city": city,
            "temperature": None,
            "conditions": None,
            "humidity": None,
            "wind_speed": None,
            "description": "Unable to fetch weather data."
        }

@mcp.tool
def web_search(query: str, limit: Optional[int] = 5) -> List[Dict[str, Any]]:
    """Search the web using DuckDuckGo search (no API key required).
    
    Args:
        query: The search query
        limit: Maximum number of results to return (default: 5)
        
    Returns:
        A list of web search results with titles, URLs, and snippets
    """
    try:
        # Use DuckDuckGo search which doesn't require an API key
        import urllib.parse
        import urllib.request
        import re
        
        # URL encode the query
        encoded_query = urllib.parse.quote_plus(query)
        
        # DuckDuckGo instant answer API
        search_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        # Make the request
        with urllib.request.urlopen(search_url) as response:
            data = json.loads(response.read().decode())
        
        results = []
        
        # Extract abstract if available
        if data.get('Abstract'):
            results.append({
                "title": data.get('Heading', query),
                "snippet": data['Abstract'],
                "url": data.get('AbstractURL', ''),
                "source": "DuckDuckGo Abstract",
                "relevance_score": 1.0
            })
        
        # Extract related topics
        for topic in data.get('RelatedTopics', [])[:limit-len(results)]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append({
                    "title": topic.get('Text', '')[:100] + "...",
                    "snippet": topic.get('Text', ''),
                    "url": topic.get('FirstURL', ''),
                    "source": "DuckDuckGo Related",
                    "relevance_score": 0.8
                })
        
        # If we have results, return them
        if results:
            return results[:limit]
        
        # Fallback: Use OpenAI to generate search-like results based on knowledge
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful search assistant. Provide factual, up-to-date information about the query. Format your response as if it were search results."
                        },
                        {
                            "role": "user",
                            "content": f"Provide information about: {query}"
                        }
                    ],
                    max_tokens=500
                )
                
                content = response.choices[0].message.content
                return [{
                    "title": f"Information about: {query}",
                    "snippet": content,
                    "url": "",
                    "source": "AI Knowledge Base",
                    "relevance_score": 0.9,
                    "timestamp": datetime.now().isoformat()
                }]
                
            except ImportError:
                pass
            except Exception as e:
                return [{
                    "error": f"OpenAI search fallback failed: {str(e)}",
                    "query": query
                }]
        
        # Final fallback
        return [{
            "title": f"Search: {query}",
            "snippet": f"No specific results found for '{query}'. This is a basic search implementation using DuckDuckGo API.",
            "url": f"https://duckduckgo.com/?q={encoded_query}",
            "source": "DuckDuckGo",
            "relevance_score": 0.5,
            "timestamp": datetime.now().isoformat()
        }]
        
    except Exception as e:
        return [{
            "error": f"Web search failed: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "suggestion": "Check your internet connection and try again"
        }]

# --- AWS Cost Analysis Tools ---

@mcp.tool
def discover_aws_profiles() -> Dict[str, Any]:
    """Discover AWS profiles from local configuration files.
    
    Returns:
        A dictionary containing discovered AWS profiles and their details
    """
    try:
        analyzer = AWSCostAnalyzer()
        profiles = analyzer.discover_aws_profiles()
        
        return {
            "success": True,
            "total_profiles": len(profiles),
            "profiles": profiles,
            "message": f"Found {len(profiles)} AWS profiles in local configuration"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to discover AWS profiles. Make sure AWS CLI is configured."
        }

@mcp.tool
def analyze_aws_costs(days: Optional[int] = 30, profile: Optional[str] = None) -> Dict[str, Any]:
    """Analyze AWS costs for all profiles or a specific profile.
    
    Args:
        days: Number of days to analyze (default: 30)
        profile: Specific profile to analyze (if None, analyzes all profiles)
        
    Returns:
        Detailed cost analysis including top 5 services by cost
    """
    try:
        analyzer = AWSCostAnalyzer()
        
        if profile:
            # Analyze specific profile
            result = analyzer.get_cost_and_usage(profile, days)
            return {
                "success": True,
                "analysis_type": "single_profile",
                "profile": profile,
                "result": result
            }
        else:
            # Analyze all profiles
            result = analyzer.analyze_all_profiles(days)
            return result
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to analyze AWS costs. Check your AWS credentials and permissions."
        }

@mcp.tool
def get_aws_cost_report(days: Optional[int] = 30, format_type: Optional[str] = "detailed") -> str:
    """Get a formatted AWS cost analysis report.
    
    Args:
        days: Number of days to analyze (default: 30)
        format_type: Report format - 'detailed' or 'summary' (default: 'detailed')
        
    Returns:
        A formatted text report of AWS costs
    """
    try:
        analyzer = AWSCostAnalyzer()
        result = analyzer.analyze_all_profiles(days)
        
        if format_type == "summary":
            # Generate summary report
            if not result['success']:
                return f"❌ Analysis failed: {result.get('error', 'Unknown error')}"
            
            summary = result['summary']
            report = f"""🏦 AWS COST SUMMARY
💰 Total Cost (All Accounts): ${result['total_cost_all_accounts']}
👥 Profiles Analyzed: {result['profiles_successful']}/{result['total_profiles']}
📊 Period: Last {result['period_days']} days

🌟 TOP 5 SERVICES:
"""
            for i, service in enumerate(summary['top_5_services_across_all_accounts'][:5], 1):
                report += f"{i}. {service['service']}: ${service['cost']} ({service['percentage']}%)\n"
            
            if summary['most_expensive_account']:
                expensive = summary['most_expensive_account']
                report += f"\n💸 Most Expensive Account: {expensive['profile']} (${expensive['cost']})"
            
            return report
        else:
            # Generate detailed report
            return format_cost_analysis_report(result)
            
    except Exception as e:
        return f"❌ Failed to generate cost report: {str(e)}"

# --- Stock Market Analysis Tools ---

@mcp.tool
def get_stock_info(symbol: str) -> Dict[str, Any]:
    """Get comprehensive stock information including price, fundamentals, and key metrics.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
        
    Returns:
        Detailed stock information including current price, change, volume, P/E ratio, market cap, etc.
    """
    try:
        analyzer = StockMarketAnalyzer()
        return analyzer.get_stock_info(symbol)
    except Exception as e:
        return {
            'success': False,
            'symbol': symbol.upper(),
            'error': str(e)
        }

@mcp.tool
def get_historical_stock_data(symbol: str, period: Optional[str] = "1y", interval: Optional[str] = "1d") -> Dict[str, Any]:
    """Get historical stock price data.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        period: Time period - '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        interval: Data interval - '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'
        
    Returns:
        Historical price data with OHLCV (Open, High, Low, Close, Volume) information
    """
    try:
        analyzer = StockMarketAnalyzer()
        return analyzer.get_historical_data(symbol, period, interval)
    except Exception as e:
        return {
            'success': False,
            'symbol': symbol.upper(),
            'error': str(e)
        }

@mcp.tool
def get_technical_indicators(symbol: str, period: Optional[str] = "6mo") -> Dict[str, Any]:
    """Calculate technical indicators for stock analysis.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        period: Time period for analysis - '1mo', '3mo', '6mo', '1y', '2y'
        
    Returns:
        Technical indicators including RSI, MACD, moving averages, Bollinger Bands, and trend analysis
    """
    try:
        analyzer = StockMarketAnalyzer()
        return analyzer.calculate_technical_indicators(symbol, period)
    except Exception as e:
        return {
            'success': False,
            'symbol': symbol.upper(),
            'error': str(e)
        }

@mcp.tool
def screen_stocks(max_pe_ratio: Optional[float] = 50, min_market_cap: Optional[float] = 0, 
                 max_market_cap: Optional[float] = None, min_price: Optional[float] = 0, 
                 max_price: Optional[float] = None) -> Dict[str, Any]:
    """Screen stocks based on fundamental criteria.
    
    Args:
        max_pe_ratio: Maximum P/E ratio (default: 50)
        min_market_cap: Minimum market cap in dollars (default: 0)
        max_market_cap: Maximum market cap in dollars (default: unlimited)
        min_price: Minimum stock price (default: 0)
        max_price: Maximum stock price (default: unlimited)
        
    Returns:
        List of stocks matching the criteria with key metrics
    """
    try:
        analyzer = StockMarketAnalyzer()
        criteria = {
            'max_pe_ratio': max_pe_ratio,
            'min_market_cap': min_market_cap,
            'max_market_cap': max_market_cap or float('inf'),
            'min_price': min_price,
            'max_price': max_price or float('inf')
        }
        return analyzer.screen_stocks(criteria)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool
def get_market_indices() -> Dict[str, Any]:
    """Get current data for major market indices.
    
    Returns:
        Current values and changes for S&P 500, NASDAQ, Dow Jones, Russell 2000, and VIX
    """
    try:
        analyzer = StockMarketAnalyzer()
        return analyzer.get_market_indices()
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool
def analyze_portfolio(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze a stock portfolio with performance metrics.
    
    Args:
        holdings: List of holdings with format: [{"symbol": "AAPL", "shares": 100, "cost_basis": 150.0}, ...]
        
    Returns:
        Portfolio analysis including total value, gains/losses, weights, and performance rankings
    """
    try:
        analyzer = StockMarketAnalyzer()
        return analyzer.analyze_portfolio(holdings)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool
def get_crypto_data(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get cryptocurrency price data.
    
    Args:
        symbols: List of crypto symbols (e.g., ['BTC-USD', 'ETH-USD']) - defaults to major cryptos
        
    Returns:
        Current prices and changes for specified cryptocurrencies
    """
    try:
        analyzer = StockMarketAnalyzer()
        return analyzer.get_crypto_data(symbols)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool
def get_stock_report(symbol: str) -> str:
    """Get a formatted stock analysis report.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Formatted text report with stock information and analysis
    """
    try:
        analyzer = StockMarketAnalyzer()
        stock_data = analyzer.get_stock_info(symbol)
        return format_stock_report(stock_data)
    except Exception as e:
        return f"❌ Failed to generate stock report for {symbol}: {str(e)}"

# --- Snowflake Cost Analysis Tools ---

@mcp.tool
def connect_snowflake_sso(account: str, user: str) -> Dict[str, Any]:
    """Connect to Snowflake using SSO/External Browser authentication.
    
    Args:
        account: Snowflake account identifier (e.g., 'xy12345.us-east-1') or full URL
        user: Your Snowflake username
        
    Returns:
        Connection status and details
    """
    try:
        # Parse account if it's a URL
        def parse_snowflake_account(account_input: str) -> str:
            """Parse account identifier from various input formats including full URLs"""
            account_input = account_input.strip()
            
            # If it's a full URL, parse it
            if account_input.startswith('https://') or account_input.startswith('http://'):
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
                    return account
            
            # If it's already an account identifier, return as-is
            return account_input
        
        # Parse the account parameter
        parsed_account = parse_snowflake_account(account)
        
        analyzer = SnowflakeCostAnalyzer()
        result = analyzer.connect_with_sso(parsed_account, user)
        
        # Store the analyzer instance for subsequent calls
        # Note: In a real implementation, you'd want to manage connections more carefully
        globals()['_snowflake_analyzer'] = analyzer if result['success'] else None
        
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to connect to Snowflake with SSO'
        }

@mcp.tool
def connect_snowflake_credentials(account: str, user: str, password: str, 
                                role: Optional[str] = None, warehouse: Optional[str] = None) -> Dict[str, Any]:
    """Connect to Snowflake using username/password authentication.
    
    Args:
        account: Snowflake account identifier or full URL
        user: Your Snowflake username
        password: Your Snowflake password
        role: Optional role to assume
        warehouse: Optional default warehouse
        
    Returns:
        Connection status and details
    """
    try:
        # Parse account if it's a URL
        def parse_snowflake_account(account_input: str) -> str:
            """Parse account identifier from various input formats including full URLs"""
            account_input = account_input.strip()
            
            # If it's a full URL, parse it
            if account_input.startswith('https://') or account_input.startswith('http://'):
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
                    return account
            
            # If it's already an account identifier, return as-is
            return account_input
        
        # Parse the account parameter
        parsed_account = parse_snowflake_account(account)
        
        analyzer = SnowflakeCostAnalyzer()
        result = analyzer.connect_with_credentials(parsed_account, user, password, role, warehouse)
        
        # Store the analyzer instance for subsequent calls
        globals()['_snowflake_analyzer'] = analyzer if result['success'] else None
        
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to connect to Snowflake with credentials'
        }

@mcp.tool
def get_snowflake_overall_costs(days: Optional[int] = 30) -> Dict[str, Any]:
    """Get overall Snowflake costs for the specified period.
    
    Args:
        days: Number of days to analyze (default: 30)
        
    Returns:
        Overall cost breakdown including compute and storage costs
    """
    try:
        analyzer = globals().get('_snowflake_analyzer')
        if not analyzer:
            return {
                'success': False,
                'error': 'Not connected to Snowflake. Please connect first using connect_snowflake_sso or connect_snowflake_credentials.'
            }
        
        return analyzer.get_overall_costs(days)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool
def get_snowflake_top_warehouses(days: Optional[int] = 30, limit: Optional[int] = 5) -> Dict[str, Any]:
    """Get top warehouses by cost/credit usage.
    
    Args:
        days: Number of days to analyze (default: 30)
        limit: Number of top warehouses to return (default: 5)
        
    Returns:
        List of top warehouses with cost and usage metrics
    """
    try:
        analyzer = globals().get('_snowflake_analyzer')
        if not analyzer:
            return {
                'success': False,
                'error': 'Not connected to Snowflake. Please connect first using connect_snowflake_sso or connect_snowflake_credentials.'
            }
        
        return analyzer.get_top_warehouses_by_cost(days, limit)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool
def get_snowflake_cost_summary(days: Optional[int] = 30) -> Dict[str, Any]:
    """Get comprehensive Snowflake cost summary including overall costs and top warehouses.
    
    Args:
        days: Number of days to analyze (default: 30)
        
    Returns:
        Complete Snowflake cost analysis with overall costs and warehouse breakdown
    """
    try:
        analyzer = globals().get('_snowflake_analyzer')
        if not analyzer:
            return {
                'success': False,
                'error': 'Not connected to Snowflake. Please connect first using connect_snowflake_sso or connect_snowflake_credentials.'
            }
        
        return analyzer.get_snowflake_summary(days)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool
def get_snowflake_cost_report(days: Optional[int] = 30) -> str:
    """Get a formatted Snowflake cost analysis report.
    
    Args:
        days: Number of days to analyze (default: 30)
        
    Returns:
        Formatted text report with Snowflake cost analysis
    """
    try:
        analyzer = globals().get('_snowflake_analyzer')
        if not analyzer:
            return "❌ Not connected to Snowflake. Please connect first using connect_snowflake_sso or connect_snowflake_credentials."
        
        result = analyzer.get_snowflake_summary(days)
        return format_snowflake_report(result)
    except Exception as e:
        return f"❌ Failed to generate Snowflake cost report: {str(e)}"

@mcp.tool
def connect_snowflake_auto() -> Dict[str, Any]:
    """Auto-connect to Snowflake using environment variables.
    
    Looks for SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and optionally SNOWFLAKE_PASSWORD
    or uses SSO if SNOWFLAKE_AUTHENTICATOR=externalbrowser
    
    Returns:
        Connection status and details
    """
    try:
        account = os.getenv("SNOWFLAKE_ACCOUNT")
        user = os.getenv("SNOWFLAKE_USER")
        password = os.getenv("SNOWFLAKE_PASSWORD")
        authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser")
        role = os.getenv("SNOWFLAKE_ROLE")
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        
        if not account or not user:
            return {
                'success': False,
                'error': 'Missing required environment variables',
                'message': 'Please set SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER environment variables, or use connect_snowflake_sso/connect_snowflake_credentials tools'
            }
        
        # Parse account if it's a URL
        def parse_snowflake_account(account_input: str) -> str:
            """Parse account identifier from various input formats including full URLs"""
            account_input = account_input.strip()
            
            # If it's a full URL, parse it
            if account_input.startswith('https://') or account_input.startswith('http://'):
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
                    return account
            
            # If it's already an account identifier, return as-is
            return account_input
        
        # Parse the account parameter
        parsed_account = parse_snowflake_account(account)
        
        analyzer = SnowflakeCostAnalyzer()
        
        if authenticator == "externalbrowser" or not password:
            # Use SSO
            result = analyzer.connect_with_sso(parsed_account, user, authenticator)
        else:
            # Use credentials
            result = analyzer.connect_with_credentials(parsed_account, user, password, role, warehouse)
        
        # Store the analyzer instance for subsequent calls
        globals()['_snowflake_analyzer'] = analyzer if result['success'] else None
        
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to auto-connect to Snowflake'
        }

# --- Resources ---

# Create a config resource
@mcp.resource("config://settings")
def config() -> Dict[str, Any]:
    """Returns the server configuration."""
    return {
        "app_name": "Pulse",
        "version": "3.0.0",
        "features": ["tools", "resources", "prompts", "aws_cost_analysis", "stock_market_analysis", "snowflake_cost_analysis"],
        "max_connections": 100,
        "aws_features": {
            "cost_analysis": True,
            "profile_discovery": True,
            "multi_account_support": True
        },
        "stock_market_features": {
            "real_time_data": True,
            "technical_analysis": True,
            "portfolio_tracking": True,
            "market_screening": True,
            "crypto_support": True,
            "market_indices": True
        },
        "snowflake_features": {
            "sso_authentication": True,
            "overall_cost_monitoring": True,
            "warehouse_cost_analysis": True,
            "storage_cost_tracking": True,
            "credit_usage_analysis": True
        }
    }

# Create a dynamic resource
@mcp.resource("status://server")
def server_status() -> Dict[str, Any]:
    """Returns the current server status."""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "uptime": "3 hours 12 minutes",
        "active_connections": 5,
        "cpu_usage": "23%",
        "memory_usage": "156MB",
        "aws_integration": "enabled"
    }

# AWS profiles resource
@mcp.resource("aws://profiles")
def aws_profiles() -> Dict[str, Any]:
    """Returns discovered AWS profiles."""
    try:
        analyzer = AWSCostAnalyzer()
        profiles = analyzer.discover_aws_profiles()
        return {
            "success": True,
            "profiles": profiles,
            "total_profiles": len(profiles)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Stock market resource
@mcp.resource("stocks://market-overview")
def market_overview() -> Dict[str, Any]:
    """Returns current market overview with major indices."""
    try:
        analyzer = StockMarketAnalyzer()
        indices = analyzer.get_market_indices()
        crypto = analyzer.get_crypto_data()
        
        return {
            "success": True,
            "market_indices": indices.get('indices', {}),
            "cryptocurrencies": crypto.get('cryptocurrencies', []),
            "timestamp": datetime.now().isoformat(),
            "market_status": "open" if datetime.now().weekday() < 5 else "closed"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# --- Prompts ---

@mcp.prompt("data_analyst")
def data_analysis_template() -> str:
    """A template for analyzing data."""
    return """
    You are a data analyst examining the following dataset:
    
    {data}
    
    Please analyze this data and provide:
    1. A summary of key statistics
    2. Identification of trends and patterns
    3. Actionable insights based on the data
    4. Recommendations for further analysis
    
    Use clear explanations and visual descriptions where helpful.
    """

@mcp.prompt("aws_cost_analyst")
def aws_cost_analysis_template() -> str:
    """A template for AWS cost analysis."""
    return """
    You are an AWS cost optimization analyst examining the following cost data:
    
    {cost_data}
    
    Please provide:
    1. Cost breakdown analysis by service
    2. Identification of cost optimization opportunities
    3. Recommendations for reducing AWS spending
    4. Potential cost anomalies or unexpected charges
    5. Best practices for cost management
    
    Focus on actionable insights that can help reduce costs while maintaining performance.
    """

@mcp.prompt("stock_market_analyst")
def stock_market_analysis_template() -> str:
    """A template for stock market analysis."""
    return """
    You are a professional stock market analyst examining the following data:
    
    {stock_data}
    
    Please provide:
    1. Current stock performance analysis
    2. Technical indicator interpretation (RSI, MACD, moving averages)
    3. Fundamental analysis based on P/E, market cap, and other metrics
    4. Risk assessment and volatility analysis
    5. Investment recommendation with rationale
    6. Price targets and key support/resistance levels
    
    Focus on actionable insights for both short-term trading and long-term investing.
    """

@mcp.prompt("snowflake_cost_analyst")
def snowflake_cost_analysis_template() -> str:
    """A template for Snowflake cost analysis."""
    return """
    You are a Snowflake cost optimization expert examining the following cost data:
    
    {snowflake_data}
    
    Please provide:
    1. Overall cost breakdown analysis (compute vs storage)
    2. Warehouse utilization and efficiency analysis
    3. Cost optimization opportunities and recommendations
    4. Identification of potential cost anomalies or spikes
    5. Best practices for Snowflake cost management
    6. Warehouse sizing and auto-suspend recommendations
    
    Focus on actionable insights that can help reduce Snowflake costs while maintaining performance.
    """

@mcp.prompt("api_documentation")
def api_docs_template() -> str:
    """A template for generating API documentation."""
    return """
    # API Documentation for {endpoint_name}
    
    ## Overview
    {description}
    
    ## Endpoint
    `{http_method} {endpoint_path}`
    
    ## Request Parameters
    {request_params}
    
    ## Response Format
    {response_format}
    
    ## Example Usage
    ```
    {example_usage}
    ```
    
    ## Error Codes
    {error_codes}
    """

# --- Testing the server with a client ---
async def test_client():
    from fastmcp import Client
    
    # Create a client pointing to this server
    client = Client(mcp)
    
    async with client:
        # Call the calculate tool
        sum_result = await client.call_tool("calculate", {"operation": "sum", "numbers": [1, 2, 3, 4, 5]})
        print(f"Sum of [1, 2, 3, 4, 5]: {sum_result}", file=sys.stderr)
        
        # Call the weather tool
        weather = await client.call_tool("get_weather", {"city": "Tokyo", "units": "metric"})
        print(f"Weather in Tokyo: {weather}", file=sys.stderr)
        
        # Call the web search tool
        search_results = await client.call_tool("web_search", {"query": "python", "limit": 2})
        print(f"Web search results for 'python': {search_results}", file=sys.stderr)
        
        # Test AWS profile discovery
        aws_profiles = await client.call_tool("discover_aws_profiles", {})
        print(f"AWS profiles: {aws_profiles}", file=sys.stderr)
        
        # Get server status
        status = await client.read_resource("status://server")
        print(f"Server status: {status}", file=sys.stderr)
        
        # Get config
        config = await client.read_resource("config://settings")
        print(f"Config: {config}", file=sys.stderr)

# --- Server Setup ---
if __name__ == "__main__":
    # Determine which transport to use based on environment variables
    transport = os.environ.get("MCP_TRANSPORT", "stdio")  # Changed default from "http" to "stdio"
    
    if transport in ("streamable-http", "sse"):  # Updated from "http" to include both HTTP transports
        # Run as HTTP server
        port = int(os.environ.get("MCP_PORT", 8000))
        mcp.run(
            transport=transport, 
            host="0.0.0.0", 
            port=port
        )
    elif transport == "stdio":
        # Run using STDIO transport (useful for local testing)
        mcp.run(transport="stdio")
    else:
        print(f"Unsupported transport: {transport}", file=sys.stderr)
        print("Supported transports: stdio, streamable-http, sse", file=sys.stderr)
        exit(1) 