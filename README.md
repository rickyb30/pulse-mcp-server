# Pulse 🔍⚡

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Model Context Protocol (MCP) server built with FastMCP 2.0 that provides weather data, web search, calculations, **AWS cost analysis**, **stock market analysis**, and **Snowflake cost monitoring** capabilities.

## 🌟 Features

### Core Tools
- **🧮 Calculator**: Statistical operations (sum, average, min, max)
- **🌤️ Weather Data**: Real-time weather information using OpenWeather API
- **🔍 Web Search**: DuckDuckGo search with OpenAI fallback
- **🏦 AWS Cost Analysis**: Multi-account AWS cost monitoring and optimization
- **📈 Stock Market Analysis**: Real-time prices, technical indicators, portfolio tracking
- **❄️ Snowflake Cost Monitoring**: Warehouse costs, credit usage, storage analysis

### AWS Cost Analysis Features
- **📊 Profile Discovery**: Automatically discovers AWS profiles from `~/.aws/config` and `~/.aws/credentials`
- **💰 Cost Analysis**: Analyzes running costs across multiple AWS accounts
- **📈 Top 5 Services**: Identifies the most expensive AWS services by cost
- **📋 Detailed Reports**: Comprehensive cost breakdowns with percentages
- **🎯 Multi-Account Support**: Aggregates costs across all configured AWS profiles

### Stock Market Analysis Features
- **📊 Real-time Data**: Current prices, changes, volume for any stock
- **🔍 Technical Analysis**: RSI, MACD, moving averages, Bollinger Bands
- **💼 Portfolio Tracking**: Performance analysis, gains/losses, allocations
- **🎯 Stock Screening**: Filter stocks by P/E ratio, market cap, price ranges
- **💰 Crypto Support**: Bitcoin, Ethereum, and major cryptocurrencies
- **📈 Market Indices**: S&P 500, NASDAQ, Dow Jones, VIX tracking

### Snowflake Cost Analysis Features
- **🔐 SSO Authentication**: External browser authentication for company SSO
- **💰 Overall Cost Monitoring**: Compute and storage cost breakdown
- **🏭 Warehouse Analysis**: Top 5 warehouses by cost and credit usage
- **📊 Credit Usage Tracking**: Detailed credit consumption analysis
- **💾 Storage Cost Analysis**: Data, stage, and failsafe storage costs

### Resources & Prompts
- **Server Status**: Real-time server information
- **Configuration**: Server settings and capabilities
- **AWS Profiles**: Discovered AWS profile information
- **Market Overview**: Current market indices and crypto prices
- **Analysis Templates**: Pre-built prompts for AWS, stock, and Snowflake analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Virtual environment
- AWS CLI configured (for AWS cost analysis)
- API Keys (optional):
  - OpenWeather API key
  - OpenAI API key

### Installation

1. **Clone and Setup**:
```bash
git clone https://github.com/yourusername/pulse-mcp-server.git
cd pulse-mcp-server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment** (optional):
```bash
python setup_env.py
```

3. **Configure AWS** (for cost analysis):
```bash
aws configure  # Follow prompts to set up your AWS credentials
```

## 🔧 Usage

### Option 1: HTTP Server (Standalone)
```bash
# Start HTTP server on localhost:8000
python run_http_server.py
```

### Option 2: Claude Desktop Integration
1. Copy configuration from `claude_config.json` to:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Update paths in the configuration file
3. Restart Claude Desktop
4. Look for the tools icon (🔨)

## 🏦 AWS Cost Analysis

### Available AWS Tools

#### 1. Discover AWS Profiles
```
discover_aws_profiles()
```
- Scans `~/.aws/config` and `~/.aws/credentials`
- Returns all configured AWS profiles
- Shows profile details and credentials status

#### 2. Analyze AWS Costs
```
analyze_aws_costs(days=30, profile=None)
```
- **days**: Number of days to analyze (default: 30)
- **profile**: Specific profile to analyze (if None, analyzes all)
- Returns detailed cost breakdown by service
- Identifies top 5 most expensive services

#### 3. Get Cost Report
```
get_aws_cost_report(days=30, format_type="detailed")
```
- **format_type**: "detailed" or "summary"
- Returns formatted text report
- Includes cost optimization insights

### Example Usage with Claude Desktop

Try these commands in Claude Desktop:

**AWS Cost Analysis:**
- "Analyze my AWS costs for the last 30 days"
- "Show me the top 5 most expensive AWS services"
- "Generate a cost report for my AWS accounts"
- "Which AWS profile is costing me the most?"

**Stock Market Analysis:**
- "Get Apple stock information and technical analysis"
- "Show me the current market indices"
- "Analyze my portfolio with AAPL 100 shares at $150 cost basis"
- "Screen stocks with P/E ratio under 25"
- "What's Bitcoin's current price?"

**Snowflake Cost Analysis:**
- "Connect to Snowflake using SSO with account xyz123 and user john.doe"
- "Show me overall Snowflake costs for the last 30 days"
- "Which are my top 5 most expensive warehouses?"
- "Generate a Snowflake cost report"

**Other Tools:**
- "What's the weather in Tokyo?"
- "Calculate the average of 10, 20, 30, 40, 50"
- "Search for information about Python programming"

## 📊 Sample AWS Cost Report

```
🏦 AWS COST ANALYSIS REPORT
==================================================
📅 Analysis Date: 2025-06-19T21:47:50
📊 Period: Last 30 days
👥 Total Profiles: 2
✅ Successful: 2
❌ Failed: 0
💰 Total Cost (All Accounts): $127.45

🌟 TOP 5 SERVICES (ALL ACCOUNTS)
----------------------------------------
1. Amazon EC2
   💰 $89.32 (70.1%)
2. Amazon RDS
   💰 $23.45 (18.4%)
3. Amazon S3
   💰 $8.92 (7.0%)
4. Amazon CloudWatch
   💰 $3.21 (2.5%)
5. AWS Lambda
   💰 $2.55 (2.0%)

💸 MOST EXPENSIVE ACCOUNT
------------------------------
Profile: production
Account ID: 123456789012
Cost: $98.76
```

## 🛠️ Configuration

### Environment Variables
```bash
# API Keys (optional)
OPENWEATHER_API_KEY=your_openweather_key
OPENAI_API_KEY=your_openai_key

# Server Configuration
MCP_TRANSPORT=stdio  # or http
MCP_HOST=localhost
MCP_PORT=8000
```

### AWS Configuration
The server automatically discovers AWS profiles from:
- `~/.aws/config` - AWS configuration file
- `~/.aws/credentials` - AWS credentials file

Ensure your AWS credentials have the following permissions:
- `ce:GetCostAndUsage` (Cost Explorer)
- `sts:GetCallerIdentity` (Account information)

## 📁 Project Structure

```
pulse-mcp-server/
├── advanced_mcp_server.py      # Main MCP server with all tools
├── aws_cost_analyzer.py        # AWS cost analysis engine
├── stock_market_analyzer.py    # Stock market analysis engine
├── snowflake_cost_analyzer.py  # Snowflake cost monitoring engine
├── run_http_server.py          # Flexible server runner
├── claude_config.json          # Claude Desktop configuration
├── requirements.txt            # Python dependencies
├── setup_env.py               # Environment setup utility
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## 🔍 Troubleshooting

### AWS Issues
- **No profiles found**: Run `aws configure` to set up credentials
- **Permission denied**: Ensure your AWS user has Cost Explorer permissions
- **Region errors**: Cost Explorer API requires `us-east-1` region

### General Issues
- **Import errors**: Ensure virtual environment is activated
- **API key errors**: Check `.env` file configuration
- **Server startup**: Verify all dependencies are installed

## 🚀 Advanced Usage

### Custom Cost Analysis
```python
from aws_cost_analyzer import AWSCostAnalyzer

analyzer = AWSCostAnalyzer()
result = analyzer.analyze_all_profiles(days=7)  # Last 7 days
print(result)
```

### HTTP API Integration
```bash
# Start HTTP server
export MCP_TRANSPORT=http
python run_http_server.py

# Test AWS cost analysis via HTTP
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"analyze_aws_costs","arguments":{"days":30}}}'
```

## 📚 Documentation

- **[FastMCP Documentation](https://gofastmcp.com/)**: Official FastMCP docs
- **[AWS Cost Explorer API](https://docs.aws.amazon.com/ce/)**: AWS Cost Explorer documentation
- **[Yahoo Finance API](https://pypi.org/project/yfinance/)**: Stock market data source
- **[Snowflake Python Connector](https://docs.snowflake.com/en/user-guide/python-connector.html)**: Snowflake integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **FastMCP**: Excellent MCP framework
- **AWS SDK**: Boto3 for AWS integration
- **OpenWeather**: Weather data API
- **DuckDuckGo**: Web search API 