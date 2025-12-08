from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from core.models import BeetBatch, ExperimentConfig
from core.generators import MatrixGenerator
from core.losses import LossModel
from algorithms.optimizer import Optimizer

app = Flask(__name__)
CORS(app)

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    
    # Parse Config
    config = ExperimentConfig(
        n=data['n'],
        m=data['m'],
        a_min=data['a_min'],
        a_max=data['a_max'],
        beta1=data['beta1'],
        beta2=data['beta2'],
        distribution_type=data['distribution_type'],
        enable_ripening=data.get('enable_ripening', False),
        v=data.get('v'),
        beta_max=data.get('beta_max')
    )
    
    # Generate Batches [1..n]
    batches = []
    for i in range(config.n):
        # Allow manual override or random generation if not provided?
        # For now, let's generate random parameters based on ranges
        # Task implies we generate these "parameters of batches"
        
        # Initial sugar
        a_i = np.random.uniform(config.a_min, config.a_max)
        
        # Loss params
        k = np.random.uniform(config.k_min, config.k_max)
        na = np.random.uniform(config.na_min, config.na_max)
        n_cont = np.random.uniform(config.n_content_min, config.n_content_max)
        i0 = np.random.uniform(config.i0_min, config.i0_max)
        
        # Concentrated distribution params (delta)
        delta = None
        b_start = None
        b_end = None
        if config.distribution_type == 'concentrated':
            # "delta_i <= |beta2 - beta1| / 4"
            max_delta = abs(config.beta2 - config.beta1) / 4
            delta_i = np.random.uniform(0, max_delta)
            
            # center in [beta1 + delta, beta2 - delta]
            center = np.random.uniform(config.beta1 + delta_i, config.beta2 - delta_i)
            b_start = center - delta_i
            b_end = center + delta_i
            
            delta = delta_i
            
        batches.append(BeetBatch(
            index=i,
            initial_sugar=a_i,
            k=k, na=na, n_content=n_cont, i0=i0,
            delta=delta, beta_range_start=b_start, beta_range_end=b_end
        ))
        
    # Generate Matrices
    B = MatrixGenerator.generate_coefficients(config, batches)
    C = MatrixGenerator.generate_states(batches, B)
    L = LossModel.calculate_losses(batches, config.n)
    S_tilde = LossModel.calculate_final_yield_matrix(C, L)
    
    return jsonify({
        'matrices': {
            'B': B.tolist(),
            'C': C.tolist(),
            'L': L.tolist(),
            'S': S_tilde.tolist()
        },
        'batches': [vars(b) for b in batches]
    })

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.json
    S_tilde = np.array(data['matrix'])
    
    # Greedy
    perm_greedy, yield_greedy = Optimizer.optimize_greedy(S_tilde)
    
    # Random (Baseline)
    perm_random, yield_random = Optimizer.optimize_random(S_tilde)
    
    return jsonify({
        'greedy': {
            'permutation': perm_greedy, # 0-based indices
            'yield': yield_greedy
        },
        'random': {
            'permutation': perm_random,
            'yield': yield_random
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
