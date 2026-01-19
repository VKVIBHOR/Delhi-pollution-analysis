/**
 * Delhi Pollution Policy Simulator - Frontend Application
 * Handles all UI interactions and API communication
 */

// ============================================================================
// Configuration
// ============================================================================
const API_BASE = window.location.origin;

// Chart colors matching CSS theme
const CHART_COLORS = {
    pm25: 'rgba(239, 68, 68, 0.8)',
    pm10: 'rgba(245, 158, 11, 0.8)',
    baseline: 'rgba(100, 116, 139, 0.5)',
    delhi: '#ef4444',
    global: '#10b981',
    experimental: '#f59e0b',
    scenarios: [
        'rgba(99, 102, 241, 0.8)',   // primary
        'rgba(239, 68, 68, 0.8)',    // red
        'rgba(16, 185, 129, 0.8)',   // green
        'rgba(245, 158, 11, 0.8)',   // orange
        'rgba(236, 72, 153, 0.8)',   // pink
        'rgba(139, 92, 246, 0.8)',   // purple
    ]
};

// AQI thresholds for coloring
const AQI_THRESHOLDS = {
    good: 30,
    satisfactory: 60,
    moderate: 90,
    poor: 120,
    veryPoor: 250,
    severe: 380
};

// ============================================================================
// State
// ============================================================================
let pollutionChart = null;
let comparisonChart = null;
let policiesData = [];
let scenariosData = [];

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadPolicies();
    loadScenarios();
    loadRankings();
    loadWaterAnalysis();
    initEventListeners();
});

// ============================================================================
// Navigation
// ============================================================================
function initNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.dataset.section;
            showSection(section);
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
}

// ============================================================================
// Event Listeners
// ============================================================================
function initEventListeners() {
    // Duration slider
    const durationSlider = document.getElementById('duration-slider');
    const durationValue = document.getElementById('duration-value');
    durationSlider.addEventListener('input', () => {
        durationValue.textContent = `${durationSlider.value} days`;
    });

    // Scenario select
    document.getElementById('scenario-select').addEventListener('change', (e) => {
        if (e.target.value) {
            // Clear individual policy selections when scenario is chosen
            document.querySelectorAll('.policy-item input').forEach(cb => cb.checked = false);
        }
    });

    // Run simulation button
    document.getElementById('run-simulation').addEventListener('click', runSimulation);

    // Run comparison button
    document.getElementById('run-comparison').addEventListener('click', runComparison);

    // Forecast sliders
    const windSlider = document.getElementById('forecast-wind');
    const tempSlider = document.getElementById('forecast-temp');
    const humiditySlider = document.getElementById('forecast-humidity');

    if (windSlider) {
        windSlider.addEventListener('input', () => {
            document.getElementById('wind-value').textContent = `${windSlider.value} km/h`;
        });
    }
    if (tempSlider) {
        tempSlider.addEventListener('input', () => {
            document.getElementById('temp-value').textContent = `${tempSlider.value}°C`;
        });
    }
    if (humiditySlider) {
        humiditySlider.addEventListener('input', () => {
            document.getElementById('humidity-value').textContent = `${humiditySlider.value}%`;
        });
    }

    // Run forecast button
    const forecastBtn = document.getElementById('run-forecast');
    if (forecastBtn) {
        forecastBtn.addEventListener('click', runForecast);
    }
}

// ============================================================================
// API Functions
// ============================================================================
async function loadPolicies() {
    try {
        const response = await fetch(`${API_BASE}/api/policies`);
        const data = await response.json();
        policiesData = data.policies;
        renderPolicies(data.policies);
    } catch (error) {
        console.error('Failed to load policies:', error);
    }
}

async function loadScenarios() {
    try {
        const response = await fetch(`${API_BASE}/api/scenarios`);
        const data = await response.json();
        scenariosData = data.scenarios;
        renderScenarios(data.scenarios);
    } catch (error) {
        console.error('Failed to load scenarios:', error);
    }
}

async function loadRankings() {
    try {
        const response = await fetch(`${API_BASE}/api/rankings`);
        const data = await response.json();
        renderRankings(data);
    } catch (error) {
        console.error('Failed to load rankings:', error);
    }
}

async function loadWaterAnalysis() {
    try {
        const response = await fetch(`${API_BASE}/api/water-analysis`);
        const data = await response.json();
        renderWaterAnalysis(data);
    } catch (error) {
        console.error('Failed to load water analysis:', error);
    }
}

async function runSimulation() {
    const btn = document.getElementById('run-simulation');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Running...';

    try {
        const scenario = document.getElementById('scenario-select').value;
        const weather = document.getElementById('weather-select').value;
        const days = parseInt(document.getElementById('duration-slider').value);

        let body;
        if (scenario) {
            body = { scenario };
        } else {
            // Get selected policies
            const policies = [];
            document.querySelectorAll('.policy-item input:checked').forEach(cb => {
                policies.push(cb.value);
            });
            body = { policies, weather, days };
        }

        const response = await fetch(`${API_BASE}/api/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        if (data.success) {
            renderSimulationResults(data.result);
        } else {
            alert('Simulation failed: ' + data.error);
        }
    } catch (error) {
        console.error('Simulation error:', error);
        alert('Failed to run simulation');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">▶️</span> Run Simulation';
    }
}

async function runComparison() {
    const btn = document.getElementById('run-comparison');
    btn.disabled = true;
    btn.textContent = 'Comparing...';

    try {
        const scenarios = [];
        document.querySelectorAll('#comparison-scenarios input:checked').forEach(cb => {
            scenarios.push(cb.value);
        });

        if (scenarios.length < 2) {
            alert('Please select at least 2 scenarios to compare');
            return;
        }

        const response = await fetch(`${API_BASE}/api/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenarios })
        });

        const data = await response.json();
        if (data.success) {
            renderComparisonResults(data);
        }
    } catch (error) {
        console.error('Comparison error:', error);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Compare Selected Scenarios';
    }
}

// ============================================================================
// Render Functions
// ============================================================================
function renderPolicies(policies) {
    const containers = {
        delhi: document.getElementById('delhi-policies'),
        global: document.getElementById('global-policies'),
        experimental: document.getElementById('experimental-policies')
    };

    // Clear containers
    Object.values(containers).forEach(c => c.innerHTML = '');

    policies.forEach(policy => {
        const container = containers[policy.category];
        if (!container) return;

        const item = document.createElement('div');
        item.className = 'policy-item';
        item.innerHTML = `
            <input type="checkbox" id="policy-${policy.name}" value="${policy.name}">
            <label for="policy-${policy.name}" title="${policy.description}">
                ${policy.display_name}
            </label>
        `;
        container.appendChild(item);
    });
}

function renderScenarios(scenarios) {
    // Populate scenario select
    const select = document.getElementById('scenario-select');
    scenarios.forEach(scenario => {
        const option = document.createElement('option');
        option.value = scenario.name;
        option.textContent = scenario.display_name;
        option.title = scenario.description;
        select.appendChild(option);
    });

    // Populate comparison checkboxes
    const checkboxContainer = document.getElementById('comparison-scenarios');
    scenarios.forEach(scenario => {
        const label = document.createElement('label');
        label.className = 'scenario-checkbox';
        label.innerHTML = `
            <input type="checkbox" value="${scenario.name}" 
                ${['baseline', 'delhi_current', 'global_best'].includes(scenario.name) ? 'checked' : ''}>
            ${scenario.display_name}
        `;
        checkboxContainer.appendChild(label);
    });
}

function renderSimulationResults(result) {
    // Update stats
    document.getElementById('stat-pm25').textContent = result.stats.pm25.mean.toFixed(0);
    document.getElementById('stat-pm10').textContent = result.stats.pm10.mean.toFixed(0);
    document.getElementById('stat-severe').textContent = result.stats.severe_hours;
    document.getElementById('stat-good').textContent = result.stats.good_hours;

    // Color code PM2.5 based on level
    const pm25Value = document.getElementById('stat-pm25');
    const pm25 = result.stats.pm25.mean;
    pm25Value.className = 'stat-value ' + getAQIClass(pm25);

    // Render chart
    renderPollutionChart(result.history);

    // Generate and show insight
    const insight = generateInsight(result);
    document.getElementById('insights-list').innerHTML = `
        <div class="insight-item">${insight}</div>
    `;
}

function renderPollutionChart(history) {
    const ctx = document.getElementById('pollution-chart').getContext('2d');

    // Sample data for readability (every 6 hours)
    const sampledHistory = history.filter((_, i) => i % 6 === 0);
    const labels = sampledHistory.map(h => h.timestamp);
    const pm25Data = sampledHistory.map(h => h.pm25);
    const pm10Data = sampledHistory.map(h => h.pm10);

    if (pollutionChart) {
        pollutionChart.destroy();
    }

    pollutionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'PM2.5',
                    data: pm25Data,
                    borderColor: CHART_COLORS.pm25,
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                },
                {
                    label: 'PM10',
                    data: pm10Data,
                    borderColor: CHART_COLORS.pm10,
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f8fafc' }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: {
                        color: '#94a3b8',
                        maxTicksLimit: 10
                    }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: {
                        display: true,
                        text: 'Concentration (µg/m³)',
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

function renderComparisonResults(data) {
    const comparisons = data.comparison.comparisons;

    // Render comparison chart
    renderComparisonChart(comparisons);

    // Render comparison table
    const tbody = document.querySelector('#comparison-table tbody');
    tbody.innerHTML = comparisons.map((c, i) => `
        <tr class="${i < 3 ? 'rank-' + (i + 1) : ''}">
            <td>#${c.rank}</td>
            <td>${c.display_name}</td>
            <td>${c.pm25_mean.toFixed(0)} µg/m³</td>
            <td>${c.pm25_reduction_pct >= 0 ? '+' : ''}${c.pm25_reduction_pct.toFixed(1)}%</td>
            <td>${c.severe_hours}</td>
            <td>${c.good_hours}</td>
        </tr>
    `).join('');

    // Render insights
    const insightsContainer = document.getElementById('comparison-insights');
    insightsContainer.innerHTML = data.insights.map(i =>
        `<div class="insight-item">${formatInsight(i)}</div>`
    ).join('');
}

function renderComparisonChart(comparisons) {
    const ctx = document.getElementById('comparison-chart').getContext('2d');

    if (comparisonChart) {
        comparisonChart.destroy();
    }

    comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: comparisons.map(c => c.display_name),
            datasets: [
                {
                    label: 'PM2.5 Reduction (%)',
                    data: comparisons.map(c => c.pm25_reduction_pct),
                    backgroundColor: comparisons.map((_, i) => CHART_COLORS.scenarios[i % CHART_COLORS.scenarios.length]),
                    borderRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: {
                        display: true,
                        text: 'PM2.5 Reduction (%)',
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

function renderRankings(data) {
    // Render comparison matrix
    const matrixBody = document.getElementById('matrix-body');
    matrixBody.innerHTML = data.comparison_matrix.map(row => `
        <tr>
            <td><strong>${row.measure}</strong></td>
            <td>${row.delhi_uses}</td>
            <td>${row.global_uses}</td>
            <td>${row.effectiveness}</td>
            <td><em>${row.why}</em></td>
        </tr>
    `).join('');

    // Render overall rankings
    const rankingsList = document.getElementById('rankings-list');
    rankingsList.innerHTML = data.rankings.map(r => `
        <div class="ranking-item">
            <span class="ranking-rank ${r.rank <= 3 ? 'top-3' : ''}">#${r.rank}</span>
            <span class="ranking-name">
                ${r.display_name}
                <span class="ranking-category ${r.category}">${r.category}</span>
            </span>
            <span class="hide-mobile">🎯 ${r.pollution_score}</span>
            <span class="hide-mobile">💰 ${r.cost_score}</span>
            <span class="hide-mobile">♻️ ${r.sustainability_score}</span>
            <span class="hide-mobile">📊 ${r.economic_impact_score}</span>
            <span class="ranking-score">${r.overall_score}/10</span>
        </div>
    `).join('');

    // Render top recommendations
    const recommendationsList = document.getElementById('recommendations-list');
    recommendationsList.innerHTML = data.top_recommendations.map(r => `
        <div class="recommendation-card">
            <span class="recommendation-rank">#${r.rank}</span>
            <div class="recommendation-content">
                <h4>${r.name}</h4>
                <p>${r.description}</p>
                <span class="recommendation-benefit">✓ Key benefit: ${r.key_benefit}</span>
            </div>
        </div>
    `).join('');
}

function renderWaterAnalysis(data) {
    if (!data.success) return;

    // Update equivalence number
    const match = data.analysis.equivalence.match(/(\d+)/);
    if (match) {
        document.getElementById('water-equivalence').textContent = match[1];
    }

    // Render sections
    const sectionsContainer = document.getElementById('water-sections');
    sectionsContainer.innerHTML = data.deep_dive.sections.map(section => `
        <div class="water-section">
            <h4>${section.heading}</h4>
            <p>${section.content}</p>
        </div>
    `).join('');

    // Render key insight
    const keyInsightBox = document.getElementById('water-key-insight');
    keyInsightBox.querySelector('p').textContent = data.deep_dive.key_insight;
}

// ============================================================================
// Helper Functions
// ============================================================================
function getAQIClass(pm25) {
    if (pm25 <= AQI_THRESHOLDS.good) return 'good';
    if (pm25 <= AQI_THRESHOLDS.satisfactory) return 'good';
    if (pm25 <= AQI_THRESHOLDS.moderate) return 'moderate';
    if (pm25 <= AQI_THRESHOLDS.poor) return 'poor';
    return 'severe';
}

function generateInsight(result) {
    const pm25 = result.stats.pm25.mean;
    const severeHours = result.stats.severe_hours;
    const totalHours = result.stats.total_hours;
    const severePct = ((severeHours / totalHours) * 100).toFixed(0);

    let insight = `**Simulation Complete**: Average PM2.5 of ${pm25.toFixed(0)} µg/m³. `;

    if (pm25 > 250) {
        insight += `Air quality remained in 'Very Poor' to 'Severe' category for ${severePct}% of the simulation period. `;
        insight += `The selected policies are insufficient to bring pollution to safe levels.`;
    } else if (pm25 > 120) {
        insight += `Air quality was in 'Poor' category. Some improvement seen but more aggressive measures needed.`;
    } else if (pm25 > 60) {
        insight += `Air quality improved to 'Moderate' levels. This is a meaningful reduction but still unhealthy for sensitive groups.`;
    } else {
        insight += `Excellent result! Air quality reached 'Satisfactory' levels for significant periods.`;
    }

    return insight;
}

function formatInsight(text) {
    // Convert markdown-style bold to HTML
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// ============================================================================
// ML Forecast Functions
// ============================================================================
async function runForecast() {
    const btn = document.getElementById('run-forecast');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Predicting...';

    try {
        // Get current values
        const currentPm25 = parseFloat(document.getElementById('forecast-pm25').value) || 150;
        const currentPm10 = parseFloat(document.getElementById('forecast-pm10').value) || 300;
        const windSpeed = parseFloat(document.getElementById('forecast-wind').value) || 8;
        const temperature = parseFloat(document.getElementById('forecast-temp').value) || 20;
        const humidity = parseFloat(document.getElementById('forecast-humidity').value) || 60;
        const isInversion = document.getElementById('forecast-inversion').checked;

        // Get selected policies
        const activePolicies = [];
        document.querySelectorAll('#forecast .policy-checkboxes input:checked').forEach(cb => {
            activePolicies.push(cb.value);
        });

        const response = await fetch(`${API_BASE}/api/forecast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_pm25: currentPm25,
                current_pm10: currentPm10,
                wind_speed: windSpeed,
                temperature: temperature,
                humidity: humidity,
                is_inversion: isInversion,
                active_policies: activePolicies,
            })
        });

        const data = await response.json();
        if (data.success) {
            renderForecastResults(data.forecast);
        } else {
            alert('Forecast failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Forecast error:', error);
        alert('Failed to run forecast');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">🔮</span> Predict Next-Day AQI';
    }
}

function renderForecastResults(forecast) {
    // Update predicted PM2.5
    document.getElementById('predicted-pm25').textContent = forecast.predicted_pm25;

    // Update AQI category with color
    const categoryBadge = document.getElementById('category-badge');
    categoryBadge.textContent = forecast.aqi_category;
    categoryBadge.className = 'category-badge ' + getCategoryClass(forecast.aqi_category);

    // Update confidence
    document.getElementById('confidence-value').textContent =
        `${(forecast.confidence * 100).toFixed(0)}%`;

    // Update recommendation
    document.getElementById('recommendation-text').textContent = forecast.recommendation;

    // Update feature importance bars
    renderFeatureImportance(forecast.feature_importance);
}

function renderFeatureImportance(importance) {
    const container = document.getElementById('importance-bars');

    // Sort by importance
    const sorted = Object.entries(importance)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8); // Top 8 features

    const maxImportance = sorted[0][1];

    container.innerHTML = sorted.map(([feature, value]) => {
        const percentage = (value / maxImportance) * 100;
        const displayName = formatFeatureName(feature);
        return `
            <div class="importance-bar">
                <span class="label">${displayName}</span>
                <div class="bar-container">
                    <div class="bar" style="width: ${percentage}%"></div>
                </div>
                <span class="value">${(value * 100).toFixed(1)}%</span>
            </div>
        `;
    }).join('');
}

function formatFeatureName(name) {
    const names = {
        'current_pm25': 'Current PM2.5',
        'current_pm10': 'Current PM10',
        'wind_speed': 'Wind Speed',
        'temperature': 'Temperature',
        'humidity': 'Humidity',
        'is_inversion': 'Inversion',
        'hour': 'Hour',
        'day_of_week': 'Day of Week',
        'month': 'Month',
        'is_winter': 'Winter Season',
        'policy_water': 'Water Spray',
        'policy_oddeven': 'Odd-Even',
        'policy_construction': 'Constr. Ban',
        'policy_grap': 'GRAP',
        'policy_source_elim': 'Source Elim.',
        'policy_congestion': 'Congestion Price',
    };
    return names[name] || name;
}

function getCategoryClass(category) {
    const classes = {
        'Good': 'good',
        'Satisfactory': 'satisfactory',
        'Moderate': 'moderate',
        'Poor': 'poor',
        'Very Poor': 'very-poor',
        'Severe': 'severe',
    };
    return classes[category] || 'moderate';
}
