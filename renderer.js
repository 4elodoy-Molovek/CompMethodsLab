
const API_URL = 'http://127.0.0.1:5000';

let currentMatrixS = null;

async function runSimulation() {
    const config = {
        n: parseInt(document.getElementById('n').value),
        m: parseFloat(document.getElementById('m').value),
        a_min: parseFloat(document.getElementById('a_min').value),
        a_max: parseFloat(document.getElementById('a_max').value),
        beta1: parseFloat(document.getElementById('beta1').value),
        beta2: parseFloat(document.getElementById('beta2').value),
        distribution_type: document.querySelector('input[name="distType"]:checked').value,
        enable_ripening: document.getElementById('enableRipening').checked,
        v: parseInt(document.getElementById('v').value),
        beta_max: parseFloat(document.getElementById('beta_max').value),
    };

    try {
        const response = await fetch(`${API_URL}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (!response.ok) throw new Error('Simulation failed');

        const data = await response.json();

        renderMatrix('containerC', data.matrices.C, 'C');
        renderMatrix('containerL', data.matrices.L, 'L');
        renderMatrix('containerS', data.matrices.S, 'S (Yield)');
        renderMatrix('containerB', data.matrices.B, 'B (Coeffs)');

        currentMatrixS = data.matrices.S;
        document.getElementById('optBtn').disabled = false;

    } catch (e) {
        alert("Error connecting to backend (make sure it's running): " + e.message);
        console.error(e);
    }
}

async function runOptimization() {
    if (!currentMatrixS) return;

    try {
        const response = await fetch(`${API_URL}/optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matrix: currentMatrixS })
        });

        const data = await response.json();

        let html = `<h6>Optimization Results</h6>`;
        html += `<div class="alert alert-success">Greedy Strategy Yield: <b>${data.greedy.yield.toFixed(2)}</b><br>`;
        html += `Batch Order: ${data.greedy.permutation.map(i => i + 1).join(' -> ')}</div>`;

        html += `<div class="alert alert-secondary">Random Strategy Yield: <b>${data.random.yield.toFixed(2)}</b><br>`;
        html += `Batch Order: ${data.random.permutation.map(i => i + 1).join(' -> ')}</div>`;

        document.getElementById('optResults').innerHTML = html;

    } catch (e) {
        alert("Optimization failed: " + e.message);
    }
}

function renderMatrix(containerId, matrix, title) {
    let html = `<table class="table table-bordered table-sm matrix-table">`;
    html += `<thead><tr><th>Batch\\Stage</th>`;
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
