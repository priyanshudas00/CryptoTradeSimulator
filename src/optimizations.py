import numpy as np
from numba import jit
import pandas as pd

class OptimizedCalculations:
    @staticmethod
    @jit(nopython=True)
    def numba_slippage(levels, quantity, mid_price, side):
        """Optimized slippage calculation using Numba"""
        executed_qty = 0
        total_cost = 0
        
        for i in range(len(levels)):
            price = float(levels[i][0])
            qty = float(levels[i][1])
            
            if executed_qty >= quantity:
                break
                
            fill_qty = min(qty, quantity - executed_qty)
            executed_qty += fill_qty
            total_cost += fill_qty * price
            
        if executed_qty > 0:
            avg_price = total_cost / executed_qty
            if side == 'buy':
                slippage = (avg_price - mid_price) / mid_price
            else:
                slippage = (mid_price - avg_price) / mid_price
            return slippage * 100
        return 0
        
    @staticmethod
    def vectorized_volatility(price_series):
        """Vectorized volatility calculation"""
        log_returns = np.log(price_series[1:]/price_series[:-1])
        return np.std(log_returns) * np.sqrt(365*24)
        
    @staticmethod
    def optimized_market_impact(quantity, liquidity, volatility, side='buy'):
        """Optimized market impact calculation"""
        # Precompute often-used values
        q_over_l = quantity / liquidity
        temp_impact = 0.1 * q_over_l  # eta = 0.1
        perm_impact = 0.01 * q_over_l  # gamma = 0.01
        return (temp_impact + perm_impact) * 100