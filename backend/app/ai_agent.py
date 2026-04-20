import subprocess
import json
import asyncio
from .config import Config

class AIAgent:
    def __init__(self):
        self.claude_path = Config.CLAUDE_CODE_PATH
        self.omniroute_path = Config.OMNIROUTE_PATH
        self.auto_confirm = Config.AUTO_CONFIRM
    
    async def analyze_logs(self, logs, context=""):
        """Analyze logs using Claude Code and OmniRoute to identify issues"""
        prompt = f"""
        Analyze the following system logs for errors and potential issues.
        Context: {context}
        
        Logs:
        {logs}
        
        Provide:
        1. Summary of errors found
        2. Root cause analysis
        3. Recommended fix commands
        4. Confidence level (high/medium/low)
        
        Format response as JSON with keys: summary, root_cause, commands, confidence
        """
        
        try:
            # Use Claude Code with OmniRoute for analysis
            cmd = [
                self.claude_path,
                "--route", self.omniroute_path,
                "--prompt", prompt,
                "--json"
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return json.loads(stdout.decode())
            else:
                return {"error": stderr.decode(), "summary": "Analysis failed"}
                
        except Exception as e:
            return {"error": str(e), "summary": "Analysis exception"}
    
    async def generate_fix_proposal(self, error_context, logs):
        """Generate a fix proposal using AI"""
        analysis = await self.analyze_logs(logs, error_context)
        
        if "commands" in analysis and analysis["commands"]:
            return {
                "proposal_id": hash(str(analysis)) % 100000,
                "summary": analysis.get("summary", "Unknown issue"),
                "root_cause": analysis.get("root_cause", "Unable to determine"),
                "commands": analysis["commands"],
                "confidence": analysis.get("confidence", "low"),
                "requires_confirmation": not self.auto_confirm
            }
        
        return None
    
    async def execute_command(self, command, node_id=None, ct_id=None, ct_type='lxc'):
        """Execute a command via OmniRoute and Claude Code"""
        # In a real implementation, this would use SSH or Proxmox API
        # For now, we'll simulate execution
        
        prompt = f"""
        Execute the following command safely:
        {command}
        
        Target: {ct_type} {ct_id} on node {node_id}
        
        Return execution result as JSON with keys: success, output, error
        """
        
        try:
            cmd = [
                self.claude_path,
                "--route", self.omniroute_path,
                "--prompt", prompt,
                "--execute"
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return json.loads(stdout.decode())
            else:
                return {"success": False, "output": "", "error": stderr.decode()}
                
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    def toggle_auto_confirm(self, enabled):
        """Toggle auto-confirm mode"""
        self.auto_confirm = enabled
        return {"auto_confirm": enabled}