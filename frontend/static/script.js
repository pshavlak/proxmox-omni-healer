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
                <div class="resource-item">
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
