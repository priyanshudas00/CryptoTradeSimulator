import numpy as np
from scipy.stats import linregress, norm
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import time
from collections import deque
from numba import jit
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

class TradeSimulator:
    def __init__(self):
        self.last_orderbook = None
        self.historical_data = deque(maxlen=2000)  # Increased history
        self.volatility_window = 50  # Longer lookback for volatility
        self.fee_tiers = {
            'taker': {1: 0.0010, 2: 0.0008, 3: 0.0005},  # Tiered fee structure
            'maker': {1: 0.0008, 2: 0.0006, 3: 0.0004}
        }
        self.processing_times = deque(maxlen=500)
        self.update_frequencies = deque(maxlen=500)
        self.last_update_time = time.time()
        self.slippage_model = self._init_slippage_model()
        self.maker_taker_model = self._init_maker_taker_model()
        self.scaler = StandardScaler()
        self.last_volatility = 0
        self.last_impact = 0
        
    def _init_slippage_model(self):
        """Initialize ensemble model for slippage with better configuration"""
        return make_pipeline(
            StandardScaler(),
            HistGradientBoostingRegressor(
                loss='quantile',
                quantile=0.5,
                max_iter=200,
                max_depth=5,
                learning_rate=0.05,
                min_samples_leaf=20
            )
        )
        
    def _init_maker_taker_model(self):
        """Initialize enhanced maker/taker prediction model"""
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(
                penalty='elasticnet',
                solver='saga',
                l1_ratio=0.5,
                max_iter=1000,
                class_weight='balanced'
            )
        )

    def update_orderbook(self, orderbook):
        """Enhanced orderbook update with model retraining logic"""
        current_time = time.time()
        if self.last_orderbook:
            self.update_frequencies.append(current_time - self.last_update_time)
        self.last_update_time = current_time

        # Validate orderbook structure
        if not self._validate_orderbook(orderbook):
            return

        self.last_orderbook = orderbook
        self.historical_data.append(orderbook)
        
        # Adaptive model retraining
        if len(self.historical_data) % 50 == 0:  # More frequent retraining
            self._train_models()
            
    def _validate_orderbook(self, orderbook):
        """Validate orderbook structure and data quality"""
        required_keys = {'asks', 'bids', 'timestamp'}
        if not all(key in orderbook for key in required_keys):
            return False
            
        try:
            # Validate at least 5 levels on each side
            if len(orderbook['asks']) < 5 or len(orderbook['bids']) < 5:
                return False
                
            # Validate numeric values
            float(orderbook['asks'][0][0])
            float(orderbook['asks'][0][1])
            return True
        except (ValueError, IndexError, TypeError):
            return False
            
    def _train_models(self):
        """Train all models with enhanced features"""
        if len(self.historical_data) < 100:
            return
            
        # Prepare slippage model data
        X_slip, y_slip = self._prepare_slippage_training_data()
        if len(X_slip) > 20:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.slippage_model.fit(X_slip, y_slip)
        
        # Prepare maker/taker model data
        X_mt, y_mt = self._prepare_maker_taker_data()
        if len(set(y_mt)) > 1:  # Need at least two classes
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.maker_taker_model.fit(X_mt, y_mt)
                
    def _prepare_slippage_training_data(self):
        """Prepare enhanced features for slippage model"""
        X = []
        y = []
        
        for i in range(2, len(self.historical_data)):
            current = self.historical_data[i]
            previous = self.historical_data[i-1]
            
            try:
                # Enhanced feature set
                spread = self._get_spread(current)
                imbalance = self._get_orderbook_imbalance(current)
                vol = self._calculate_volatility(window=30)
                depth_ratio = self._get_depth_ratio(current)
                price_change = self._get_price_change(current, previous)
                
                X.append([spread, imbalance, vol, depth_ratio, price_change])
                
                # Calculate actual slippage
                mid_price = self._get_mid_price_from_snapshot(previous)
                executed_price = float(current['asks'][0][0])
                y.append((executed_price - mid_price)/mid_price)
            except (IndexError, ValueError):
                continue
                
        return np.array(X), np.array(y)
        
    def _prepare_maker_taker_data(self):
        """Prepare enhanced features for maker/taker model"""
        X = []
        y = []
        
        for i in range(2, len(self.historical_data)):
            current = self.historical_data[i]
            previous = self.historical_data[i-1]
            
            try:
                # Enhanced features
                price_change = self._get_price_change(current, previous)
                volume_ratio = self._get_volume_ratio(current, previous)
                spread_change = self._get_spread_change(current, previous)
                vol = self._calculate_volatility(window=20)
                
                X.append([price_change, volume_ratio, spread_change, vol])
                
                # Label based on aggressive order detection
                mid_price = self._get_mid_price_from_snapshot(previous)
                current_price = float(current['asks'][0][0])
                y.append(1 if current_price < mid_price * 1.0001 else 0)
            except (IndexError, ValueError):
                continue
                
        return np.array(X), np.array(y)

    def calculate_slippage(self, quantity, side='buy', volatility_sens=0.5):
        """Enhanced slippage calculation with size and volatility sensitivity"""
        if not self.last_orderbook:
            return 0
            
        # Base slippage from model
        spread = self._get_spread(self.last_orderbook)
        imbalance = self._get_orderbook_imbalance(self.last_orderbook)
        vol = self._calculate_volatility()
        depth_ratio = self._get_depth_ratio(self.last_orderbook)
        price_change = self._get_recent_price_change()
        
        try:
            model_input = np.array([[spread, imbalance, vol, depth_ratio, price_change]])
            predicted = self.slippage_model.predict(model_input)[0]
            base_slippage = max(0, predicted) * 100
        except Exception:
            base_slippage = 0
            
        # Size-based adjustment (non-linear)
        size_factor = min(0.5, (quantity ** 0.8) * 0.001)
        
        # Volatility sensitivity (0-1 input scales adjustment)
        vol_adjustment = 1 + (volatility_sens * 2)  # 1x-3x scaling
        
        return base_slippage * vol_adjustment + size_factor
        
    def calculate_market_impact(self, quantity, side='buy', volatility_sens=0.5):
        """Enhanced Almgren-Chriss model with volatility sensitivity"""
        if not self.last_orderbook or len(self.historical_data) < 20:
            return self.last_impact if hasattr(self, 'last_impact') else 0
            
        # Calculate liquidity at different depth tiers
        levels = self.last_orderbook['asks'] if side == 'buy' else self.last_orderbook['bids']
        liquidity_tiers = [
            sum(float(qty) for _, qty in levels[:5]),  # Immediate
            sum(float(qty) for _, qty in levels[5:10]), # Near
            sum(float(qty) for _, qty in levels[10:20]) # Deep
        ]
        total_liquidity = sum(liquidity_tiers)
        
        if total_liquidity <= 0:
            return 0
            
        # Weighted liquidity calculation
        liquidity = (
            0.6 * liquidity_tiers[0] + 
            0.3 * liquidity_tiers[1] + 
            0.1 * liquidity_tiers[2]
        )
        
        # Dynamic impact parameters based on volatility
        vol = self._calculate_volatility()
        eta = 0.05 + (vol * 0.15)  # Temporary impact coefficient
        gamma = 0.01 + (vol * 0.04) # Permanent impact coefficient
        
        # Size-adjusted impact
        size_ratio = quantity / liquidity
        temp_impact = eta * (size_ratio ** 0.7)
        perm_impact = gamma * (size_ratio ** 0.5)
        
        # Apply volatility sensitivity
        impact = (temp_impact + perm_impact) * (0.8 + volatility_sens * 0.4)
        self.last_impact = impact * 100  # Store as percentage
        return self.last_impact
        
    def estimate_maker_taker_proportion(self):
        """Enhanced maker/taker prediction with current market features"""
        if len(self.historical_data) < 50:
            return (0.7, 0.3)  # Default to more maker activity
            
        try:
            # Current market features
            price_change = self._get_recent_price_change()
            volume_ratio = self._get_volume_ratio(self.last_orderbook, self.historical_data[-2])
            spread_change = self._get_spread_change(self.last_orderbook, self.historical_data[-2])
            vol = self._calculate_volatility(window=20)
            
            # Predict
            proba = self.maker_taker_model.predict_proba(
                np.array([[price_change, volume_ratio, spread_change, vol]])
            )[0]
            return (proba[0], proba[1])  # (maker, taker)
        except Exception:
            return (0.7, 0.3)
            
    # Helper methods --------------------------------------------------------
    
    def _get_spread(self, snapshot):
        """Bid-ask spread in percentage terms"""
        if not snapshot['asks'] or not snapshot['bids']:
            return 0
        best_ask = float(snapshot['asks'][0][0])
        best_bid = float(snapshot['bids'][0][0])
        mid = (best_ask + best_bid) / 2
        return (best_ask - best_bid) / mid if mid > 0 else 0
        
    def _get_orderbook_imbalance(self, snapshot, depth=10):
        """Order book imbalance metric (-1 to 1)"""
        bids = sum(float(qty) for _, qty in snapshot['bids'][:depth])
        asks = sum(float(qty) for _, qty in snapshot['asks'][:depth])
        total = bids + asks
        return (bids - asks) / total if total > 0 else 0
        
    def _get_depth_ratio(self, snapshot):
        """Ratio of deep liquidity to immediate liquidity"""
        immediate = sum(float(qty) for _, qty in snapshot['asks'][:5] + snapshot['bids'][:5])
        deep = sum(float(qty) for _, qty in snapshot['asks'][5:20] + snapshot['bids'][5:20])
        return deep / (immediate + 1e-6)
        
    def _get_price_change(self, current, previous, window=5):
        """Price change over recent history"""
        if len(self.historical_data) < window:
            return 0
        current_mid = self._get_mid_price_from_snapshot(current)
        previous_mid = self._get_mid_price_from_snapshot(previous)
        return (current_mid - previous_mid) / previous_mid if previous_mid > 0 else 0
        
    def _get_recent_price_change(self):
        """Most recent price change"""
        if len(self.historical_data) < 2:
            return 0
        return self._get_price_change(self.historical_data[-1], self.historical_data[-2])
        
    def _get_volume_ratio(self, current, previous):
        """Volume change ratio"""
        current_vol = sum(float(qty) for _, qty in current['asks'][:5] + current['bids'][:5])
        previous_vol = sum(float(qty) for _, qty in previous['asks'][:5] + previous['bids'][:5])
        return current_vol / (previous_vol + 1e-6)
        
    def _get_spread_change(self, current, previous):
        """Spread change ratio"""
        current_spread = self._get_spread(current)
        previous_spread = self._get_spread(previous)
        return current_spread / (previous_spread + 1e-6)
        
    def _calculate_volatility(self, window=30):
        """Realized volatility with adaptive window"""
        if len(self.historical_data) < window:
            return self.last_volatility if hasattr(self, 'last_volatility') else 0
            
        prices = [self._get_mid_price_from_snapshot(snap) 
                 for snap in list(self.historical_data)[-window:]]
        if len(prices) < 2:
            return 0
            
        log_returns = np.diff(np.log(prices))
        vol = np.std(log_returns) * np.sqrt(365*24)  # Annualized
        self.last_volatility = vol
        return vol
        
    def _get_mid_price_from_snapshot(self, snapshot):
        """Robust mid price calculation"""
        try:
            best_ask = float(snapshot['asks'][0][0]) if snapshot['asks'] else 0
            best_bid = float(snapshot['bids'][0][0]) if snapshot['bids'] else 0
            return (best_ask + best_bid) / 2 if best_ask and best_bid else 0
        except (IndexError, ValueError):
            return 0

    def get_mid_price(self):
        """Public method to get mid price of the last orderbook"""
        if not self.last_orderbook:
            return 0
        return self._get_mid_price_from_snapshot(self.last_orderbook)
            
    def calculate_fees(self, quantity, price, tier=1, is_maker=False):
        """Tiered fee calculation"""
        fee_type = 'maker' if is_maker else 'taker'
        fee_rate = self.fee_tiers[fee_type].get(tier, self.fee_tiers[fee_type][1])
        return quantity * price * fee_rate
        
    def calculate_all_metrics(self, quantity, side='buy', volatility_sens=0.5, fee_tier=1, price=None):
        """Comprehensive metric calculation with timing"""
        start_time = time.time()
        
        if not self.last_orderbook:
            return None
            
        mid_price = self._get_mid_price_from_snapshot(self.last_orderbook)
        if mid_price <= 0:
            return None
        
        used_price = price if price is not None else mid_price
            
        # Calculate components
        slippage = self.calculate_slippage(quantity, side, volatility_sens)
        maker_prob, taker_prob = self.estimate_maker_taker_proportion()
        is_maker = maker_prob > 0.5
        fees = self.calculate_fees(quantity, used_price, fee_tier, is_maker)
        market_impact = self.calculate_market_impact(quantity, side, volatility_sens)
        
        # Net cost calculation (slippage + fees + impact)
        slippage_cost = (slippage/100) * used_price * quantity
        impact_cost = (market_impact/100) * used_price * quantity
        net_cost = slippage_cost + fees + impact_cost
        
        # Performance metrics
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
        return {
            'mid_price': mid_price,
            'slippage': slippage,
            'fees': fees,
            'market_impact': market_impact,
            'net_cost': net_cost,
            'maker_taker_proportion': (maker_prob, taker_prob),
            'processing_time': processing_time,
            'avg_processing_time': self._get_avg_processing_time(),
            'update_frequency': self._get_avg_update_frequency(),
            'orderbook_depth': len(self.last_orderbook['asks']) if self.last_orderbook else 0,
            'volatility': self._calculate_volatility(),
            'liquidity': self._get_liquidity_estimate()
        }
        
    def _get_avg_processing_time(self):
        """Robust average processing time calculation"""
        if not self.processing_times:
            return 0
        return np.percentile(self.processing_times, 50)  # Median
        
    def _get_avg_update_frequency(self):
        """Average update frequency in seconds"""
        if not self.update_frequencies:
            return 0
        return np.mean(self.update_frequencies)
        
    def _get_liquidity_estimate(self):
        """Estimate total liquidity in order book"""
        if not self.last_orderbook:
            return 0
        bids = sum(float(qty) for _, qty in self.last_orderbook['bids'][:20])
        asks = sum(float(qty) for _, qty in self.last_orderbook['asks'][:20])
        return bids + asks