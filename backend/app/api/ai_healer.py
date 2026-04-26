"""
API routes for AI healer with Claude Code CLI + OmniRoute
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
import logging
import subprocess
import asyncio
from datetime import datetime
import json

logger = logging.getLogger("omni_healer")
router = APIRouter()

# In-memory storage for demo (will be replaced with DB)
ai_commands = []
auto_mode_enabled = False


@router.get("/status")
async def get_ai_status():
    """Get AI healer status"""
    return {
        "success": True,
        "data": {
            "auto_mode": auto_mode_enabled,
            "pending_commands": len([c for c in ai_commands if c.get("status") == "pending"]),
            "executed_today": len([
                c for c in ai_commands 
                if c.get("status") == "executed" and 
                c.get("executed_at", "")[:10] == datetime.utcnow().strftime("%Y-%m-%d")
            ]),
            "claude_code_available": check_claude_available(),
            "omniroute_enabled": True
        }
    }


@router.post("/mode/auto")
async def enable_auto_mode(enable: bool):
    """Enable or disable auto mode"""
    global auto_mode_enabled
    auto_mode_enabled = enable
    logger.warning(f"Auto mode {'enabled' if enable else 'disabled'}")
    return {
        "success": True,
        "message": f"Auto mode {'enabled' if enable else 'disabled'}",
        "warning": "Auto mode will execute commands without confirmation!" if enable else None
    }


@router.get("/commands")
async def get_commands(status: Optional[str] = None, limit: int = 50):
    """Get AI-suggested commands"""
    filtered = ai_commands
    
    if status:
        filtered = [c for c in filtered if c.get("status") == status]
    
    # Sort by created_at descending
    filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "success": True,
        "data": filtered[:limit],
        "total": len(filtered)
    }


@router.post("/commands/{command_id}/approve")
async def approve_command(command_id: int, background_tasks: BackgroundTasks):
    """Approve and execute a pending command"""
    for cmd in ai_commands:
        if cmd.get("id") == command_id:
            if cmd.get("status") != "pending":
                raise HTTPException(status_code=400, detail="Command not pending")
            
            cmd["status"] = "approved"
            background_tasks.add_task(execute_command, cmd)
            
            return {
                "success": True,
                "message": f"Command {command_id} approved and executing"
            }
    
    raise HTTPException(status_code=404, detail="Command not found")


@router.post("/commands/{command_id}/reject")
async def reject_command(command_id: int, reason: str = ""):
    """Reject a pending command"""
    for cmd in ai_commands:
        if cmd.get("id") == command_id:
            cmd["status"] = "rejected"
            cmd["rejection_reason"] = reason
            return {"success": True, "message": f"Command {command_id} rejected"}
    
    raise HTTPException(status_code=404, detail="Command not found")


@router.post("/analyze/{error_id}")
async def analyze_error(error_id: int):
    """Analyze an error and suggest fixes using Claude Code CLI"""
    # This would normally fetch the error from DB
    # For demo, we'll create a sample analysis
    
    analysis_result = await run_claude_analysis(error_id)
    
    if not analysis_result:
        raise HTTPException(status_code=500, detail="Failed to analyze error")
    
    # Create command suggestion
    command_entry = {
        "id": len(ai_commands) + 1,
        "error_id": error_id,
        "command": analysis_result.get("command", ""),
        "description": analysis_result.get("description", ""),
        "status": "pending" if not auto_mode_enabled else "approved",
        "auto_mode": auto_mode_enabled,
        "created_at": datetime.utcnow().isoformat(),
        "ai_analysis": analysis_result
    }
    
    ai_commands.append(command_entry)
    
    if auto_mode_enabled:
        # Auto-execute in background
        from fastapi import BackgroundTasks
        # Note: Can't use background_tasks here directly, would need refactoring
        logger.info(f"Auto-mode: Command {command_entry['id']} will be executed")
    
    return {
        "success": True,
        "data": command_entry,
        "auto_executed": auto_mode_enabled
    }


@router.post("/execute/manual")
async def execute_manual_command(command: str, description: str = ""):
    """Execute a manual command via Claude Code CLI + OmniRoute"""
    result = await execute_claude_command(command, description)
    
    command_entry = {
        "id": len(ai_commands) + 1,
        "error_id": None,
        "command": command,
        "description": description,
        "status": "executed" if result.get("success") else "failed",
        "auto_mode": False,
        "created_at": datetime.utcnow().isoformat(),
        "executed_at": datetime.utcnow().isoformat() if result.get("success") else None,
        "result": result.get("output", ""),
        "error": result.get("error", "")
    }
    
    ai_commands.append(command_entry)
    
    return {
        "success": result.get("success", False),
        "data": command_entry
    }


def check_claude_available() -> bool:
    """Check if Claude Code CLI is available"""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


async def run_claude_analysis(error_id: int) -> Optional[Dict]:
    """Run Claude Code CLI to analyze an error"""
    # Sample analysis - in production this would query actual error
    sample_analysis = {
        "error_id": error_id,
        "analysis": "Detected Docker container crash due to OOM",
        "command": "docker update --memory=512m container_name",
        "description": "Increase memory limit for the container to prevent OOM kills",
        "confidence": 0.85,
        "risk_level": "low"
    }
    
    # In production, would call:
    # claude --prompt "Analyze this error: {error_message}. Suggest a fix command."
    
    await asyncio.sleep(0.1)  # Simulate API call
    return sample_analysis


async def execute_claude_command(command: str, description: str = "") -> Dict:
    """Execute command via Claude Code CLI + OmniRoute"""
    try:
        # In production, this would use OmniRoute to execute safely
        # For now, simulate execution
        
        logger.info(f"Executing command: {command}")
        
        # Simulate command execution
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "output": f"Command executed successfully: {command}",
            "command": command,
            "execution_time": 0.5
        }
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command
        }


async def execute_command(cmd: Dict):
    """Execute a command (background task)"""
    logger.info(f"Executing command {cmd['id']}: {cmd['command']}")
    
    result = await execute_claude_command(cmd["command"], cmd.get("description", ""))
    
    # Update command status
    for c in ai_commands:
        if c["id"] == cmd["id"]:
            c["status"] = "executed" if result["success"] else "failed"
            c["executed_at"] = datetime.utcnow().isoformat()
            c["result"] = result.get("output", "")
            if not result["success"]:
                c["error"] = result.get("error", "")
            break
    
    logger.info(f"Command {cmd['id']} execution completed: {cmd['status']}")
