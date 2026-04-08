let mainChart, lightMotionChart, alertChart;
let currentData = [];
let updateInterval;
let visibleDatasets = {
    temperature: true,
    humidity: true,
    gas: true,
    vibration: false
};

$(document).ready(function() {
    initializeCharts();
    loadData();
    startRealTimeUpdates();
    setupEventListeners();
});

function initializeCharts() {
    // Main Chart with multiple datasets
    const ctx = document.getElementById('mainChart').getContext('2d');
    mainChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    hidden: false,
                    yAxisID: 'y'
                },
                {
                    label: 'Humidity (%)',
                    data: [],
                    borderColor: '#4ecdc4',
                    backgroundColor: 'rgba(78, 205, 196, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    hidden: false,
                    yAxisID: 'y1'
                },
                {
                    label: 'Gas Level (ppm)',
                    data: [],
                    borderColor: '#ffd93d',
                    backgroundColor: 'rgba(255, 217, 61, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    hidden: false,
                    yAxisID: 'y2'
                },
                {
                    label: 'Vibration (mm/s)',
                    data: [],
                    borderColor: '#a8e6cf',
                    backgroundColor: 'rgba(168, 230, 207, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    hidden: true,
                    yAxisID: 'y3'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Temperature (°C)',
                        color: '#ff6b6b'
                    },
                    position: 'left'
                },
                y1: {
                    title: {
                        display: true,
                        text: 'Humidity (%)',
                        color: '#4ecdc4'
                    },
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    }
                },
                y2: {
                    title: {
                        display: true,
                        text: 'Gas Level (ppm)',
                        color: '#ffd93d'
                    },
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    offset: true
                },
                y3: {
                    title: {
                        display: true,
                        text: 'Vibration (mm/s)',
                        color: '#a8e6cf'
                    },
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    offset: true
                }
            }
        }
    });
    
    // Light & Motion Chart
    const ctx2 = document.getElementById('lightMotionChart').getContext('2d');
    lightMotionChart = new Chart(ctx2, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Light Level (lux)',
                    data: [],
                    borderColor: '#2196f3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Motion Detected',
                    data: [],
                    borderColor: '#ff9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.2)',
                    borderWidth: 2,
                    stepped: true,
                    borderDash: [5, 5],
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === 'Motion Detected') {
                                return context.parsed.y === 1 ? 'Motion Detected' : 'No Motion';
                            }
                            return `${context.dataset.label}: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Light Level (lux)'
                    }
                },
                y1: {
                    title: {
                        display: true,
                        text: 'Motion'
                    },
                    position: 'right',
                    min: 0,
                    max: 1,
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            return value === 1 ? 'Motion' : 'No Motion';
                        }
                    }
                }
            }
        }
    });
    
    // Alert Distribution Chart
    const ctx3 = document.getElementById('alertChart').getContext('2d');
    alertChart = new Chart(ctx3, {
        type: 'doughnut',
        data: {
            labels: ['Normal', 'Alerts'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#4caf50', '#ff9800'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function loadData() {
    const startDate = $('#startDate').val();
    const endDate = $('#endDate').val();
    
    let url = '/api/data';
    const params = [];
    if (startDate) params.push(`start_date=${startDate}`);
    if (endDate) params.push(`end_date=${endDate}`);
    if (params.length) url += '?' + params.join('&');
    
    $.get(url, function(data) {
        currentData = data;
        updateCharts(data);
        updateStatistics(data);
        updateAlerts(data);
        updateDataTable(data);
        updateKPIs(data);
        updateLastUpdate();
    });
    
    // Load latest for real-time KPI
    $.get('/api/latest', function(latest) {
        if (latest && Object.keys(latest).length) {
            updateRealtimeKPI(latest);
        }
    });
}

function updateCharts(data) {
    const timestamps = data.map(d => d.timestamp);
    
    // Update main chart
    mainChart.data.labels = timestamps;
    mainChart.data.datasets[0].data = data.map(d => d.temperature);
    mainChart.data.datasets[1].data = data.map(d => d.humidity);
    mainChart.data.datasets[2].data = data.map(d => d.gas_level);
    mainChart.data.datasets[3].data = data.map(d => d.vibration);
    mainChart.update();
    
    // Update light & motion chart
    lightMotionChart.data.labels = timestamps;
    lightMotionChart.data.datasets[0].data = data.map(d => d.light_level);
    lightMotionChart.data.datasets[1].data = data.map(d => d.motion_detected);
    lightMotionChart.update();
    
    // Update alert chart
    const normalCount = data.filter(d => d.alert_flag === 0).length;
    const alertCount = data.filter(d => d.alert_flag === 1).length;
    alertChart.data.datasets[0].data = [normalCount, alertCount];
    alertChart.update();
}

function updateStatistics(data) {
    if (!data.length) return;
    
    const temps = data.map(d => d.temperature);
    const humidities = data.map(d => d.humidity);
    const gases = data.map(d => d.gas_level);
    const vibrations = data.map(d => d.vibration);
    
    const stats = {
        temperature: {
            avg: (temps.reduce((a,b) => a+b, 0) / temps.length).toFixed(2),
            min: Math.min(...temps).toFixed(2),
            max: Math.max(...temps).toFixed(2)
        },
        humidity: {
            avg: (humidities.reduce((a,b) => a+b, 0) / humidities.length).toFixed(2),
            min: Math.min(...humidities).toFixed(2),
            max: Math.max(...humidities).toFixed(2)
        },
        gas: {
            avg: (gases.reduce((a,b) => a+b, 0) / gases.length).toFixed(2),
            min: Math.min(...gases).toFixed(2),
            max: Math.max(...gases).toFixed(2)
        },
        vibration: {
            avg: (vibrations.reduce((a,b) => a+b, 0) / vibrations.length).toFixed(2),
            min: Math.min(...vibrations).toFixed(2),
            max: Math.max(...vibrations).toFixed(2)
        }
    };
    
    const html = `
        <div class="stat-item">
            <div class="stat-label">Temperature</div>
            <div class="stat-value">${stats.temperature.avg}°C</div>
            <div class="stat-range">Range: ${stats.temperature.min} - ${stats.temperature.max}°C</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Humidity</div>
            <div class="stat-value">${stats.humidity.avg}%</div>
            <div class="stat-range">Range: ${stats.humidity.min} - ${stats.humidity.max}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Gas Level</div>
            <div class="stat-value">${stats.gas.avg} ppm</div>
            <div class="stat-range">Range: ${stats.gas.min} - ${stats.gas.max} ppm</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Vibration</div>
            <div class="stat-value">${stats.vibration.avg} mm/s</div>
            <div class="stat-range">Range: ${stats.vibration.min} - ${stats.vibration.max} mm/s</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Total Readings</div>
            <div class="stat-value">${data.length}</div>
        </div>
    `;
    
    $('#statisticsContent').html(html);
}

function updateAlerts(data) {
    const alerts = data.filter(d => d.alert_flag === 1).slice(-10).reverse();
    $('#alertsCount').text(alerts.length);
    
    if (alerts.length === 0) {
        $('#alertsList').html('<div class="text-center p-4">No active alerts</div>');
        return;
    }
    
    const alertsHtml = alerts.map(alert => `
        <div class="alert-item ${alert.alerts.length > 2 ? 'alert-critical' : 'alert-warning'}">
            <div>
                <strong>${new Date(alert.timestamp).toLocaleString()}</strong>
                <div>${alert.alerts.join(', ')}</div>
            </div>
            <div>
                <span class="badge">${alert.gas_level} ppm</span>
                ${alert.motion_detected ? '<i class="fas fa-running"></i>' : ''}
            </div>
        </div>
    `).join('');
    
    $('#alertsList').html(alertsHtml);
}

function updateDataTable(data) {
    const searchTerm = $('#tableSearch').val().toLowerCase();
    const filteredData = searchTerm ? 
        data.filter(row => 
            row.timestamp.toLowerCase().includes(searchTerm) ||
            row.alerts.join(',').toLowerCase().includes(searchTerm)
        ) : data;
    
    const rows = filteredData.slice().reverse().map(row => `
        <tr class="${row.alert_flag === 1 ? 'alert-row' : ''}">
            <td>${new Date(row.timestamp).toLocaleString()}</td>
            <td>${row.temperature}°C</td>
            <td>${row.humidity}%</td>
            <td>${row.gas_level} ppm</td>
            <td>${row.light_level} lux</td>
            <td>${row.vibration} mm/s</td>
            <td>${row.motion_detected ? '<i class="fas fa-running"></i> Yes' : '<i class="fas fa-ban"></i> No'}</td>
            <td><span class="status-badge ${row.alert_flag === 1 ? 'status-alert' : 'status-normal'}">
                ${row.alert_flag === 1 ? 'Alert' : 'Normal'}
            </span></td>
            <td>${row.alerts.join(', ')}</td>
        </tr>
    `).join('');
    
    $('#tableBody').html(rows || '<tr><td colspan="9" class="text-center">No data found</td></tr>');
}

function updateKPIs(data) {
    if (!data.length) return;
    
    const latest = data[data.length - 1];
    const previous = data[data.length - 2];
    
    if (previous) {
        updateTrend('tempTrend', latest.temperature, previous.temperature, '°C');
        updateTrend('humidityTrend', latest.humidity, previous.humidity, '%');
        updateTrend('gasTrend', latest.gas_level, previous.gas_level, 'ppm');
        updateTrend('vibrationTrend', latest.vibration, previous.vibration, 'mm/s');
    }
}

function updateRealtimeKPI(latest) {
    $('#currentTemp').html(`${latest.temperature}°C`);
    $('#currentHumidity').html(`${latest.humidity}%`);
    $('#currentGas').html(`${latest.gas_level} ppm`);
    $('#currentVibration').html(`${latest.vibration} mm/s`);
}

function updateTrend(elementId, current, previous, unit) {
    const change = ((current - previous) / previous * 100).toFixed(1);
    const trendClass = change > 0 ? 'trend-up' : 'trend-down';
    const icon = change > 0 ? '↑' : '↓';
    $(`#${elementId}`).html(`${icon} ${Math.abs(change)}% ${unit} from last reading`).removeClass('trend-up trend-down').addClass(trendClass);
}

function updateLastUpdate() {
    const now = new Date();
    $('#lastUpdate').html(`Last updated: ${now.toLocaleString()}`);
}

function startRealTimeUpdates() {
    updateInterval = setInterval(() => {
        loadData();
    }, 30000); // Update every 30 seconds
}

function applyDateFilter() {
    loadData();
    Swal.fire({
        icon: 'success',
        title: 'Filter Applied',
        text: 'Data has been filtered based on selected date range',
        timer: 2000,
        showConfirmButton: false
    });
}

function resetDateFilter() {
    $('#startDate').val('');
    $('#endDate').val('');
    loadData();
    Swal.fire({
        icon: 'info',
        title: 'Filter Reset',
        text: 'Showing all available data',
        timer: 2000,
        showConfirmButton: false
    });
}

function refreshData() {
    loadData();
    Swal.fire({
        icon: 'success',
        title: 'Refreshed',
        text: 'Dashboard data has been updated',
        timer: 1500,
        showConfirmButton: false
    });
}

function exportData() {
    if (!currentData.length) {
        Swal.fire('Error', 'No data to export', 'error');
        return;
    }
    
    const csv = convertToCSV(currentData);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sensor_data_${new Date().toISOString()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    Swal.fire('Success', 'Data exported successfully', 'success');
}

function convertToCSV(data) {
    const headers = ['timestamp', 'temperature', 'humidity', 'gas_level', 'light_level', 'vibration', 'motion_detected', 'alert_flag', 'alerts'];
    const rows = data.map(row => headers.map(header => {
        let value = row[header];
        if (Array.isArray(value)) value = value.join(';');
        return JSON.stringify(value);
    }).join(','));
    return [headers.join(','), ...rows].join('\n');
}

function toggleDataset(dataset) {
    const index = {
        'temperature': 0,
        'humidity': 1,
        'gas': 2,
        'vibration': 3
    }[dataset];
    
    visibleDatasets[dataset] = !visibleDatasets[dataset];
    mainChart.data.datasets[index].hidden = !visibleDatasets[dataset];
    mainChart.update();
}

function setupEventListeners() {
    $('#tableSearch').on('keyup', function() {
        updateDataTable(currentData);
    });
}

// Cleanup on page unload
$(window).on('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});