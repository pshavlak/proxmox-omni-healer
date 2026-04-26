"""
API routes for log collection and error monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger("omni_healer")
router = APIRouter()


# In-memory storage for demo (will be replaced with DB)
error_logs = []


@router.get("/errors")
async def get_errors(
    acknowledged: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = 100
):
    """Get error logs with optional filtering"""
    filtered = error_logs
    
    if acknowledged is not None:
        filtered = [e for e in filtered if e.get("acknowledged") == acknowledged]
    
    if severity:
        filtered = [e for e in filtered if e.get("severity") == severity]
    
    # Sort by timestamp descending
    filtered = sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "success": True,
        "data": filtered[:limit],
        "total": len(filtered)
    }


@router.post("/errors/{error_id}/acknowledge")
async def acknowledge_error(error_id: int):
    """Acknowledge an error"""
    for error in error_logs:
        if error.get("id") == error_id:
            error["acknowledged"] = True
            error["acknowledged_at"] = datetime.utcnow().isoformat()
            return {"success": True, "message": f"Error {error_id} acknowledged"}
    
    raise HTTPException(status_code=404, detail="Error not found")


@router.get("/errors/{error_id}")
async def get_error_details(error_id: int):
    """Get detailed error information"""
    for error in error_logs:
        if error.get("id") == error_id:
            return {"success": True, "data": error}
    
    raise HTTPException(status_code=404, detail="Error not found")


@router.get("/logs/{source_type}/{source_id}")
async def get_source_logs(
    source_type: str,  # vm, container, docker
    source_id: int,
    limit: int = 100
):
    """Get logs for a specific source (VM, container, or Docker)"""
    filtered = [
        e for e in error_logs
        if e.get("source_type") == source_type and e.get("source_id") == source_id
    ]
    
    filtered = sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "success": True,
        "data": filtered[:limit],
        "total": len(filtered)
    }


@router.get("/stats")
async def get_log_stats():
    """Get log statistics"""
    stats = {
        "total_errors": len(error_logs),
        "unacknowledged": sum(1 for e in error_logs if not e.get("acknowledged")),
        "by_severity": {},
        "by_source_type": {},
        "recent_errors_24h": 0
    }
    
    # Count by severity
    for error in error_logs:
        severity = error.get("severity", "unknown")
        stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        source_type = error.get("source_type", "unknown")
        stats["by_source_type"][source_type] = stats["by_source_type"].get(source_type, 0) + 1
    
    return {"success": True, "data": stats}


@router.delete("/errors/clear")
async def clear_errors(acknowledged_only: bool = False):
    """Clear error logs (optionally only acknowledged ones)"""
    global error_logs
    
    if acknowledged_only:
        error_logs = [e for e in error_logs if not e.get("acknowledged")]
        return {"success": True, "message": "Cleared acknowledged errors"}
    else:
        error_logs = []
        return {"success": True, "message": "Cleared all errors"}
