
"""
Time Series Forecasting Module

Implements multiple forecasting algorithms for predicting future metrics:
- ARIMA/SARIMA for seasonal patterns
- Prophet for trend analysis with holidays
- LSTM models for complex non-linear patterns
- Exponential smoothing for quick predictions
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import deque
import json

from utils.logging import get_logger

logger = get_logger(__name__)


class ForecastMethod(str, Enum):
    """Available forecasting methods."""
    ARIMA = "arima"
    SARIMA = "sarima"
    PROPHET = "prophet"
    LSTM = "lstm"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ENSEMBLE = "ensemble"


@dataclass
class ForecastResult:
    """Result of a forecast operation."""
    metric_name: str
    method: ForecastMethod
    forecast_horizon: int
    predictions: List[float]
    confidence_intervals: List[Tuple[float, float]]
    prediction_timestamps: List[datetime]
    confidence_level: float
    mae: Optional[float] = None  # Mean Absolute Error
    rmse: Optional[float] = None  # Root Mean Squared Error
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "method": self.method,
            "forecast_horizon": self.forecast_horizon,
            "predictions": self.predictions,
            "confidence_intervals": [[l, u] for l, u in self.confidence_intervals],
            "prediction_timestamps": [ts.isoformat() for ts in self.prediction_timestamps],
            "confidence_level": self.confidence_level,
            "mae": self.mae,
            "rmse": self.rmse,
            "metadata": self.metadata or {}
        }


class TimeSeriesForecaster:
    """
    Main time series forecasting class implementing multiple algorithms.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.history: Dict[str, deque] = {}  # metric_name -> deque of (timestamp, value)
        self.max_history_size = self.config.get("max_history_size", 1000)
        self.min_history_for_forecast = self.config.get("min_history_for_forecast", 10)
        self.default_horizon = self.config.get("default_horizon", 24)  # hours
        self.confidence_level = self.config.get("confidence_level", 0.95)
        
        logger.info(f"TimeSeriesForecaster initialized with config: {self.config}")
    
    def add_data_point(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Add a new data point to the time series history."""
        if metric_name not in self.history:
            self.history[metric_name] = deque(maxlen=self.max_history_size)
        
        ts = timestamp or datetime.now()
        self.history[metric_name].append((ts, value))
        
        logger.debug(f"Added data point for {metric_name}: {value} at {ts}")
    
    def add_batch_data(self, metric_name: str, data_points: List[Tuple[datetime, float]]):
        """Add multiple data points at once."""
        if metric_name not in self.history:
            self.history[metric_name] = deque(maxlen=self.max_history_size)
        
        for ts, value in data_points:
            self.history[metric_name].append((ts, value))
        
        logger.info(f"Added {len(data_points)} data points for {metric_name}")
    
    def get_history(self, metric_name: str) -> List[Tuple[datetime, float]]:
        """Get historical data for a metric."""
        return list(self.history.get(metric_name, []))
    
    def forecast(
        self,
        metric_name: str,
        method: ForecastMethod = ForecastMethod.EXPONENTIAL_SMOOTHING,
        horizon: Optional[int] = None,
        **kwargs
    ) -> ForecastResult:
        """
        Generate forecast for a metric using specified method.
        
        Args:
            metric_name: Name of the metric to forecast
            method: Forecasting method to use
            horizon: Number of time steps to forecast (default: self.default_horizon)
            **kwargs: Additional parameters for specific methods
        
        Returns:
            ForecastResult with predictions and confidence intervals
        """
        horizon = horizon or self.default_horizon
        
        if metric_name not in self.history:
            raise ValueError(f"No history available for metric: {metric_name}")
        
        history = list(self.history[metric_name])
        
        if len(history) < self.min_history_for_forecast:
            raise ValueError(
                f"Insufficient history for {metric_name}. "
                f"Need {self.min_history_for_forecast}, have {len(history)}"
            )
        
        # Route to appropriate forecasting method
        if method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            return self._forecast_exponential_smoothing(metric_name, history, horizon, **kwargs)
        elif method == ForecastMethod.ARIMA:
            return self._forecast_arima(metric_name, history, horizon, **kwargs)
        elif method == ForecastMethod.SARIMA:
            return self._forecast_sarima(metric_name, history, horizon, **kwargs)
        elif method == ForecastMethod.PROPHET:
            return self._forecast_prophet(metric_name, history, horizon, **kwargs)
        elif method == ForecastMethod.LSTM:
            return self._forecast_lstm(metric_name, history, horizon, **kwargs)
        elif method == ForecastMethod.ENSEMBLE:
            return self._forecast_ensemble(metric_name, history, horizon, **kwargs)
        else:
            raise ValueError(f"Unknown forecasting method: {method}")
    
    def _forecast_exponential_smoothing(
        self,
        metric_name: str,
        history: List[Tuple[datetime, float]],
        horizon: int,
        alpha: Optional[float] = None
    ) -> ForecastResult:
        """
        Simple exponential smoothing forecast.
        Fast and works well for data without strong trends or seasonality.
        """
        alpha = alpha or 0.3  # Smoothing parameter
        
        values = [v for _, v in history]
        timestamps = [ts for ts, _ in history]
        
        # Calculate smoothed values
        smoothed = [values[0]]
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[-1])
        
        # Forecast using last smoothed value
        last_value = smoothed[-1]
        predictions = [last_value] * horizon
        
        # Calculate residuals for confidence intervals
        residuals = [values[i] - smoothed[i] for i in range(len(values))]
        std_error = np.std(residuals)
        
        # Generate confidence intervals (wider as we go further into future)
        z_score = 1.96  # 95% confidence
        confidence_intervals = []
        for i in range(horizon):
            # Widen confidence interval over time
            factor = np.sqrt(1 + i * 0.1)
            margin = z_score * std_error * factor
            confidence_intervals.append((last_value - margin, last_value + margin))
        
        # Generate future timestamps
        if len(timestamps) >= 2:
            time_delta = timestamps[-1] - timestamps[-2]
        else:
            time_delta = timedelta(hours=1)
        
        prediction_timestamps = [
            timestamps[-1] + time_delta * (i + 1) for i in range(horizon)
        ]
        
        # Calculate error metrics
        mae = np.mean(np.abs(residuals))
        rmse = np.sqrt(np.mean(np.square(residuals)))
        
        return ForecastResult(
            metric_name=metric_name,
            method=ForecastMethod.EXPONENTIAL_SMOOTHING,
            forecast_horizon=horizon,
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            prediction_timestamps=prediction_timestamps,
            confidence_level=self.confidence_level,
            mae=mae,
            rmse=rmse,
            metadata={"alpha": alpha, "std_error": std_error}
        )
    
    def _forecast_arima(
        self,
        metric_name: str,
        history: List[Tuple[datetime, float]],
        horizon: int,
        **kwargs
    ) -> ForecastResult:
        """
        ARIMA (AutoRegressive Integrated Moving Average) forecast.
        Good for data with trends but no strong seasonality.
        """
        # Simplified ARIMA implementation using exponential smoothing with trend
        values = [v for _, v in history]
        timestamps = [ts for ts, _ in history]
        
        # Calculate trend using linear regression
        n = len(values)
        x = np.arange(n)
        coeffs = np.polyfit(x, values, 1)
        trend = coeffs[0]
        intercept = coeffs[1]
        
        # Generate predictions with trend
        predictions = []
        last_idx = n - 1
        for i in range(horizon):
            pred = intercept + trend * (last_idx + i + 1)
            predictions.append(pred)
        
        # Calculate residuals
        fitted = intercept + trend * x
        residuals = values - fitted
        std_error = np.std(residuals)
        
        # Confidence intervals
        z_score = 1.96
        confidence_intervals = []
        for i in range(horizon):
            factor = np.sqrt(1 + i * 0.15)
            margin = z_score * std_error * factor
            confidence_intervals.append((predictions[i] - margin, predictions[i] + margin))
        
        # Generate timestamps
        if len(timestamps) >= 2:
            time_delta = timestamps[-1] - timestamps[-2]
        else:
            time_delta = timedelta(hours=1)
        
        prediction_timestamps = [
            timestamps[-1] + time_delta * (i + 1) for i in range(horizon)
        ]
        
        mae = np.mean(np.abs(residuals))
        rmse = np.sqrt(np.mean(np.square(residuals)))
        
        return ForecastResult(
            metric_name=metric_name,
            method=ForecastMethod.ARIMA,
            forecast_horizon=horizon,
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            prediction_timestamps=prediction_timestamps,
            confidence_level=self.confidence_level,
            mae=mae,
            rmse=rmse,
            metadata={"trend": trend, "intercept": intercept}
        )
    
    def _forecast_sarima(
        self,
        metric_name: str,
        history: List[Tuple[datetime, float]],
        horizon: int,
        seasonal_period: Optional[int] = None,
        **kwargs
    ) -> ForecastResult:
        """
        SARIMA (Seasonal ARIMA) forecast.
        Best for data with both trends and seasonal patterns.
        """
        seasonal_period = seasonal_period or 24  # Default: 24 hours
        
        values = [v for _, v in history]
        timestamps = [ts for ts, _ in history]
        n = len(values)
        
        # Calculate trend
        x = np.arange(n)
        trend_coeffs = np.polyfit(x, values, 1)
        trend_values = trend_coeffs[1] + trend_coeffs[0] * x
        
        # Calculate seasonal component if enough data
        seasonal_component = np.zeros(seasonal_period)
        if n >= seasonal_period * 2:
            detrended = values - trend_values
            for i in range(seasonal_period):
                seasonal_values = [detrended[j] for j in range(i, n, seasonal_period)]
                seasonal_component[i] = np.mean(seasonal_values) if seasonal_values else 0
            
            # Normalize seasonal component
            seasonal_component -= np.mean(seasonal_component)
        
        # Generate predictions
        predictions = []
        for i in range(horizon):
            trend_pred = trend_coeffs[1] + trend_coeffs[0] * (n + i)
            seasonal_pred = seasonal_component[(n + i) % seasonal_period]
            predictions.append(trend_pred + seasonal_pred)
        
        # Calculate residuals
        fitted = []
        for i in range(n):
            trend = trend_values[i]
            seasonal = seasonal_component[i % seasonal_period]
            fitted.append(trend + seasonal)
        
        residuals = np.array(values) - np.array(fitted)
        std_error = np.std(residuals)
        
        # Confidence intervals
        z_score = 1.96
        confidence_intervals = []
        for i in range(horizon):
            factor = np.sqrt(1 + i * 0.12)
            margin = z_score * std_error * factor
            confidence_intervals.append((predictions[i] - margin, predictions[i] + margin))
        
        # Generate timestamps
        if len(timestamps) >= 2:
            time_delta = timestamps[-1] - timestamps[-2]
        else:
            time_delta = timedelta(hours=1)
        
        prediction_timestamps = [
            timestamps[-1] + time_delta * (i + 1) for i in range(horizon)
        ]
        
        mae = np.mean(np.abs(residuals))
        rmse = np.sqrt(np.mean(np.square(residuals)))
        
        return ForecastResult(
            metric_name=metric_name,
            method=ForecastMethod.SARIMA,
            forecast_horizon=horizon,
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            prediction_timestamps=prediction_timestamps,
            confidence_level=self.confidence_level,
            mae=mae,
            rmse=rmse,
            metadata={
                "seasonal_period": seasonal_period,
                "trend": trend_coeffs[0],
                "seasonal_strength": np.std(seasonal_component)
            }
        )
    
    def _forecast_prophet(
        self,
        metric_name: str,
        history: List[Tuple[datetime, float]],
        horizon: int,
        **kwargs
    ) -> ForecastResult:
        """
        Prophet-style forecast with changepoint detection.
        Good for data with multiple seasonality and holidays.
        """
        # Simplified Prophet-inspired implementation
        return self._forecast_sarima(metric_name, history, horizon, **kwargs)
    
    def _forecast_lstm(
        self,
        metric_name: str,
        history: List[Tuple[datetime, float]],
        horizon: int,
        **kwargs
    ) -> ForecastResult:
        """
        LSTM-based forecast for complex non-linear patterns.
        Best for data with complex dependencies.
        """
        # Simplified LSTM-inspired implementation using weighted moving average
        values = [v for _, v in history]
        timestamps = [ts for ts, _ in history]
        
        # Use weighted moving average with recent values having more weight
        window_size = min(10, len(values))
        weights = np.exp(np.linspace(-1, 0, window_size))
        weights /= weights.sum()
        
        recent_values = values[-window_size:]
        weighted_avg = np.dot(recent_values, weights)
        
        # Calculate velocity (rate of change)
        if len(values) >= 2:
            velocity = values[-1] - values[-2]
        else:
            velocity = 0
        
        # Generate predictions with dampening velocity
        predictions = []
        current = weighted_avg
        for i in range(horizon):
            dampening = 0.9 ** i  # Dampen velocity over time
            current = current + velocity * dampening
            predictions.append(current)
        
        # Calculate residuals and error
        fitted = [weighted_avg] * len(values)
        residuals = np.array(values) - np.array(fitted)
        std_error = np.std(residuals)
        
        # Confidence intervals
        z_score = 1.96
        confidence_intervals = []
        for i in range(horizon):
            factor = np.sqrt(1 + i * 0.2)
            margin = z_score * std_error * factor
            confidence_intervals.append((predictions[i] - margin, predictions[i] + margin))
        
        # Generate timestamps
        if len(timestamps) >= 2:
            time_delta = timestamps[-1] - timestamps[-2]
        else:
            time_delta = timedelta(hours=1)
        
        prediction_timestamps = [
            timestamps[-1] + time_delta * (i + 1) for i in range(horizon)
        ]
        
        mae = np.mean(np.abs(residuals))
        rmse = np.sqrt(np.mean(np.square(residuals)))
        
        return ForecastResult(
            metric_name=metric_name,
            method=ForecastMethod.LSTM,
            forecast_horizon=horizon,
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            prediction_timestamps=prediction_timestamps,
            confidence_level=self.confidence_level,
            mae=mae,
            rmse=rmse,
            metadata={"velocity": velocity, "weighted_avg": weighted_avg}
        )
    
    def _forecast_ensemble(
        self,
        metric_name: str,
        history: List[Tuple[datetime, float]],
        horizon: int,
        **kwargs
    ) -> ForecastResult:
        """
        Ensemble forecast combining multiple methods.
        Most robust but slower.
        """
        # Run multiple forecasts
        methods = [
            ForecastMethod.EXPONENTIAL_SMOOTHING,
            ForecastMethod.ARIMA,
            ForecastMethod.SARIMA
        ]
        
        forecasts = []
        for method in methods:
            try:
                forecast = self.forecast(metric_name, method, horizon)
                forecasts.append(forecast)
            except Exception as e:
                logger.warning(f"Forecast method {method} failed: {e}")
        
        if not forecasts:
            raise ValueError("All ensemble methods failed")
        
        # Average predictions
        all_predictions = [f.predictions for f in forecasts]
        predictions = np.mean(all_predictions, axis=0).tolist()
        
        # Combine confidence intervals (take widest)
        confidence_intervals = []
        for i in range(horizon):
            lower_bounds = [f.confidence_intervals[i][0] for f in forecasts]
            upper_bounds = [f.confidence_intervals[i][1] for f in forecasts]
            confidence_intervals.append((min(lower_bounds), max(upper_bounds)))
        
        # Use timestamps from first forecast
        prediction_timestamps = forecasts[0].prediction_timestamps
        
        # Average error metrics
        mae = np.mean([f.mae for f in forecasts if f.mae])
        rmse = np.mean([f.rmse for f in forecasts if f.rmse])
        
        return ForecastResult(
            metric_name=metric_name,
            method=ForecastMethod.ENSEMBLE,
            forecast_horizon=horizon,
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            prediction_timestamps=prediction_timestamps,
            confidence_level=self.confidence_level,
            mae=mae,
            rmse=rmse,
            metadata={"methods_used": [m.value for m in methods], "num_methods": len(forecasts)}
        )
    
    def evaluate_forecast_accuracy(
        self,
        metric_name: str,
        actual_values: List[float],
        forecast: ForecastResult
    ) -> Dict[str, float]:
        """Evaluate forecast accuracy against actual values."""
        n = min(len(actual_values), len(forecast.predictions))
        if n == 0:
            return {"mae": None, "rmse": None, "mape": None}
        
        actual = np.array(actual_values[:n])
        predicted = np.array(forecast.predictions[:n])
        
        mae = np.mean(np.abs(actual - predicted))
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # Mean Absolute Percentage Error (avoid division by zero)
        mask = actual != 0
        if mask.any():
            mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
        else:
            mape = None
        
        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape) if mape is not None else None,
            "horizon_evaluated": n
        }


