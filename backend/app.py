from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from core.models import BeetBatch, ExperimentConfig
from core.generators import MatrixGenerator
from core.losses import LossModel
from algorithms.optimizer import Optimizer

app = Flask(__name__)
CORS(app)

def validate_config(data):
    """Validate input parameters according to task.md requirements."""
    errors = []
    
    # Basic validations
    n = data.get('n')
    if not n or n <= 0:
        errors.append("n must be positive integer")
    
    m = data.get('m')
    if not m or m <= 0:
        errors.append("M (mass per batch) must be positive")
    
    a_min = data.get('a_min')
    a_max = data.get('a_max')
    if a_min is None or a_max is None or a_min >= a_max:
        errors.append("a_min must be less than a_max")
    
    beta1 = data.get('beta1')
    beta2 = data.get('beta2')
    if beta1 is None or beta2 is None:
        errors.append("beta1 and beta2 must be provided")
    else:
        if beta1 >= beta2:
            errors.append("beta1 must be less than beta2")
        if beta1 <= 0:
            errors.append("beta1 must be positive (for wilting, should be in (0,1))")
        if beta2 >= 1:
            errors.append("beta2 must be less than 1 (for wilting)")
    
    # Ripening validations
    enable_ripening = data.get('enable_ripening', False)
    if enable_ripening:
        v = data.get('v')
        if v is None:
            errors.append("v (number of ripening stages) must be provided when ripening is enabled")
        else:
            if n:
                max_v = n // 2  # [n/2]
                if v < 2 or v > max_v:
                    errors.append(f"v must satisfy: 2 ≤ v ≤ [n/2] = {max_v}")
        
        beta_max = data.get('beta_max')
        if beta_max is not None and beta_max <= 1:
            errors.append("beta_max must be greater than 1 (for ripening)")

    # Growth base selection
    growth_base = data.get('growth_base', 1.029)
    if growth_base not in [1.029, 1.03]:
        errors.append("growth_base must be 1.029 or 1.03")

    # Delta denominator validation (concentrated)
    delta_k = data.get('delta_k', 4)
    delta_k_ripening = data.get('delta_k_ripening', 4)
    if delta_k not in [2, 3, 4]:
        errors.append("delta_k must be one of {2,3,4}")
    if delta_k_ripening not in [2, 3, 4]:
        errors.append("delta_k_ripening must be one of {2,3,4}")
    
    return errors

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    
    # Validate input
    validation_errors = validate_config(data)
    if validation_errors:
        return jsonify({'error': 'Validation failed', 'errors': validation_errors}), 400
    
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
        beta_max=data.get('beta_max'),
        use_losses=data.get('use_losses', True),
        growth_base=data.get('growth_base', 1.029),
        delta_k=data.get('delta_k', 4),
        delta_k_ripening=data.get('delta_k_ripening', 4),
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
        
        # Concentrated distribution params for wilting (delta)
        delta = None
        b_start = None
        b_end = None
        if config.distribution_type == 'concentrated':
            # "delta_i <= |beta2 - beta1| / k"
            max_delta = abs(config.beta2 - config.beta1) / config.delta_k
            delta_i = np.random.uniform(0, max_delta)
            
            # center in [beta1 + delta, beta2 - delta]
            center = np.random.uniform(config.beta1 + delta_i, config.beta2 - delta_i)
            b_start = center - delta_i
            b_end = center + delta_i
            
            delta = delta_i
        
        # Concentrated distribution params for ripening
        delta_ripening = None
        b_start_ripening = None
        b_end_ripening = None
        if config.distribution_type == 'concentrated' and config.enable_ripening:
            # Calculate beta_max for ripening range
            beta_max = config.beta_max
            if beta_max is None:
                if config.n > 2:
                    beta_max = (config.n - 1) / (config.n - 2)
                else:
                    beta_max = 1.1
            
            # Similar logic for ripening: delta <= |beta_max - 1| / k
            max_delta_ripening = abs(beta_max - 1.0) / config.delta_k_ripening
            delta_ripening_i = np.random.uniform(0, max_delta_ripening)
            
            # center in (1 + delta, beta_max - delta]
            center_ripening = np.random.uniform(1.0 + delta_ripening_i, beta_max - delta_ripening_i)
            b_start_ripening = center_ripening - delta_ripening_i
            b_end_ripening = center_ripening + delta_ripening_i
            
            delta_ripening = delta_ripening_i
            
        batches.append(BeetBatch(
            index=i,
            initial_sugar=a_i,
            k=k, na=na, n_content=n_cont, i0=i0,
            delta=delta, beta_range_start=b_start, beta_range_end=b_end,
            delta_ripening=delta_ripening,
            beta_range_start_ripening=b_start_ripening,
            beta_range_end_ripening=b_end_ripening
        ))
        
    # Generate Matrices
    B = MatrixGenerator.generate_coefficients(config, batches)
    C = MatrixGenerator.generate_states(batches, B)
    if config.use_losses:
        L = LossModel.calculate_losses(batches, config.n, growth_base=config.growth_base)
        S_tilde = LossModel.calculate_final_yield_matrix(C, L)
    else:
        L = np.zeros_like(C)
        S_tilde = C
    
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
    mass_per_batch = data.get('mass_per_batch', 1000.0)  # Default M if not provided
    
    n = S_tilde.shape[0]
    nu = n // 2  # Default nu = [n/2]
    
    results = {}
    
    # 1. Greedy (Жадная)
    perm_greedy, yield_greedy = Optimizer.optimize_greedy(S_tilde)
    results['greedy'] = {
        'permutation': perm_greedy,
        'yield': yield_greedy,
        'final_mass': Optimizer.calculate_final_mass(yield_greedy, mass_per_batch)
    }
    
    # 2. Thrifty (Бережливая)
    perm_thrifty, yield_thrifty = Optimizer.optimize_thrifty(S_tilde)
    results['thrifty'] = {
        'permutation': perm_thrifty,
        'yield': yield_thrifty,
        'final_mass': Optimizer.calculate_final_mass(yield_thrifty, mass_per_batch)
    }
    
    # 3. Thrifty/Greedy (Бережливая/жадная)
    perm_tg, yield_tg = Optimizer.optimize_thrifty_greedy(S_tilde, nu)
    results['thrifty_greedy'] = {
        'permutation': perm_tg,
        'yield': yield_tg,
        'final_mass': Optimizer.calculate_final_mass(yield_tg, mass_per_batch)
    }
    
    # 4. Greedy/Thrifty (Жадная/бережливая)
    perm_gt, yield_gt = Optimizer.optimize_greedy_thrifty(S_tilde, nu)
    results['greedy_thrifty'] = {
        'permutation': perm_gt,
        'yield': yield_gt,
        'final_mass': Optimizer.calculate_final_mass(yield_gt, mass_per_batch)
    }
    
    # 5. T(1)G (Б1Ж - бережливая/жадная, same as #3 but explicit)
    perm_t1g, yield_t1g = Optimizer.optimize_tkg(S_tilde, k=1, nu=nu)
    results['t1g'] = {
        'permutation': perm_t1g,
        'yield': yield_t1g,
        'final_mass': Optimizer.calculate_final_mass(yield_t1g, mass_per_batch)
    }
    
    # 6. Gk strategies (variations of greedy)
    # G1 = greedy (already done)
    # G5, G10, G20 for comparison
    for k in [5, 10, 20]:
        if k <= n:
            perm_gk, yield_gk = Optimizer.optimize_gk(S_tilde, k)
            results[f'g{k}'] = {
                'permutation': perm_gk,
                'yield': yield_gk,
                'final_mass': Optimizer.calculate_final_mass(yield_gk, mass_per_batch)
            }
    
    # 7. Hungarian (Optimal - absolute maximum)
    perm_hungarian, yield_hungarian = Optimizer.optimize_hungarian(S_tilde)
    results['optimal'] = {
        'permutation': perm_hungarian,
        'yield': yield_hungarian,
        'final_mass': Optimizer.calculate_final_mass(yield_hungarian, mass_per_batch)
    }
    
    # 8. Random (Baseline)
    perm_random, yield_random = Optimizer.optimize_random(S_tilde)
    results['random'] = {
        'permutation': perm_random,
        'yield': yield_random,
        'final_mass': Optimizer.calculate_final_mass(yield_random, mass_per_batch)
    }
    
    # Calculate relative losses compared to optimal
    if yield_hungarian > 0:
        for key in results:
            if key != 'optimal':
                relative_loss = ((yield_hungarian - results[key]['yield']) / yield_hungarian) * 100
                results[key]['relative_loss_percent'] = relative_loss
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
