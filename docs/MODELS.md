# Model Implementation Documentation

## 1. Slippage Estimation (Quantile Regression)
- **Model Type**: Gradient Boosting Quantile Regression
- **Features Used**:
  - Order book imbalance (top 5 levels)
  - Bid-ask spread
  - Historical volatility (30-period)
- **Training**: Online training every 100 updates
- **Output**: Median predicted slippage (50th percentile)

## 2. Market Impact (Almgren-Chriss Model)
- **Parameters**:
  - η (temporary impact) = 0.1
  - γ (permanent impact) = 0.01
- **Volatility Input**: 30-period realized volatility
- **Liquidity Measure**: Sum of top 10 order book levels

## 3. Maker/Taker Prediction
- **Model Type**: Logistic Regression
- **Features**:
  - Recent price movement direction
  - Order book imbalance
  - Trade frequency
- **Output**: Probability of next trade being taker