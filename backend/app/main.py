from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from pathlib import Path
from .config import Config
from .proxmox_client import ProxmoxClient
from .ai_agent import AIAgent
from .db_manager import DatabaseManager

app = FastAPI(title="Proxmox Omni-Healer")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        db_manager = DatabaseManager()
        await db_manager.init_db()
        print("Database initialized")

        # Only initialize Proxmox client if credentials are provided
        if Config.PROXMOX_TOKEN_NAME and Config.PROXMOX_TOKEN_VALUE:
            proxmox_client = ProxmoxClient()
            print("Proxmox client initialized")
        else:
            print("Proxmox credentials not configured, running in demo mode")

        ai_agent = AIAgent()
        print("AI Agent initialized")
    except Exception as e:
        print(f"Startup error: {e}")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logs", response_class=HTMLResponse)
async def get_logs_page(request: Request):
    """Logs page"""
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/services", response_class=HTMLResponse)
async def get_services_page(request: Request):
    """Services status page"""
    return templates.TemplateResponse("services.html", {"request": request})

@app.get("/api/cluster")
async def get_cluster_info():
    """Get cluster information"""
    if not proxmox_client:
        return {"error": "Proxmox not configured"}

    try:
        cluster = proxmox_client.get_cluster_info()
        nodes = proxmox_client.get_all_nodes()

        resources = []
        for node in nodes:
            node_resources = proxmox_client.get_node_resources(node["node"])
            resources.extend(node_resources)

        return {
            "cluster": cluster,
            "nodes": nodes,
            "resources": resources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vm/{node_id}/{vm_id}/status")
async def get_vm_status(node_id: str, vm_id: int, vm_type: str = "qemu"):
    """Get VM/CT status"""
    if not proxmox_client:
        return {"error": "Proxmox not configured"}

    try:
        status = proxmox_client.get_vm_status(node_id, vm_id, vm_type)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vm/{node_id}/{vm_id}/logs")
async def get_vm_logs(node_id: str, vm_id: int, vm_type: str = "qemu", limit: int = 100):
    """Get VM/CT logs"""
    if not proxmox_client:
        return {"error": "Proxmox not configured"}

    try:
        logs = proxmox_client.get_vm_logs(node_id, vm_id, vm_type, limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/services/status")
async def get_services_status():
    """Get status of services in all containers"""
    if not proxmox_client:
        return {"error": "Proxmox not configured"}

    try:
        nodes = proxmox_client.get_all_nodes()
        containers_status = []

        for node in nodes:
            resources = proxmox_client.get_node_resources(node['node'])
            for resource in resources:
                if resource.get('type') == 'lxc':
                    services = proxmox_client.get_container_services_status(resource['vmid'])
                    containers_status.append({
                        'name': resource.get('name', resource['vmid']),
                        'vmid': resource['vmid'],
                        'node': node['node'],
                        'services': services
                    })

        return {"containers": containers_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/services/{ct_id}/restart-failed")
async def restart_failed_services(ct_id: int):
    """Restart all failed services in a container"""
    if not proxmox_client:
        return {"error": "Proxmox not configured"}

    try:
        result = proxmox_client.restart_all_failed_services(ct_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/services/{ct_id}/restart/{service_name}")
async def restart_service(ct_id: int, service_name: str):
    """Restart a specific service in a container"""
    if not proxmox_client:
        return {"error": "Proxmox not configured"}

    try:
        result = proxmox_client.restart_service_in_ct(ct_id, service_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_logs(data: dict):
    """Analyze logs using AI agent"""
    if not ai_agent:
        return {"error": "AI Agent not initialized"}

    logs = data.get("logs", "")
    context = data.get("context", "")

    proposal = await ai_agent.generate_fix_proposal(context, logs)

    if proposal and db_manager:
        await db_manager.save_proposal(proposal)

    return proposal if proposal else {"message": "No issues found or analysis failed"}

@app.get("/api/proposals")
async def get_proposals(status: str = None):
    """Get all fix proposals"""
    if not db_manager:
        return []

    proposals = await db_manager.get_proposals(status)
    return proposals

@app.post("/api/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: int):
    """Approve a fix proposal"""
    if not db_manager:
        return {"error": "Database not initialized"}

    await db_manager.update_proposal_status(proposal_id, "approved")
    return {"message": "Proposal approved"}

@app.post("/api/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: int):
    """Reject a fix proposal"""
    if not db_manager:
        return {"error": "Database not initialized"}

    await db_manager.update_proposal_status(proposal_id, "rejected")
    return {"message": "Proposal rejected"}

@app.post("/api/proposals/{proposal_id}/execute")
async def execute_proposal(proposal_id: int, command: str = None):
    """Execute a fix proposal"""
    if not db_manager or not ai_agent:
        return {"error": "Components not initialized"}

    proposals = await db_manager.get_proposals()
    proposal = next((p for p in proposals if p["proposal_id"] == proposal_id), None)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    commands = eval(proposal["commands"]) if isinstance(proposal["commands"], str) else proposal["commands"]

    results = []
    for cmd in commands:
        result = await ai_agent.execute_command(cmd)
        await db_manager.save_execution_result(
            proposal_id, cmd,
            result.get("success", False),
            result.get("output", ""),
            result.get("error", "")
        )
        results.append(result)

    await db_manager.update_proposal_status(proposal_id, "executed")

    return {"results": results}

@app.post("/api/auto-confirm/toggle")
async def toggle_auto_confirm(data: dict):
    """Toggle auto-confirm mode"""
    if not ai_agent:
        return {"error": "AI Agent not initialized"}

    enabled = data.get("enabled", False)
    result = ai_agent.toggle_auto_confirm(enabled)
    return result

@app.get("/api/logs/errors")
async def get_error_logs(limit: int = 100):
    """Get recent error logs"""
    if not db_manager:
        return []

    logs = await db_manager.get_error_logs(limit)
    return logs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
