from proxmoxer import ProxmoxAPI
from requests.auth import HTTPBasicAuth
import requests
from .config import Config

class ProxmoxClient:
    def __init__(self):
        self.host = Config.PROXMOX_HOST
        self.port = Config.PROXMOX_PORT
        self.user = Config.PROXMOX_USER
        self.token_name = Config.PROXMOX_TOKEN_NAME
        self.token_value = Config.PROXMOX_TOKEN_VALUE
        self.verify_ssl = Config.PROXMOX_VERIFY_SSL
        
        self.proxmox = None
        self._connect()
    
    def _connect(self):
        """Connect to Proxmox API using token authentication"""
        try:
            self.proxmox = ProxmoxAPI(
                host=self.host,
                port=int(self.port),
                user=self.user,
                token_name=self.token_name,
                token_value=self.token_value,
                verify_ssl=self.verify_ssl
            )
            print(f"Connected to Proxmox at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to Proxmox: {e}")
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
        try:
            if vm_type == 'qemu':
                logs = self.proxmox.nodes(node_id).qemu(vm_id).log.get(limit=limit)
            else:
                logs = self.proxmox.nodes(node_id).lxc(vm_id).log.get(limit=limit)
            return logs
        except Exception as e:
            print(f"Error getting logs for {vm_type} {vm_id}: {e}")
            return []
    
    def execute_command_in_ct(self, node_id, ct_id, command):
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