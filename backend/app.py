"""
===================================================================
FLASK BACKEND API - ГЛАВНЫЙ ФАЙЛ ПРИЛОЖЕНИЯ
===================================================================

НАЗНАЧЕНИЕ:
    Этот файл содержит Flask REST API сервер, который обрабатывает запросы
    от frontend (Electron приложения) для симуляции и оптимизации процесса
    переработки сахарной свёклы.

СТРУКТУРА:
    - Flask приложение (app) - основной объект веб-сервера
    - CORS - разрешает запросы с frontend (кросс-доменные запросы)
    - API endpoints:
        * POST /simulate - генерация матриц состояний и параметров партий
        * POST /multi_simulate - генерация 50 наборов матриц
        * POST /optimize - оптимизация последовательности переработки
        * POST /multi_optimize - оптимизация для 50 матриц

АРХИТЕКТУРА:
    Frontend (Electron) <--HTTP--> Flask Backend <--использует--> Модули:
                                                                    - core.models (модели данных)
                                                                    - core.generators (генерация матриц)
                                                                    - core.losses (расчёт потерь)
                                                                    - algorithms.optimizer (алгоритмы оптимизации)

КАК ЗАПУСТИТЬ:
    1. Установите зависимости: pip install -r requirements.txt
    2. Запустите сервер: 
    3. Сервер будет доступен на http://localhost:5000
    4. Frontend автоматически запускает этот сервер при старте

API ENDPOINTS:

    POST /simulate
    ---------------
    Входные данные (JSON):
        {
            "n": 10,                    # Количество партий
            "m": 1000.0,                # Масса партии
            "a_min": 0.10,              # Минимальная начальная сахаристость
            "a_max": 0.20,              # Максимальная начальная сахаристость
            "beta1": 0.85,              # Минимальный коэффициент деградации (увядание)
            "beta2": 0.95,              # Максимальный коэффициент деградации (увядание)
            "distribution_type": "uniform",  # "uniform" или "concentrated"
            "enable_ripening": false,    # Включить дозаривание
            "v": 3,                     # Количество этапов дозаривания (если включено)
            "beta_max": 1.2,            # Максимальный коэффициент для дозаривания
            "use_losses": true,         # Учитывать потери сахара
            "growth_base": 1.029,       # База роста для расчёта потерь
            "delta_k": 4,               # Знаменатель для концентрированного распределения
            "delta_k_ripening": 4      # То же для дозаривания
        }
    
    Выходные данные (JSON):
        {
            "matrices": {
                "B": [[...]],  # Матрица коэффициентов деградации
                "C": [[...]],  # Матрица содержания сахара
                "L": [[...]],  # Матрица потерь (в %)
                "S": [[...]]   # Итоговая матрица после учёта потерь
            },
            "batches": [...]   # Список партий с их параметрами
        }

    POST /multi_simulate
    ---------------------
    Входные данные (JSON): те же, что и для /simulate
    Выходные данные (JSON):
        {
            "experiments": [
                {
                    "matrices": {
                        "B": [[...]],
                        "C": [[...]],
                        "L": [[...]],
                        "S": [[...]]
                    },
                    "batches": [...]
                },
                ...  # 50 экспериментов
            ]
        }

    POST /optimize
    ---------------
    Входные данные (JSON):
        {
            "matrix": [[...]],          # Матрица S (итоговая матрица состояний)
            "mass_per_batch": 1000.0    # Масса партии (для расчёта итоговой массы)
        }
    
    Выходные данные (JSON):
        {
            "greedy": {
                "permutation": [2, 5, 1, ...],  # Перестановка (последовательность партий)
                "yield": 15.5,                  # Выход сахара
                "final_mass": 108500.0          # Итоговая масса продукта
            },
            "thrifty": {...},
            "thrifty_greedy": {...},
            "greedy_thrifty": {...},
            "optimal": {...},  # Венгерский алгоритм (оптимальное решение)
            "notoptimal": {...} # Венгерский алгоритм (минимальное решение)
        }

    POST /multi_optimize
    --------------------
    Входные данные (JSON):
        {
            "matrices": [[[...]], ...],  # Массив из 50 матриц S
            "mass_per_batch": 1000.0     # Масса партии
        }
    
    Выходные данные (JSON):
        {
            "averages": {
                "greedy": {
                    "yield": 15.5,                  # Средний выход сахара
                    "final_mass": 108500.0          # Средняя итоговая масса
                },
                "thrifty": {...},
                "thrifty_greedy": {...},
                "greedy_thrifty": {...},
                "optimal": {...},
                "notoptimal": {...}
            },
            "all_results": [  # Результаты для каждой матрицы (опционально)
                {
                    "greedy": {...},
                    "thrifty": {...},
                    ...
                },
                ...
            ]
        }

ВАЛИДАЦИЯ:
    Функция validate_config() проверяет все входные параметры согласно
    требованиям из task.md. При ошибках возвращается список ошибок.

ОБРАБОТКА ОШИБОК:
    - 400 Bad Request - если валидация не прошла
    - 500 Internal Server Error - если произошла ошибка при обработке

РАСШИРЕНИЕ ФУНКЦИОНАЛЬНОСТИ:
    Чтобы добавить новый endpoint:
        1. Создайте функцию-обработчик
        2. Добавьте декоратор @app.route('/путь', methods=['GET/POST'])
        3. Верните JSON через jsonify()
    
    Пример:
        @app.route('/new_endpoint', methods=['POST'])
        def new_endpoint():
            data = request.json
            # Ваша логика
            return jsonify({'result': 'success'})

АВТОР: [Ваше имя]
ДАТА СОЗДАНИЯ: [Дата]
===================================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from core.models import BeetBatch, ExperimentConfig
from core.generators import MatrixGenerator
from core.losses import LossModel
from algorithms.optimizer import Optimizer

# Создаём Flask приложение
app = Flask(__name__)

# Включаем CORS (Cross-Origin Resource Sharing)
# Это необходимо, чтобы frontend (Electron) мог делать запросы к backend
# Без этого браузер заблокирует запросы из-за политики безопасности
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
    
    # Chemical parameters validation (optional, but good for sanity check)
    # Ranges from Textbook Section 7:
    # K: [4.8, 7.05], Na: [0.21, 0.82], N: [1.58, 2.8], I0: [0.62, 0.64]
    # We assume frontend sends valid ranges if provided.
    if data.get('k_min') and data.get('k_max') and data['k_min'] > data['k_max']:
        errors.append("k_min must be <= k_max")

    return errors

def generate_single_experiment(config):
    """Generate a single experiment with matrices."""
    # Generate Batches [1..n]
    batches = []
    for i in range(config.n):
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
            
            b_start = np.random.uniform(config.beta1, config.beta2 - delta_i)
            b_end = b_start + delta_i
            
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
        L = LossModel.calculate_losses(batches, C, config.n, growth_base=config.growth_base)
        S_tilde = LossModel.calculate_final_yield_matrix(C, L)
    else:
        L = np.zeros_like(C)
        S_tilde = C
    
    return {
        'matrices': {
            'B': B.tolist(),
            'C': C.tolist(),
            'L': L.tolist(),
            'S': S_tilde.tolist()
        },
        'batches': [vars(b) for b in batches]
    }

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    
    # Validate input
    validation_errors = validate_config(data)
    if validation_errors:
        return jsonify({'error': 'Validation failed', 'errors': validation_errors}), 400
    
    # Parse Config
    # Normalize sugar inputs: accept either fraction (0.12) or percent (12)
    a_min_in = data['a_min']
    a_max_in = data['a_max']
    # If values are given as fractions (<= 1), convert to percent
    if a_min_in is not None and a_min_in <= 1.0:
        a_min_in = a_min_in * 100.0
    if a_max_in is not None and a_max_in <= 1.0:
        a_max_in = a_max_in * 100.0

    config = ExperimentConfig(
        n=data['n'],
        m=data['m'],
        a_min=a_min_in,
        a_max=a_max_in,
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
        # Chemical parameters from Textbook Section 7
        # Passing them to config so generate_single_experiment can use them
        k_min=data.get('k_min', 4.8),
        k_max=data.get('k_max', 7.05),
        na_min=data.get('na_min', 0.21),
        na_max=data.get('na_max', 0.82),
        n_content_min=data.get('n_content_min', 1.58),
        n_content_max=data.get('n_content_max', 2.8),
        i0_min=data.get('i0_min', 0.62),
        i0_max=data.get('i0_max', 0.64),
    )
    
    # Generate single experiment
    experiment = generate_single_experiment(config)
    
    return jsonify(experiment)

@app.route('/multi_simulate', methods=['POST'])
def multi_simulate():
    """Generate 50 different experiments with the same parameters."""
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
        # Chemical parameters
        k_min=data.get('k_min', 4.8),
        k_max=data.get('k_max', 7.05),
        na_min=data.get('na_min', 0.21),
        na_max=data.get('na_max', 0.82),
        n_content_min=data.get('n_content_min', 1.58),
        n_content_max=data.get('n_content_max', 2.8),
        i0_min=data.get('i0_min', 0.62),
        i0_max=data.get('i0_max', 0.64),
    )
    
    # Generate 50 experiments
    experiments = []
    for exp_idx in range(50):
        experiment = generate_single_experiment(config)
        experiments.append(experiment)
    
    return jsonify({
        'experiments': experiments,
        'count': len(experiments)
    })

def to_native(obj):
    """
    Рекурсивно конвертирует объекты в JSON-сериализуемые:
    - np.ndarray -> list
    - np.generic (np.int64, np.float64, ...) -> Python int/float via .item()
    - list/tuple/dict -> обрабатывает рекурсивно
    """
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {to_native(k): to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_native(i) for i in obj]
    return obj

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        data = request.json
        S_tilde = np.array(data['matrix'])
        mass_per_batch = data.get('mass_per_batch', 1000.0)

        n = S_tilde.shape[0]
        nu = n // 2

        results = {}

        # 1. Greedy
        perm_greedy, yield_greedy = Optimizer.optimize_greedy(S_tilde)
        results['greedy'] = {
            'permutation': [int(x) for x in perm_greedy],
            'yield': float(yield_greedy),
            'final_mass': float(Optimizer.calculate_final_mass(yield_greedy, mass_per_batch))
        }

        # 2. Thrifty
        perm_thrifty, yield_thrifty = Optimizer.optimize_thrifty(S_tilde)
        results['thrifty'] = {
            'permutation': [int(x) for x in perm_thrifty],
            'yield': float(yield_thrifty),
            'final_mass': float(Optimizer.calculate_final_mass(yield_thrifty, mass_per_batch))
        }

        # 3. Thrifty/Greedy
        perm_tg, yield_tg = Optimizer.optimize_thrifty_greedy(S_tilde, nu)
        results['thrifty_greedy'] = {
            'permutation': [int(x) for x in perm_tg],
            'yield': float(yield_tg),
            'final_mass': float(Optimizer.calculate_final_mass(yield_tg, mass_per_batch))
        }

        # 4. Greedy/Thrifty
        perm_gt, yield_gt = Optimizer.optimize_greedy_thrifty(S_tilde, nu)
        results['greedy_thrifty'] = {
            'permutation': [int(x) for x in perm_gt],
            'yield': float(yield_gt),
            'final_mass': float(Optimizer.calculate_final_mass(yield_gt, mass_per_batch))
        }

        # 5. Hungarian (optimal) - обернём вызов, если может падать
        try:
            perm_hungarian, yield_hungarian = Optimizer.optimize_hungarian(S_tilde)
            results['optimal'] = {
                'permutation': [int(x) for x in perm_hungarian],
                'yield': float(yield_hungarian),
                'final_mass': float(Optimizer.calculate_final_mass(yield_hungarian, mass_per_batch))
            }
        except Exception as e:
            app.logger.warning("Hungarian optimization failed: %s", e)
            results['optimal'] = {
                'permutation': list(range(n)),
                'yield': 0.0,
                'final_mass': 0.0
            }
            yield_hungarian = 0.0

        # 6. Hungarian min (notoptimal)
        try:
            perm_hungarian_min, yield_hungarian_min = Optimizer.optimize_hungarian_min(S_tilde)
            results['notoptimal'] = {
                'permutation': [int(x) for x in perm_hungarian_min],
                'yield': float(yield_hungarian_min),
                'final_mass': float(Optimizer.calculate_final_mass(yield_hungarian_min, mass_per_batch))
            }
        
        except Exception as e:
            app.logger.warning("Hungarian min optimization failed: %s", e)
            results['notoptimal'] = {
                'permutation': list(range(n)),
                'yield': 0.0,
                'final_mass': 0.0
            }
            yield_hungarian = 0.0

        # relative losses vs optimal
        yield_hungarian = locals().get('yield_hungarian', results.get('optimal', {}).get('yield', 0.0))
        if yield_hungarian and yield_hungarian > 0:
            for key in results:
                if key != 'optimal':
                    relative_loss = ((yield_hungarian - results[key]['yield']) / yield_hungarian) * 100
                    results[key]['relative_loss_percent'] = float(relative_loss)

        # final conversion of any remaining numpy types
        results_native = to_native(results)

        return jsonify(results_native)

    except Exception as e:
        app.logger.exception("Optimization failed")
        return jsonify({'error': 'Optimization failed', 'message': str(e)}), 500

def run_algorithm(algo_name, func, args, mass_per_batch):
    """
    Helper to run a single optimization algorithm safely.
    Returns tuple: (yield_val, final_mass, success_bool)
    """
    try:
        # Unpack args if it's a tuple/list, otherwise pass as single arg
        if isinstance(args, (list, tuple)):
            perm, yield_val = func(*args)
        else:
            perm, yield_val = func(args)
            
        final_mass = Optimizer.calculate_final_mass(yield_val, mass_per_batch)
        return float(yield_val), float(final_mass), True
    except Exception as e:
        # app.logger is accessible here because it's in the same module scope,
        # but ideally should be passed or obtained via current_app
        app.logger.warning(f"{algo_name} optimization failed: {e}")
        return 0.0, 0.0, False

def get_optimizer_map(S_tilde, nu):
    """Returns a dictionary mapping algorithm names to (function, arguments)."""
    return {
        'greedy': (Optimizer.optimize_greedy, S_tilde),
        'thrifty': (Optimizer.optimize_thrifty, S_tilde),
        'thrifty_greedy': (Optimizer.optimize_thrifty_greedy, (S_tilde, nu)),
        'greedy_thrifty': (Optimizer.optimize_greedy_thrifty, (S_tilde, nu)),
        'optimal': (Optimizer.optimize_hungarian, S_tilde),
        'notoptimal': (Optimizer.optimize_hungarian_min, S_tilde)
    }

@app.route('/multi_optimize', methods=['POST'])
def multi_optimize():
    """Apply optimization algorithms to 50 matrices and return average results."""
    try:
        data = request.json
        matrices = data['matrices']  # Array of 50 matrices
        mass_per_batch = data.get('mass_per_batch', 1000.0)
        
        if len(matrices) != 50:
            return jsonify({'error': 'Exactly 50 matrices are required'}), 400
        
        # Initialize accumulators for each algorithm
        algorithm_names = ['greedy', 'thrifty', 'thrifty_greedy', 'greedy_thrifty', 'optimal', 'notoptimal']
        accumulators = {algo: {'yield_sum': 0.0, 'mass_sum': 0.0, 'count': 0} for algo in algorithm_names}
        
        all_results = []  # Store results for each matrix
        
        # Process each matrix
        for matrix_idx, matrix_data in enumerate(matrices):
            S_tilde = np.array(matrix_data)
            n = S_tilde.shape[0]
            nu = n // 2
            
            # Define algorithms and their arguments for this matrix
            algo_map = get_optimizer_map(S_tilde, nu)
            matrix_results = {}
            
            for algo_name in algorithm_names:
                func, args = algo_map[algo_name]
                y_val, m_val, success = run_algorithm(algo_name, func, args, mass_per_batch)
                
                if success:
                    accumulators[algo_name]['yield_sum'] += y_val
                    accumulators[algo_name]['mass_sum'] += m_val
                    accumulators[algo_name]['count'] += 1
                
                matrix_results[algo_name] = {
                    'yield': y_val,
                    'final_mass': m_val
                }
            
            all_results.append(matrix_results)
        
        # Calculate averages
        averages = {}
        for algo in algorithm_names:
            if accumulators[algo]['count'] > 0:
                avg_yield = accumulators[algo]['yield_sum'] / accumulators[algo]['count']
                avg_mass = accumulators[algo]['mass_sum'] / accumulators[algo]['count']
                
                averages[algo] = {
                    'yield': float(avg_yield),
                    'final_mass': float(avg_mass),
                    'success_count': accumulators[algo]['count']
                }
            else:
                averages[algo] = {
                    'yield': 0.0,
                    'final_mass': 0.0,
                    'success_count': 0
                }
        
        # Calculate relative losses vs optimal
        if 'optimal' in averages and averages['optimal']['yield'] > 0:
            for algo in algorithm_names:
                if algo != 'optimal' and algo in averages:
                    relative_loss = ((averages['optimal']['yield'] - averages[algo]['yield']) / 
                                    averages['optimal']['yield']) * 100
                    averages[algo]['relative_loss_percent'] = float(relative_loss)
        
        return jsonify({
            'averages': averages,
            'all_results': all_results,  # Optional: detailed results for each matrix
            'total_matrices': len(matrices)
        })
        
    except Exception as e:
        app.logger.exception("Multi-optimization failed")
        return jsonify({'error': 'Multi-optimization failed', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)