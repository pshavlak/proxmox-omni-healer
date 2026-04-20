// Logs page functionality
let currentNodeId = null;
let currentVmId = null;
let currentVmType = null;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    // Get parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentNodeId = urlParams.get('node');
    currentVmId = urlParams.get('vmid');
    currentVmType = urlParams.get('type') || 'qemu';

    if (!currentNodeId || !currentVmId) {
        document.getElementById('containerTitle').textContent = 'Ошибка: Не указаны параметры контейнера';
        return;
    }

    setupEventListeners();
    loadContainerInfo();
    loadLogs();
});

function setupEventListeners() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.filter;
            filterLogs();
        });
    });

    // Refresh logs button
    document.getElementById('refreshLogs').addEventListener('click', loadLogs);

    // Analyze button
    document.getElementById('analyzeBtn').addEventListener('click', analyzeLogs);
}

async function loadContainerInfo() {
    try {
        const response = await fetch(`/api/vm/${currentNodeId}/${currentVmId}/status?vm_type=${currentVmType}`);
        const data = await response.json();

        if (data.error) {
            document.getElementById('containerTitle').textContent = `Ошибка: ${data.error}`;
            return;
        }

        const typeIcon = currentVmType === 'qemu' ? '🖥️' : '📦';
        const typeName = currentVmType === 'qemu' ? 'VM' : 'LXC';

        document.getElementById('containerTitle').textContent =
            `${typeIcon} ${data.name || currentVmId} (${typeName})`;

        const containerInfo = document.getElementById('containerInfo');
        containerInfo.innerHTML = `
            <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value" style="color: ${data.status === 'running' ? '#48bb78' : '#f56565'}">
                    ${data.status || 'unknown'}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Узел</div>
                <div class="info-value">${currentNodeId}</div>
            </div>
            <div class="info-item">
                <div class="info-label">ID</div>
                <div class="info-value">${currentVmId}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Тип</div>
                <div class="info-value">${typeName}</div>
            </div>
            <div class="info-item">
                <div class="info-label">CPU</div>
                <div class="info-value">${data.cpu ? (data.cpu * 100).toFixed(1) + '%' : 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Память</div>
                <div class="info-value">${data.mem ? formatBytes(data.mem) : 'N/A'}</div>
            </div>
        `;
    } catch (error) {
        document.getElementById('containerTitle').textContent = `Ошибка загрузки: ${error.message}`;
    }
}

async function loadLogs() {
    const logsContent = document.getElementById('logsContent');
    logsContent.innerHTML = '<div class="loading">Загрузка логов...</div>';

    try {
        const response = await fetch(`/api/vm/${currentNodeId}/${currentVmId}/logs?vm_type=${currentVmType}&limit=200`);
        const data = await response.json();

        if (data.error) {
            logsContent.innerHTML = `<div class="error-message">${data.error}</div>`;
            return;
        }

        if (!data.logs || data.logs.length === 0) {
            logsContent.innerHTML = '<div style="color: #718096; text-align: center; padding: 20px;">Логи не найдены</div>';
            return;
        }

        displayLogs(data.logs);
        analyzeLogsForIssues(data.logs);
    } catch (error) {
        logsContent.innerHTML = `<div class="error-message">Ошибка загрузки: ${error.message}</div>`;
    }
}

function displayLogs(logs) {
    const logsContent = document.getElementById('logsContent');

    const html = logs.map(log => {
        const logType = detectLogType(log);
        const timestampMatch = log.match(/^([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})/); const timestamp = timestampMatch ? timestampMatch[1] : new Date().toLocaleString();

        return `
            <div class="log-entry ${logType}" data-type="${logType}">
                <div class="log-timestamp">${timestamp}</div>
                <div>${escapeHtml(log)}</div>
            </div>
        `;
    }).join('');

    logsContent.innerHTML = html;
    filterLogs();
}

function detectLogType(logLine) {
    const line = logLine.toLowerCase();

    if (line.includes('error') || line.includes('failed') || line.includes('fatal') ||
        line.includes('critical') || line.includes('exception')) {
        return 'error';
    }

    if (line.includes('warning') || line.includes('warn') || line.includes('deprecated')) {
        return 'warning';
    }

    return 'info';
}

function filterLogs() {
    const logEntries = document.querySelectorAll('.log-entry');

    logEntries.forEach(entry => {
        if (currentFilter === 'all' || entry.dataset.type === currentFilter) {
            entry.style.display = 'block';
        } else {
            entry.style.display = 'none';
        }
    });
}

function analyzeLogsForIssues(logs) {
    const issues = [];

    logs.forEach(log => {
        const line = log.toLowerCase();

        // Detect critical issues
        if (line.includes('out of memory') || line.includes('oom')) {
            issues.push({
                severity: 'critical',
                message: 'Недостаток памяти (OOM)',
                description: 'Система испытывает нехватку памяти',
                recommendation: 'Увеличить лимит памяти или оптимизировать приложения'
            });
        }

        if (line.includes('disk full') || line.includes('no space left')) {
            issues.push({
                severity: 'critical',
                message: 'Недостаток дискового пространства',
                description: 'Закончилось место на диске',
                recommendation: 'Очистить диск или увеличить размер'
            });
        }

        if (line.includes('connection refused') || line.includes('network unreachable')) {
            issues.push({
                severity: 'warning',
                message: 'Проблемы с сетью',
                description: 'Обнаружены сетевые ошибки',
                recommendation: 'Проверить сетевые настройки и подключения'
            });
        }

        if (line.includes('service failed') || line.includes('systemd')) {
            issues.push({
                severity: 'warning',
                message: 'Сбой системных служб',
                description: 'Некоторые службы работают некорректно',
                recommendation: 'Перезапустить проблемные службы'
            });
        }
    });

    if (issues.length > 0) {
        displayIssues(issues);
    }
}

function displayIssues(issues) {
    const issuesSummary = document.getElementById('issuesSummary');
    const issuesList = document.getElementById('issuesList');

    // Remove duplicates
    const uniqueIssues = issues.filter((issue, index, self) =>
        index === self.findIndex(i => i.message === issue.message)
    );

    const html = uniqueIssues.map(issue => `
        <div class="issue-item">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                <strong>${issue.message}</strong>
                <span class="issue-severity severity-${issue.severity}">${issue.severity}</span>
            </div>
            <div style="color: #4a5568; margin-bottom: 8px;">${issue.description}</div>
            <div style="color: #2d3748; font-weight: 500;">💡 ${issue.recommendation}</div>
        </div>
    `).join('');

    issuesList.innerHTML = html;
    issuesSummary.style.display = 'block';
}

async function analyzeLogs() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const recommendationsContent = document.getElementById('recommendationsContent');

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Анализируем...';
    recommendationsContent.innerHTML = '<div class="loading">ИИ анализирует логи...</div>';

    try {
        // Get current logs
        const response = await fetch(`/api/vm/${currentNodeId}/${currentVmId}/logs?vm_type=${currentVmType}&limit=100`);
        const data = await response.json();

        if (data.logs) {
            const analysisResponse = await fetch('/api/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    logs: data.logs.join('\n'),
                    context: `Node: ${currentNodeId}, VM/CT: ${currentVmId}, Type: ${currentVmType}`
                })
            });

            const analysis = await analysisResponse.json();

            if (analysis.error) {
                recommendationsContent.innerHTML = `<div class="error-message">${analysis.error}</div>`;
            } else if (analysis.message) {
                recommendationsContent.innerHTML = `<div style="color: #48bb78; text-align: center; padding: 20px;">✓ ${analysis.message}</div>`;
            } else {
                displayRecommendations(analysis);
            }
        }
    } catch (error) {
        recommendationsContent.innerHTML = `<div class="error-message">Ошибка анализа: ${error.message}</div>`;
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Анализировать проблемы';
    }
}

function displayRecommendations(analysis) {
    const recommendationsContent = document.getElementById('recommendationsContent');

    const html = `
        <div style="background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 15px; margin-bottom: 15px;">
            <h4 style="margin: 0 0 10px 0; color: #2d3748;">📋 Краткое описание</h4>
            <p style="margin: 0; color: #4a5568;">${analysis.summary || 'Анализ завершен'}</p>
        </div>

        <div style="background: #e6fffa; border: 1px solid #81e6d9; border-radius: 6px; padding: 15px; margin-bottom: 15px;">
            <h4 style="margin: 0 0 10px 0; color: #234e52;">🎯 Уровень уверенности</h4>
            <div style="background: #4fd1c7; height: 8px; border-radius: 4px; width: ${analysis.confidence || 50}%;"></div>
            <span style="font-size: 12px; color: #234e52;">${analysis.confidence || 50}%</span>
        </div>

        ${analysis.commands && analysis.commands.length > 0 ? `
        <div style="background: #fffaf0; border: 1px solid #fbd38d; border-radius: 6px; padding: 15px;">
            <h4 style="margin: 0 0 10px 0; color: #744210;">🔧 Рекомендуемые команды</h4>
            ${analysis.commands.map(cmd => `
                <div style="background: #2d3748; color: #e2e8f0; padding: 10px; border-radius: 4px; margin-bottom: 8px; font-family: monospace;">
                    ${escapeHtml(cmd)}
                </div>
            `).join('')}
            <button class="btn btn-success" onclick="executeRecommendations(${analysis.proposal_id || 0})" style="margin-top: 10px;">
                ▶ Выполнить рекомендации
            </button>
        </div>
        ` : ''}
    `;

    recommendationsContent.innerHTML = html;
}

async function executeRecommendations(proposalId) {
    if (!proposalId) {
        alert('Нет активных предложений для выполнения');
        return;
    }

    if (!confirm('Вы уверены, что хотите выполнить рекомендованные команды?')) {
        return;
    }

    try {
        const response = await fetch(`/api/proposals/${proposalId}/execute`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.results) {
            alert('Команды выполнены. Обновите логи для проверки результата.');
            loadLogs(); // Refresh logs
        } else {
            alert('Выполнение завершено');
        }
    } catch (error) {
        alert('Ошибка выполнения: ' + error.message);
    }
}

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}