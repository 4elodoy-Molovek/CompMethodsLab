const API_URL = 'http://127.0.0.1:5000';

let currentMatrixS = null;
let currentMassPerBatch = 1000;
let currentConfig = null;
let currentBatches = null;

async function runSimulation() {
    const config = {
        n: parseInt(document.getElementById('n').value),
        m: parseFloat(document.getElementById('m').value),
        a_min: parseFloat(document.getElementById('a_min').value),
        a_max: parseFloat(document.getElementById('a_max').value),
        beta1: parseFloat(document.getElementById('beta1').value),
        beta2: parseFloat(document.getElementById('beta2').value),
        distribution_type: document.querySelector('input[name="distType"]:checked').value,
        //enable_ripening: document.getElementById('enableRipening').checked,
        //v: parseInt(document.getElementById('v').value),
        //beta_max: parseFloat(document.getElementById('beta_max').value),
        use_losses: document.getElementById('useLosses').checked,
        growth_base: parseFloat(document.getElementById('growth_base').value),
        delta_k: parseInt(document.getElementById('delta_k').value),
        //delta_k_ripening: parseInt(document.getElementById('delta_k_ripening').value),
    };

    try {
        const response = await fetch(`${API_URL}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (!response.ok) throw new Error('Ошибка симуляции');

        const data = await response.json();

        renderMatrix('containerC', data.matrices.C, 'C');
        renderMatrix('containerL', data.matrices.L, 'L');
        renderMatrix('containerS', data.matrices.S, 'S (Выход)');
        renderMatrix('containerB', data.matrices.B, 'B (Коэфф.)');

        currentMatrixS = data.matrices.S;
        currentMassPerBatch = config.m;
        currentConfig = config;
        currentBatches = data.batches;
        document.getElementById('optBtn').disabled = false;
        
        // Show ripening information if enabled
        //showRipeningInfo(config);
        // Show distribution and delta info
        // showDistributionInfo(config, currentBatches);
        // Update results section
        //updateResultsSection(config, currentBatches);

    } catch (e) {
        alert("Ошибка подключения к серверу (убедитесь, что он запущен): " + e.message);
        console.error(e);
    }
}

async function runOptimization() {
    if (!currentMatrixS) return;

    try {
        const response = await fetch(`${API_URL}/optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                matrix: currentMatrixS,
                mass_per_batch: currentMassPerBatch
            })
        });

        const data = await response.json();

        // Sort strategies by yield (descending) for better visualization
        const strategies = Object.entries(data).sort((a, b) => b[1].yield - a[1].yield);
        console.log("Hello");
        const strategyNames = {
            'optimal': 'Венгерский максимальный',
            'notoptimal': 'Венгерский минимальный',
            'greedy': 'Жадная',
            'g5': 'G5 (жадная вариация)',
            'g10': 'G10 (жадная вариация)',
            'g20': 'G20 (жадная вариация)',
            'thrifty_greedy': 'Бережливая/жадная',
            't1g': 'T(1)G (Б1Ж)',
            'greedy_thrifty': 'Жадная/бережливая',
            'thrifty': 'Бережливая',
            'random': 'Случайная'
        };
        
        const strategyColors = {
            'optimal': 'alert-info',
            'notoptimal': 'alert-info',
            'greedy': 'alert-success',
            'g5': 'alert-success',
            'g10': 'alert-success',
            'g20': 'alert-success',
            'thrifty_greedy': 'alert-warning',
            't1g': 'alert-warning',
            'greedy_thrifty': 'alert-warning',
            'thrifty': 'alert-warning',
            'random': 'alert-secondary'
        };

        let html = `<h6>Результаты оптимизации</h6>`;
        
        // Show optimal first
        if (data.optimal) {
            html += `<div class="alert ${strategyColors['optimal'] || 'alert-info'}">`;
            html += `<strong> ${strategyNames['optimal']}</strong><br>`;
            html += `Выход (S(σ)): <b>${data.optimal.yield.toFixed(2)}</b> (максимум)<br>`;
            html += `Итоговая масса: <b>${data.optimal.final_mass.toFixed(2)}</b> (S(σ) × M × d, где d=7 дней)<br>`;
            html += `Порядок партий: `;
            html += visualizeSequence(data.optimal.permutation, data.optimal.yield, currentMatrixS);
            html += `</div>`;
        }
        if (data.notoptimal) {
            html += `<div class="alert ${strategyColors['notoptimal'] || 'alert-info'}">`;
            html += `<strong> ${strategyNames['notoptimal']}</strong><br>`;
            html += `Выход (S(σ)): <b>${data.notoptimal.yield.toFixed(2)}</b> (минимум)<br>`;
            html += `Итоговая масса: <b>${data.notoptimal.final_mass.toFixed(2)}</b> (S(σ) × M × d, где d=7 дней)<br>`;
            html += `Порядок партий: `;
            html += visualizeSequence(data.notoptimal.permutation, data.notoptimal.yield, currentMatrixS);
            html += `</div>`;
        }
        let flag = 1
        // Show other strategies
        for (const [key, result] of strategies) {
            if (key === 'optimal') continue;
            if (key === 'notoptimal') continue;
            const name = strategyNames[key] || key;
            const color = strategyColors[key] || 'alert-secondary';
            const loss = result.relative_loss_percent ? 
                ` (потери: ${result.relative_loss_percent.toFixed(2)}% от оптимальной)` : '';
            if (flag) {
                flag = 0;
                html += `<div class="alert ${strategyColors['optimal'] || 'alert-info'}">`;
                html += `<strong>⭐ Оптимальный алгоритм: <br>`;
                html += ` ${name}</strong>${loss}<br>`;
            }
            else {
                html += `<div class="alert ${color}">`;
                html += `<strong>${name}</strong>${loss}<br>`;
            }
            html += `Выход (S(σ)): <b>${result.yield.toFixed(2)}</b><br>`;
            html += `Итоговая масса: <b>${result.final_mass.toFixed(2)}</b> (S(σ) × M × d, где d=7 дней)<br>`;
            html += `Порядок партий: `;
            html += visualizeSequence(result.permutation, result.yield, currentMatrixS);
            html += `</div>`;
        }

        document.getElementById('optResults').innerHTML = html;

        // Render chart in Results tab
        renderResultsChart(data, strategyNames, strategyColors);

        console.log(data);

    } catch (e) {
        alert("Ошибка оптимизации: " + e.message);
    }
}

// New: renderResultsChart - draws line chart of sugar content per stage for different strategies
function renderResultsChart(data, strategyNames = {}, strategyColors = {}) {
    // Wait until Chart is available
    if (typeof Chart === 'undefined') {
        // try again shortly if Chart.js is still loading
        setTimeout(() => renderResultsChart(data, strategyNames, strategyColors), 200);
        return;
    }

    const canvas = document.getElementById('resultsChartCanvas');
    if (!canvas) return;

    const n = currentMatrixS ? currentMatrixS.length : 0;
    if (!n) return;

    // Determine which strategies to plot: take top N by yield, but include optimal, greedy and thrifty if present
    const preferred = ['optimal', 'greedy', 'thrifty', 'thrifty_greedy', 'greedy_thrifty', 'random'];
    const keys = Object.keys(data);
    const datasets = [];

    // helper to build series from permutation
    const buildSeries = (perm) => {
        const series = [];
        for (let j = 0; j < perm.length; j++) {
            const batchIdx = perm[j];
            const val = (currentMatrixS[batchIdx] && currentMatrixS[batchIdx][j] != null) ? currentMatrixS[batchIdx][j] : 0;
            series.push(Number(val));
        }
        return series;
    };

    // choose up to 6 series: preferred first then highest yields
    const added = new Set();
    for (const k of preferred) {
        if (data[k] && data[k].permutation && !added.has(k)) {
            const perm = data[k].permutation;
            datasets.push({
                label: strategyNames[k] || k,
                data: buildSeries(perm),
                borderColor: strategyColors[k] || getComputedStyle(document.documentElement).getPropertyValue('--primary-color') || '#667eea',
                backgroundColor: 'transparent',
                pointRadius: 4,
                tension: 0.28,
                borderWidth: 2
            });
            added.add(k);
        }
    }

    // add others by descending yield until 6 datasets total
    const others = Object.entries(data).sort((a,b) => (b[1].yield||0) - (a[1].yield||0));
    for (const [k, v] of others) {
        if (datasets.length >= 6) break;
        if (added.has(k)) continue;
        if (!v.permutation) continue;
        datasets.push({
            label: strategyNames[k] || k,
            data: buildSeries(v.permutation),
            borderColor: strategyColors[k] || randomColorForKey(k),
            backgroundColor: 'transparent',
            pointRadius: 3,
            tension: 0.28,
            borderWidth: 2
        });
        added.add(k);
    }

    // labels: stages 1..n
    const labels = Array.from({length: n}, (_, i) => `Этап ${i+1}`);

    // destroy previous chart if exists
    if (canvas._chartInstance) {
        try { canvas._chartInstance.destroy(); } catch(e){ /* ignore */ }
        canvas._chartInstance = null;
    }

    // create chart with modern look: dark grid, right-side legend
    const ctx = canvas.getContext('2d');
    canvas.style.background = 'transparent';

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10,
                        padding: 12,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: function(ctx) {
                            return `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.04)'
                    },
                    ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#718096' }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.06)'
                    },
                    ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#718096' }
                }
            }
        }
    });

    canvas._chartInstance = chart;

    // Also populate the results section summary (params) if available
    updateResultsSection(currentConfig || {}, currentBatches || []);
}

// helper: generate deterministic color for a key if none provided
function randomColorForKey(key) {
    // simple hash to color
    let h = 0;
    for (let i = 0; i < key.length; i++) h = (h << 5) - h + key.charCodeAt(i);
    const c = (h & 0x00FFFFFF).toString(16).toUpperCase();
    return '#' + '00000'.substring(0, 6 - c.length) + c;
}

function renderMatrix(containerId, matrix, title) {
    let html = `<table class="table table-bordered table-sm matrix-table">`;
    html += `<thead><tr><th>Партия\\Стадия</th>`;
    for (let j = 0; j < matrix[0].length; j++) {
        html += `<th>${j + 1}</th>`;
    }
    html += `</tr></thead><tbody>`;

    matrix.forEach((row, i) => {
        html += `<tr><th>${i + 1}</th>`;
        row.forEach(val => {
            html += `<td>${val.toFixed(2)}</td>`;
        });
        html += `</tr>`;
    });
    html += `</tbody></table>`;

    document.getElementById(containerId).innerHTML = html;
}

function showRipeningInfo(config) {
    if (!config.enable_ripening) return;
    
    const v = config.v || 2;
    const n = config.n;
    const ripeningStages = Array.from({length: v - 1}, (_, i) => i + 2); // Stages 2 to v (1-based)
    const wiltingStages = Array.from({length: n - v}, (_, i) => i + v + 1); // Stages v+1 to n (1-based)
    
    let infoHtml = `<div class="alert alert-info mt-3">`;
    infoHtml += `<strong>Информация о дозаривании:</strong><br>`;
    infoHtml += `Стадии дозаривания (v=${v}): Стадии ${ripeningStages.join(', ')}<br>`;
    infoHtml += `Стадии увядания: Стадии ${wiltingStages.join(', ')}<br>`;
    if (config.beta_max) {
        infoHtml += `β_max: ${config.beta_max.toFixed(3)}`;
    } else {
        infoHtml += `β_max: Автоматически рассчитано как (n-1)/(n-2) = ${((n-1)/(n-2)).toFixed(3)}`;
    }
    infoHtml += `</div>`;
    
    // Add to optimization section
    const optResults = document.getElementById('optResults');
    if (optResults) {
        const existingInfo = optResults.parentElement.querySelector('.ripening-info');
        if (existingInfo) {
            existingInfo.remove();
        }
        const infoDiv = document.createElement('div');
        infoDiv.className = 'ripening-info';
        infoDiv.innerHTML = infoHtml;
        optResults.parentElement.insertBefore(infoDiv, optResults);
    }
}

function showDistributionInfo(config, batches) {
    const infoContainerId = 'distributionInfo';
    const optResults = document.getElementById('optResults');
    if (!optResults) return;
    const parent = optResults.parentElement;

    const existing = parent.querySelector(`#${infoContainerId}`);
    if (existing) existing.remove();

    let html = `<div id="${infoContainerId}" class="alert alert-info mt-3">`;
    html += `<strong>Параметры распределения b:</strong><br>`;
    html += `Тип: ${config.distribution_type}; `;
    html += `Δ (wilting) ≤ |β₂-β₁| / ${config.delta_k}`;
    if (config.enable_ripening) {
        html += `, Δ (ripening) ≤ |βmax-1| / ${config.delta_k_ripening}`;
    }
    html += `<br>`;
    html += `Функция I(t): base = ${config.growth_base}<sup>7j-7</sup>; `;
    html += `Потери: ${config.use_losses ? 'учитываются' : 'не учитываются'}`;

    if (batches && batches.length) {
        html += `<hr><div style="max-height:160px; overflow:auto;">`;
        html += `<table class="table table-sm table-bordered mb-0"><thead><tr><th>Партия</th><th>Увядание [β₁,β₂]</th>`;
        if (config.enable_ripening) html += `<th>Дозаривание [β₁,β₂]</th>`;
        html += `</tr></thead><tbody>`;
        batches.forEach((b) => {
            html += `<tr><td>${b.index + 1}</td>`;
            const wStart = b.beta_range_start ?? config.beta1;
            const wEnd = b.beta_range_end ?? config.beta2;
            html += `<td>${wStart.toFixed(3)} — ${wEnd.toFixed(3)}</td>`;
            if (config.enable_ripening) {
                const rStart = b.beta_range_start_ripening ?? 1.0;
                const rEnd = b.beta_range_end_ripening ?? (config.beta_max || (config.n - 1)/(config.n - 2));
                html += `<td>${rStart.toFixed(3)} — ${rEnd.toFixed(3)}</td>`;
            }
            html += `</tr>`;
        });
        html += `</tbody></table></div>`;
    }

    html += `</div>`;

    const infoDiv = document.createElement('div');
    infoDiv.innerHTML = html;
    parent.insertBefore(infoDiv, optResults);
}

function updateResultsSection(config, batches) {
    const resultsContent = document.getElementById('resultsContent');
    if (!resultsContent) return;

    let html = '';
    
    // Parameters info card
    html += `<div class="card-modern">`;
    html += `<div class="card-header-modern"><h3>Параметры модели</h3></div>`;
    html += `<div class="card-body-modern">`;
    html += `<div class="params-grid">`;
    html += `<div class="param-item"><strong>Количество партий:</strong> ${config.n}</div>`;
    html += `<div class="param-item"><strong>Масса партии:</strong> ${config.m}</div>`;
    html += `<div class="param-item"><strong>Начальная сахаристость:</strong> [${config.a_min}, ${config.a_max}]</div>`;
    html += `<div class="param-item"><strong>Коэффициенты деградации:</strong> [${config.beta1}, ${config.beta2}]</div>`;
    html += `<div class="param-item"><strong>Тип распределения:</strong> ${config.distribution_type}</div>`;
    html += `<div class="param-item"><strong>Δ denominator:</strong> k = ${config.delta_k}</div>`;
    if (config.enable_ripening) {
        html += `<div class="param-item"><strong>Дозаривание:</strong> включено (v=${config.v})</div>`;
        html += `<div class="param-item"><strong>β_max:</strong> ${config.beta_max || 'auto'}</div>`;
    } else {
        html += `<div class="param-item"><strong>Дозаривание:</strong> выключено</div>`;
    }
    html += `<div class="param-item"><strong>Потери:</strong> ${config.use_losses ? 'учитываются' : 'не учитываются'}</div>`;
    html += `<div class="param-item"><strong>I(t) функция:</strong> ${config.growth_base}^(7j-7)</div>`;
    html += `</div></div></div>`;

    // Batches info card
    if (batches && batches.length) {
        html += `<div class="card-modern">`;
        html += `<div class="card-header-modern"><h3>Интервалы коэффициентов по партиям</h3></div>`;
        html += `<div class="card-body-modern">`;
        html += `<div class="matrix-container-modern" style="max-height: 400px; overflow: auto;">`;
        html += `<table class="table"><thead><tr><th>Партия</th><th>Увядание [β₁,β₂]</th>`;
        if (config.enable_ripening) html += `<th>Дозаривание [β₁,β₂]</th>`;
        html += `</tr></thead><tbody>`;
        batches.forEach((b) => {
            html += `<tr><td><strong>${b.index + 1}</strong></td>`;
            const wStart = b.beta_range_start ?? config.beta1;
            const wEnd = b.beta_range_end ?? config.beta2;
            html += `<td>${wStart.toFixed(3)} — ${wEnd.toFixed(3)}</td>`;
            if (config.enable_ripening) {
                const rStart = b.beta_range_start_ripening ?? 1.0;
                const rEnd = b.beta_range_end_ripening ?? (config.beta_max || (config.n - 1)/(config.n - 2));
                html += `<td>${rStart.toFixed(3)} — ${rEnd.toFixed(3)}</td>`;
            }
            html += `</tr>`;
        });
        html += `</tbody></table></div></div></div>`;
    }

    resultsContent.innerHTML = html;
}

function visualizeSequence(permutation, totalYield, matrixS) {
    let html = `<div class="sequence-visualization mt-2">`;
    html += `<div class="d-flex flex-wrap align-items-center">`;
    
    permutation.forEach((batchIdx, stageIdx) => {
        const value = matrixS[batchIdx][stageIdx];
        const contribution = (value / totalYield * 100).toFixed(1);
        
        html += `<span class="badge badge-primary mr-1 mb-1" style="font-size: 0.9em;" title="Стадия ${stageIdx + 1}: Партия ${batchIdx + 1}, Значение: ${value.toFixed(2)} (${contribution}%)">`;
        html += `${batchIdx + 1}`;
        html += `</span>`;
        
        if (stageIdx < permutation.length - 1) {
            html += `<span class="mx-1">→</span>`;
        }
    });
    
    html += `</div>`;
    html += `<small class="text-muted d-block mt-1">Цифры показывают индексы партий, наведите для деталей</small>`;
    html += `</div>`;
    
    return html;
}
