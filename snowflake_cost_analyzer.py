#!/usr/bin/env python3
"""
Snowflake Cost Analyzer
-----------------------
Monitors Snowflake costs and warehouse usage with SSO support.
"""
import sys
import os
import snowflake.connector
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import io
import contextlib
import re
import threading
import time
import webbrowser

class SnowflakeCostAnalyzer:
    """Snowflake Cost Analysis Tool"""
    
    def __init__(self):
        self.connection = None
        self.auth_url = None
        self.connection_result = None
        self.connection_error = None
        
    def _connection_thread(self, account: str, user: str, authenticator: str = 'externalbrowser'):
        """Run the connection in a separate thread to avoid blocking"""
        try:
            # Capture output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            try:
                sys.stdout = stdout_buffer
                sys.stderr = stderr_buffer
                
                self.connection = snowflake.connector.connect(
                    account=account,
                    user=user,
                    authenticator=authenticator,
                    login_timeout=300,  # 5 minutes timeout
                )
                
                self.connection_result = {
                    'success': True,
                    'message': f'Successfully connected to Snowflake account: {account}',
                    'user': user,
                    'account': account,
                    'authentication_method': 'SSO'
                }
                
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                # Try to extract URL from captured output
                all_output = stdout_buffer.getvalue() + stderr_buffer.getvalue()
                if all_output:
                    self.auth_url = self._extract_auth_url(all_output)
                
        except Exception as e:
            self.connection_error = str(e)
    
    def connect_with_sso(self, account: str, user: str, authenticator: str = 'externalbrowser') -> Dict[str, Any]:
        """Connect to Snowflake using SSO/External Browser authentication"""
        
        # Try to generate a predictable auth URL based on account info
        predicted_url = self._generate_auth_url(account, user)
        
        # Start connection in background thread
        connection_thread = threading.Thread(
            target=self._connection_thread, 
            args=(account, user, authenticator)
        )
        connection_thread.daemon = True
        connection_thread.start()
        
        # Wait a short time to see if we get a URL or connection
        wait_time = 0
        max_wait = 10  # Wait up to 10 seconds
        
        while wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
            
            # Check if connection completed
            if self.connection_result:
                return self.connection_result
            
            # Check if we got an auth URL
            if self.auth_url:
                return {
                    'success': False,
                    'waiting_for_authentication': True,
                    'authentication_url': self.auth_url,
                    'authentication_instructions': 'Please click the URL above to complete SSO authentication, then try connecting again',
                    'message': 'SSO authentication URL generated. Please complete authentication in browser.',
                    'account': account,
                    'user': user,
                    'claude_desktop_note': f'Click this URL to authenticate: {self.auth_url}'
                }
            
            # Check if connection failed
            if self.connection_error:
                break
        
        # If we get here, either connection is taking too long or failed
        if self.connection_error:
            error_response = {
                'success': False,
                'error': self.connection_error,
                'message': 'Failed to connect to Snowflake with SSO',
                'account': account,
                'user': user
            }
        else:
            # Connection is taking too long, provide predicted URL
            error_response = {
                'success': False,
                'waiting_for_authentication': True,
                'message': 'SSO authentication is in progress. Please use the authentication URL below.',
                'account': account,
                'user': user,
                'connection_status': 'Authentication in progress...'
            }
        
        # Include predicted URL if available
        if predicted_url:
            error_response['predicted_authentication_url'] = predicted_url
            error_response['authentication_instructions'] = 'Try clicking the predicted authentication URL below'
            error_response['claude_desktop_note'] = f'Try this authentication URL: {predicted_url}'
        
        # Include actual URL if we captured one
        if self.auth_url:
            error_response['authentication_url'] = self.auth_url
            error_response['claude_desktop_note'] = f'Click this URL to authenticate: {self.auth_url}'
        
        error_response['troubleshooting'] = {
            'next_steps': [
                'Click the authentication URL provided above',
                'Complete the SSO authentication in your browser', 
                'Try the connection again after authentication',
                'Ensure pop-ups are enabled for Snowflake domains'
            ],
            'common_issues': [
                'Browser pop-ups might be blocked',
                'Network connectivity issues',
                'SSO not configured for this account',
                'Invalid account identifier format'
            ]
        }
        
        return error_response
    
    def _generate_auth_url(self, account: str, user: str) -> Optional[str]:
        """Generate a predictable authentication URL based on account info"""
        try:
            # For accounts with privatelink, construct the SSO URL
            if 'privatelink' in account:
                # Extract the base URL parts
                parts = account.split('.')
                if len(parts) >= 3:
                    account_id = parts[0]  # e.g., sx18286
                    region = parts[1]      # e.g., canada-central
                    
                    # Common SSO URL patterns for Snowflake
                    possible_urls = [
                        f"https://{account}.snowflakecomputing.com/fed/login",
                        f"https://{account}.snowflakecomputing.com/console/login",
                        f"https://{account_id}.{region}.snowflakecomputing.com/fed/login",
                    ]
                    
                    # Return the first one as a starting point
                    return possible_urls[0]
            else:
                # For regular accounts
                return f"https://{account}.snowflakecomputing.com/fed/login"
                
        except Exception:
            pass
        
        return None
    
    def _extract_auth_url(self, captured_output: str) -> Optional[str]:
        """Extract authentication URL from captured Snowflake connector output"""
        # Look for authentication URL patterns - order matters, most specific first
        url_patterns = [
            # Microsoft login URLs (most common for SSO)
            r'Going to open: (https://login\.microsoftonline\.com/[a-f0-9\-]+/saml2\?[^\s\n\r]*)',
            r'(https://login\.microsoftonline\.com/[a-f0-9\-]+/saml2\?SAMLRequest=[^\s\n\r]*)',
            r'Going to open: (https://login\.microsoftonline\.com/[^\s\n\r]+)',
            r'(https://login\.microsoftonline\.com/[^\s\n\r]+)',
            
            # Generic patterns for other SSO providers
            r'Going to open: (https?://[^\s\n\r]+)',
            r'Open the following link: (https?://[^\s\n\r]+)',
            r'Please open: (https?://[^\s\n\r]+)',
            r'Navigate to: (https?://[^\s\n\r]+)',
            
            # Snowflake direct login URLs
            r'(https://[^.\s]+\.snowflakecomputing\.com/[^\s\n\r]*)',
            r'(https://[^.\s]+\.privatelink\.snowflakecomputing\.com/[^\s\n\r]*)',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, captured_output, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                url = match.group(1).rstrip('.,!?\n\r')
                # Don't split on spaces for URLs - they might have encoded spaces
                return url
        
        return None
    
    def connect_with_credentials(self, account: str, user: str, password: str, 
                               role: Optional[str] = None, warehouse: Optional[str] = None) -> Dict[str, Any]:
        """Connect to Snowflake using username/password (fallback)"""
        try:
            connection_params = {
                'account': account,
                'user': user,
                'password': password
            }
            
            if role:
                connection_params['role'] = role
            if warehouse:
                connection_params['warehouse'] = warehouse
                
            self.connection = snowflake.connector.connect(**connection_params)
            
            return {
                'success': True,
                'message': f'Successfully connected to Snowflake account: {account}',
                'user': user,
                'account': account
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to connect to Snowflake with provided credentials.'
            }
    
    def get_overall_costs(self, days: int = 30) -> Dict[str, Any]:
        """Get overall Snowflake costs for the specified period"""
        if not self.connection:
            return {
                'success': False,
                'error': 'Not connected to Snowflake. Please connect first.'
            }
        
        try:
            cursor = self.connection.cursor()
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Query for overall compute costs (warehouse usage)
            compute_query = f"""
            SELECT 
                SUM(CREDITS_USED) as total_compute_credits,
                COUNT(DISTINCT WAREHOUSE_NAME) as warehouses_used,
                COUNT(*) as total_queries
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY 
            WHERE START_TIME >= '{start_date}'
            AND START_TIME < '{end_date}'
            """
            
            cursor.execute(compute_query)
            compute_result = cursor.fetchone()
            
            # Query for storage costs
            storage_query = f"""
            SELECT 
                AVG(STORAGE_BYTES) / POWER(1024, 3) as avg_storage_gb,
                AVG(STAGE_BYTES) / POWER(1024, 3) as avg_stage_gb,
                AVG(FAILSAFE_BYTES) / POWER(1024, 3) as avg_failsafe_gb
            FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE 
            WHERE USAGE_DATE >= '{start_date}'
            AND USAGE_DATE < '{end_date}'
            """
            
            cursor.execute(storage_query)
            storage_result = cursor.fetchone()
            
            # Estimate costs (approximate rates)
            compute_credits = float(compute_result[0]) if compute_result[0] else 0
            estimated_compute_cost = compute_credits * 2.0  # Approximate $2 per credit
            
            storage_gb = float(storage_result[0]) if storage_result[0] else 0
            stage_gb = float(storage_result[1]) if storage_result[1] else 0
            failsafe_gb = float(storage_result[2]) if storage_result[2] else 0
            
            # Approximate storage costs per GB per month
            estimated_storage_cost = (storage_gb * 0.023) + (stage_gb * 0.023) + (failsafe_gb * 0.023)
            estimated_storage_cost = estimated_storage_cost * (days / 30)  # Adjust for period
            
            total_estimated_cost = estimated_compute_cost + estimated_storage_cost
            
            cursor.close()
            
            return {
                'success': True,
                'period_days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'compute_metrics': {
                    'total_credits_used': round(compute_credits, 2),
                    'estimated_compute_cost': round(estimated_compute_cost, 2),
                    'warehouses_used': int(compute_result[1]) if compute_result[1] else 0,
                    'total_queries': int(compute_result[2]) if compute_result[2] else 0
                },
                'storage_metrics': {
                    'avg_storage_gb': round(storage_gb, 2),
                    'avg_stage_gb': round(stage_gb, 2),
                    'avg_failsafe_gb': round(failsafe_gb, 2),
                    'estimated_storage_cost': round(estimated_storage_cost, 2)
                },
                'total_estimated_cost': round(total_estimated_cost, 2),
                'currency': 'USD',
                'note': 'Costs are estimated based on standard Snowflake pricing. Actual costs may vary based on your contract.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve cost data. Ensure you have access to ACCOUNT_USAGE views.'
            }
    
    def get_top_warehouses_by_cost(self, days: int = 30, limit: int = 5) -> Dict[str, Any]:
        """Get top warehouses by cost/credit usage"""
        if not self.connection:
            return {
                'success': False,
                'error': 'Not connected to Snowflake. Please connect first.'
            }
        
        try:
            cursor = self.connection.cursor()
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Query for warehouse costs
            warehouse_query = f"""
            SELECT 
                WAREHOUSE_NAME,
                SUM(CREDITS_USED) as total_credits,
                COUNT(*) as query_count,
                AVG(CREDITS_USED) as avg_credits_per_query,
                MAX(CREDITS_USED) as max_credits_single_query,
                MIN(START_TIME) as first_usage,
                MAX(END_TIME) as last_usage
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY 
            WHERE START_TIME >= '{start_date}'
            AND START_TIME < '{end_date}'
            AND WAREHOUSE_NAME IS NOT NULL
            GROUP BY WAREHOUSE_NAME
            ORDER BY total_credits DESC
            LIMIT {limit}
            """
            
            cursor.execute(warehouse_query)
            results = cursor.fetchall()
            
            warehouses = []
            total_credits_all_warehouses = 0
            
            for row in results:
                warehouse_name = row[0]
                total_credits = float(row[1]) if row[1] else 0
                query_count = int(row[2]) if row[2] else 0
                avg_credits = float(row[3]) if row[3] else 0
                max_credits = float(row[4]) if row[4] else 0
                first_usage = row[5]
                last_usage = row[6]
                
                estimated_cost = total_credits * 2.0  # Approximate $2 per credit
                total_credits_all_warehouses += total_credits
                
                warehouses.append({
                    'warehouse_name': warehouse_name,
                    'total_credits': round(total_credits, 2),
                    'estimated_cost': round(estimated_cost, 2),
                    'query_count': query_count,
                    'avg_credits_per_query': round(avg_credits, 4),
                    'max_credits_single_query': round(max_credits, 4),
                    'first_usage': first_usage.isoformat() if first_usage else None,
                    'last_usage': last_usage.isoformat() if last_usage else None,
                    'percentage_of_total': 0  # Will calculate after loop
                })
            
            # Calculate percentages
            for warehouse in warehouses:
                if total_credits_all_warehouses > 0:
                    warehouse['percentage_of_total'] = round(
                        (warehouse['total_credits'] / total_credits_all_warehouses) * 100, 1
                    )
            
            cursor.close()
            
            return {
                'success': True,
                'period_days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_warehouses_analyzed': len(warehouses),
                'total_credits_top_warehouses': round(total_credits_all_warehouses, 2),
                'estimated_total_cost': round(total_credits_all_warehouses * 2.0, 2),
                'top_warehouses': warehouses
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve warehouse data. Ensure you have access to ACCOUNT_USAGE views.'
            }
    
    def get_snowflake_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive Snowflake cost summary"""
        try:
            overall_costs = self.get_overall_costs(days)
            top_warehouses = self.get_top_warehouses_by_cost(days)
            
            if not overall_costs['success'] or not top_warehouses['success']:
                return {
                    'success': False,
                    'error': 'Failed to retrieve complete Snowflake data',
                    'overall_costs_error': overall_costs.get('error') if not overall_costs['success'] else None,
                    'warehouses_error': top_warehouses.get('error') if not top_warehouses['success'] else None
                }
            
            return {
                'success': True,
                'analysis_date': datetime.now().isoformat(),
                'period_days': days,
                'overall_costs': overall_costs,
                'top_warehouses': top_warehouses,
                'summary': {
                    'total_estimated_cost': overall_costs['total_estimated_cost'],
                    'compute_cost': overall_costs['compute_metrics']['estimated_compute_cost'],
                    'storage_cost': overall_costs['storage_metrics']['estimated_storage_cost'],
                    'most_expensive_warehouse': top_warehouses['top_warehouses'][0]['warehouse_name'] if top_warehouses['top_warehouses'] else None,
                    'total_warehouses_used': overall_costs['compute_metrics']['warehouses_used']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def close_connection(self):
        """Close Snowflake connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

def format_snowflake_report(analysis_result: Dict[str, Any]) -> str:
    """Format Snowflake analysis into a readable report"""
    if not analysis_result['success']:
        return f"❌ Snowflake analysis failed: {analysis_result.get('error', 'Unknown error')}"
    
    report = []
    report.append("❄️ SNOWFLAKE COST ANALYSIS REPORT")
    report.append("=" * 50)
    report.append(f"📅 Analysis Date: {analysis_result['analysis_date'][:19]}")
    report.append(f"📊 Period: Last {analysis_result['period_days']} days")
    report.append(f"💰 Total Estimated Cost: ${analysis_result['summary']['total_estimated_cost']}")
    report.append("")
    
    # Overall costs breakdown
    overall = analysis_result['overall_costs']
    report.append("💻 COMPUTE COSTS")
    report.append("-" * 30)
    report.append(f"Credits Used: {overall['compute_metrics']['total_credits_used']}")
    report.append(f"Estimated Cost: ${overall['compute_metrics']['estimated_compute_cost']}")
    report.append(f"Warehouses Used: {overall['compute_metrics']['warehouses_used']}")
    report.append(f"Total Queries: {overall['compute_metrics']['total_queries']}")
    report.append("")
    
    report.append("💾 STORAGE COSTS")
    report.append("-" * 30)
    report.append(f"Avg Storage: {overall['storage_metrics']['avg_storage_gb']} GB")
    report.append(f"Avg Stage: {overall['storage_metrics']['avg_stage_gb']} GB")
    report.append(f"Estimated Cost: ${overall['storage_metrics']['estimated_storage_cost']}")
    report.append("")
    
    # Top warehouses
    warehouses = analysis_result['top_warehouses']
    report.append("🏭 TOP 5 WAREHOUSES BY COST")
    report.append("-" * 40)
    
    for i, warehouse in enumerate(warehouses['top_warehouses'], 1):
        report.append(f"{i}. {warehouse['warehouse_name']}")
        report.append(f"   💰 Cost: ${warehouse['estimated_cost']} ({warehouse['percentage_of_total']}%)")
        report.append(f"   🔄 Credits: {warehouse['total_credits']}")
        report.append(f"   📊 Queries: {warehouse['query_count']}")
        report.append("")
    
    report.append("📝 Note: Costs are estimated based on standard Snowflake pricing.")
    report.append("Actual costs may vary based on your contract and region.")
    
    return "\n".join(report)

# For testing
if __name__ == "__main__":
    analyzer = SnowflakeCostAnalyzer()
    
    print("❄️ Snowflake Cost Analyzer Test")
    print("=" * 40)
    print("This is a test of the Snowflake cost analyzer.")
    print("To use it, you need to:")
    print("1. Have a Snowflake account")
    print("2. Configure SSO or provide credentials")
    print("3. Have access to ACCOUNT_USAGE views")
    print("\nExample usage:")
    print("analyzer.connect_with_sso('your_account', 'your_username')")
    print("result = analyzer.get_snowflake_summary(30)")
    print("print(format_snowflake_report(result))") 