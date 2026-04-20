"""
Proxmox VE service integration
"""

from proxmoxer import ProxmoxAPI
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional
import asyncio

# Add config to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "config"))

try:
    from settings import (
        PROXMOX_HOST, PROXMOX_PORT, PROXMOX_USER, PROXMOX_PASSWORD,
        PROXMOX_TOKEN_NAME, PROXMOX_TOKEN_VALUE, PROXMOX_VERIFY_SSL,
        SSH_KEY_PATH, SSH_USERNAME, SSH_TIMEOUT
    )
except ImportError:
    PROXMOX_HOST = "localhost"
    PROXMOX_PORT = 8006
    PROXMOX_USER = "root@pam"
    PROXMOX_PASSWORD = ""
    PROXMOX_TOKEN_NAME = ""
    PROXMOX_TOKEN_VALUE = ""
    PROXMOX_VERIFY_SSL = False
    SSH_KEY_PATH = "/root/.ssh/id_ed25519"
    SSH_USERNAME = "root"
    SSH_TIMEOUT = 30

logger = logging.getLogger("omni_healer")


class ProxmoxService:
    """Service for interacting with Proxmox VE API"""
    
    def __init__(self):
        self.proxmox = None
        self.connected = False
    
    async def connect(self):
        """Connect to Proxmox VE API"""
        try:
            if PROXMOX_TOKEN_NAME and PROXMOX_TOKEN_VALUE:
                # Use token authentication (recommended)
                self.proxmox = ProxmoxAPI(
                    PROXMOX_HOST,
                    port=PROXMOX_PORT,
                    user=PROXMOX_USER,
                    token_name=PROXMOX_TOKEN_NAME,
                    token_value=PROXMOX_TOKEN_VALUE,
                    verify_ssl=PROXMOX_VERIFY_SSL
                )
            else:
                # Use password authentication (less secure)
                self.proxmox = ProxmoxAPI(
                    PROXMOX_HOST,
                    port=PROXMOX_PORT,
                    user=PROXMOX_USER,
                    password=PROXMOX_PASSWORD,
                    verify_ssl=PROXMOX_VERIFY_SSL
                )
            
            # Test connection
            self.proxmox.nodes.get()
            self.connected = True
            logger.info(f"Connected to Proxmox VE at {PROXMOX_HOST}:{PROXMOX_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox VE: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Proxmox VE"""
        self.proxmox = None
        self.connected = False
        logger.info("Disconnected from Proxmox VE")
    
    async def get_nodes(self) -> List[Dict]:
        """Get all Proxmox nodes"""
        if not self.connected:
            await self.connect()
        
        try:
            nodes = self.proxmox.nodes.get()
            return nodes
        except Exception as e:
            logger.error(f"Failed to get nodes: {e}")
            return []
    
    async def get_vms(self, node_name: str) -> List[Dict]:
        """Get all VMs on a node"""
        if not self.connected:
            await self.connect()
        
        try:
            vms = self.proxmox.nodes(node_name).qemu.get()
            return vms
        except Exception as e:
            logger.error(f"Failed to get VMs on node {node_name}: {e}")
            return []
    
    async def get_containers(self, node_name: str) -> List[Dict]:
        """Get all LXC containers on a node"""
        if not self.connected:
            await self.connect()
        
        try:
            containers = self.proxmox.nodes(node_name).lxc.get()
            return containers
        except Exception as e:
            logger.error(f"Failed to get containers on node {node_name}: {e}")
            return []
    
    async def get_vm_status(self, node_name: str, vmid: int) -> Dict:
        """Get VM status and configuration"""
        if not self.connected:
            await self.connect()
        
        try:
            vm = self.proxmox.nodes(node_name).qemu(vmid).status.current.get()
            config = self.proxmox.nodes(node_name).qemu(vmid).config.get()
            return {**vm, "config": config}
        except Exception as e:
            logger.error(f"Failed to get VM {vmid} status: {e}")
            return {}
    
    async def get_container_status(self, node_name: str, ctid: int) -> Dict:
        """Get container status and configuration"""
        if not self.connected:
            await self.connect()
        
        try:
            ct = self.proxmox.nodes(node_name).lxc(ctid).status.current.get()
            config = self.proxmox.nodes(node_name).lxc(ctid).config.get()
            return {**ct, "config": config}
        except Exception as e:
            logger.error(f"Failed to get container {ctid} status: {e}")
            return {}
    
    async def scan_all_resources(self) -> Dict:
        """Scan all nodes, VMs, and containers"""
        result = {
            "nodes": [],
            "vms": [],
            "containers": []
        }
        
        nodes = await self.get_nodes()
        for node in nodes:
            node_name = node["node"]
            result["nodes"].append({
                "name": node_name,
                "status": node.get("status", "unknown"),
                "level": node.get("level", "")
            })
            
            # Get VMs
            vms = await self.get_vms(node_name)
            for vm in vms:
                result["vms"].append({
                    "node": node_name,
                    "vmid": vm["vmid"],
                    "name": vm.get("name", f"VM {vm['vmid']}"),
                    "status": vm.get("status", "unknown"),
                    "has_docker": False  # Will be updated by Docker scanner
                })
            
            # Get Containers
            containers = await self.get_containers(node_name)
            for ct in containers:
                result["containers"].append({
                    "node": node_name,
                    "ctid": ct["vmid"],
                    "name": ct.get("name", f"CT {ct['vmid']}"),
                    "status": ct.get("status", "unknown"),
                    "has_docker": False  # Will be updated by Docker scanner
                })
        
        return result


# Singleton instance
proxmox_service = ProxmoxService()
