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
        """Simple log analysis without external AI"""
        issues = []
        commands = []

        # Analyze common error patterns
        if "systemd-networkd-wait-online" in logs and "error code (1)" in logs:
            issues.append("Таймаут ожидания сети при операциях apt")
            commands.append("systemctl disable systemd-networkd-wait-online.service")
            commands.append("systemctl mask systemd-networkd-wait-online.service")

        if "out of memory" in logs.lower() or "oom" in logs.lower():
            issues.append("Обнаружена нехватка памяти")
            commands.append("free -h")
            commands.append("# Рассмотрите увеличение лимита памяти")

        if "disk full" in logs.lower() or "no space left" in logs.lower():
            issues.append("Закончилось место на диске")
            commands.append("df -h")
            commands.append("du -sh /* | sort -h")

        if "connection refused" in logs.lower():
            issues.append("Обнаружены ошибки отказа в соединении")
            commands.append("netstat -tlnp")

        if "failed" in logs.lower() and "service" in logs.lower():
            issues.append("Обнаружены сбои служб")
            commands.append("systemctl --failed")
            commands.append("journalctl -xe")

        if not issues:
            return {"message": "Критических проблем не обнаружено"}

        return {
            "summary": "; ".join(issues),
            "root_cause": "Обнаружены системные ошибки в логах",
            "commands": commands,
            "confidence": "средняя" if len(issues) > 1 else "низкая"
        }
    
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