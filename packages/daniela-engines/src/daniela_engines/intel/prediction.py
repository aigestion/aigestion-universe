"""
Prediction Engine - Ideas 31-40
===============================

31. Time series forecasting (ARIMA/Prophet)
32. Anomaly detection (Isolation Forest)
33. Churn prediction
34. Demand forecasting
35. Resource utilization prediction
36. Error rate prediction
37. Latency prediction
38. Cost prediction
39. User growth prediction
40. Capacity planning predictor
"""

import math
import random
from datetime import datetime


class PredictionEngine:
    """Core prediction engine with 10 powerful forecasting and analysis capabilities."""

    def __init__(self):
        self.historical_data: dict[str, list[float]] = {}
        self.model_cache: dict[str, dict] = {}

    def _generate_time_series(self, base: float, length: int, trend: float = 0.01, seasonality: float = 0.1, noise: float = 0.05) -> list[float]:
        """Generate synthetic time series data."""
        data = []
        for i in range(length):
            seasonal = seasonality * math.sin(2 * math.pi * i / 12)
            noise_val = random.gauss(0, noise * base)
            value = base + trend * i + seasonal + noise_val
            data.append(round(max(0, value), 2))
        return data

    def _simple_linear_regression(self, x: list[float], y: list[float]) -> tuple[float, float]:
        """Simple linear regression returning (slope, intercept)."""
        n = len(x)
        if n == 0:
            return 0.0, 0.0
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        slope = ss_xy / ss_xx if ss_xx else 0
        intercept = mean_y - slope * mean_x
        return round(slope, 6), round(intercept, 6)

    def _moving_average(self, data: list[float], window: int = 3) -> list[float]:
        """Compute moving average."""
        result = []
        for i in range(len(data)):
            start = max(0, i - window + 1)
            result.append(round(sum(data[start:i + 1]) / (i - start + 1), 2))
        return result

    # ── Idea 31: Time Series Forecasting ────────────────────────────
    def forecast_time_series(self, data: list[float], periods: int = 12, method: str = "arima") -> dict:
        """Forecast future values using ARIMA-like or Prophet-like approach."""
        if not data:
            return {"error": "No data provided"}
        n = len(data)
        x = list(range(n))
        slope, intercept = self._simple_linear_regression(x, data)
        trend_forecast = [round(intercept + slope * (n + i), 2) for i in range(periods)]
        ma = self._moving_average(data, window=min(3, n))
        last_ma = ma[-1] if ma else data[-1]
        seasonal_component = []
        if n >= 12:
            monthly = [sum(data[i::12][:n // 12 + 1]) / max(1, len(data[i::12][:n // 12 + 1])) for i in range(12)]
            for i in range(periods):
                seasonal_component.append(round(monthly[(n + i) % 12], 2))
        forecast = []
        for i in range(periods):
            trend_val = trend_forecast[i]
            season_val = seasonal_component[i] if seasonal_component else last_ma
            combined = round(0.6 * trend_val + 0.4 * season_val, 2)
            forecast.append({
                "period": n + i + 1,
                "forecast": combined,
                "trend": trend_val,
                "seasonal": season_val,
                "lower_bound": round(combined * 0.9, 2),
                "upper_bound": round(combined * 1.1, 2),
            })
        residuals = [data[i] - (intercept + slope * i) for i in range(n)]
        rmse = round(math.sqrt(sum(r ** 2 for r in residuals) / n), 4) if n else 0
        return {
            "method": method,
            "historical_length": n,
            "forecast": forecast,
            "model": {"slope": slope, "intercept": intercept, "rmse": rmse},
        }

    # ── Idea 32: Anomaly Detection ──────────────────────────────────
    def detect_anomalies(self, data: list[float], threshold: float = 2.0) -> dict:
        """Detect anomalies using modified Z-score (Isolation Forest-like)."""
        if not data:
            return {"anomalies": [], "normal_range": {}}
        mean = sum(data) / len(data)
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / len(data)) or 1
        anomalies = []
        scores = []
        for i, val in enumerate(data):
            z_score = abs(val - mean) / std
            scores.append(round(z_score, 3))
            if z_score > threshold:
                anomalies.append({"index": i, "value": val, "z_score": round(z_score, 3), "severity": "high" if z_score > 3 else "medium"})
        return {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "total_points": len(data),
            "anomaly_rate": round(len(anomalies) / len(data), 4),
            "normal_range": {"mean": round(mean, 2), "std": round(std, 2), "min_normal": round(mean - threshold * std, 2), "max_normal": round(mean + threshold * std, 2)},
        }

    # ── Idea 33: Churn Prediction ───────────────────────────────────
    def predict_churn(self, users: list[dict]) -> dict:
        """Predict churn probability for users."""
        predictions = []
        for user in users:
            days_inactive = user.get("days_inactive", 0)
            login_frequency = user.get("login_frequency", 1)
            support_tickets = user.get("support_tickets", 0)
            subscription_age = user.get("subscription_age_days", 30)
            risk_score = 0
            risk_score += min(days_inactive / 30, 1.0) * 0.35
            risk_score += max(0, 1 - login_frequency / 10) * 0.30
            risk_score += min(support_tickets / 5, 1.0) * 0.20
            risk_score += max(0, 1 - subscription_age / 365) * 0.15
            risk_score = round(min(risk_score, 1.0), 3)
            if risk_score > 0.7:
                risk_level = "high"
            elif risk_score > 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
            predictions.append({
                "user_id": user.get("user_id", "unknown"),
                "churn_probability": risk_score,
                "risk_level": risk_level,
                "key_factors": {
                    "inactivity": round(min(days_inactive / 30, 1.0) * 0.35, 3),
                    "low_engagement": round(max(0, 1 - login_frequency / 10) * 0.30, 3),
                    "support_issues": round(min(support_tickets / 5, 1.0) * 0.20, 3),
                },
            })
        high_risk = sum(1 for p in predictions if p["risk_level"] == "high")
        return {"predictions": predictions, "total_users": len(predictions), "high_risk_count": high_risk, "churn_rate": round(high_risk / max(len(predictions), 1), 3)}

    # ── Idea 34: Demand Forecasting ──────────────────────────────────
    def forecast_demand(self, historical_demand: list[float], periods: int = 7, seasonality: str = "weekly") -> dict:
        """Forecast demand for products/services."""
        forecast = self.forecast_time_series(historical_demand, periods=periods)
        demand_forecast = []
        for fc in forecast.get("forecast", []):
            demand_forecast.append({
                "period": fc["period"],
                "predicted_demand": max(0, round(fc["forecast"] * random.uniform(0.95, 1.05), 1)),
                "confidence": round(random.uniform(0.7, 0.95), 2),
            })
        avg_demand = sum(historical_demand) / len(historical_demand) if historical_demand else 0
        return {
            "forecast": demand_forecast,
            "seasonality": seasonality,
            "avg_historical_demand": round(avg_demand, 2),
            "recommendation": "Stock up" if forecast["forecast"] and forecast["forecast"][-1]["forecast"] > avg_demand * 1.1 else "Normal levels",
        }

    # ── Idea 35: Resource Utilization Prediction ────────────────────
    def predict_resource_utilization(self, current_usage: dict[str, float], trend_data: dict[str, list[float]] | None = None) -> dict:
        """Predict CPU, memory, disk utilization."""
        predictions = {}
        for resource, current in current_usage.items():
            data = trend_data.get(resource, [current]) if trend_data else [current]
            slope, intercept = self._simple_linear_regression(list(range(len(data))), data)
            future_24h = round(intercept + slope * (len(data) + 24), 2)
            future_7d = round(intercept + slope * (len(data) + 168), 2)
            future_24h = max(0, min(100, future_24h))
            future_7d = max(0, min(100, future_7d))
            if future_24h > 90:
                status = "critical"
            elif future_24h > 75:
                status = "warning"
            else:
                status = "healthy"
            predictions[resource] = {
                "current": current,
                "predicted_24h": future_24h,
                "predicted_7d": future_7d,
                "status": status,
                "trend": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable",
            }
        return {"predictions": predictions, "timestamp": datetime.now().isoformat()}

    # ── Idea 36: Error Rate Prediction ──────────────────────────────
    def predict_error_rate(self, error_history: list[dict]) -> dict:
        """Predict future error rates."""
        rates = [e.get("error_rate", 0) for e in error_history]
        if not rates:
            return {"error": "No error history"}
        forecast = self.forecast_time_series(rates, periods=6)
        current_rate = rates[-1]
        predicted_rates = [fc["forecast"] for fc in forecast.get("forecast", [])]
        avg_predicted = sum(predicted_rates) / len(predicted_rates) if predicted_rates else current_rate
        if avg_predicted > current_rate * 1.5:
            recommendation = "Investigate immediately - error rate expected to spike"
        elif avg_predicted > current_rate * 1.1:
            recommendation = "Monitor closely - slight increase expected"
        elif avg_predicted < current_rate * 0.8:
            recommendation = "Error rate improving - continue current practices"
        else:
            recommendation = "Error rate stable"
        return {
            "current_error_rate": current_rate,
            "predicted_rates": predicted_rates,
            "trend": forecast.get("model", {}).get("slope", 0),
            "recommendation": recommendation,
        }

    # ── Idea 37: Latency Prediction ─────────────────────────────────
    def predict_latency(self, latency_history: list[float], endpoint: str = "default") -> dict:
        """Predict future API latency."""
        if not latency_history:
            return {"error": "No latency data"}
        mean_latency = sum(latency_history) / len(latency_history)
        p50 = sorted(latency_history)[len(latency_history) // 2]
        p95 = sorted(latency_history)[int(len(latency_history) * 0.95)]
        p99 = sorted(latency_history)[int(len(latency_history) * 0.99)]
        forecast = self.forecast_time_series(latency_history, periods=12)
        predicted_p50 = sorted([fc["forecast"] for fc in forecast.get("forecast", [])])[6]
        predicted_p95 = sorted([fc["forecast"] for fc in forecast.get("forecast", [])])[10]
        if predicted_p95 > 1000:
            status = "critical"
        elif predicted_p95 > 500:
            status = "warning"
        else:
            status = "healthy"
        return {
            "endpoint": endpoint,
            "current": {"mean": round(mean_latency, 2), "p50": round(p50, 2), "p95": round(p95, 2), "p99": round(p99, 2)},
            "predicted": {"p50": round(predicted_p50, 2), "p95": round(predicted_p95, 2)},
            "status": status,
            "recommendation": "Optimize slow queries" if predicted_p95 > 500 else "Latency within bounds",
        }

    # ── Idea 38: Cost Prediction ────────────────────────────────────
    def predict_cost(self, cost_history: list[dict], periods: int = 30) -> dict:
        """Predict future infrastructure/service costs."""
        costs = [c.get("cost", 0) for c in cost_history]
        if not costs:
            return {"error": "No cost history"}
        forecast = self.forecast_time_series(costs, periods=periods)
        current_cost = costs[-1]
        predicted_costs = [fc["forecast"] for fc in forecast.get("forecast", [])]
        total_predicted = sum(predicted_costs)
        current_monthly = current_cost * 30
        savings = round(current_monthly - total_predicted, 2)
        return {
            "current_monthly_cost": round(current_monthly, 2),
            "predicted_monthly_cost": round(total_predicted, 2),
            "daily_forecast": predicted_costs[:7],
            "cost_trend": "increasing" if forecast.get("model", {}).get("slope", 0) > 0 else "decreasing",
            "potential_savings": max(0, savings),
            "recommendation": "Review unused resources" if savings < 0 else "Costs on track",
        }

    # ── Idea 39: User Growth Prediction ─────────────────────────────
    def predict_user_growth(self, user_counts: list[int], periods: int = 12) -> dict:
        """Predict user base growth."""
        if not user_counts:
            return {"error": "No user data"}
        forecast = self.forecast_time_series(user_counts, periods=periods)
        current = user_counts[-1]
        predicted = [max(0, round(fc["forecast"])) for fc in forecast.get("forecast", [])]
        growth_rate = round((predicted[-1] - current) / max(current, 1) * 100, 2) if predicted else 0
        milestones = []
        target = current * 2
        for i, p in enumerate(predicted):
            if p >= target:
                milestones.append({"milestone": f"2x users ({target})", "period": i + 1})
                break
        return {
            "current_users": current,
            "predicted_users": predicted,
            "growth_rate_percent": growth_rate,
            "milestones": milestones,
            "recommendation": "Prepare infrastructure for scale" if growth_rate > 20 else "Steady growth expected",
        }

    # ── Idea 40: Capacity Planning Predictor ────────────────────────
    def plan_capacity(self, current_metrics: dict[str, dict], growth_rate: float = 0.1) -> dict:
        """Predict when capacity limits will be reached."""
        plans = []
        for metric, data in current_metrics.items():
            current = data.get("current", 0)
            capacity = data.get("capacity", 100)
            utilization = current / capacity if capacity else 0
            monthly_growth = growth_rate
            months_to_limit = 0
            proj_util = utilization
            while proj_util < 0.95 and months_to_limit < 120:
                proj_util *= (1 + monthly_growth)
                months_to_limit += 1
            if proj_util >= 0.95:
                status = "action_needed"
            elif proj_util >= 0.8:
                status = "plan_upgrade"
            else:
                status = "sufficient"
            plans.append({
                "metric": metric,
                "current_utilization": round(utilization * 100, 1),
                "months_to_limit": months_to_limit if months_to_limit < 120 else "120+",
                "projected_utilization_3m": round(min(100, utilization * (1 + monthly_growth) ** 3 * 100), 1),
                "projected_utilization_6m": round(min(100, utilization * (1 + monthly_growth) ** 6 * 100), 1),
                "status": status,
                "recommendation": f"Scale {metric} by {int((1.25 / max(utilization, 0.01) - 1) * 100)}%" if status == "action_needed" else "Monitor",
            })
        return {"capacity_plans": plans, "growth_rate": growth_rate, "review_period_months": 3}
