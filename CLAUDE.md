# Claude Code Instructions

## Project: Proxmox Omni-Healer

### Build & Run
```bash
cd /opt/proxmox-omni-healer
source venv/bin/activate
./start.sh
```

Backend runs on port 8000 (uvicorn with auto-reload).

### Testing
- API: `curl http://localhost:8000/api/vm/{node}/{vmid}/services?vm_type=lxc`
- Test all containers: Check all 9 LXC containers (100-108, 111)

### User Preferences
- **Краткие ответы** - пользователь предпочитает минимум текста
- Избегать длинных объяснений
- Фокус на действиях, не на описаниях

### Git
- Remote: https://github.com/pshavlak/proxmox-omni-healer
- Always test before commit
- Use Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
