#!/usr/bin/env python3
"""
AWS Cost Analyzer
-----------------
Analyzes AWS costs across multiple profiles and accounts.
"""
import os
import sys
import boto3
import configparser
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

class AWSCostAnalyzer:
    """AWS Cost Analysis Tool"""
    
    def __init__(self):
        self.aws_config_path = Path.home() / ".aws" / "config"
        self.aws_credentials_path = Path.home() / ".aws" / "credentials"
        self.profiles = {}
        
    def discover_aws_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Discover AWS profiles from config and credentials files"""
        profiles = {}
        
        # Read AWS config file
        if self.aws_config_path.exists():
            config = configparser.ConfigParser()
            config.read(self.aws_config_path)
            
            for section in config.sections():
                if section.startswith('profile '):
                    profile_name = section.replace('profile ', '')
                    profiles[profile_name] = {
                        'region': config.get(section, 'region', fallback='us-east-1'),
                        'output': config.get(section, 'output', fallback='json'),
                        'source': 'config'
                    }
                elif section == 'default':
                    profiles['default'] = {
                        'region': config.get(section, 'region', fallback='us-east-1'),
                        'output': config.get(section, 'output', fallback='json'),
                        'source': 'config'
                    }
        
        # Read AWS credentials file
        if self.aws_credentials_path.exists():
            creds = configparser.ConfigParser()
            creds.read(self.aws_credentials_path)
            
            for section in creds.sections():
                if section not in profiles:
                    profiles[section] = {
                        'region': 'us-east-1',  # Default region
                        'output': 'json',
                        'source': 'credentials'
                    }
                
                # Add credential info
                if creds.has_option(section, 'aws_access_key_id'):
                    profiles[section]['has_credentials'] = True
                    profiles[section]['access_key_id'] = creds.get(section, 'aws_access_key_id')[:8] + "..."
                
                if creds.has_option(section, 'role_arn'):
                    profiles[section]['role_arn'] = creds.get(section, 'role_arn')
                
                if creds.has_option(section, 'source_profile'):
                    profiles[section]['source_profile'] = creds.get(section, 'source_profile')
        
        self.profiles = profiles
        return profiles
    
    def get_cost_and_usage(self, profile_name: str, days: int = 30) -> Dict[str, Any]:
        """Get cost and usage data for a specific profile"""
        try:
            # Create session for the profile
            session = boto3.Session(profile_name=profile_name)
            
            # Get account ID
            sts_client = session.client('sts')
            account_info = sts_client.get_caller_identity()
            account_id = account_info['Account']
            
            # Create Cost Explorer client (always in us-east-1)
            ce_client = session.client('ce', region_name='us-east-1')
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get cost and usage by service
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            # Process the response
            services_cost = []
            total_cost = 0
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    cost_amount = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if cost_amount > 0:  # Only include services with actual costs
                        services_cost.append({
                            'service': service_name,
                            'cost': cost_amount,
                            'currency': group['Metrics']['BlendedCost']['Unit']
                        })
                        total_cost += cost_amount
            
            # Sort by cost (descending) and get top 5
            services_cost.sort(key=lambda x: x['cost'], reverse=True)
            top_5_services = services_cost[:5]
            
            return {
                'success': True,
                'profile': profile_name,
                'account_id': account_id,
                'region': session.region_name,
                'period_days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_cost': round(total_cost, 2),
                'currency': 'USD',
                'top_5_services': [
                    {
                        'service': service['service'],
                        'cost': round(service['cost'], 2),
                        'percentage': round((service['cost'] / total_cost * 100), 1) if total_cost > 0 else 0
                    }
                    for service in top_5_services
                ],
                'total_services': len(services_cost)
            }
            
        except Exception as e:
            return {
                'success': False,
                'profile': profile_name,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def analyze_all_profiles(self, days: int = 30) -> Dict[str, Any]:
        """Analyze costs for all discovered AWS profiles"""
        profiles = self.discover_aws_profiles()
        
        if not profiles:
            return {
                'success': False,
                'error': 'No AWS profiles found',
                'message': 'Please configure AWS credentials using "aws configure" or manually create ~/.aws/credentials'
            }
        
        results = {
            'success': True,
            'analysis_date': datetime.now().isoformat(),
            'period_days': days,
            'total_profiles': len(profiles),
            'profiles_analyzed': 0,
            'profiles_successful': 0,
            'profiles_failed': 0,
            'total_cost_all_accounts': 0,
            'currency': 'USD',
            'profiles': {},
            'summary': {
                'top_5_services_across_all_accounts': [],
                'most_expensive_account': None,
                'total_accounts_with_costs': 0
            }
        }
        
        all_services_cost = {}
        account_costs = []
        
        for profile_name in profiles:
            print(f"Analyzing profile: {profile_name}...", file=sys.stderr)
            
            profile_result = self.get_cost_and_usage(profile_name, days)
            results['profiles'][profile_name] = profile_result
            results['profiles_analyzed'] += 1
            
            if profile_result['success']:
                results['profiles_successful'] += 1
                total_cost = profile_result['total_cost']
                results['total_cost_all_accounts'] += total_cost
                
                if total_cost > 0:
                    results['summary']['total_accounts_with_costs'] += 1
                    account_costs.append({
                        'profile': profile_name,
                        'account_id': profile_result['account_id'],
                        'cost': total_cost
                    })
                
                # Aggregate services across all accounts
                for service in profile_result['top_5_services']:
                    service_name = service['service']
                    if service_name not in all_services_cost:
                        all_services_cost[service_name] = 0
                    all_services_cost[service_name] += service['cost']
            else:
                results['profiles_failed'] += 1
        
        # Calculate summary statistics
        if all_services_cost:
            # Top 5 services across all accounts
            sorted_services = sorted(all_services_cost.items(), key=lambda x: x[1], reverse=True)[:5]
            total_all_accounts = results['total_cost_all_accounts']
            
            results['summary']['top_5_services_across_all_accounts'] = [
                {
                    'service': service_name,
                    'cost': round(cost, 2),
                    'percentage': round((cost / total_all_accounts * 100), 1) if total_all_accounts > 0 else 0
                }
                for service_name, cost in sorted_services
            ]
        
        # Most expensive account
        if account_costs:
            most_expensive = max(account_costs, key=lambda x: x['cost'])
            results['summary']['most_expensive_account'] = most_expensive
        
        results['total_cost_all_accounts'] = round(results['total_cost_all_accounts'], 2)
        
        return results

def format_cost_analysis_report(analysis_result: Dict[str, Any]) -> str:
    """Format the analysis result into a readable report"""
    if not analysis_result['success']:
        return f"❌ Analysis failed: {analysis_result.get('error', 'Unknown error')}"
    
    report = []
    report.append("🏦 AWS COST ANALYSIS REPORT")
    report.append("=" * 50)
    report.append(f"📅 Analysis Date: {analysis_result['analysis_date'][:19]}")
    report.append(f"📊 Period: Last {analysis_result['period_days']} days")
    report.append(f"👥 Total Profiles: {analysis_result['total_profiles']}")
    report.append(f"✅ Successful: {analysis_result['profiles_successful']}")
    report.append(f"❌ Failed: {analysis_result['profiles_failed']}")
    report.append(f"💰 Total Cost (All Accounts): ${analysis_result['total_cost_all_accounts']}")
    report.append("")
    
    # Summary across all accounts
    summary = analysis_result['summary']
    if summary['top_5_services_across_all_accounts']:
        report.append("🌟 TOP 5 SERVICES (ALL ACCOUNTS)")
        report.append("-" * 40)
        for i, service in enumerate(summary['top_5_services_across_all_accounts'], 1):
            report.append(f"{i}. {service['service']}")
            report.append(f"   💰 ${service['cost']} ({service['percentage']}%)")
        report.append("")
    
    # Most expensive account
    if summary['most_expensive_account']:
        expensive = summary['most_expensive_account']
        report.append("💸 MOST EXPENSIVE ACCOUNT")
        report.append("-" * 30)
        report.append(f"Profile: {expensive['profile']}")
        report.append(f"Account ID: {expensive['account_id']}")
        report.append(f"Cost: ${expensive['cost']}")
        report.append("")
    
    # Individual profile details
    report.append("📋 INDIVIDUAL PROFILE DETAILS")
    report.append("-" * 40)
    
    for profile_name, profile_data in analysis_result['profiles'].items():
        if profile_data['success']:
            report.append(f"🔹 {profile_name} (Account: {profile_data['account_id']})")
            report.append(f"   Region: {profile_data['region']}")
            report.append(f"   Total Cost: ${profile_data['total_cost']}")
            report.append(f"   Services: {profile_data['total_services']}")
            
            if profile_data['top_5_services']:
                report.append("   Top 5 Services:")
                for i, service in enumerate(profile_data['top_5_services'], 1):
                    report.append(f"     {i}. {service['service']}: ${service['cost']} ({service['percentage']}%)")
            report.append("")
        else:
            report.append(f"❌ {profile_name}: {profile_data['error']}")
            report.append("")
    
    return "\n".join(report)

# For testing
if __name__ == "__main__":
    import sys
    analyzer = AWSCostAnalyzer()
    
    print("🔍 Discovering AWS profiles...")
    profiles = analyzer.discover_aws_profiles()
    print(f"Found {len(profiles)} profiles: {list(profiles.keys())}")
    
    print("\n📊 Analyzing costs...")
    result = analyzer.analyze_all_profiles(days=30)
    
    print("\n" + format_cost_analysis_report(result)) 