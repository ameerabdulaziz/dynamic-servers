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
    def __init__(self, project_id=None, api_token=None):
        self.project_id = project_id
        self.project = None
        
        # Get API token from project or environment
        if api_token:
            self.api_token = api_token
        elif project_id:
            from models import HetznerProject
            self.project = HetznerProject.query.get(project_id)
            if self.project and self.project.is_active:
                # If project token is 'USE_ENV_TOKEN', use environment variable
                if self.project.hetzner_api_token == 'USE_ENV_TOKEN':
                    self.api_token = os.environ.get('HETZNER_API_TOKEN')
                else:
                    self.api_token = self.project.hetzner_api_token
            else:
                raise ValueError(f"Project {project_id} not found or inactive")
        else:
            self.api_token = os.environ.get('HETZNER_API_TOKEN')
            
        if not self.api_token:
            raise ValueError("No API token available - check project configuration or HETZNER_API_TOKEN environment variable")
        
        self.client = Client(token=self.api_token)
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
    
    def create_server(self, name: str, server_type: str, image: str = 'ubuntu-22.04', location: str = 'nbg1', labels: dict = None):
        """Create a new server in Hetzner Cloud"""
        try:
            self.logger.info(f"Creating server: {name} ({server_type}) in {location}")
            
            # Get server type and image objects
            server_type_obj = ServerType(name=server_type)
            image_obj = Image(name=image)
            location_obj = Location(name=location)
            
            # Create server with labels
            server_labels = labels or {}
            if self.project_id:
                server_labels['project_id'] = str(self.project_id)
            
            # Create the server
            response = self.client.servers.create(
                name=name,
                server_type=server_type_obj,
                image=image_obj,
                location=location_obj,
                labels=server_labels
            )
            
            hetzner_server = response.server
            self.logger.info(f"Server created successfully: {hetzner_server.name} (ID: {hetzner_server.id})")
            
            # Wait for server to be ready and get IP
            self.client.servers.wait_until_ready(hetzner_server)
            
            # Refresh server data to get IP address
            hetzner_server = self.client.servers.get_by_id(hetzner_server.id)
            
            # Create local database entry
            local_server = self._create_server_from_hetzner(hetzner_server)
            db.session.commit()
            
            return {
                'success': True,
                'server': local_server,
                'hetzner_server': hetzner_server,
                'ip_address': hetzner_server.public_net.ipv4.ip if hetzner_server.public_net.ipv4 else None,
                'message': f'Server {name} created successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating server {name}: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_server(self, server_id: int):
        """Delete a server from Hetzner Cloud"""
        try:
            hetzner_server = self.client.servers.get_by_id(server_id)
            if hetzner_server:
                self.client.servers.delete(hetzner_server)
                self.logger.info(f"Server {hetzner_server.name} (ID: {server_id}) deleted from Hetzner Cloud")
                
                # Update local database
                local_server = HetznerServer.query.filter_by(hetzner_id=server_id).first()
                if local_server:
                    local_server.status = 'deleting'
                    local_server.last_synced = datetime.utcnow()
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': f'Server {hetzner_server.name} deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Server with ID {server_id} not found'
                }
                
        except Exception as e:
            self.logger.error(f"Error deleting server {server_id}: {str(e)}")
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
        
        # Get reverse DNS
        server.reverse_dns = self._get_reverse_dns(hetzner_server)
        
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
        
        # Assign to project if specified
        if self.project_id:
            server.project_id = self.project_id
        
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
        
        # Update reverse DNS
        new_reverse_dns = self._get_reverse_dns(hetzner_server)
        if local_server.reverse_dns != new_reverse_dns:
            local_server.reverse_dns = new_reverse_dns
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
    
    def get_server_current_status(self, hetzner_id):
        """Get the current status of a single server from Hetzner Cloud"""
        try:
            server = self.client.servers.get_by_id(hetzner_id)
            if server:
                return {'success': True, 'status': server.status}
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
    
    def _get_reverse_dns(self, hetzner_server):
        """Get reverse DNS for server's public IP"""
        try:
            if not hetzner_server.public_net.ipv4:
                return None
            
            # Get reverse DNS for IPv4
            rdns_entries = hetzner_server.public_net.ipv4.dns_ptr
            
            if rdns_entries:
                # dns_ptr is a list of dict objects with 'dns_ptr' key
                if isinstance(rdns_entries, list) and len(rdns_entries) > 0:
                    first_entry = rdns_entries[0]
                    if hasattr(first_entry, 'dns_ptr'):
                        return first_entry.dns_ptr
                    elif isinstance(first_entry, dict) and 'dns_ptr' in first_entry:
                        return first_entry['dns_ptr']
                    else:
                        # If it's a string, return it directly
                        return str(first_entry)
                elif isinstance(rdns_entries, str):
                    # Sometimes it might be a direct string
                    return rdns_entries
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting reverse DNS for {hetzner_server.name}: {str(e)}")
            self.logger.debug(f"DNS PTR structure: {type(hetzner_server.public_net.ipv4.dns_ptr)} - {hetzner_server.public_net.ipv4.dns_ptr}")
            return None