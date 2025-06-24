# Pulse 🔍⚡

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/rickyb30/pulse-mcp-server/workflows/Build%20and%20Test/badge.svg)](https://github.com/rickyb30/pulse-mcp-server/actions/workflows/build.yml)
[![Release](https://github.com/rickyb30/pulse-mcp-server/workflows/Release/badge.svg)](https://github.com/rickyb30/pulse-mcp-server/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/release/rickyb30/pulse-mcp-server.svg)](https://github.com/rickyb30/pulse-mcp-server/releases/latest)

A comprehensive Model Context Protocol (MCP) server built with FastMCP 2.0 that provides weather data, web search, calculations, **AWS cost analysis**, **stock market analysis**, **Snowflake cost monitoring**, and **Databricks cost analysis** capabilities.

## 🌟 Features

### Core Tools
- **🧮 Calculator**: Statistical operations (sum, average, min, max)
- **🌤️ Weather Data**: Real-time weather information using OpenWeather API
- **🔍 Web Search**: DuckDuckGo search with OpenAI fallback
- **🏦 AWS Cost Analysis**: Multi-account AWS cost monitoring and optimization
- **📈 Stock Market Analysis**: Real-time prices, technical indicators, portfolio tracking
- **❄️ Snowflake Cost Monitoring**: Warehouse costs, credit usage, storage analysis
- **🧱 Databricks Cost Analysis**: Cluster costs, workspace monitoring, SSO authentication

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

### Databricks Cost Analysis Features
- **🔐 SSO Authentication**: Personal Access Token with workspace URL integration
- **💰 Cluster Cost Monitoring**: Estimated costs based on node types and usage
- **🖥️ Workspace Analysis**: Comprehensive cluster and job cost breakdown
- **🏆 Top Clusters Ranking**: Identify most expensive clusters by cost
- **💡 Cost Optimization**: Actionable recommendations for cost reduction
- **☁️ Multi-Cloud Support**: AWS, Azure, and GCP Databricks deployments

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

### Option 3: VSCode Integration
1. **Built-in MCP Support**: Enable `chat.mcp.enabled` in VSCode settings
2. Open the project in VSCode (`.vscode/mcp.json` is pre-configured)
3. Use Chat view (Ctrl+Alt+I) in Agent mode
4. **Alternative**: Install **Cline** extension for additional MCP features

📖 **[Complete VSCode Setup Guide](VSCODE_SETUP.md)**

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

**Databricks Cost Analysis:**
- "Connect to Databricks using SSO with workspace URL https://dbc-12345678-abcd.cloud.databricks.com"
- "Show me Databricks cluster costs for the last 30 days"
- "Which are my top 5 most expensive Databricks clusters?"
- "Generate a Databricks workspace cost report"
- "Analyze my Databricks workspace costs using SSO"

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

## 🧱 Databricks Cost Analysis

### Available Databricks Tools

#### 1. Connect with SSO
```
connect_databricks_sso(workspace_url, personal_access_token=None)
```
- **workspace_url**: Databricks workspace URL (e.g., `https://dbc-12345678-abcd.cloud.databricks.com`)
- **personal_access_token**: Optional PAT token for API access
- Supports AWS, Azure, and GCP Databricks deployments
- Provides step-by-step SSO setup guidance

#### 2. Get Overall Costs
```
get_databricks_overall_costs(days=30)
```
- **days**: Number of days to analyze (default: 30)
- Returns cluster cost estimation based on node types
- Includes active vs total cluster counts
- Provides job and workspace object counts

#### 3. Get Top Clusters
```
get_databricks_top_clusters(days=30, limit=5)
```
- **days**: Number of days to analyze (default: 30)
- **limit**: Maximum number of clusters to return (default: 5)
- Ranks clusters by estimated cost
- Shows cluster states and configurations

#### 4. Workspace Summary
```
get_databricks_workspace_summary(days=30)
```
- **days**: Number of days to analyze (default: 30)
- Comprehensive workspace analysis
- Cost optimization recommendations
- Average cost per cluster metrics

#### 5. Cost Report
```
get_databricks_cost_report(days=30)
```
- **days**: Number of days to analyze (default: 30)
- Formatted text report with insights
- Includes cost optimization recommendations

### Databricks Authentication Setup

#### Step-by-Step SSO Setup:

1. **Get Your Workspace URL**:
   - Find your Databricks workspace URL (e.g., `https://dbc-12345678-abcd.cloud.databricks.com`)
   - Works with AWS, Azure (`*.azuredatabricks.net`), and GCP deployments

2. **Generate Personal Access Token**:
   ```
   1. Go to your Databricks workspace
   2. Click on your user icon → User Settings  
   3. Go to 'Access tokens' tab
   4. Click 'Generate new token'
   5. Set expiration and click 'Generate'
   6. Copy the generated token
   ```

3. **Connect via Agent**:
   - The agent will guide you through the complete setup process
   - Provides interactive prompts for workspace URL and token
   - Validates connection and provides helpful error messages

### Sample Databricks Cost Report

```
🧱 DATABRICKS COST ANALYSIS REPORT
==================================================
Workspace: https://dbc-12345678-abcd.cloud.databricks.com
Analysis Period: 30 days
Date Range: 2024-12-01 to 2024-12-31

💰 COST SUMMARY
--------------------
Estimated Total Cost: $2,847.50
Total Clusters: 8
Active Clusters: 3
Average Cost per Cluster: $355.94

🖥️ TOP CLUSTERS BY COST
-------------------------
1. ml-training-cluster ($945.60)
   State: RUNNING
   Workers: 4 x i3.2xlarge

2. analytics-prod ($612.30)
   State: TERMINATED
   Workers: 2 x m5.xlarge

3. data-processing ($398.75)
   State: RUNNING
   Workers: 3 x r5.large

💡 COST OPTIMIZATION RECOMMENDATIONS
-------------------------------------
1. Enable auto-termination for interactive clusters to avoid idle costs
2. Use job clusters instead of interactive clusters for scheduled workloads
3. Consider using spot instances for fault-tolerant workloads
4. Monitor cluster utilization and right-size based on actual usage

📝 Note: Costs are estimated based on AWS instance pricing and assumed 
8 hours daily usage. Actual costs may vary based on actual usage, 
Databricks units pricing, and your contract.
```

### Databricks Cost Optimization Tips

#### 🏆 Best Practices:
- **Auto-Termination**: Set automatic cluster termination (15-30 minutes idle)
- **Job Clusters**: Use dedicated job clusters for scheduled workloads
- **Spot Instances**: Leverage spot instances for fault-tolerant workloads
- **Right-Sizing**: Monitor utilization and adjust cluster sizes
- **Pool Management**: Use cluster pools for faster startup times
- **Delta Lake**: Optimize storage costs with Delta Lake features

#### 💡 Cost Monitoring:
- **Regular Reviews**: Monitor costs weekly using the cost analysis tools
- **Cluster Audits**: Review idle and underutilized clusters monthly
- **Usage Patterns**: Track peak usage times and optimize accordingly
- **Cost Alerts**: Set up cost thresholds and monitoring

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

### Databricks Configuration
For Databricks cost analysis, you'll need:
- **Workspace URL**: Your Databricks workspace URL
- **Personal Access Token**: Generated from User Settings → Access tokens
- **Permissions**: Token should have access to:
  - Clusters API (`clusters:read`)
  - Jobs API (`jobs:read`)
  - Workspace API (`workspace:read`)

## 📁 Project Structure

```
pulse-mcp-server/
├── .gitignore                  # Git ignore rules
├── .vscode/                    # VSCode configuration
│   ├── mcp.json                # Official VSCode MCP config
│   ├── settings.json           # Workspace settings
│   ├── launch.json             # Debug configurations
│   └── extensions.json         # Recommended extensions
├── LICENSE                     # MIT license
├── README.md                   # Comprehensive documentation
├── VSCODE_SETUP.md             # VSCode integration guide
├── advanced_mcp_server.py      # Main MCP server with all tools
├── aws_cost_analyzer.py        # AWS cost analysis engine
├── stock_market_analyzer.py    # Stock market analysis engine
├── snowflake_cost_analyzer.py  # Snowflake cost monitoring engine
├── databricks_cost_analyzer.py # Databricks cost analysis engine
├── run_http_server.py          # Flexible server runner
├── claude_config.json          # Claude Desktop configuration
├── requirements.txt            # Python dependencies
└── setup_env.py               # Environment setup utility
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
# AWS Cost Analysis
from aws_cost_analyzer import AWSCostAnalyzer

analyzer = AWSCostAnalyzer()
result = analyzer.analyze_all_profiles(days=7)  # Last 7 days
print(result)

# Databricks Cost Analysis
from databricks_cost_analyzer import DatabricksCostAnalyzer

analyzer = DatabricksCostAnalyzer()
connection = analyzer.connect_with_sso(
    workspace_url="https://dbc-12345678-abcd.cloud.databricks.com",
    personal_access_token="your_token_here"
)
if connection['success']:
    result = analyzer.get_workspace_summary(days=30)
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
- **[Databricks REST API](https://docs.databricks.com/dev-tools/api/latest/)**: Databricks workspace API integration

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