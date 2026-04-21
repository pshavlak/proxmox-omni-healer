from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import os
from pathlib import Path
from .config import Config
from .proxmox_client import ProxmoxClient
from .ai_agent import AIAgent
from .db_manager import DatabaseManager
from .logger import app_logger as logger
import traceback

app = FastAPI(title="Proxmox Omni-Healer")

# Get base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Mount static files with absolute paths
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

# Initialize components
proxmox_client = None
ai_agent = None
db_manager = None

@app.on_event("startup")
async def startup_event():
    global proxmox_client, ai_agent, db_manager
    logger.info("=" * 60)
    logger.info("Starting Proxmox Omni-Healer")
    logger.info("=" * 60)
    
    try:
        # Database
        logger.info("Initializing database...")
        db_manager = DatabaseManager()
        await db_manager.init_db()
        logger.info("✓ Database initialized")
        
        # Proxmox client
        logger.info(f"Checking Proxmox credentials: TOKEN_NAME={Config.PROXMOX_TOKEN_NAME}, TOKEN_VALUE={'*' * 8 if Config.PROXMOX_TOKEN_VALUE else None}")
        if Config.PROXMOX_TOKEN_NAME and Config.PROXMOX_TOKEN_VALUE:
            logger.info("Initializing Proxmox client...")
            try:
                proxmox_client = ProxmoxClient()
                logger.info("✓ Proxmox client initialized successfully")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Proxmox client: {e}")
                logger.debug(traceback.format_exc())
        else:
            logger.warning("⚠ Proxmox credentials not configured, running in demo mode")
        
        # AI Agent
        logger.info("Initializing AI Agent...")
        ai_agent = AIAgent()
        logger.info("✓ AI Agent initialized")
        
        logger.info("=" * 60)
        logger.info("Startup complete!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"✗ Startup error: {e}")
        logger.debug(traceback.format_exc())

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Main dashboard page"""
    logger.debug("Dashboard requested")
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/logs", response_class=HTMLResponse)
async def get_logs_page(request: Request):
    """Logs page"""
    logger.debug("Logs page requested")
    return templates.TemplateResponse("logs.html", {"request": request})


@app.get("/api/cluster")
async def get_cluster_info():
    """Get cluster information"""
    logger.info("API: get_cluster_info called")
    if not proxmox_client:
        logger.warning("Proxmox client not available")
        return {"error": "Proxmox not configured"}
    
    try:
        cluster = proxmox_client.get_cluster_info()
        nodes = proxmox_client.get_all_nodes()
        
        resources = []
        for node in nodes:
            node_resources = proxmox_client.get_node_resources(node['node'])
            resources.extend(node_resources)
        
        logger.info(f"Cluster info retrieved: {len(nodes)} nodes, {len(resources)} resources")
        return {
            "cluster": cluster,
            "nodes": nodes,
            "resources": resources
        }
    except Exception as e:
        logger.error(f"Error getting cluster info: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vm/{node_id}/{vm_id}/status")
async def get_vm_status(node_id: str, vm_id: int, vm_type: str = "qemu"):
    """Get VM/CT status"""
    logger.info(f"API: get_vm_status called for {vm_type} {vm_id} on {node_id}")
    if not proxmox_client:
        return {"error": "Proxmox not configured"}
    
    try:
        status = proxmox_client.get_vm_status(node_id, vm_id, vm_type)
        logger.debug(f"Status retrieved for {vm_type} {vm_id}: {status}")
        return status
    except Exception as e:
        logger.error(f"Error getting VM status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vm/{node_id}/{vm_id}/logs")
async def get_vm_logs(node_id: str, vm_id: int, vm_type: str = "qemu", limit: int = 100):
    """Get VM/CT logs"""
    logger.info(f"API: get_vm_logs called for {vm_type} {vm_id}, limit={limit}")
    if not proxmox_client:
        return {"error": "Proxmox not configured"}
    
    try:
        logs = proxmox_client.get_vm_logs(node_id, vm_id, vm_type, limit)
        logger.info(f"Retrieved {len(logs)} log lines for {vm_type} {vm_id}")
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error getting VM logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_logs(data: dict):
    """Analyze logs using AI agent"""
    logger.info("API: analyze_logs called")
    if not ai_agent:
        return {"error": "AI Agent not initialized"}
    
    logs = data.get("logs", "")
    context = data.get("context", "")
    
    proposal = await ai_agent.generate_fix_proposal(context, logs)
    
    if proposal and db_manager:
        await db_manager.save_proposal(proposal)
        logger.info(f"Proposal saved: {proposal}")
    
    return proposal if proposal else {"message": "No issues found or analysis failed"}

@app.get("/api/proposals")
async def get_proposals(status: str = None):
    """Get all fix proposals"""
    logger.info(f"API: get_proposals called with status={status}")
    if not db_manager:
        return []
    
    proposals = await db_manager.get_proposals(status)
    logger.info(f"Retrieved {len(proposals)} proposals")
    return proposals

@app.post("/api/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: int):
    """Approve a fix proposal"""
    logger.info(f"API: approve_proposal called for ID {proposal_id}")
    if not db_manager:
        return {"error": "Database not initialized"}
    
    await db_manager.update_proposal_status(proposal_id, "approved")
    return {"message": "Proposal approved"}

@app.post("/api/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: int):
    """Reject a fix proposal"""
    logger.info(f"API: reject_proposal called for ID {proposal_id}")
    if not db_manager:
        return {"error": "Database not initialized"}
    
    await db_manager.update_proposal_status(proposal_id, "rejected")
    return {"message": "Proposal rejected"}

@app.post("/api/proposals/{proposal_id}/execute")
async def execute_proposal(proposal_id: int, command: str = None):
    """Execute a fix proposal"""
    logger.info(f"API: execute_proposal called for ID {proposal_id}")
    if not db_manager or not ai_agent:
        return {"error": "Components not initialized"}
    
    proposals = await db_manager.get_proposals()
    proposal = next((p for p in proposals if p[proposal_id] == proposal_id), None)
    
    if not proposal:
        logger.warning(f"Proposal {proposal_id} not found")
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    commands = eval(proposal[commands]) if isinstance(proposal[commands], str) else proposal[commands]
    
    results = []
    for cmd in commands:
        logger.info(f"Executing command: {cmd}")
        result = await ai_agent.execute_command(cmd)
        await db_manager.save_execution_result(
            proposal_id, cmd, 
            result.get(success, False), 
            result.get(output, ), 
            result.get(error, )
        )
        results.append(result)
    
    await db_manager.update_proposal_status(proposal_id, "executed")
    logger.info(f"Proposal {proposal_id} executed")
    
    return {"results": results}

@app.post("/api/auto-confirm/toggle")
async def toggle_auto_confirm(data: dict):
    """Toggle auto-confirm mode"""
    logger.info("API: toggle_auto_confirm called")
    if not ai_agent:
        return {"error": "AI Agent not initialized"}
    
    enabled = data.get("enabled", False)
    result = ai_agent.toggle_auto_confirm(enabled)
    logger.info(f"Auto-confirm toggled: {enabled}")
    return result

@app.get("/api/logs/errors")
async def get_error_logs(limit: int = 100):
    """Get recent error logs"""
    logger.info(f"API: get_error_logs called with limit={limit}")
    if not db_manager:
        return []
    
    logs = await db_manager.get_error_logs(limit)
    return logs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
