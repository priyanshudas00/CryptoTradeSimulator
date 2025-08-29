import time
import statistics
import numpy as np
from models import TradeSimulator
from optimizations import OptimizedCalculations

def run_benchmarks():
    print("Running performance benchmarks...")
    
    # Test data
    levels = [[str(10000 + i), str(1.0)] for i in range(1000)]
    quantity = 50
    mid_price = 10050.0
    
    # Convert levels to numpy array of floats for numba compatibility
    float_levels = np.array([[float(price), float(qty)] for price, qty in levels], dtype=np.float64)
    
    # Benchmark slippage calculation
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        OptimizedCalculations.numba_slippage(float_levels, quantity, mid_price, 'buy')
        times.append(time.perf_counter() - start)
    
    print(f"Slippage calculation (optimized): {statistics.mean(times)*1000:.4f} ms avg")
    
    # Benchmark volatility calculation
    prices = np.linspace(10000, 11000, 1000)
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        OptimizedCalculations.vectorized_volatility(prices)
        times.append(time.perf_counter() - start)
    
    print(f"Volatility calculation: {statistics.mean(times)*1000:.4f} ms avg")
    
    # Benchmark market impact
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        OptimizedCalculations.optimized_market_impact(50, 1000, 0.2)
        times.append(time.perf_counter() - start)
    
    print(f"Market impact calculation: {statistics.mean(times)*1000:.4f} ms avg")

if __name__ == "__main__":
    run_benchmarks()
