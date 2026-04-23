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
        criticality_map = {}  # Track criticality for each issue

        # Analyze common error patterns
        # ⚠️ SYSTEMD-NETWORKD-WAIT-ONLINE: LOW CRITICALITY
        # This is a known LXC issue where systemd-networkd-wait-online times out
        # waiting for full network connectivity that may never come in containerized environments.
        # The service itself is running fine (eth0 has IP 192.168.1.10/24).
        # Impact: Delays apt operations but doesn't affect application functionality.
        if "systemd-networkd-wait-online" in logs and "Timeout occurred" in logs:
            issues.append("Таймаут ожидания сети при операциях apt (LXC)")
            criticality_map["systemd-networkd-wait-online"] = "LOW"
            commands.append("# Отключить systemd-networkd-wait-online (не критично для LXC)")
            commands.append("systemctl disable systemd-networkd-wait-online.service")
            commands.append("systemctl mask systemd-networkd-wait-online.service")
            commands.append("# Проверить сетевое подключение")
            commands.append("ip addr show eth0")

        # 🔴 OUT OF MEMORY: CRITICAL
        if "out of memory" in logs.lower() or "oom" in logs.lower():
            issues.append("Обнаружена нехватка памяти")
            criticality_map["oom"] = "CRITICAL"
            commands.append("free -h")
            commands.append("# КРИТИЧНО: Рассмотрите увеличение лимита памяти контейнера")

        # 🔴 DISK FULL: CRITICAL
        if "disk full" in logs.lower() or "no space left" in logs.lower():
            issues.append("Закончилось место на диске")
            criticality_map["disk_full"] = "CRITICAL"
            commands.append("df -h")
            commands.append("du -sh /* | sort -h")
            commands.append("# КРИТИЧНО: Освободите место на диске немедленно")

        # 🟠 CONNECTION REFUSED: MEDIUM
        if "connection refused" in logs.lower():
            issues.append("Обнаружены ошибки отказа в соединении")
            criticality_map["connection_refused"] = "MEDIUM"
            commands.append("netstat -tlnp")
            commands.append("# Проверьте, запущены ли необходимые сервисы")

        # 🟠 SERVICE FAILURES: MEDIUM
        if "failed" in logs.lower() and "service" in logs.lower():
            issues.append("Обнаружены сбои служб")
            criticality_map["service_failed"] = "MEDIUM"
            commands.append("systemctl --failed")
            commands.append("journalctl -xe")

        if not issues:
            return {"message": "Критических проблем не обнаружено"}

        # Determine overall criticality
        max_criticality = "LOW"
        if any(c == "CRITICAL" for c in criticality_map.values()):
            max_criticality = "CRITICAL"
        elif any(c == "MEDIUM" for c in criticality_map.values()):
            max_criticality = "MEDIUM"

        return {
            "summary": "; ".join(issues),
            "root_cause": "Обнаружены системные ошибки в логах",
            "commands": commands,
            "confidence": "средняя" if len(issues) > 1 else "низкая",
            "criticality": max_criticality,
            "criticality_details": criticality_map
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