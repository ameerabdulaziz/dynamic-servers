"""
GoDaddy DNS management service for automatic subdomain creation
"""
import requests
import os
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class GoDaddyService:
    """Service for managing DNS records via GoDaddy API"""
    
    def __init__(self):
        self.api_key = os.environ.get('GODADDY_API_KEY')
        self.api_secret = os.environ.get('GODADDY_API_SECRET')
        self.base_url = 'https://api.godaddy.com/v1'
        
        if not self.api_key or not self.api_secret:
            logger.warning("GoDaddy API credentials not found in environment variables")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GoDaddy API requests"""
        return {
            'Authorization': f'sso-key {self.api_key}:{self.api_secret}',
            'Content-Type': 'application/json'
        }
    
    def get_dns_records(self, domain: str, record_type: str = 'A') -> List[Dict]:
        """Get DNS records for a domain"""
        if not self.api_key:
            return []
            
        url = f"{self.base_url}/domains/{domain}/records/{record_type}"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching DNS records for {domain}: {e}")
            return []
    
    def add_dns_record(self, domain: str, subdomain: str, ip_address: str, record_type: str = 'A', ttl: int = 600) -> Dict:
        """Add a DNS A record for a subdomain"""
        if not self.api_key:
            return {'success': False, 'error': 'GoDaddy API credentials not configured'}
        
        url = f"{self.base_url}/domains/{domain}/records"
        
        # Prepare the DNS record data
        dns_record = {
            'type': record_type,
            'name': subdomain,
            'data': ip_address,
            'ttl': ttl
        }
        
        try:
            response = requests.patch(url, json=[dns_record], headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully added DNS record: {subdomain}.{domain} -> {ip_address}")
            return {
                'success': True,
                'record': dns_record,
                'message': f'DNS record created: {subdomain}.{domain} -> {ip_address}'
            }
            
        except requests.RequestException as e:
            error_msg = f"Error creating DNS record for {subdomain}.{domain}: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def update_dns_record(self, domain: str, subdomain: str, ip_address: str, record_type: str = 'A', ttl: int = 600) -> Dict:
        """Update an existing DNS record"""
        if not self.api_key:
            return {'success': False, 'error': 'GoDaddy API credentials not configured'}
        
        url = f"{self.base_url}/domains/{domain}/records/{record_type}/{subdomain}"
        
        dns_record = {
            'type': record_type,
            'name': subdomain,
            'data': ip_address,
            'ttl': ttl
        }
        
        try:
            response = requests.put(url, json=[dns_record], headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully updated DNS record: {subdomain}.{domain} -> {ip_address}")
            return {
                'success': True,
                'record': dns_record,
                'message': f'DNS record updated: {subdomain}.{domain} -> {ip_address}'
            }
            
        except requests.RequestException as e:
            error_msg = f"Error updating DNS record for {subdomain}.{domain}: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def delete_dns_record(self, domain: str, subdomain: str, record_type: str = 'A') -> Dict:
        """Delete a DNS record"""
        if not self.api_key:
            return {'success': False, 'error': 'GoDaddy API credentials not configured'}
        
        url = f"{self.base_url}/domains/{domain}/records/{record_type}/{subdomain}"
        
        try:
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully deleted DNS record: {subdomain}.{domain}")
            return {
                'success': True,
                'message': f'DNS record deleted: {subdomain}.{domain}'
            }
            
        except requests.RequestException as e:
            error_msg = f"Error deleting DNS record for {subdomain}.{domain}: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def check_domain_availability(self, domain: str) -> Dict:
        """Check if a domain is available for management"""
        if not self.api_key:
            return {'success': False, 'error': 'GoDaddy API credentials not configured'}
        
        url = f"{self.base_url}/domains/{domain}"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            if response.status_code == 200:
                domain_info = response.json()
                return {
                    'success': True,
                    'available': True,
                    'domain_info': domain_info
                }
            else:
                return {
                    'success': True,
                    'available': False,
                    'message': f'Domain {domain} not found or not accessible'
                }
                
        except requests.RequestException as e:
            error_msg = f"Error checking domain {domain}: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }