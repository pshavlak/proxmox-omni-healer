// Proxmox Omni-Healer Frontend Script

let autoConfirm = false;
let currentProposalId = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', loadDashboard);
    document.getElementById('toggleAutoConfirm').addEventListener('click', toggleAutoConfirm);
    document.getElementById('closeModalBtn').addEventListener('click', closeModal);
    document.getElementById('approveBtn').addEventListener('click', approveProposal);
    document.getElementById('rejectBtn').addEventListener('click', rejectProposal);
    document.getElementById('executeBtn').addEventListener('click', executeProposal);
}

async function loadDashboard() {
    await loadClusterInfo();
    await loadResources();
    await loadErrorLogs();
    await loadProposals();
}

async function loadClusterInfo() {
    const clusterInfoEl = document.getElementById('clusterInfo');
    clusterInfoEl.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch('/api/cluster');
        const data = await response.json();
        
        if (data.error) {
            clusterInfoEl.innerHTML = `<div class="error-message">${data.error}</div>`;
            return;
        }
        
        const nodesCount = data.nodes ? data.nodes.length : 0;
        const resourcesCount = data.resources ? data.resources.length : 0;
        const runningCount = data.resources ? data.resources.filter(r => r.status === 'running').length : 0;
        
        clusterInfoEl.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                <div style="text-align: center; padding: 20px; background: #ebf8ff; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #667eea;">${nodesCount}</div>
                    <div style="color: #4a5568;">Узлов</div>
                </div>
                <div style="text-align: center; padding: 20px; background: #c6f6d5; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #22543d;">${resourcesCount}</div>
                    <div style="color: #4a5568;">Ресурсов</div>
                </div>
                <div style="text-align: center; padding: 20px; background: #fed7d7; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #742a2a;">${runningCount}</div>
                    <div style="color: #4a5568;">Запущено</div>
                </div>
            </div>
        `;
    } catch (error) {
        clusterInfoEl.innerHTML = `<div class="error-message">Ошибка загрузки: ${error.message}</div>`;
    }
}

async function loadResources() {
    const resourcesEl = document.getElementById('resourcesList');
    resourcesEl.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch('/api/cluster');
        const data = await response.json();
        
        if (!data.resources || data.resources.length === 0) {
            resourcesEl.innerHTML = '<div class="loading">Нет доступных ресурсов</div>';
            return;
        }
        
        const html = data.resources.map(resource => {
            const statusClass = resource.status === 'running' ? 'status-running' : 'status-stopped';
            const typeIcon = resource.type === 'qemu' ? '🖥️' : '📦';

            return `
                <div class="resource-item" onclick="openContainerLogs('${resource.node}', '${resource.vmid}', '${resource.type}')" style="cursor: pointer;">
                    <div class="resource-info">
                        <div class="resource-name">${typeIcon} ${resource.name || resource.vmid} (${resource.type.toUpperCase()})</div>
                        <div class="resource-meta">Node: ${resource.node} | ID: ${resource.vmid}</div>
                    </div>
                    <span class="status-badge ${statusClass}">${resource.status || 'unknown'}</span>
                </div>
            `;
        }).join('');
        
        resourcesEl.innerHTML = html;
    } catch (error) {
        resourcesEl.innerHTML = `<div class="error-message">Ошибка загрузки: ${error.message}</div>`;
    }
}

async function loadErrorLogs() {
    const errorLogsEl = document.getElementById('errorLogs');
    errorLogsEl.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch('/api/logs/errors');
        const logs = await response.json();
        
        if (!logs || logs.length === 0) {
            errorLogsEl.innerHTML = '<div style="color: #48bb78; text-align: center; padding: 20px;">✓ Ошибок не обнаружено</div>';
            return;
        }
        
        const html = logs.slice(0, 10).map(log => `
            <div class="log-entry">
                <strong>${new Date(log.created_at).toLocaleString()}</strong><br>
                Node: ${log.node_id} | VM: ${log.vm_id}<br>
                ${log.log_content}
            </div>
        `).join('');
        
        errorLogsEl.innerHTML = html;
    } catch (error) {
        errorLogsEl.innerHTML = `<div class="error-message">Ошибка загрузки: ${error.message}</div>`;
    }
}

async function loadProposals() {
    const proposalsEl = document.getElementById('proposalsList');
    proposalsEl.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch('/api/proposals');
        const proposals = await response.json();
        
        if (!proposals || proposals.length === 0) {
            proposalsEl.innerHTML = '<div style="color: #718096; text-align: center; padding: 20px;">Нет активных предложений</div>';
            return;
        }
        
        const html = proposals.map(proposal => {
            const statusColors = {
                'pending': '#ed8936',
                'approved': '#48bb78',
                'rejected': '#f56565',
                'executed': '#4299e1'
            };
            
            return `
                <div class="proposal-card" onclick="showProposalDetails(${proposal.proposal_id})">
                    <div class="proposal-header">
                        <span class="proposal-summary">${proposal.summary}</span>
                        <span class="proposal-confidence">${proposal.confidence}</span>
                    </div>
                    <div class="proposal-details">Статус: <span style="color: ${statusColors[proposal.status]}">${proposal.status}</span></div>
                    <div style="font-size: 12px; color: #718096;">${new Date(proposal.created_at).toLocaleString()}</div>
                </div>
            `;
        }).join('');
        
        proposalsEl.innerHTML = html;
    } catch (error) {
        proposalsEl.innerHTML = `<div class="error-message">Ошибка загрузки: ${error.message}</div>`;
    }
}

async function toggleAutoConfirm() {
    try {
        const response = await fetch('/api/auto-confirm/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({enabled: !autoConfirm})
        });
        
        const result = await response.json();
        autoConfirm = result.auto_confirm;
        
        const btn = document.getElementById('toggleAutoConfirm');
        btn.textContent = autoConfirm ? 'Автоподтверждение: ВКЛ' : 'Автоподтверждение: ВЫКЛ';
        btn.className = autoConfirm ? 'btn btn-success' : 'btn btn-warning';
    } catch (error) {
        alert('Ошибка переключения режима: ' + error.message);
    }
}

function showProposalDetails(proposalId) {
    currentProposalId = proposalId;
    const modal = document.getElementById('proposalModal');
    const detailsEl = document.getElementById('proposalDetails');
    
    // Загрузка деталей предложения
    detailsEl.innerHTML = '<div class="loading">Загрузка...</div>';
    modal.classList.remove('hidden');
    
    // Здесь должна быть логика загрузки деталей конкретного предложения
    detailsEl.innerHTML = `
        <p><strong>ID:</strong> ${proposalId}</p>
        <p><strong>Описание:</strong> Анализ логов и предложение по исправлению</p>
        <p><strong>Команды:</strong></p>
        <div class="proposal-commands">systemctl restart docker</div>
    `;
}

function closeModal() {
    document.getElementById('proposalModal').classList.add('hidden');
    currentProposalId = null;
}

async function approveProposal() {
    if (!currentProposalId) return;
    
    try {
        await fetch(`/api/proposals/${currentProposalId}/approve`, {method: 'POST'});
        alert('Предложение одобрено');
        closeModal();
        loadProposals();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function rejectProposal() {
    if (!currentProposalId) return;
    
    try {
        await fetch(`/api/proposals/${currentProposalId}/reject`, {method: 'POST'});
        alert('Предложение отклонено');
        closeModal();
        loadProposals();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function executeProposal() {
    if (!currentProposalId) return;
    
    try {
        const response = await fetch(`/api/proposals/${currentProposalId}/execute`, {method: 'POST'});
        const result = await response.json();
        
        if (result.results) {
            alert('Выполнение завершено. Результаты: ' + JSON.stringify(result.results));
        } else {
            alert('Выполнение завершено');
        }
        
        closeModal();
        loadProposals();
    } catch (error) {
        alert('Ошибка выполнения: ' + error.message);
    }
}


// Terminal functionality
let term = null;
let fitAddon = null;
let ws = null;

function initTerminal() {
    if (term) return;
    
    term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Courier New, monospace',
        theme: {
            background: '#1e1e1e',
            foreground: '#d4d4d4',
            cursor: '#ffffff'
        }
    });
    
    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    
    term.open(document.getElementById('terminal-container'));
    fitAddon.fit();
    
    term.writeln('\x1b[1;32mProxmox Omni-Healer AI Terminal\x1b[0m');
    term.writeln('Нажмите "Запустить Claude Code" для начала работы\n');
    
    // Handle terminal input
    term.onData(data => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'input', data: data }));
        }
    });
}

function startClaudeTerminal() {
    if (!term) initTerminal();
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/terminal`);
    
    ws.onopen = () => {
        term.writeln('\x1b[1;32m[Подключено к Claude Code]\x1b[0m\n');
        document.getElementById('startTerminalBtn').disabled = true;
        document.getElementById('stopTerminalBtn').disabled = false;
    };
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'output') {
            term.write(msg.data);
        }
    };
    
    ws.onerror = (error) => {
        term.writeln('\x1b[1;31m[Ошибка подключения]\x1b[0m\n');
    };
    
    ws.onclose = () => {
        term.writeln('\n\x1b[1;33m[Отключено от Claude Code]\x1b[0m\n');
        document.getElementById('startTerminalBtn').disabled = false;
        document.getElementById('stopTerminalBtn').disabled = true;
    };
}

function stopClaudeTerminal() {
    if (ws) {
        ws.close();
        ws = null;
    }
}

function clearTerminal() {
    if (term) {
        term.clear();
    }
}

// Add event listeners for terminal buttons
document.addEventListener('DOMContentLoaded', () => {
    initTerminal();
    
    document.getElementById('startTerminalBtn').addEventListener('click', startClaudeTerminal);
    document.getElementById('stopTerminalBtn').addEventListener('click', stopClaudeTerminal);
    document.getElementById('clearTerminalBtn').addEventListener('click', clearTerminal);
});

// Terminal Modal Management
function openTerminalModal() {
    document.getElementById('terminalModal').classList.remove('hidden');
    if (!term) {
        initTerminal();
    }
}

function closeTerminalModal() {
    document.getElementById('terminalModal').classList.add('hidden');
    if (ws) {
        stopClaudeTerminal();
    }
}

function openTerminalTab() {
    // Create standalone terminal page
    const terminalWindow = window.open('', '_blank');
    terminalWindow.document.write(`
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Code Terminal</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1e1e1e;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .header {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            color: #fff;
            margin: 0;
            font-size: 20px;
        }
        .controls {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .btn-success { background: #48bb78; color: white; }
        .btn-danger { background: #f56565; color: white; }
        .btn-secondary { background: #718096; color: white; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        #terminal-container {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 10px;
            height: calc(100vh - 150px);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Claude Code Terminal</h1>
        <div class="controls">
            <button id="startBtn" class="btn btn-success">Запустить</button>
            <button id="stopBtn" class="btn btn-danger" disabled>Остановить</button>
            <button id="clearBtn" class="btn btn-secondary">Очистить</button>
        </div>
    </div>
    <div id="terminal-container"></div>
    
    <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
    <script>
        let term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Courier New, monospace',
            theme: {
                background: '#1e1e1e',
                foreground: '#d4d4d4',
                cursor: '#ffffff'
            }
        });
        
        let fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
        term.open(document.getElementById('terminal-container'));
        fitAddon.fit();
        
        term.writeln('\\x1b[1;32mClaude Code Terminal\\x1b[0m');
        term.writeln('Нажмите "Запустить" для начала работы\\n');
        
        let ws = null;
        
        document.getElementById('startBtn').onclick = () => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(\`\${protocol}//\${window.location.host}/ws/terminal\`);
            
            ws.onopen = () => {
                term.writeln('\\x1b[1;32m[Подключено]\\x1b[0m\\n');
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
            };
            
            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'output') {
                    term.write(msg.data);
                }
            };
            
            ws.onclose = () => {
                term.writeln('\\n\\x1b[1;33m[Отключено]\\x1b[0m\\n');
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            };
            
            term.onData(data => {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'input', data: data }));
                }
            });
        };
        
        document.getElementById('stopBtn').onclick = () => {
            if (ws) ws.close();
        };
        
        document.getElementById('clearBtn').onclick = () => {
            term.clear();
        };
        
        window.addEventListener('resize', () => fitAddon.fit());
    </script>
</body>
</html>
    `);
}

// Update event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('openTerminalModalBtn').addEventListener('click', openTerminalModal);
    document.getElementById('openTerminalTabBtn').addEventListener('click', openTerminalTab);
    document.getElementById('closeTerminalModalBtn').addEventListener('click', closeTerminalModal);
    
    // Close modal on outside click
    document.getElementById('terminalModal').addEventListener('click', (e) => {
        if (e.target.id === 'terminalModal') {
            closeTerminalModal();
        }
    });
});

// Function to open container logs page
function openContainerLogs(nodeId, vmId, vmType) {
    const url = `/logs?node=${encodeURIComponent(nodeId)}&vmid=${encodeURIComponent(vmId)}&type=${encodeURIComponent(vmType)}`;
    window.location.href = url;
}
