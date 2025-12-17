const API_URL = 'http://127.0.0.1:5000';

let currentMatrixS = null;
let currentMassPerBatch = 1000;
let currentConfig = null;
let currentBatches = null;
let currentExperiments = null; // For storing 50 experiments
let currentExperimentIndex = 0; // For pagination

function _el(id) { return document.getElementById(id); }
function _num(v, fallback = 0) { const x = Number(v); return Number.isFinite(x) ? x : fallback; }
function _int(v, fallback = 0) { const x = parseInt(v); return Number.isFinite(x) ? x : fallback; }

async function runSimulation() {
    // Defensive access to DOM elements
    const nEl = _el('n');
    const mEl = _el('m');
    const aMinEl = _el('a_min');
    const aMaxEl = _el('a_max');
    const beta1El = _el('beta1');
    const beta2El = _el('beta2');
    const growthBaseEl = _el('growth_base');
    const deltaKEl = _el('delta_k');
    const useLossesEl = _el('useLosses');

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

        if (data.matrices) {
            renderMatrix('containerC', data.matrices.C || [[]], 'C');
            renderMatrix('containerL', data.matrices.L || [[]], 'L');
            renderMatrix('containerS', data.matrices.S || [[]], 'S (Выход)');
            renderMatrix('containerB', data.matrices.B || [[]], 'B (Коэфф.)');

            currentMatrixS = data.matrices.S || null;
            currentMassPerBatch = config.m || currentMassPerBatch;
            currentBatches = data.batches || [];
            
            // Clear multi-experiment data
            currentExperiments = null;
            currentExperimentIndex = 0;
            updateMatrixNavigation();
        } else {
            throw new Error('Empty matrices from backend');
        }

        const optBtn = _el('optBtn');
        const multiOptBtn = _el('multiOptBtn');
        if (optBtn) optBtn.disabled = false;
        if (multiOptBtn) multiOptBtn.disabled = true; // Disable multi-opt for single matrix

    } catch (e) {
        console.error(e);
        alert('Ошибка при генерации матриц: ' + (e.message || e));
    }
}

async function runMultiSimulation() {
    // Defensive access to DOM elements
    const nEl = _el('n');
    const mEl = _el('m');
    const aMinEl = _el('a_min');
    const aMaxEl = _el('a_max');
    const beta1El = _el('beta1');
    const beta2El = _el('beta2');
    const growthBaseEl = _el('growth_base');
    const deltaKEl = _el('delta_k');
    const useLossesEl = _el('useLosses');

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

    currentConfig = config;

    try {
        const response = await fetch(`${API_URL}/multi_simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            const txt = await response.text();
            throw new Error(`Server error: ${response.status} ${txt}`);
        }

        const data = await response.json();

        if (data.experiments && data.experiments.length > 0) {
            currentExperiments = data.experiments;
            currentExperimentIndex = 0;
            
            // Show first experiment
            showExperiment(currentExperimentIndex);
            
            // Update navigation controls
            updateMatrixNavigation();
            
            // Enable multi-optimization button
            const multiOptBtn = _el('multiOptBtn');
            if (multiOptBtn) multiOptBtn.disabled = false;
            
            // Disable single optimization button
            const optBtn = _el('optBtn');
            if (optBtn) optBtn.disabled = true;
            
            // Show success message
            showNotification(`Успешно сгенерировано ${data.experiments.length} матриц`, 'success');
        } else {
            throw new Error('No experiments generated');
        }

    } catch (e) {
        console.error(e);
        alert('Ошибка при генерации 50 матриц: ' + (e.message || e));
    }
}

function showExperiment(index) {
    if (!currentExperiments || index < 0 || index >= currentExperiments.length) {
        return;
    }
    
    const experiment = currentExperiments[index];
    currentExperimentIndex = index;
    
    // Update matrix displays
    renderMatrix('containerC', experiment.matrices.C || [[]], 'C');
    renderMatrix('containerL', experiment.matrices.L || [[]], 'L');
    renderMatrix('containerS', experiment.matrices.S || [[]], 'S (Выход)');
    renderMatrix('containerB', experiment.matrices.B || [[]], 'B (Коэфф.)');
    
    currentMatrixS = experiment.matrices.S || null;
    currentMassPerBatch = currentConfig.m || currentMassPerBatch;
    currentBatches = experiment.batches || [];
    
    // Update experiment counter
    const counter = _el('experimentCounter');
    if (counter) {
        counter.textContent = `Эксперимент ${index + 1} из ${currentExperiments.length}`;
    }
    
    // Update navigation buttons
    const prevBtn = _el('prevExperiment');
    const nextBtn = _el('nextExperiment');
    if (prevBtn) prevBtn.disabled = (index === 0);
    if (nextBtn) nextBtn.disabled = (index === currentExperiments.length - 1);
}

function updateMatrixNavigation() {
    const matricesSection = _el('matrices-section');
    if (!matricesSection) return;
    
    // Remove existing navigation if any
    const existingNav = matricesSection.querySelector('.matrix-navigation');
    if (existingNav) existingNav.remove();
    
    const existingCounter = matricesSection.querySelector('.experiment-counter');
    if (existingCounter) existingCounter.remove();
    
    // Add navigation only if we have multiple experiments
    if (currentExperiments && currentExperiments.length > 1) {
        // Create navigation container
        const navContainer = document.createElement('div');
        navContainer.className = 'matrix-navigation';
        navContainer.style.cssText = `
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin: 20px 0;
            padding: 15px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border-radius: 12px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        `;
        
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.id = 'prevExperiment';
        prevBtn.innerHTML = '← Предыдущая';
        prevBtn.className = 'btn-primary-modern';
        prevBtn.onclick = () => showExperiment(currentExperimentIndex - 1);
        prevBtn.disabled = currentExperimentIndex === 0;
        
        // Counter
        const counter = document.createElement('div');
        counter.id = 'experimentCounter';
        counter.className = 'experiment-counter';
        counter.textContent = `Эксперимент ${currentExperimentIndex + 1} из ${currentExperiments.length}`;
        counter.style.cssText = `
            font-weight: 600;
            color: var(--primary-color);
            background: white;
            padding: 8px 16px;
            border-radius: 8px;
            box-shadow: var(--shadow);
        `;
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.id = 'nextExperiment';
        nextBtn.innerHTML = 'Следующая →';
        nextBtn.className = 'btn-primary-modern';
        nextBtn.onclick = () => showExperiment(currentExperimentIndex + 1);
        nextBtn.disabled = currentExperimentIndex === currentExperiments.length - 1;
        
        // Add to navigation
        navContainer.appendChild(prevBtn);
        navContainer.appendChild(counter);
        navContainer.appendChild(nextBtn);
        
        // Insert after tab content
        const tabContent = matricesSection.querySelector('.tab-content-modern');
        if (tabContent) {
            tabContent.parentNode.insertBefore(navContainer, tabContent.nextSibling);
        }
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

        // Render results summary
        let html = `<h6>Результаты оптимизации (одна матрица)</h6>`;
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

async function runMultiOptimization() {
    if (!currentExperiments || currentExperiments.length === 0) {
        alert('Сначала сгенерируйте 50 матриц (кнопка "Сгенерировать 50 матриц")');
        return;
    }

    try {
        // Extract S matrices from all experiments
        const matrices = currentExperiments.map(exp => exp.matrices.S);
        
        const response = await fetch(`${API_URL}/multi_optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                matrices: matrices,
                mass_per_batch: currentMassPerBatch
            })
        });

        if (!response.ok) {
            const txt = await response.text();
            throw new Error(`Server error: ${response.status} ${txt}`);
        }

        const data = await response.json();

        // Render average results
        renderMultiOptimizationResults(data);

        // Update chart with average results
        if (typeof renderMultiResultsChart === 'function') {
            renderMultiResultsChart(data);
        }
    } catch (e) {
        console.error(e);
        alert('Ошибка многократной оптимизации: ' + (e && e.message ? e.message : e));
    }
}

function renderMultiOptimizationResults(data) {
    const optResultsEl = _el('optResults');
    if (!optResultsEl) return;
    
    let html = `<h6>Средние результаты оптимизации (50 матриц)</h6>`;
    
    if (data.averages) {
        const averages = data.averages;
        const algorithms = ['optimal', 'greedy', 'thrifty', 'thrifty_greedy', 'greedy_thrifty', 'notoptimal'];
        
        // Sort by yield (optimal first, then descending)
        const sortedAlgos = [...algorithms].sort((a, b) => {
            if (a === 'optimal') return -1;
            if (b === 'optimal') return 1;
            return (averages[b]?.yield || 0) - (averages[a]?.yield || 0);
        });
        
        for (const algo of sortedAlgos) {
            const result = averages[algo];
            if (!result) continue;
            
            const successRate = (result.success_count / data.total_matrices) * 100;
            const algoName = getAlgorithmName(algo);
            
            html += `<div class="alert ${algo === 'optimal' ? 'alert-info' : 'alert-secondary'}">`;
            html += `<strong>${algoName}</strong><br>`;
            html += `Средний выход: <b>${result.yield.toFixed(2)}</b><br>`;
            html += `Средняя масса: <b>${result.final_mass.toFixed(0)}</b><br>`;
            html += `Успешных применений: ${result.success_count}/${data.total_matrices} (${successRate.toFixed(1)}%)`;
            
            if (result.relative_loss_percent !== undefined) {
                html += `<br>Потери относительно оптимального: <b style="color: #e53e3e;">${result.relative_loss_percent.toFixed(2)}%</b>`;
            }
            
            html += `</div>`;
        }
        
        // Add summary statistics
        html += `<div class="alert alert-success">`;
        html += `<strong>Статистика по 50 экспериментам</strong><br>`;
        html += `• Всего матриц: ${data.total_matrices}<br>`;
        html += `• Оптимальный алгоритм даёт в среднем ${averages.optimal?.yield?.toFixed(2) || '0.00'} выхода<br>`;
        html += `• Лучший эвристический алгоритм: ${getBestHeuristicAlgorithm(averages)}`;
        html += `</div>`;
    } else {
        html += `<div class="alert alert-warning">Нет данных для отображения</div>`;
    }
    
    optResultsEl.innerHTML = html;
}

function getAlgorithmName(key) {
    const names = {
        'greedy': 'Жадный (Greedy)',
        'thrifty': 'Бережливый (Thrifty)',
        'thrifty_greedy': 'Бережливый/Жадный',
        'greedy_thrifty': 'Жадный/Бережливый',
        'optimal': 'Оптимальный (Венгерский)',
        'notoptimal': 'Минимальный (Венгерский)'
    };
    return names[key] || key;
}

function getBestHeuristicAlgorithm(averages) {
    const heuristicAlgos = ['greedy', 'thrifty', 'thrifty_greedy', 'greedy_thrifty'];
    let bestAlgo = null;
    let bestYield = -Infinity;
    
    for (const algo of heuristicAlgos) {
        if (averages[algo] && averages[algo].yield > bestYield) {
            bestYield = averages[algo].yield;
            bestAlgo = algo;
        }
    }
    
    return bestAlgo ? `${getAlgorithmName(bestAlgo)} (${bestYield.toFixed(2)})` : 'нет данных';
}

function renderMultiResultsChart(data) {
    if (typeof Chart === 'undefined') {
        setTimeout(() => renderMultiResultsChart(data), 200);
        return;
    }

    const canvas = _el('resultsChartCanvas');
    if (!canvas) return;

    if (data.averages) {
        const labels = Object.keys(data.averages).map(getAlgorithmName);
        const yields = Object.values(data.averages).map(avg => avg.yield || 0);
        const colors = [
            'rgba(102, 126, 234, 0.8)',
            'rgba(72, 187, 120, 0.8)',
            'rgba(237, 137, 54, 0.8)',
            'rgba(231, 76, 60, 0.8)',
            'rgba(155, 89, 182, 0.8)',
            'rgba(52, 152, 219, 0.8)'
        ];

        // Sort by yield for better visualization
        const combined = labels.map((label, idx) => ({
            label,
            yield: yields[idx],
            color: colors[idx % colors.length]
        })).sort((a, b) => b.yield - a.yield);

        const sortedLabels = combined.map(item => item.label);
        const sortedYields = combined.map(item => item.yield);
        const sortedColors = combined.map(item => item.color);

        if (canvas._chartInstance) {
            try { canvas._chartInstance.destroy(); } catch(e) {}
            canvas._chartInstance = null;
        }

        const ctx = canvas.getContext('2d');
        canvas.style.background = 'transparent';

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedLabels,
                datasets: [{
                    label: 'Средний выход сахара',
                    data: sortedYields,
                    backgroundColor: sortedColors,
                    borderColor: sortedColors.map(color => color.replace('0.8', '1')),
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Средний выход: ${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Сравнение алгоритмов по 50 экспериментам',
                        font: { size: 16 }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(0,0,0,0.04)' },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#718096',
                            font: { size: 12 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.06)' },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#718096',
                            callback: function(value) {
                                return value.toFixed(1);
                            }
                        },
                        title: {
                            display: true,
                            text: 'Средний выход сахара',
                            color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#718096'
                        }
                    }
                }
            }
        });

        canvas._chartInstance = chart;
    }
}

function renderMatrix(containerId, matrix, title) {
    let html = `<div style="margin-bottom: 15px; color: var(--primary-color); font-weight: 600;">${title}</div>`;
    html += `<table class="table table-bordered table-sm matrix-table">`;
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

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.global-notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `global-notification alert alert-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        box-shadow: var(--shadow-lg);
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: inherit;">×</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
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

    // Batches info card (only for single experiment)
    if (batches && batches.length && (!currentExperiments || currentExperiments.length === 1)) {
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
    } else if (currentExperiments && currentExperiments.length > 1) {
        // Show multi-experiment info
        html += `<div class="card-modern">`;
        html += `<div class="card-header-modern"><h3>Информация о множественных экспериментах</h3></div>`;
        html += `<div class="card-body-modern">`;
        html += `<div class="alert alert-info">`;
        html += `<strong>Сгенерировано ${currentExperiments.length} различных матриц</strong><br>`;
        html += `• Все матрицы созданы с одинаковыми параметрами<br>`;
        html += `• Каждая матрица имеет случайно сгенерированные значения<br>`;
        html += `• Используйте навигацию во вкладке "Матрицы" для просмотра<br>`;
        html += `• Результаты оптимизации будут усреднены по всем матрицам`;
        html += `</div></div></div>`;
    }

    resultsContent.innerHTML = html;
}

// Add CSS animation for notification
const style = document.createElement('style');
style.textContent = `
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
`;
document.head.appendChild(style);