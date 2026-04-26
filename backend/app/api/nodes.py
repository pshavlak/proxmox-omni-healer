"""
API routes for nodes, VMs, and containers
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
import logging

from app.models.database import ProxmoxNode, VirtualMachine, Container, DockerContainer
from app.services.proxmox_service import proxmox_service
from app.utils.database import get_session

logger = logging.getLogger("omni_healer")
router = APIRouter()


@router.get("/scan")
async def scan_resources():
    """Scan all Proxmox resources (nodes, VMs, containers)"""
    try:
        result = await proxmox_service.scan_all_resources()
        return {
            "success": True,
            "data": result,
            "message": f"Scanned {len(result['nodes'])} nodes, {len(result['vms'])} VMs, {len(result['containers'])} containers"
        }
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes")
async def get_nodes():
    """Get all Proxmox nodes"""
    try:
        nodes = await proxmox_service.get_nodes()
        return {"success": True, "data": nodes}
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_name}/vms")
async def get_node_vms(node_name: str):
    """Get all VMs on a specific node"""
    try:
        vms = await proxmox_service.get_vms(node_name)
        return {"success": True, "data": vms}
    except Exception as e:
        logger.error(f"Failed to get VMs on node {node_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_name}/containers")
async def get_node_containers(node_name: str):
    """Get all LXC containers on a specific node"""
    try:
        containers = await proxmox_service.get_containers(node_name)
        return {"success": True, "data": containers}
    except Exception as e:
        logger.error(f"Failed to get containers on node {node_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vm/{node_name}/{vmid}")
async def get_vm_details(node_name: str, vmid: int):
    """Get detailed VM status"""
    try:
        vm_status = await proxmox_service.get_vm_status(node_name, vmid)
        if not vm_status:
            raise HTTPException(status_code=404, detail="VM not found")
        return {"success": True, "data": vm_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VM details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/container/{node_name}/{ctid}")
async def get_container_details(node_name: str, ctid: int):
    """Get detailed container status"""
    try:
        ct_status = await proxmox_service.get_container_status(node_name, ctid)
        if not ct_status:
            raise HTTPException(status_code=404, detail="Container not found")
        return {"success": True, "data": ct_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get container details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary():
    """Get infrastructure summary"""
    try:
        scan_result = await proxmox_service.scan_all_resources()
        
        summary = {
            "total_nodes": len(scan_result["nodes"]),
            "total_vms": len(scan_result["vms"]),
            "total_containers": len(scan_result["containers"]),
            "vms_by_status": {},
            "containers_by_status": {},
            "nodes_online": sum(1 for n in scan_result["nodes"] if n.get("status") == "online")
        }
        
        # Count VMs by status
        for vm in scan_result["vms"]:
            status = vm.get("status", "unknown")
            summary["vms_by_status"][status] = summary["vms_by_status"].get(status, 0) + 1
        
        # Count containers by status
        for ct in scan_result["containers"]:
            status = ct.get("status", "unknown")
            summary["containers_by_status"][status] = summary["containers_by_status"].get(status, 0) + 1
        
        return {"success": True, "data": summary}
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
