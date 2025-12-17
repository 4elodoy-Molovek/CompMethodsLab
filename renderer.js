const API_URL = 'http://127.0.0.1:5000';

let currentMatrixS = null;
let currentMassPerBatch = 1000;
let currentConfig = null;
let currentBatches = null;

function _el(id) { return document.getElementById(id); }
function _num(v, fallback = 0) { const x = Number(v); return Number.isFinite(x) ? x : fallback; }
function _int(v, fallback = 0) { const x = parseInt(v); return Number.isFinite(x) ? x : fallback; }

// defensive helper already present; add extra guard where DOM elements might be missing
async function runSimulation() {
    // Defensive access to DOM elements (fixes "document.getElementById(...) is null" errors)
    const nEl = _el('n');
    const mEl = _el('m');
    const aMinEl = _el('a_min');
    const aMaxEl = _el('a_max');
    const beta1El = _el('beta1');
    const beta2El = _el('beta2');
    const growthBaseEl = _el('growth_base');
    const deltaKEl = _el('delta_k');
    const useLossesEl = _el('useLosses');

    // guard for the radio group (may be absent in some builds)
    const distSel = document.querySelector('input[name="distType"]:checked');

    const config = {
        n: _int(nEl ? nEl.value : null, 0),
        m: _num(mEl ? mEl.value : null, 0),
        a_min: _num(aMinEl ? aMinEl.value : null, 0),
        a_max: _num(aMaxEl ? aMaxEl.value : null, 0),
        beta1: _num(beta1El ? beta1El.value : null, 0),
        beta2: _num(beta2El ? beta2El.value : null, 0),
        distribution_type: distSel ? distSel.value : 'uniform',
        use_losses: !!(useLossesEl && useLossesEl.checked),
        growth_base: _num(growthBaseEl ? growthBaseEl.value : null, 1.029),
        delta_k: _int(deltaKEl ? deltaKEl.value : null, 4),
    };

    // Keep a copy for results UI
    currentConfig = config;

    try {
        const response = await fetch(`${API_URL}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            const txt = await response.text();
            throw new Error(`Server error: ${response.status} ${txt}`);
        }

        const data = await response.json();

        // Render matrices (safe guards if server returned undefined)
        if (data.matrices) {
            renderMatrix('containerC', data.matrices.C || [[]], 'C');
            renderMatrix('containerL', data.matrices.L || [[]], 'L');
            renderMatrix('containerS', data.matrices.S || [[]], 'S (Выход)');
            renderMatrix('containerB', data.matrices.B || [[]], 'B (Коэфф.)');

            currentMatrixS = data.matrices.S || null;
            currentMassPerBatch = config.m || currentMassPerBatch;
            currentBatches = data.batches || [];
        } else {
            throw new Error('Empty matrices from backend');
        }

        // Enable optimization button
        const optBtn = _el('optBtn');
        if (optBtn) optBtn.disabled = false;

    } catch (e) {
        console.error(e);
        alert('Ошибка при генерации матриц: ' + (e.message || e));
    }
}

async function runOptimization() {
    if (!currentMatrixS) {
        alert('Сначала сгенерируйте матрицы (кнопка "Сгенерировать матрицы")');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                matrix: currentMatrixS,
                mass_per_batch: currentMassPerBatch
            })
        });

        if (!response.ok) {
            const txt = await response.text();
            throw new Error(`Server error: ${response.status} ${txt}`);
        }

        const data = await response.json();

        // Build sorted strategies list (descending by yield) to display consistently
        const strategies = Object.entries(data).sort((a, b) => (b[1].yield || 0) - (a[1].yield || 0));

        // Render results summary (kept simple and robust)
        let html = `<h6>Результаты оптимизации</h6>`;
        if (data.optimal) {
            html += `<div class="alert alert-info"><strong>Оптимальный (optimal)</strong><br>`;
            html += `Выход: <b>${(data.optimal.yield||0).toFixed(2)}</b><br>`;
            html += `Порядок партий: ${visualizeSequence(data.optimal.permutation || [], data.optimal.yield || 0, currentMatrixS)}</div>`;
        }

        for (const [key, result] of strategies) {
            if (!result || key === 'optimal') continue;
            html += `<div class="alert alert-secondary"><strong>${key}</strong><br>`;
            html += `Выход: <b>${(result.yield||0).toFixed(2)}</b><br>`;
            html += `Порядок партий: ${visualizeSequence(result.permutation || [], result.yield || 0, currentMatrixS)}</div>`;
        }

        const optResultsEl = _el('optResults');
        if (optResultsEl) optResultsEl.innerHTML = html;

        // Update chart in Results tab
        if (typeof renderResultsChart === 'function') {
            renderResultsChart(data);
        }
    } catch (e) {
        console.error(e);
        alert('Ошибка оптимизации: ' + (e && e.message ? e.message : e));
    }
}

// New: renderResultsChart - draws line chart of sugar content per stage for different strategies
function renderResultsChart(data, strategyNames = {}, strategyColors = {}) {
    if (typeof Chart === 'undefined') {
        setTimeout(() => renderResultsChart(data, strategyNames, strategyColors), 200);
        return;
    }

    const canvas = _el('resultsChartCanvas');
    if (!canvas) return;

    // currentMatrixS is expected to be [batch][stage] -> number of stages:
    const stages = (currentMatrixS && currentMatrixS[0]) ? currentMatrixS[0].length : 0;
    if (!stages) return;

    const preferred = ['optimal', 'greedy', 'thrifty', 'thrifty_greedy', 'greedy_thrifty', 'random'];
    const datasets = [];
    const added = new Set();

    const buildSeries = (perm) => {
        const series = [];
        for (let j = 0; j < stages; j++) {
            const batchIdx = perm[j];
            const val = (currentMatrixS[batchIdx] && currentMatrixS[batchIdx][j] != null) ? currentMatrixS[batchIdx][j] : 0;
            series.push(Number(val));
        }
        return series;
    };

    for (const k of preferred) {
        if (data[k] && data[k].permutation && !added.has(k)) {
            datasets.push({
                label: strategyNames[k] || k,
                data: buildSeries(data[k].permutation),
                borderColor: strategyColors[k] || randomColorForKey(k),
                backgroundColor: 'transparent',
                pointRadius: 4,
                tension: 0.28,
                borderWidth: 2
            });
            added.add(k);
        }
    }

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

    const labels = Array.from({length: stages}, (_, i) => `Этап ${i+1}`);

    if (canvas._chartInstance) {
        try { canvas._chartInstance.destroy(); } catch(e) {}
        canvas._chartInstance = null;
    }

    const ctx = canvas.getContext('2d');
    canvas.style.background = 'transparent';

    const chart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'right', labels: { usePointStyle: true, boxWidth: 10, padding: 12, font: { size: 12 } } },
                tooltip: { callbacks: { label: function(ctx) { return `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}`; } } }
            },
            scales: {
                x: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#718096' } },
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.06)' }, ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#718096' } }
            }
        }
    });

    canvas._chartInstance = chart;
    updateResultsSection(currentConfig || {}, currentBatches || []);
}

// helper: generate deterministic color for a key if none provided
function randomColorForKey(key) {
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
