import os
from proxmoxer import ProxmoxAPI
from requests.auth import HTTPBasicAuth
import requests
from .config import Config

import time
from typing import Optional

class ProxmoxClient:
    REQUEST_DELAY = 0.5  # Minimum delay between API requests in seconds
    
    def __init__(self, auto_rotate=False):
        self._last_request_time: Optional[float] = None
        """Initialize Proxmox client with configuration validation"""
        if auto_rotate:
            self._rotate_credentials()
        
        # Validate required configuration
        self.host = Config.PROXMOX_HOST
        if not self.host:
            raise ValueError("PROXMOX_HOST not configured")
            
        self.port = Config.PROXMOX_PORT
        self.user = Config.PROXMOX_USER
        if not self.user:
            raise ValueError("PROXMOX_USER not configured")
            
        self.token_name = Config.PROXMOX_TOKEN_NAME
        self.token_value = os.getenv('PROXMOX_API_TOKEN', Config.PROXMOX_TOKEN_VALUE)
        if not self.token_value:
            raise ValueError("PROXMOX_API_TOKEN not configured")
            
        self.verify_ssl = Config.PROXMOX_VERIFY_SSL
        
        # Validate SSH key exists
        ssh_key_path = os.getenv('PROXMOX_SSH_KEY_PATH', Config.SSH_KEY_PATH)
        if not os.path.exists(ssh_key_path):
            raise ValueError(f"SSH key not found at {ssh_key_path}")
        
        self.proxmox = None
        self._connect()
    
    def _connect(self):
        """Connect to Proxmox API using ONLY SSH key authentication
        Validates token expiration before connecting"""
        if self._is_token_expired():
            raise ValueError("Proxmox API token expired")
            
        import paramiko
        from paramiko.ssh_exception import SSHException
        
        try:
            # Validate SSH key
            ssh_key_path = os.getenv('PROXMOX_SSH_KEY_PATH', Config.SSH_KEY_PATH)
            if not os.path.exists(ssh_key_path):
                raise ValueError(f"SSH key not found at {ssh_key_path}")
                
            ssh_key_passphrase = os.getenv('PROXMOX_SSH_KEY_PASSPHRASE', '')
            
            try:
                pkey = paramiko.RSAKey.from_private_key_file(
                    filename=ssh_key_path,
                    password=ssh_key_passphrase if ssh_key_passphrase else None
                )
            except SSHException as e:
                raise ValueError(f"Invalid SSH key or passphrase: {str(e)}")
            
            self.proxmox = ProxmoxAPI(
                host=self.host,
                port=int(self.port),
                user=self.user,
                backend='ssh_paramiko',
                ssh_private_key=pkey,
                ssh_user=Config.SSH_USERNAME,
                timeout=Config.SSH_TIMEOUT,
                verify_ssl=self.verify_ssl
            )
            print(f"Connected to Proxmox via SSH at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to Proxmox via SSH: {e}")
            raise
    
    def get_all_nodes(self):
        """Get all nodes in the cluster"""
        try:
            return self.proxmox.nodes.get()
        except Exception as e:
            print(f"Error getting nodes: {e}")
            return []
    
    def get_node_resources(self, node_id):
        """Get all VMs and CTs on a specific node"""
        try:
            resources = []
            # Get QEMU VMs
            vms = self.proxmox.nodes(node_id).qemu.get()
            for vm in vms:
                vm['type'] = 'qemu'
                vm['node'] = node_id
                resources.append(vm)
            
            # Get LXC Containers
            cts = self.proxmox.nodes(node_id).lxc.get()
            for ct in cts:
                ct['type'] = 'lxc'
                ct['node'] = node_id
                resources.append(ct)
            
            return resources
        except Exception as e:
            print(f"Error getting resources for node {node_id}: {e}")
            return []
    
    def get_vm_status(self, node_id, vm_id, vm_type='qemu'):
        """Get status of a specific VM or CT"""
        try:
            if vm_type == 'qemu':
                return self.proxmox.nodes(node_id).qemu(vm_id).status.current.get()
            else:
                return self.proxmox.nodes(node_id).lxc(vm_id).status.current.get()
        except Exception as e:
            print(f"Error getting status for {vm_type} {vm_id}: {e}")
            return None
    
    def get_vm_logs(self, node_id, vm_id, vm_type='qemu', limit=100):
        """Get logs for a specific VM or CT"""
        import subprocess
        try:
            if vm_type == 'qemu':
                try:
                    logs = self.proxmox.nodes(node_id).qemu(vm_id).log.get(limit=limit)
                    return [log.get('t', '') for log in logs] if logs else []
                except:
                    return []
            else:
                # For LXC containers, use SSH to Proxmox host and execute pct
                try:
                    # Execute pct command on Proxmox host via SSH
                    result = subprocess.run(
                        ['ssh', '-o', 'StrictHostKeyChecking=no',
                         f'root@192.168.1.110',
                         f'pct exec {vm_id} -- journalctl -n {limit} --no-pager'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout:
                        return result.stdout.strip().split('\n')

                    # Fallback to syslog
                    result = subprocess.run(
                        ['ssh', '-i', os.getenv('PROXMOX_SSH_KEY_PATH', ''), '-o', 'StrictHostKeyChecking=no',
                         f'root@{self.host}',
                         f'pct exec {vm_id} -- tail -n {limit} /var/log/syslog'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout:
                        return result.stdout.strip().split('\n')
                except Exception as e:
                    print(f"Error executing SSH command: {e}")
                return []
        except Exception as e:
            print(f"Error getting logs for {vm_type} {vm_id}: {e}")
            return []
    
    def execute_command_in_ct(self, node_id, ct_id, command, timeout=30):
        """Execute command in container with rate limiting and timeout"""
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.REQUEST_DELAY:
                time.sleep(self.REQUEST_DELAY - elapsed)
        """Execute a command inside an LXC container"""
        try:
            result = self.proxmox.nodes(node_id).lxc(ct_id).exec.post(
                command=['bash', '-c', command]
            )
            return result
        except Exception as e:
            print(f"Error executing command in CT {ct_id}: {e}")
            return None
    
    def get_cluster_info(self):
        """Get basic cluster information"""
        try:
            return self.proxmox.cluster.get()
        except Exception as e:
            print(f"Error getting cluster info: {e}")
            return None
            
    def test_connection(self):
        """Test Proxmox API connection"""
        try:
            # Verify minimum required API version (must be >= 7.2)
            version = self.proxmox.version.get()
            if int(version['version'].split('.')[1]) < 2:
                raise ValueError(f"Unsupported Proxmox version {version['version']}. Requires >= 7.2")
            
            # Try to get cluster status
            status = self.get_cluster_info()
            if status:
                return {
                    'connected': True,
                    'version': status.get('version'),
                    'nodes': len(status.get('nodes', []))
                }
            return {'connected': False, 'error': 'No cluster info available'}
        except Exception as e:
            return {'connected': False, 'error': str(e)}

    def get_running_containers(self):
        """Get list of running LXC containers"""
        try:
            running_containers = []
            nodes = self.get_all_nodes()
            
            for node in nodes:
                containers = self.proxmox.nodes(node['node']).lxc.get()
                for ct in containers:
                    if ct.get('status') == 'running':
                        ct_info = {
                            'node': node['node'],
                            'ctid': ct['vmid'],
                            'name': ct.get('name', f"CT {ct['vmid']}"),
                            'status': ct['status'],
                            'uptime': ct.get('uptime', 0)
                        }
                        running_containers.append(ct_info)
            
            return running_containers
        except Exception as e:
            print(f"Error getting running containers: {e}")
            return []
    def get_container_services_status(self, ct_id):
        """Get status of systemd services in an LXC container"""
        import subprocess
        try:
            result = subprocess.run(
                ['ssh', '-i', Config.SSH_KEY_PATH,
                 f'root@{self.host}',
                 f'pct exec {ct_id} -- systemctl list-units --type=service --all --output=json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout:
                import json
                services = json.loads(result.stdout)
                failed_services = [s for s in services if s.get('state') == 'failed' or s.get('active') == 'failed']
                return {
                    'total': len(services),
                    'failed': len(failed_services),
                    'failed_services': failed_services
                }
            return {'total': 0, 'failed': 0, 'failed_services': []}
        except Exception as e:
            print(f"Error getting services status for CT {ct_id}: {e}")
            return {'total': 0, 'failed': 0, 'failed_services': [], 'error': str(e)}
    
    def restart_service_in_ct(self, ct_id, service_name):
        """Restart a specific service in an LXC container"""
        import subprocess
        try:
            ssh_key = os.getenv('PROXMOX_SSH_KEY_PATH', '')
            if not ssh_key:
                raise ValueError("PROXMOX_SSH_KEY_PATH not set")
                
            result = subprocess.run(
                ['ssh', '-i', ssh_key, '-o', 'BatchMode=yes',
                 f'{Config.SSH_USERNAME}@{self.host}',
                 f'pct exec {ct_id} -- systemctl restart {service_name}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            print(f"Error restarting service {service_name} in CT {ct_id}: {e}")
            return {'success': False, 'error': str(e)}
