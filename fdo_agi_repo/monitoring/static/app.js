// API Base URL
const API_BASE = '';

// Chart instances
let successRateChart = null;
let responseTimeChart = null;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 RPA Monitoring Dashboard initialized');

    // Initialize charts
    initializeCharts();

    // Load initial data
    loadDashboardData();

    // Auto-refresh every 3 seconds
    setInterval(loadDashboardData, 3000);
});

// Initialize Chart.js charts
function initializeCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };

    // Success Rate Chart
    const successCtx = document.getElementById('success-rate-chart').getContext('2d');
    successRateChart = new Chart(successCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Success Rate (%)',
                data: [],
                borderColor: '#48bb78',
                backgroundColor: 'rgba(72, 187, 120, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Response Time Chart
    const responseCtx = document.getElementById('response-time-chart').getContext('2d');
    responseTimeChart = new Chart(responseCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Avg Response Time (ms)',
                data: [],
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: '#667eea',
                borderWidth: 1
            }]
        },
        options: commonOptions
    });
}

// Load all dashboard data
async function loadDashboardData() {
    try {
        // Load system status
        await loadSystemStatus();

        // Load metrics history
        await loadMetricsHistory();

        // Load recent alerts
        await loadRecentAlerts();

        // Update timestamp
        updateTimestamp();
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

// Load system status (current metrics)
async function loadSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/system/status`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Update status cards
        updateStatusCard('success-rate', `${data.success_rate.toFixed(1)}%`);
        updateStatusCard('avg-response', `${data.avg_response_time_ms.toFixed(0)}`);
        updateStatusCard('active-workers', data.active_workers);
        updateStatusCard('queue-size', data.queue_size);

        // Update success rate indicator
        updateSuccessIndicator(data.success_rate);

    } catch (error) {
        console.error('Failed to load system status:', error);
    }
}

// Load metrics history for charts
async function loadMetricsHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics/history?minutes=30`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const metrics = data.metrics || [];

        if (metrics.length === 0) {
            return;
        }

        // Extract timestamps and values
        const timestamps = metrics.map(m => formatTime(m.timestamp));
        const successRates = metrics.map(m => m.success_rate || 0);
        const responseTimes = metrics.map(m => m.avg_response_time_ms || 0);

        // Update Success Rate Chart
        successRateChart.data.labels = timestamps;
        successRateChart.data.datasets[0].data = successRates;
        successRateChart.update('none'); // No animation

        // Update Response Time Chart
        responseTimeChart.data.labels = timestamps;
        responseTimeChart.data.datasets[0].data = responseTimes;
        responseTimeChart.update('none');

    } catch (error) {
        console.error('Failed to load metrics history:', error);
    }
}

// Load recent alerts
async function loadRecentAlerts() {
    try {
        const response = await fetch(`${API_BASE}/api/alerts/recent?count=10`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const alerts = data.alerts || [];

        // Render alerts
        renderAlerts(alerts);

    } catch (error) {
        console.error('Failed to load alerts:', error);
    }
}

// Render alerts in the list
function renderAlerts(alerts) {
    const container = document.getElementById('alerts-container');

    if (alerts.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center;">No recent alerts</p>';
        return;
    }

    container.innerHTML = alerts.map(alert => {
        const severity = alert.severity.toLowerCase();
        const icon = getSeverityIcon(severity);
        const time = formatFullTime(alert.timestamp);

        return `
            <div class="alert-item ${severity}">
                <div>
                    <span class="alert-severity ${severity}">${icon} ${alert.severity}</span>
                    <span class="alert-message">${alert.message}</span>
                </div>
                <span class="alert-time">${time}</span>
            </div>
        `;
    }).join('');
}

// Update status card value
function updateStatusCard(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Update success rate indicator (color dot)
function updateSuccessIndicator(successRate) {
    const indicator = document.getElementById('success-indicator');
    if (!indicator) return;

    if (successRate >= 90) {
        indicator.textContent = '●';
        indicator.className = 'card-indicator status-healthy';
    } else if (successRate >= 70) {
        indicator.textContent = '●';
        indicator.className = 'card-indicator status-degraded';
    } else {
        indicator.textContent = '●';
        indicator.className = 'card-indicator status-error';
    }
}

// Update last updated timestamp
function updateTimestamp() {
    const element = document.getElementById('last-updated');
    if (element) {
        const now = new Date();
        element.textContent = `Last updated: ${now.toLocaleTimeString()}`;
    }
}

// Format timestamp to HH:MM:SS
function formatTime(timestamp) {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
}

// Format timestamp to full datetime
function formatFullTime(timestamp) {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    return date.toLocaleString('ko-KR', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// Get severity icon
function getSeverityIcon(severity) {
    switch (severity) {
        case 'critical': return '🚨';
        case 'warning': return '⚠️';
        case 'info': return 'ℹ️';
        default: return '📢';
    }
}

// Manual refresh button
function refreshData() {
    console.log('🔄 Manual refresh triggered');
    loadDashboardData();
}

// WebSocket connection (optional - for real-time push)
function connectWebSocket() {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/metrics');

    ws.onopen = () => {
        console.log('✅ WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message:', data);

        // Update status cards in real-time
        updateStatusCard('success-rate', `${data.success_rate.toFixed(1)}%`);
        updateStatusCard('avg-response', `${data.avg_response_time_ms.toFixed(0)}`);
        updateStatusCard('active-workers', data.active_workers);
        updateStatusCard('queue-size', data.queue_size);
        updateSuccessIndicator(data.success_rate);
    };

    ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('❌ WebSocket disconnected - reconnecting in 5s...');
        setTimeout(connectWebSocket, 5000);
    };
}

// Uncomment to enable WebSocket
// connectWebSocket();
