"""
AQI Forecasting Module

Machine Learning model to predict next-day AQI based on:
- Current pollution levels
- Weather conditions
- Time/seasonal features
- Active policies

Uses Random Forest for interpretability and robustness.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import pickle
import os

# Try to import sklearn, provide fallback if not installed
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed. ML forecasting disabled.")

from backend.config import (
    BASELINE_PM, AQI_THRESHOLDS, EMISSIONS, 
    WEATHER_DEFAULTS, HOURS_PER_DAY
)


@dataclass
class ForecastInput:
    """Input features for AQI prediction."""
    current_pm25: float
    current_pm10: float
    wind_speed: float
    temperature: float
    humidity: float
    is_inversion: bool
    hour: int
    day_of_week: int
    month: int
    is_winter: bool  # Oct-Feb
    active_policies: List[str]
    
    def to_features(self) -> np.ndarray:
        """Convert to feature array for model."""
        # Encode policies as binary features
        policy_features = [
            1 if "water_spraying" in self.active_policies else 0,
            1 if "odd_even" in self.active_policies else 0,
            1 if "construction_ban" in self.active_policies else 0,
            1 if "grap" in str(self.active_policies) else 0,
            1 if "source_elimination" in self.active_policies else 0,
            1 if "congestion_pricing" in self.active_policies else 0,
        ]
        
        features = [
            self.current_pm25,
            self.current_pm10,
            self.wind_speed,
            self.temperature,
            self.humidity,
            1 if self.is_inversion else 0,
            self.hour,
            self.day_of_week,
            self.month,
            1 if self.is_winter else 0,
        ] + policy_features
        
        return np.array(features).reshape(1, -1)


@dataclass
class ForecastResult:
    """Prediction result."""
    predicted_pm25: float
    predicted_pm10: float
    aqi_category: str
    confidence: float
    feature_importance: Dict[str, float]
    recommendation: str
    
    def to_dict(self) -> Dict:
        return {
            "predicted_pm25": round(self.predicted_pm25, 1),
            "predicted_pm10": round(self.predicted_pm10, 1),
            "aqi_category": self.aqi_category,
            "confidence": round(self.confidence, 2),
            "feature_importance": {k: round(v, 3) for k, v in self.feature_importance.items()},
            "recommendation": self.recommendation,
        }


class AQIForecaster:
    """
    Machine Learning model for AQI forecasting.
    
    Uses Random Forest to predict next-day PM2.5 and PM10 levels
    based on current conditions, weather, and active policies.
    """
    
    FEATURE_NAMES = [
        "current_pm25", "current_pm10", "wind_speed", "temperature",
        "humidity", "is_inversion", "hour", "day_of_week", "month",
        "is_winter", "policy_water", "policy_oddeven", "policy_construction",
        "policy_grap", "policy_source_elim", "policy_congestion"
    ]
    
    def __init__(self):
        self.model_pm25 = None
        self.model_pm10 = None
        self.scaler = None
        self.is_trained = False
        
        if SKLEARN_AVAILABLE:
            self._initialize_models()
            self._train_on_synthetic_data()
    
    def _initialize_models(self):
        """Initialize the ML models."""
        # Random Forest - good balance of accuracy and interpretability
        self.model_pm25 = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.model_pm10 = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.scaler = StandardScaler()
    
    def _generate_training_data(self, n_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate synthetic training data based on domain knowledge.
        
        In production, this would be replaced with real historical data.
        """
        np.random.seed(42)
        
        X = []
        y_pm25 = []
        y_pm10 = []
        
        for _ in range(n_samples):
            # Current conditions
            current_pm25 = np.random.uniform(30, 450)
            current_pm10 = current_pm25 * np.random.uniform(1.5, 2.5)
            
            # Weather
            wind_speed = np.random.uniform(1, 25)
            temperature = np.random.uniform(5, 40)
            humidity = np.random.uniform(30, 95)
            is_inversion = np.random.choice([0, 1], p=[0.7, 0.3])
            
            # Time features
            hour = np.random.randint(0, 24)
            day_of_week = np.random.randint(0, 7)
            month = np.random.randint(1, 13)
            is_winter = 1 if month in [10, 11, 12, 1, 2] else 0
            
            # Policies (random activation)
            policies = [
                np.random.choice([0, 1], p=[0.7, 0.3]),  # water
                np.random.choice([0, 1], p=[0.9, 0.1]),  # odd-even
                np.random.choice([0, 1], p=[0.85, 0.15]),  # construction
                np.random.choice([0, 1], p=[0.8, 0.2]),  # grap
                np.random.choice([0, 1], p=[0.95, 0.05]),  # source elim
                np.random.choice([0, 1], p=[0.95, 0.05]),  # congestion
            ]
            
            features = [
                current_pm25, current_pm10, wind_speed, temperature,
                humidity, is_inversion, hour, day_of_week, month, is_winter
            ] + policies
            
            # Generate target based on domain knowledge
            # Base: pollution tends to persist
            next_pm25 = current_pm25 * 0.85  # Some natural decay
            
            # Weather effects
            next_pm25 -= wind_speed * 2  # Wind helps dispersion
            if is_inversion:
                next_pm25 *= 1.3  # Inversion traps pollution
            if humidity > 70:
                next_pm25 *= 0.95  # Humidity helps deposition
            
            # Seasonal effects
            if is_winter:
                next_pm25 += 30  # Winter is worse
            
            # Emission additions (time-dependent)
            if 8 <= hour <= 10 or 18 <= hour <= 21:
                next_pm25 += 20  # Rush hour
            
            # Policy effects
            if policies[0]:  # Water spraying
                next_pm25 *= 0.97  # Very small effect
            if policies[1]:  # Odd-even
                next_pm25 *= 0.92
            if policies[2]:  # Construction ban
                next_pm25 *= 0.85
            if policies[3]:  # GRAP
                next_pm25 *= 0.80
            if policies[4]:  # Source elimination
                next_pm25 *= 0.60  # Major effect
            if policies[5]:  # Congestion pricing
                next_pm25 *= 0.75
            
            # Add noise
            next_pm25 += np.random.normal(0, 15)
            next_pm25 = max(20, min(500, next_pm25))
            
            # PM10 correlates with PM2.5
            next_pm10 = next_pm25 * np.random.uniform(1.8, 2.2)
            
            X.append(features)
            y_pm25.append(next_pm25)
            y_pm10.append(next_pm10)
        
        return np.array(X), np.array(y_pm25), np.array(y_pm10)
    
    def _train_on_synthetic_data(self):
        """Train the model on synthetic data."""
        if not SKLEARN_AVAILABLE:
            return
        
        print("Training AQI forecasting models...")
        
        # Generate data
        X, y_pm25, y_pm10 = self._generate_training_data(5000)
        
        # Split
        X_train, X_test, y25_train, y25_test = train_test_split(
            X, y_pm25, test_size=0.2, random_state=42
        )
        _, _, y10_train, y10_test = train_test_split(
            X, y_pm10, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train PM2.5 model
        self.model_pm25.fit(X_train_scaled, y25_train)
        pm25_pred = self.model_pm25.predict(X_test_scaled)
        pm25_mae = mean_absolute_error(y25_test, pm25_pred)
        pm25_r2 = r2_score(y25_test, pm25_pred)
        
        # Train PM10 model
        self.model_pm10.fit(X_train_scaled, y10_train)
        pm10_pred = self.model_pm10.predict(X_test_scaled)
        pm10_mae = mean_absolute_error(y10_test, pm10_pred)
        pm10_r2 = r2_score(y10_test, pm10_pred)
        
        print(f"  PM2.5 Model - MAE: {pm25_mae:.1f}, R²: {pm25_r2:.3f}")
        print(f"  PM10 Model  - MAE: {pm10_mae:.1f}, R²: {pm10_r2:.3f}")
        
        self.is_trained = True
    
    def predict(self, input_data: ForecastInput) -> ForecastResult:
        """
        Predict next-day AQI.
        
        Args:
            input_data: Current conditions and active policies
        
        Returns:
            Prediction with confidence and recommendations
        """
        if not SKLEARN_AVAILABLE or not self.is_trained:
            # Fallback to simple heuristic
            return self._heuristic_prediction(input_data)
        
        # Prepare features
        X = input_data.to_features()
        X_scaled = self.scaler.transform(X)
        
        # Get predictions
        pm25_pred = self.model_pm25.predict(X_scaled)[0]
        pm10_pred = self.model_pm10.predict(X_scaled)[0]
        
        # Get prediction confidence (based on tree variance)
        tree_predictions = np.array([
            tree.predict(X_scaled)[0] 
            for tree in self.model_pm25.estimators_
        ])
        std = np.std(tree_predictions)
        confidence = max(0.5, 1 - (std / 100))  # Higher std = lower confidence
        
        # Get feature importance
        importance = dict(zip(
            self.FEATURE_NAMES,
            self.model_pm25.feature_importances_
        ))
        
        # Determine AQI category
        aqi_category = self._get_aqi_category(pm25_pred)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            pm25_pred, input_data, importance
        )
        
        return ForecastResult(
            predicted_pm25=pm25_pred,
            predicted_pm10=pm10_pred,
            aqi_category=aqi_category,
            confidence=confidence,
            feature_importance=importance,
            recommendation=recommendation,
        )
    
    def _heuristic_prediction(self, input_data: ForecastInput) -> ForecastResult:
        """Simple rule-based fallback when ML is unavailable."""
        # Base prediction from current levels
        pm25_pred = input_data.current_pm25 * 0.9
        
        # Weather adjustments
        pm25_pred -= input_data.wind_speed * 1.5
        if input_data.is_inversion:
            pm25_pred *= 1.25
        if input_data.is_winter:
            pm25_pred += 20
        
        pm25_pred = max(30, min(450, pm25_pred))
        pm10_pred = pm25_pred * 2
        
        return ForecastResult(
            predicted_pm25=pm25_pred,
            predicted_pm10=pm10_pred,
            aqi_category=self._get_aqi_category(pm25_pred),
            confidence=0.6,
            feature_importance={"current_pm25": 0.5, "wind_speed": 0.3},
            recommendation="Enable ML by installing scikit-learn for better predictions.",
        )
    
    def _get_aqi_category(self, pm25: float) -> str:
        """Convert PM2.5 to AQI category."""
        if pm25 <= 30:
            return "Good"
        elif pm25 <= 60:
            return "Satisfactory"
        elif pm25 <= 90:
            return "Moderate"
        elif pm25 <= 120:
            return "Poor"
        elif pm25 <= 250:
            return "Very Poor"
        else:
            return "Severe"
    
    def _generate_recommendation(
        self, 
        predicted_pm25: float, 
        input_data: ForecastInput,
        importance: Dict[str, float]
    ) -> str:
        """Generate actionable recommendation based on prediction."""
        category = self._get_aqi_category(predicted_pm25)
        
        if category in ["Good", "Satisfactory"]:
            return "Air quality is expected to be acceptable. No special measures needed."
        
        # Find most impactful factors
        top_factors = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]
        
        recommendations = []
        
        if predicted_pm25 > 250:
            recommendations.append("⚠️ SEVERE: Consider activating GRAP Stage 3+")
        
        if input_data.wind_speed < 5:
            recommendations.append("Low wind expected - pollution will accumulate")
        
        if input_data.is_inversion:
            recommendations.append("Temperature inversion predicted - consider construction halt")
        
        if "policy_source_elim" in [f[0] for f in top_factors]:
            recommendations.append("Industrial emissions are a major factor - enforce scrubbers")
        
        if "current_pm25" in [f[0] for f in top_factors[:2]]:
            recommendations.append("Current pollution levels are high - act now to prevent buildup")
        
        if not recommendations:
            recommendations.append(f"Expected AQI category: {category}. Monitor closely.")
        
        return " | ".join(recommendations)
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model."""
        if not self.is_trained:
            return {"status": "not_trained", "message": "Model not available"}
        
        return {
            "status": "trained",
            "model_type": "Random Forest",
            "n_estimators": 100,
            "feature_names": self.FEATURE_NAMES,
            "feature_importance": dict(zip(
                self.FEATURE_NAMES,
                [round(x, 3) for x in self.model_pm25.feature_importances_]
            )),
        }


# Singleton instance
_forecaster = None

def get_forecaster() -> AQIForecaster:
    """Get or create the forecaster instance."""
    global _forecaster
    if _forecaster is None:
        _forecaster = AQIForecaster()
    return _forecaster


def predict_aqi(
    current_pm25: float,
    current_pm10: float,
    wind_speed: float = 8,
    temperature: float = 20,
    humidity: float = 60,
    is_inversion: bool = False,
    active_policies: List[str] = None,
) -> Dict:
    """
    Convenience function for AQI prediction.
    
    Args:
        current_pm25: Current PM2.5 level (µg/m³)
        current_pm10: Current PM10 level (µg/m³)
        wind_speed: Wind speed (km/h)
        temperature: Temperature (°C)
        humidity: Humidity (%)
        is_inversion: Temperature inversion present
        active_policies: List of active policy names
    
    Returns:
        Prediction dictionary
    """
    now = datetime.now()
    
    input_data = ForecastInput(
        current_pm25=current_pm25,
        current_pm10=current_pm10,
        wind_speed=wind_speed,
        temperature=temperature,
        humidity=humidity,
        is_inversion=is_inversion,
        hour=now.hour,
        day_of_week=now.weekday(),
        month=now.month,
        is_winter=now.month in [10, 11, 12, 1, 2],
        active_policies=active_policies or [],
    )
    
    forecaster = get_forecaster()
    result = forecaster.predict(input_data)
    
    return result.to_dict()
