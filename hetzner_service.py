import os
import logging
from datetime import datetime
from hcloud import Client
from hcloud.images import Image
from hcloud.server_types import ServerType
from hcloud.locations import Location
from models import HetznerServer
from app import db

class HetznerService:
    def __init__(self):
        api_token = os.environ.get('HETZNER_API_TOKEN')
        if not api_token:
            raise ValueError("HETZNER_API_TOKEN environment variable is required")
        
        self.client = Client(token=api_token)
        self.logger = logging.getLogger(__name__)
    
    def sync_servers_from_hetzner(self):
        """Sync servers from Hetzner Cloud API to local database"""
        try:
            # Get all servers from Hetzner
            hetzner_servers = self.client.servers.get_all()
            self.logger.info(f"Found {len(hetzner_servers)} servers in Hetzner Cloud")
            
            synced_count = 0
            updated_count = 0
            
            for hetzner_server in hetzner_servers:
                # Check if server exists in our database
                local_server = HetznerServer.query.filter_by(hetzner_id=hetzner_server.id).first()
                
                if local_server:
                    # Update existing server
                    updated = self._update_server_from_hetzner(local_server, hetzner_server)
                    if updated:
                        updated_count += 1
                else:
                    # Create new server record
                    self._create_server_from_hetzner(hetzner_server)
                    synced_count += 1
            
            db.session.commit()
            self.logger.info(f"Sync completed: {synced_count} new servers, {updated_count} updated")
            
            return {
                'success': True,
                'synced': synced_count,
                'updated': updated_count,
                'total': len(hetzner_servers)
            }
            
        except Exception as e:
            self.logger.error(f"Error syncing servers: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_server_from_hetzner(self, hetzner_server):
        """Create a new HetznerServer record from Hetzner API data"""
        server = HetznerServer()
        server.hetzner_id = hetzner_server.id
        server.name = hetzner_server.name
        server.status = hetzner_server.status
        server.server_type = hetzner_server.server_type.name
        server.image = hetzner_server.image.name if hetzner_server.image else "unknown"
        
        # Network information
        server.public_ip = hetzner_server.public_net.ipv4.ip if hetzner_server.public_net.ipv4 else None
        server.ipv6 = hetzner_server.public_net.ipv6.ip if hetzner_server.public_net.ipv6 else None
        
        # Private networks
        if hetzner_server.private_net:
            server.private_ip = hetzner_server.private_net[0].ip if hetzner_server.private_net else None
        
        # Location and datacenter
        server.datacenter = hetzner_server.datacenter.name if hetzner_server.datacenter else None
        server.location = hetzner_server.datacenter.location.name if hetzner_server.datacenter and hetzner_server.datacenter.location else None
        
        # Specifications
        server.cpu_cores = hetzner_server.server_type.cores
        server.memory_gb = hetzner_server.server_type.memory
        server.disk_gb = hetzner_server.server_type.disk
        
        server.last_synced = datetime.utcnow()
        
        db.session.add(server)
        self.logger.info(f"Created new server record: {server.name}")
    
    def _update_server_from_hetzner(self, local_server, hetzner_server):
        """Update existing HetznerServer record with fresh data from Hetzner API"""
        updated = False
        
        # Check for changes and update
        if local_server.status != hetzner_server.status:
            local_server.status = hetzner_server.status
            updated = True
        
        if local_server.name != hetzner_server.name:
            local_server.name = hetzner_server.name
            updated = True
        
        # Update IP addresses
        new_public_ip = hetzner_server.public_net.ipv4.ip if hetzner_server.public_net.ipv4 else None
        if local_server.public_ip != new_public_ip:
            local_server.public_ip = new_public_ip
            updated = True
        
        new_ipv6 = hetzner_server.public_net.ipv6.ip if hetzner_server.public_net.ipv6 else None
        if local_server.ipv6 != new_ipv6:
            local_server.ipv6 = new_ipv6
            updated = True
        
        if updated:
            local_server.last_synced = datetime.utcnow()
            self.logger.info(f"Updated server record: {local_server.name}")
        
        return updated
    
    def get_server_info(self, hetzner_id):
        """Get detailed information about a specific server"""
        try:
            server = self.client.servers.get_by_id(hetzner_id)
            if not server:
                return None
            
            return {
                'id': server.id,
                'name': server.name,
                'status': server.status,
                'server_type': server.server_type.name,
                'image': server.image.name if server.image else "unknown",
                'public_ip': server.public_net.ipv4.ip if server.public_net.ipv4 else None,
                'ipv6': server.public_net.ipv6.ip if server.public_net.ipv6 else None,
                'private_ip': server.private_net[0].ip if server.private_net else None,
                'datacenter': server.datacenter.name if server.datacenter else None,
                'location': server.datacenter.location.name if server.datacenter and server.datacenter.location else None,
                'cpu_cores': server.server_type.cores,
                'memory_gb': server.server_type.memory,
                'disk_gb': server.server_type.disk,
                'created': server.created,
                'labels': server.labels
            }
            
        except Exception as e:
            self.logger.error(f"Error getting server info for ID {hetzner_id}: {str(e)}")
            return None
    
    def get_server_metrics(self, hetzner_id):
        """Get server metrics (CPU, memory, disk usage)"""
        try:
            server = self.client.servers.get_by_id(hetzner_id)
            if not server:
                return None
            
            # Get metrics from Hetzner (this is a simplified version)
            # In a real implementation, you'd use the metrics API
            metrics = self.client.servers.get_metrics(
                server=server,
                type=['cpu', 'memory', 'disk'],
                start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                end=datetime.utcnow()
            )
            
            return {
                'cpu': metrics.time_series.get('cpu', []),
                'memory': metrics.time_series.get('memory', []),
                'disk': metrics.time_series.get('disk', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting server metrics for ID {hetzner_id}: {str(e)}")
            return None
    
    def start_server(self, hetzner_id):
        """Start a server"""
        try:
            server = self.client.servers.get_by_id(hetzner_id)
            if server:
                action = self.client.servers.power_on(server)
                return {'success': True, 'action_id': action.id}
            return {'success': False, 'error': 'Server not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_server(self, hetzner_id):
        """Stop a server"""
        try:
            server = self.client.servers.get_by_id(hetzner_id)
            if server:
                action = self.client.servers.power_off(server)
                return {'success': True, 'action_id': action.id}
            return {'success': False, 'error': 'Server not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reboot_server(self, hetzner_id):
        """Reboot a server"""
        try:
            server = self.client.servers.get_by_id(hetzner_id)
            if server:
                action = self.client.servers.reboot(server)
                return {'success': True, 'action_id': action.id}
            return {'success': False, 'error': 'Server not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_available_images(self):
        """Get list of available images for server creation"""
        try:
            images = self.client.images.get_all()
            return [
                {
                    'id': img.id,
                    'name': img.name,
                    'description': img.description,
                    'os_flavor': img.os_flavor,
                    'os_version': img.os_version,
                    'type': img.type
                }
                for img in images if img.type == 'system'
            ]
        except Exception as e:
            self.logger.error(f"Error getting available images: {str(e)}")
            return []
    
    def get_available_server_types(self):
        """Get list of available server types"""
        try:
            server_types = self.client.server_types.get_all()
            return [
                {
                    'id': st.id,
                    'name': st.name,
                    'description': st.description,
                    'cores': st.cores,
                    'memory': st.memory,
                    'disk': st.disk,
                    'prices': st.prices
                }
                for st in server_types
            ]
        except Exception as e:
            self.logger.error(f"Error getting available server types: {str(e)}")
            return []
    
    def get_available_locations(self):
        """Get list of available locations"""
        try:
            locations = self.client.locations.get_all()
            return [
                {
                    'id': loc.id,
                    'name': loc.name,
                    'description': loc.description,
                    'country': loc.country,
                    'city': loc.city
                }
                for loc in locations
            ]
        except Exception as e:
            self.logger.error(f"Error getting available locations: {str(e)}")
            return []