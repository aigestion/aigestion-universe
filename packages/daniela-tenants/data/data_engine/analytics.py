"""Analytics Engine - Ideas 11-20."""

import math
import statistics
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict


class MetricsAggregator:
    """Idea 11: Real-time Metrics Aggregation"""

    def __init__(self):
        self.metrics: Dict[str, List[dict]] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._window_seconds = 60

    def set_window(self, seconds: int):
        self._window_seconds = seconds

    def increment(self, name: str, value: int = 1):
        self.counters[name] += value
        self._record(name, self.counters[name])

    def gauge(self, name: str, value: float):
        self.gauges[name] = value
        self._record(name, value)

    def histogram(self, name: str, value: float):
        self.histograms[name].append(value)
        self._record(name, value)

    def _record(self, name: str, value: float):
        self.metrics.setdefault(name, []).append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
        })

    def get_counter(self, name: str) -> int:
        return self.counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        return self.gauges.get(name, 0.0)

    def get_histogram(self, name: str) -> dict:
        values = self.histograms.get(name, [])
        if not values:
            return {"count": 0}
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p50": statistics.median(values),
            "p95": self._percentile(values, 0.95),
            "p99": self._percentile(values, 0.99),
        }

    def _percentile(self, data: List[float], p: float) -> float:
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def get_windowed_metrics(self, name: str) -> List[dict]:
        cutoff = datetime.now() - timedelta(seconds=self._window_seconds)
        entries = self.metrics.get(name, [])
        return [e for e in entries if datetime.fromisoformat(e["timestamp"]) >= cutoff]

    def get_all(self) -> dict:
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {k: self.get_histogram(k) for k in self.histograms},
        }


class CohortAnalysis:
    """Idea 12: Cohort Analysis"""

    def __init__(self):
        self.data: List[dict] = []
        self.cohort_key: str = "cohort"
        self.period_key: str = "period"
        self.value_key: str = "value"

    def set_keys(self, cohort: str = "cohort", period: str = "period", value: str = "value"):
        self.cohort_key = cohort
        self.period_key = period
        self.value_key = value
        return self

    def add_data(self, records: List[dict]):
        self.data.extend(records)
        return self

    def analyze(self) -> dict:
        cohorts = defaultdict(lambda: defaultdict(list))
        for record in self.data:
            cohort = record.get(self.cohort_key)
            period = record.get(self.period_key)
            value = record.get(self.value_key, 0)
            cohorts[cohort][period].append(value)

        result = {}
        for cohort, periods in sorted(cohorts.items()):
            sorted_periods = sorted(periods.keys())
            cohort_data = []
            initial_values = periods.get(sorted_periods[0], [0]) if sorted_periods else [0]
            initial_avg = statistics.mean(initial_values) if initial_values else 0

            for period in sorted_periods:
                values = periods[period]
                avg = statistics.mean(values) if values else 0
                retention = (avg / initial_avg * 100) if initial_avg > 0 else 0
                cohort_data.append({
                    "period": period,
                    "count": len(values),
                    "avg_value": round(avg, 2),
                    "retention_pct": round(retention, 2),
                })
            result[cohort] = cohort_data

        return {"cohorts": result, "total_cohorts": len(result)}


class FunnelAnalysis:
    """Idea 13: Funnel Analysis"""

    def __init__(self):
        self.steps: List[str] = []
        self.data: Dict[str, int] = {}

    def add_step(self, name: str, count: int):
        self.steps.append(name)
        self.data[name] = count
        return self

    def from_user_events(self, events: List[dict], step_field: str):
        counts = defaultdict(int)
        for event in events:
            step = event.get(step_field)
            if step:
                counts[step] += 1
        self.steps = list(counts.keys())
        self.data = dict(counts)
        return self

    def analyze(self) -> dict:
        if not self.steps:
            return {"steps": [], "total_conversion": 0}

        result_steps = []
        first_count = self.data.get(self.steps[0], 0)

        for i, step in enumerate(self.steps):
            count = self.data.get(step, 0)
            step_conversion = (count / first_count * 100) if first_count > 0 else 0
            drop_off = 0
            if i > 0:
                prev_count = self.data.get(self.steps[i - 1], 0)
                drop_off = ((prev_count - count) / prev_count * 100) if prev_count > 0 else 0

            result_steps.append({
                "step": step,
                "count": count,
                "conversion_from_start": round(step_conversion, 2),
                "drop_off_pct": round(drop_off, 2),
            })

        last_count = self.data.get(self.steps[-1], 0)
        total_conversion = (last_count / first_count * 100) if first_count > 0 else 0

        return {
            "steps": result_steps,
            "total_conversion": round(total_conversion, 2),
            "total_steps": len(self.steps),
        }


class RetentionAnalysis:
    """Idea 14: Retention Analysis"""

    def __init__(self):
        self.user_activities: Dict[str, List[datetime]] = {}
        self.cohort_date_key = "cohort_date"
        self.activity_date_key = "activity_date"

    def add_user_activity(self, user_id: str, dates: List[str]):
        self.user_activities[user_id] = [datetime.fromisoformat(d) for d in dates]

    def from_records(self, records: List[dict], user_key: str, date_key: str):
        users = defaultdict(list)
        for record in records:
            uid = record.get(user_key)
            dt = record.get(date_key)
            if uid and dt:
                users[uid].append(datetime.fromisoformat(str(dt)))
        self.user_activities = dict(users)
        return self

    def calculate_retention(self, period_days: int = 30, num_periods: int = 12) -> dict:
        if not self.user_activities:
            return {"periods": [], "retention": []}

        all_dates = []
        for dates in self.user_activities.values():
            all_dates.extend(dates)

        start_date = min(all_dates)
        periods = []

        for p in range(num_periods):
            period_start = start_date + timedelta(days=p * period_days)
            period_end = period_start + timedelta(days=period_days)

            cohort_users = set()
            retained_users = set()

            for user_id, dates in self.user_activities.items():
                if any(period_start <= d < period_end for d in dates):
                    cohort_users.add(user_id)
                if any(period_end <= d for d in dates):
                    retained_users.add(user_id)

            cohort_size = len(cohort_users)
            retained_count = len(cohort_users & retained_users)
            retention_rate = (retained_count / cohort_size * 100) if cohort_size > 0 else 0

            periods.append({
                "period": p,
                "start": period_start.isoformat(),
                "cohort_size": cohort_size,
                "retained": retained_count,
                "retention_rate": round(retention_rate, 2),
            })

        return {"periods": periods, "period_days": period_days}


class ABTestAnalytics:
    """Idea 15: A/B Test Analytics"""

    def __init__(self):
        self.experiments: Dict[str, dict] = {}

    def create_experiment(self, name: str, variants: List[str]):
        self.experiments[name] = {
            "variants": {v: {"conversions": 0, "total": 0, "values": []} for v in variants},
            "created_at": datetime.now().isoformat(),
        }
        return self

    def record_event(self, experiment: str, variant: str, converted: bool, value: float = 0):
        if experiment not in self.experiments:
            raise ValueError(f"Experiment {experiment} not found")
        v = self.experiments[experiment]["variants"][variant]
        v["total"] += 1
        if converted:
            v["conversions"] += 1
        v["values"].append(value)

    def analyze(self, experiment: str) -> dict:
        exp = self.experiments.get(experiment)
        if not exp:
            return {"error": "Experiment not found"}

        results = {}
        for variant_name, data in exp["variants"].items():
            conversion_rate = (data["conversions"] / data["total"] * 100) if data["total"] > 0 else 0
            avg_value = statistics.mean(data["values"]) if data["values"] else 0
            results[variant_name] = {
                "total": data["total"],
                "conversions": data["conversions"],
                "conversion_rate": round(conversion_rate, 2),
                "avg_value": round(avg_value, 4),
            }

        variants = list(results.keys())
        if len(variants) >= 2:
            rate_a = results[variants[0]]["conversion_rate"]
            rate_b = results[variants[1]]["conversion_rate"]
            lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0
            results["lift"] = round(lift, 2)
            results["winner"] = variants[1] if rate_b > rate_a else variants[0]

        return {"experiment": experiment, "results": results, "created_at": exp["created_at"]}


class StatisticalSignificanceCalculator:
    """Idea 16: Statistical Significance Calculator"""

    @staticmethod
    def z_score(p1: float, p2: float, n1: int, n2: int) -> float:
        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        if se == 0:
            return 0
        return (p2 - p1) / se

    @staticmethod
    def p_value_from_z(z: float) -> float:
        return 0.5 * math.erfc(-z / math.sqrt(2))

    @staticmethod
    def is_significant(p1: float, p2: float, n1: int, n2: int, alpha: float = 0.05) -> dict:
        z = StatisticalSignificanceCalculator.z_score(p1, p2, n1, n2)
        p = StatisticalSignificanceCalculator.p_value_from_z(abs(z))
        return {
            "z_score": round(z, 4),
            "p_value": round(p, 6),
            "significant": p < alpha,
            "alpha": alpha,
            "confidence": round((1 - p) * 100, 2),
        }

    @staticmethod
    def confidence_interval(proportion: float, n: int, confidence: float = 0.95) -> dict:
        z_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_map.get(confidence, 1.96)
        se = math.sqrt(proportion * (1 - proportion) / n)
        margin = z * se
        return {
            "lower": round(proportion - margin, 4),
            "upper": round(proportion + margin, 4),
            "margin_of_error": round(margin, 4),
            "confidence": confidence,
        }

    @staticmethod
    def required_sample_size(baseline_rate: float, mde: float, alpha: float = 0.05, power: float = 0.8) -> int:
        z_alpha = 1.96
        z_beta = 0.84
        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)
        p_avg = (p1 + p2) / 2
        n = ((z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (mde * p1) ** 2
        return math.ceil(n)


class PercentileCalculator:
    """Idea 17: Percentile Calculations"""

    @staticmethod
    def percentile(data: List[float], p: float) -> float:
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (p / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = lower + 1
        if upper >= len(sorted_data):
            return sorted_data[-1]
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

    @staticmethod
    def quartiles(data: List[float]) -> dict:
        return {
            "q1": PercentileCalculator.percentile(data, 25),
            "q2": PercentileCalculator.percentile(data, 50),
            "q3": PercentileCalculator.percentile(data, 75),
            "iqr": PercentileCalculator.percentile(data, 75) - PercentileCalculator.percentile(data, 25),
        }

    @staticmethod
    def deciles(data: List[float]) -> List[float]:
        return [PercentileCalculator.percentile(data, d * 10) for d in range(1, 10)]

    @staticmethod
    def summary(data: List[float]) -> dict:
        if not data:
            return {"count": 0}
        return {
            "count": len(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
            **PercentileCalculator.quartiles(data),
            "p90": PercentileCalculator.percentile(data, 90),
            "p95": PercentileCalculator.percentile(data, 95),
            "p99": PercentileCalculator.percentile(data, 99),
        }


class MovingAverageCalculator:
    """Idea 18: Moving Averages (Simple, Exponential)"""

    @staticmethod
    def simple(data: List[float], window: int) -> List[float]:
        result = []
        for i in range(len(data)):
            if i < window - 1:
                result.append(None)
            else:
                window_data = data[i - window + 1: i + 1]
                result.append(statistics.mean(window_data))
        return result

    @staticmethod
    def exponential(data: List[float], span: int, adjust: bool = True) -> List[float]:
        alpha = 2 / (span + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            val = alpha * data[i] + (1 - alpha) * result[-1]
            result.append(val)
        if adjust:
            adjustment = []
            weight = 1.0
            for i in range(len(data)):
                adjustment.append(weight)
                weight *= (1 - alpha)
            adj_result = []
            for i in range(len(data)):
                adj_result.append(result[i] / adjustment[i])
            return adj_result
        return result

    @staticmethod
    def weighted(data: List[float], weights: List[float]) -> float:
        if len(data) != len(weights):
            raise ValueError("Data and weights must have same length")
        total_weight = sum(weights)
        return sum(d * w for d, w in zip(data, weights)) / total_weight

    @staticmethod
    def centered(data: List[float], window: int) -> List[float]:
        result = []
        half = window // 2
        for i in range(len(data)):
            start = max(0, i - half)
            end = min(len(data), i + half + 1)
            result.append(statistics.mean(data[start:end]))
        return result


class CorrelationAnalysis:
    """Idea 19: Correlation Analysis"""

    @staticmethod
    def pearson(x: List[float], y: List[float]) -> float:
        n = len(x)
        if n != len(y) or n < 2:
            return 0
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        den_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        if den_x == 0 or den_y == 0:
            return 0
        return num / (den_x * den_y)

    @staticmethod
    def spearman(x: List[float], y: List[float]) -> float:
        def rank(data):
            sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
            ranks = [0] * len(data)
            for rank_val, idx in enumerate(sorted_indices, 1):
                ranks[idx] = rank_val
            return ranks

        rank_x = rank(x)
        rank_y = rank(y)
        return CorrelationAnalysis.pearson(rank_x, rank_y)

    @staticmethod
    def interpret(r: float) -> str:
        abs_r = abs(r)
        if abs_r < 0.1:
            return "negligible"
        elif abs_r < 0.3:
            return "weak"
        elif abs_r < 0.5:
            return "moderate"
        elif abs_r < 0.7:
            return "strong"
        else:
            return "very strong"

    @staticmethod
    def correlation_matrix(data: Dict[str, List[float]]) -> dict:
        keys = list(data.keys())
        matrix = {}
        for k1 in keys:
            matrix[k1] = {}
            for k2 in keys:
                r = CorrelationAnalysis.pearson(data[k1], data[k2])
                matrix[k1][k2] = round(r, 4)
        return {"variables": keys, "matrix": matrix}


class RegressionAnalysis:
    """Idea 20: Regression Analysis"""

    @staticmethod
    def linear(x: List[float], y: List[float]) -> dict:
        n = len(x)
        if n != len(y) or n < 2:
            return {"error": "Insufficient data"}

        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den = sum((xi - mean_x) ** 2 for xi in x)

        if den == 0:
            return {"slope": 0, "intercept": mean_y, "r_squared": 0}

        slope = num / den
        intercept = mean_y - slope * mean_x

        ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "slope": round(slope, 6),
            "intercept": round(intercept, 6),
            "r_squared": round(r_squared, 6),
            "equation": f"y = {slope:.4f}x + {intercept:.4f}",
        }

    @staticmethod
    def predict(x_val: float, slope: float, intercept: float) -> float:
        return slope * x_val + intercept

    @staticmethod
    def multiple_linear(X: List[List[float]], y: List[float]) -> dict:
        n = len(y)
        p = len(X[0]) if X else 0
        if n < p + 1:
            return {"error": "Insufficient data"}

        means = [statistics.mean(col) for col in zip(*X)]
        y_mean = statistics.mean(y)

        XtX = [[0.0] * p for _ in range(p)]
        Xty = [0.0] * p
        for i in range(p):
            for j in range(p):
                XtX[i][j] = sum((X[k][i] - means[i]) * (X[k][j] - means[j]) for k in range(n))
            Xty[i] = sum((X[k][i] - means[i]) * (y[k] - y_mean) for k in range(n))

        try:
            inv_XtX = RegressionAnalysis._invert_matrix(XtX)
            coefficients = [sum(inv_XtX[i][j] * Xty[j] for j in range(p)) for i in range(p)]
            intercept = y_mean - sum(coefficients[i] * means[i] for i in range(p))

            y_pred = [intercept + sum(coefficients[i] * X[k][i] for i in range(p)) for k in range(n)]
            ss_res = sum((y[k] - y_pred[k]) ** 2 for k in range(n))
            ss_tot = sum((y[k] - y_mean) ** 2 for k in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {
                "coefficients": [round(c, 6) for c in coefficients],
                "intercept": round(intercept, 6),
                "r_squared": round(r_squared, 6),
            }
        except Exception:
            return {"error": "Matrix inversion failed"}

    @staticmethod
    def _invert_matrix(matrix: List[List[float]]) -> List[List[float]]:
        n = len(matrix)
        augmented = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]

        for i in range(n):
            max_row = max(range(i, n), key=lambda r: abs(augmented[r][i]))
            augmented[i], augmented[max_row] = augmented[max_row], augmented[i]

            pivot = augmented[i][i]
            if abs(pivot) < 1e-12:
                raise ValueError("Matrix is singular")

            for j in range(2 * n):
                augmented[i][j] /= pivot

            for j in range(n):
                if i != j:
                    factor = augmented[j][i]
                    for k in range(2 * n):
                        augmented[j][k] -= factor * augmented[i][k]

        return [row[n:] for row in augmented]
