import numpy as np

def generate_synthetic_clients(num_clients):
    return [{
        'features': np.random.rand(10).tolist(),
        'sensitive': np.random.choice([0,1])
    } for _ in range(num_clients)]