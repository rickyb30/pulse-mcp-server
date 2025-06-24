#!/usr/bin/env python3
"""
Databricks Cost Analyzer
------------------------
Monitors Databricks costs and cluster usage with SSO support.
"""
import sys
import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import base64

class DatabricksCostAnalyzer:
    """Databricks Cost Analysis Tool"""
    
    def __init__(self):
        self.workspace_url = None
        self.headers = None
        self.session = requests.Session()
        
    def connect_with_sso(self, workspace_url: str, personal_access_token: str = None) -> Dict[str, Any]:
        """Connect to Databricks using SSO/Personal Access Token
        
        Args:
            workspace_url: Databricks workspace URL (e.g., https://dbc-12345678-abcd.cloud.databricks.com)
            personal_access_token: Optional PAT token for API access
        """
        try:
            # Normalize workspace URL
            if not workspace_url.startswith('https://'):
                workspace_url = f'https://{workspace_url}'
            
            parsed_url = urlparse(workspace_url)
            self.workspace_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # For SSO, we'll use PAT token if provided, otherwise guide user to get one
            if personal_access_token:
                self.headers = {
                    'Authorization': f'Bearer {personal_access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Test connection with a simple API call
                test_response = self.session.get(
                    f"{self.workspace_url}/api/2.0/clusters/list",
                    headers=self.headers,
                    timeout=30
                )
                
                if test_response.status_code == 200:
                    return {
                        'success': True,
                        'message': f'Successfully connected to Databricks workspace: {self.workspace_url}',
                        'workspace_url': self.workspace_url,
                        'method': 'sso_with_token'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Authentication failed: {test_response.status_code}',
                        'message': 'Invalid token or insufficient permissions.'
                    }
            else:
                # Guide user to SSO setup
                return {
                    'success': False,
                    'requires_token': True,
                    'workspace_url': self.workspace_url,
                    'message': 'To use SSO with Databricks, you need a Personal Access Token.',
                    'instructions': [
                        f"1. Go to {self.workspace_url}/",
                        "2. Click on your user icon in the top-right corner",
                        "3. Select 'User Settings'",
                        "4. Go to 'Access tokens' tab",
                        "5. Click 'Generate new token'",
                        "6. Set expiration and click 'Generate'",
                        "7. Copy the token and use it in the connection"
                    ]
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to connect to Databricks. Check your workspace URL and token.'
            }
    
    def connect_with_credentials(self, workspace_url: str, username: str, password: str) -> Dict[str, Any]:
        """Connect to Databricks using username/password (legacy method)
        
        Note: This method is deprecated in favor of SSO/PAT tokens
        """
        return {
            'success': False,
            'error': 'Username/password authentication is deprecated',
            'message': 'Please use SSO with Personal Access Token instead. Use connect_with_sso method.'
        }
    
    def get_overall_costs(self, days: int = 30) -> Dict[str, Any]:
        """Get overall Databricks costs for the specified period"""
        if not self.workspace_url or not self.headers:
            return {
                'success': False,
                'error': 'Not connected to Databricks. Please connect first.'
            }
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get cluster information
            clusters_response = self.session.get(
                f"{self.workspace_url}/api/2.0/clusters/list",
                headers=self.headers,
                timeout=30
            )
            
            if clusters_response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to fetch clusters: {clusters_response.status_code}',
                    'message': 'Unable to retrieve cluster information.'
                }
            
            clusters_data = clusters_response.json()
            clusters = clusters_data.get('clusters', [])
            
            # Get jobs information
            jobs_response = self.session.get(
                f"{self.workspace_url}/api/2.1/jobs/list",
                headers=self.headers,
                params={'limit': 100, 'expand_tasks': False},
                timeout=30
            )
            
            jobs_data = jobs_response.json() if jobs_response.status_code == 200 else {}
            jobs = jobs_data.get('jobs', [])
            
            # Calculate estimated costs based on cluster configurations
            total_estimated_cost = 0
            cluster_costs = []
            
            for cluster in clusters:
                # Get cluster configuration
                node_type = cluster.get('node_type_id', 'unknown')
                num_workers = cluster.get('num_workers', 0)
                driver_node = cluster.get('driver_node_type_id', node_type)
                
                # Estimate hourly cost based on node types (approximate AWS pricing)
                node_cost_map = {
                    'i3.xlarge': 0.312,
                    'i3.2xlarge': 0.624,
                    'i3.4xlarge': 1.248,
                    'i3.8xlarge': 2.496,
                    'm5.large': 0.096,
                    'm5.xlarge': 0.192,
                    'm5.2xlarge': 0.384,
                    'm5.4xlarge': 0.768,
                    'r5.large': 0.126,
                    'r5.xlarge': 0.252,
                    'r5.2xlarge': 0.504,
                    'unknown': 0.2  # Default estimate
                }
                
                # Estimate based on node type
                worker_cost_per_hour = node_cost_map.get(node_type, 0.2)
                driver_cost_per_hour = node_cost_map.get(driver_node, 0.2)
                
                # Assume cluster runs 8 hours per day on average
                estimated_daily_cost = (num_workers * worker_cost_per_hour + driver_cost_per_hour) * 8
                estimated_period_cost = estimated_daily_cost * days
                
                cluster_info = {
                    'cluster_id': cluster.get('cluster_id'),
                    'cluster_name': cluster.get('cluster_name', 'Unnamed'),
                    'state': cluster.get('state', 'UNKNOWN'),
                    'node_type': node_type,
                    'num_workers': num_workers,
                    'driver_node_type': driver_node,
                    'estimated_daily_cost': round(estimated_daily_cost, 2),
                    'estimated_period_cost': round(estimated_period_cost, 2)
                }
                
                cluster_costs.append(cluster_info)
                total_estimated_cost += estimated_period_cost
            
            return {
                'success': True,
                'period_days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'workspace_url': self.workspace_url,
                'summary': {
                    'total_clusters': len(clusters),
                    'active_clusters': len([c for c in clusters if c.get('state') == 'RUNNING']),
                    'total_jobs': len(jobs),
                    'estimated_total_cost': round(total_estimated_cost, 2)
                },
                'cluster_details': cluster_costs,
                'currency': 'USD',
                'note': 'Costs are estimated based on AWS instance pricing and assumed 8 hours daily usage. Actual costs may vary based on actual usage, Databricks units pricing, and your contract.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve cost data. Ensure you have proper permissions to access cluster and job information.'
            }
    
    def get_top_clusters_by_cost(self, days: int = 30, limit: int = 5) -> Dict[str, Any]:
        """Get top clusters by estimated cost"""
        if not self.workspace_url or not self.headers:
            return {
                'success': False,
                'error': 'Not connected to Databricks. Please connect first.'
            }
        
        try:
            # Get overall costs first
            overall_costs = self.get_overall_costs(days)
            
            if not overall_costs.get('success'):
                return overall_costs
            
            # Sort clusters by estimated cost
            cluster_details = overall_costs.get('cluster_details', [])
            top_clusters = sorted(cluster_details, key=lambda x: x.get('estimated_period_cost', 0), reverse=True)[:limit]
            
            return {
                'success': True,
                'period_days': days,
                'workspace_url': self.workspace_url,
                'top_clusters': top_clusters,
                'total_clusters_analyzed': len(cluster_details),
                'note': 'Rankings based on estimated costs. Actual usage may differ.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to analyze cluster costs.'
            }
    
    def get_workspace_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive workspace summary"""
        if not self.workspace_url or not self.headers:
            return {
                'success': False,
                'error': 'Not connected to Databricks. Please connect first.'
            }
        
        try:
            # Get overall costs
            cost_data = self.get_overall_costs(days)
            
            if not cost_data.get('success'):
                return cost_data
            
            # Get additional workspace information
            try:
                # Get workspace info (if available)
                workspace_response = self.session.get(
                    f"{self.workspace_url}/api/2.0/workspace/list",
                    headers=self.headers,
                    params={'path': '/'},
                    timeout=30
                )
                
                workspace_objects = 0
                if workspace_response.status_code == 200:
                    workspace_data = workspace_response.json()
                    workspace_objects = len(workspace_data.get('objects', []))
                
            except:
                workspace_objects = 0
            
            summary = cost_data.get('summary', {})
            
            return {
                'success': True,
                'period_days': days,
                'workspace_url': self.workspace_url,
                'cost_summary': {
                    'estimated_total_cost': summary.get('estimated_total_cost', 0),
                    'total_clusters': summary.get('total_clusters', 0),
                    'active_clusters': summary.get('active_clusters', 0),
                    'average_cost_per_cluster': round(summary.get('estimated_total_cost', 0) / max(summary.get('total_clusters', 1), 1), 2)
                },
                'workspace_info': {
                    'total_jobs': summary.get('total_jobs', 0),
                    'workspace_objects': workspace_objects
                },
                'recommendations': self._generate_cost_recommendations(cost_data),
                'currency': 'USD'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate workspace summary.'
            }
    
    def _generate_cost_recommendations(self, cost_data: Dict[str, Any]) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        if not cost_data.get('success'):
            return recommendations
        
        summary = cost_data.get('summary', {})
        cluster_details = cost_data.get('cluster_details', [])
        
        # Check for idle clusters
        running_clusters = [c for c in cluster_details if c.get('state') == 'RUNNING']
        if len(running_clusters) > 3:
            recommendations.append("Consider consolidating workloads - you have multiple running clusters which may increase costs")
        
        # Check for large clusters
        expensive_clusters = [c for c in cluster_details if c.get('estimated_period_cost', 0) > 1000]
        if expensive_clusters:
            recommendations.append(f"Review {len(expensive_clusters)} high-cost clusters for optimization opportunities")
        
        # General recommendations
        recommendations.extend([
            "Enable auto-termination for interactive clusters to avoid idle costs",
            "Use job clusters instead of interactive clusters for scheduled workloads",
            "Consider using spot instances for fault-tolerant workloads",
            "Monitor cluster utilization and right-size based on actual usage"
        ])
        
        return recommendations
    
    def close_connection(self):
        """Close the connection"""
        if self.session:
            self.session.close()
        self.workspace_url = None
        self.headers = None

def format_databricks_report(analysis_result: Dict[str, Any]) -> str:
    """Format Databricks analysis result into a readable report"""
    if not analysis_result.get('success'):
        return f"❌ Error: {analysis_result.get('error', 'Unknown error')}"
    
    report = []
    report.append("🧱 DATABRICKS COST ANALYSIS REPORT")
    report.append("=" * 50)
    
    # Basic info
    if 'workspace_url' in analysis_result:
        report.append(f"Workspace: {analysis_result['workspace_url']}")
    
    if 'period_days' in analysis_result:
        report.append(f"Analysis Period: {analysis_result['period_days']} days")
        report.append(f"Date Range: {analysis_result.get('start_date', 'N/A')} to {analysis_result.get('end_date', 'N/A')}")
    
    report.append("")
    
    # Cost summary
    if 'summary' in analysis_result or 'cost_summary' in analysis_result:
        summary = analysis_result.get('summary', analysis_result.get('cost_summary', {}))
        report.append("💰 COST SUMMARY")
        report.append("-" * 20)
        report.append(f"Estimated Total Cost: ${summary.get('estimated_total_cost', 0):.2f}")
        report.append(f"Total Clusters: {summary.get('total_clusters', 0)}")
        report.append(f"Active Clusters: {summary.get('active_clusters', 0)}")
        
        if 'average_cost_per_cluster' in summary:
            report.append(f"Average Cost per Cluster: ${summary.get('average_cost_per_cluster', 0):.2f}")
        
        report.append("")
    
    # Cluster details
    if 'cluster_details' in analysis_result:
        clusters = analysis_result['cluster_details'][:5]  # Top 5
        if clusters:
            report.append("🖥️ TOP CLUSTERS BY COST")
            report.append("-" * 25)
            for i, cluster in enumerate(clusters, 1):
                report.append(f"{i}. {cluster.get('cluster_name', 'Unnamed')} (${cluster.get('estimated_period_cost', 0):.2f})")
                report.append(f"   State: {cluster.get('state', 'UNKNOWN')}")
                report.append(f"   Workers: {cluster.get('num_workers', 0)} x {cluster.get('node_type', 'unknown')}")
                if i < len(clusters):
                    report.append("")
        report.append("")
    
    # Top clusters (if separate)
    if 'top_clusters' in analysis_result:
        clusters = analysis_result['top_clusters'][:5]
        if clusters:
            report.append("🏆 TOP CLUSTERS BY COST")
            report.append("-" * 25)
            for i, cluster in enumerate(clusters, 1):
                report.append(f"{i}. {cluster.get('cluster_name', 'Unnamed')} (${cluster.get('estimated_period_cost', 0):.2f})")
                report.append(f"   State: {cluster.get('state', 'UNKNOWN')}")
                if i < len(clusters):
                    report.append("")
        report.append("")
    
    # Recommendations
    if 'recommendations' in analysis_result:
        recommendations = analysis_result['recommendations']
        if recommendations:
            report.append("💡 COST OPTIMIZATION RECOMMENDATIONS")
            report.append("-" * 35)
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
            report.append("")
    
    # Note
    if 'note' in analysis_result:
        report.append(f"📝 Note: {analysis_result['note']}")
    
    return "\n".join(report) 