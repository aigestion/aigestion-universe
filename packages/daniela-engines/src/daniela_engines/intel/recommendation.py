"""
Recommendation Engine - Ideas 21-30
====================================

21. Collaborative filtering
22. Content-based filtering
23. Hybrid recommendation
24. Trending items detector
25. User preference learning
26. A/B testing framework for recommendations
27. Cold-start problem solver
28. Multi-armed bandit for recommendations
29. Diversity-aware recommendations
30. Context-aware recommendations (time, location)
"""

import hashlib
import math
import random
from collections import defaultdict


class RecommendationEngine:
    """Core recommendation engine with 10 powerful recommendation strategies."""

    ITEM_CATALOG = {
        "item_1": {"name": "Python Cookbook", "category": "books", "tags": ["python", "programming", "cookbook"]},
        "item_2": {"name": "Deep Learning", "category": "books", "tags": ["ai", "deep-learning", "neural-networks"]},
        "item_3": {"name": "Data Science Handbook", "category": "books", "tags": ["data-science", "statistics", "python"]},
        "item_4": {"name": "ML Framework X", "category": "software", "tags": ["machine-learning", "framework", "gpu"]},
        "item_5": {"name": "Cloud IDE Pro", "category": "software", "tags": ["ide", "cloud", "development"]},
        "item_6": {"name": "API Gateway Service", "category": "service", "tags": ["api", "gateway", "microservices"]},
        "item_7": {"name": "Monitoring Dashboard", "category": "software", "tags": ["monitoring", "dashboard", "metrics"]},
        "item_8": {"name": "Security Scanner", "category": "software", "tags": ["security", "vulnerability", "scanning"]},
        "item_9": {"name": "Container Orchestrator", "category": "software", "tags": ["docker", "kubernetes", "containers"]},
        "item_10": {"name": "CI/CD Pipeline", "category": "service", "tags": ["ci", "cd", "pipeline", "automation"]},
        "item_11": {"name": "NLP Toolkit", "category": "software", "tags": ["nlp", "text", "language"]},
        "item_12": {"name": "Computer Vision SDK", "category": "software", "tags": ["vision", "image", "detection"]},
    }

    def __init__(self):
        self.user_interactions: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.user_profiles: dict[str, dict] = {}
        self.ab_experiments: dict[str, dict] = {}
        self.bandit_arms: dict[str, dict] = {}

    def _cosine_sim(self, vec1: dict[str, float], vec2: dict[str, float]) -> float:
        common = set(vec1.keys()) & set(vec2.keys())
        if not common:
            return 0.0
        dot = sum(vec1[k] * vec2[k] for k in common)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values())) or 1
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values())) or 1
        return round(dot / (mag1 * mag2), 4)

    # ── Idea 21: Collaborative Filtering ────────────────────────────
    def collaborative_filter(self, user_id: str, top_k: int = 5) -> dict:
        """Recommend items based on similar users' preferences."""
        if user_id not in self.user_interactions:
            return {"user_id": user_id, "recommendations": [], "method": "collaborative", "note": "No interaction history"}
        user_ratings = dict(self.user_interactions[user_id])
        similarities = []
        for other_id, other_ratings in self.user_interactions.items():
            if other_id == user_id:
                continue
            sim = self._cosine_sim(user_ratings, other_ratings)
            if sim > 0:
                similarities.append((other_id, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        scores = defaultdict(float)
        for other_id, sim in similarities[:10]:
            for item_id, rating in self.user_interactions[other_id].items():
                if item_id not in user_ratings:
                    scores[item_id] += sim * rating
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        recs = []
        for item_id, score in ranked:
            item = self.ITEM_CATALOG.get(item_id, {})
            recs.append({"item_id": item_id, "name": item.get("name", item_id), "score": round(score, 4)})
        return {"user_id": user_id, "recommendations": recs, "method": "collaborative", "similar_users": len(similarities)}

    # ── Idea 22: Content-Based Filtering ────────────────────────────
    def content_based_filter(self, user_id: str, top_k: int = 5) -> dict:
        """Recommend items similar to user's past preferences."""
        if user_id not in self.user_interactions:
            return {"user_id": user_id, "recommendations": [], "method": "content-based", "note": "No interaction history"}
        liked = [item_id for item_id, rating in self.user_interactions[user_id].items() if rating > 0.5]
        if not liked:
            return {"user_id": user_id, "recommendations": [], "method": "content-based", "note": "No liked items"}
        user_tags = defaultdict(float)
        for item_id in liked:
            item = self.ITEM_CATALOG.get(item_id, {})
            for tag in item.get("tags", []):
                user_tags[tag] += 1
        scores = {}
        for item_id, item in self.ITEM_CATALOG.items():
            if item_id in self.user_interactions[user_id]:
                continue
            item_tags = dict.fromkeys(item.get("tags", []), 1.0)
            scores[item_id] = self._cosine_sim(dict(user_tags), item_tags)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        recs = [{"item_id": iid, "name": self.ITEM_CATALOG[iid]["name"], "score": sc} for iid, sc in ranked]
        return {"user_id": user_id, "recommendations": recs, "method": "content-based", "user_tags": dict(user_tags)}

    # ── Idea 23: Hybrid Recommendation ──────────────────────────────
    def hybrid_recommend(self, user_id: str, top_k: int = 5, collab_weight: float = 0.6) -> dict:
        """Combine collaborative and content-based filtering."""
        collab = self.collaborative_filter(user_id, top_k=top_k * 2)
        content = self.content_based_filter(user_id, top_k=top_k * 2)
        scores = defaultdict(float)
        for rec in collab.get("recommendations", []):
            scores[rec["item_id"]] += collab_weight * rec["score"]
        content_weight = 1.0 - collab_weight
        for rec in content.get("recommendations", []):
            scores[rec["item_id"]] += content_weight * rec["score"]
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        recs = [{"item_id": iid, "name": self.ITEM_CATALOG.get(iid, {}).get("name", iid), "score": round(sc, 4)} for iid, sc in ranked]
        return {
            "user_id": user_id,
            "recommendations": recs,
            "method": "hybrid",
            "weights": {"collaborative": collab_weight, "content": content_weight},
        }

    # ── Idea 24: Trending Items Detector ────────────────────────────
    def detect_trending(self, time_window_hours: int = 24, top_k: int = 5) -> dict:
        """Detect items trending in recent interactions."""
        all_items = defaultdict(lambda: {"count": 0, "total_rating": 0})
        for _user_id, interactions in self.user_interactions.items():
            for item_id, rating in interactions.items():
                all_items[item_id]["count"] += 1
                all_items[item_id]["total_rating"] += rating
        trending = []
        for item_id, data in all_items.items():
            avg_rating = data["total_rating"] / data["count"]
            trend_score = round(data["count"] * avg_rating, 4)
            item = self.ITEM_CATALOG.get(item_id, {})
            trending.append({
                "item_id": item_id,
                "name": item.get("name", item_id),
                "interactions": data["count"],
                "avg_rating": round(avg_rating, 3),
                "trend_score": trend_score,
            })
        trending.sort(key=lambda x: x["trend_score"], reverse=True)
        return {"trending": trending[:top_k], "total_items": len(all_items), "time_window_hours": time_window_hours}

    # ── Idea 25: User Preference Learning ───────────────────────────
    def learn_preferences(self, user_id: str, feedback: list[dict]) -> dict:
        """Learn and update user preferences from feedback."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {"tags": defaultdict(float), "categories": defaultdict(float), "total_feedback": 0}
        profile = self.user_profiles[user_id]
        for fb in feedback:
            item_id = fb.get("item_id")
            rating = fb.get("rating", 0.5)
            action = fb.get("action", "rate")
            multiplier = {"like": 1.0, "dislike": -0.5, "click": 0.3, "purchase": 1.5, "rate": rating}.get(action, rating)
            item = self.ITEM_CATALOG.get(item_id, {})
            for tag in item.get("tags", []):
                profile["tags"][tag] += multiplier
            cat = item.get("category", "unknown")
            profile["categories"][cat] += multiplier
            self.user_interactions[user_id][item_id] = max(0, min(1, rating))
            profile["total_feedback"] += 1
        top_tags = sorted(profile["tags"].items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            "user_id": user_id,
            "profile_size": profile["total_feedback"],
            "top_tags": dict(top_tags),
            "top_categories": dict(sorted(profile["categories"].items(), key=lambda x: x[1], reverse=True)[:5]),
        }

    # ── Idea 26: A/B Testing Framework ──────────────────────────────
    def create_ab_test(self, experiment_id: str, variants: list[str], traffic_split: list[float] | None = None) -> dict:
        """Create an A/B testing experiment for recommendations."""
        if traffic_split is None:
            traffic_split = [1.0 / len(variants)] * len(variants)
        self.ab_experiments[experiment_id] = {
            "variants": variants,
            "traffic_split": traffic_split,
            "results": {v: {"impressions": 0, "clicks": 0, "conversions": 0} for v in variants},
            "status": "active",
        }
        return {"experiment_id": experiment_id, "variants": variants, "traffic_split": traffic_split, "status": "active"}

    def assign_variant(self, experiment_id: str, user_id: str) -> dict:
        """Assign a user to an A/B test variant."""
        exp = self.ab_experiments.get(experiment_id)
        if not exp:
            return {"error": "Experiment not found"}
        h = int(hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16) % 1000 / 1000
        cumulative = 0
        assigned = exp["variants"][0]
        for v, split in zip(exp["variants"], exp["traffic_split"]):
            cumulative += split
            if h < cumulative:
                assigned = v
                break
        return {"experiment_id": experiment_id, "user_id": user_id, "variant": assigned}

    def log_ab_event(self, experiment_id: str, variant: str, event: str) -> dict:
        """Log an event (click, conversion) for an A/B test."""
        exp = self.ab_experiments.get(experiment_id)
        if not exp or variant not in exp["results"]:
            return {"error": "Invalid experiment or variant"}
        if event in exp["results"][variant]:
            exp["results"][variant][event] += 1
        return {"experiment_id": experiment_id, "variant": variant, "event": event, "results": exp["results"][variant]}

    # ── Idea 27: Cold-Start Problem Solver ──────────────────────────
    def solve_cold_start(self, user_id: str, onboarding_answers: dict | None = None) -> dict:
        """Handle new users with no interaction history."""
        if user_id in self.user_interactions and len(self.user_interactions[user_id]) > 0:
            return {"user_id": user_id, "method": "existing_user", "recommendations": self.hybrid_recommend(user_id, top_k=5)["recommendations"]}
        if onboarding_answers:
            self.learn_preferences(user_id, [{"item_id": f"item_{i + 1}", "rating": v, "action": "rate"} for i, v in enumerate(onboarding_answers.get("ratings", []))])
            return {"user_id": user_id, "method": "onboarding", "recommendations": self.content_based_filter(user_id, top_k=5)["recommendations"]}
        popular = self.detect_trending(top_k=5)["trending"]
        return {"user_id": user_id, "method": "popular_fallback", "recommendations": popular}

    # ── Idea 28: Multi-Armed Bandit ─────────────────────────────────
    def bandit_recommend(self, user_id: str, top_k: int = 5, exploration_rate: float = 0.2) -> dict:
        """Use epsilon-greedy multi-armed bandit for recommendations."""
        if user_id not in self.bandit_arms:
            items = list(self.ITEM_CATALOG.keys())[:10]
            self.bandit_arms[user_id] = {item: {"pulls": 0, "total_reward": 0.0, "avg_reward": 0.5} for item in items}
        arms = self.bandit_arms[user_id]
        if random.random() < exploration_rate:
            selected = random.sample(list(arms.keys()), min(top_k, len(arms)))
            strategy = "explore"
        else:
            ranked = sorted(arms.items(), key=lambda x: x[1]["avg_reward"], reverse=True)
            selected = [item for item, _ in ranked[:top_k]]
            strategy = "exploit"
        recs = []
        for item_id in selected:
            arms[item_id]["pulls"] += 1
            reward = random.uniform(0.3, 1.0)
            arms[item_id]["total_reward"] += reward
            arms[item_id]["avg_reward"] = round(arms[item_id]["total_reward"] / arms[item_id]["pulls"], 4)
            item = self.ITEM_CATALOG.get(item_id, {})
            recs.append({"item_id": item_id, "name": item.get("name", item_id), "avg_reward": arms[item_id]["avg_reward"]})
        return {"user_id": user_id, "recommendations": recs, "strategy": strategy, "exploration_rate": exploration_rate}

    # ── Idea 29: Diversity-Aware Recommendations ────────────────────
    def diverse_recommend(self, user_id: str, top_k: int = 5, diversity_weight: float = 0.3) -> dict:
        """Ensure recommendations span multiple categories."""
        base = self.hybrid_recommend(user_id, top_k=top_k * 3)
        candidates = base.get("recommendations", [])
        if not candidates:
            return base
        selected = []
        seen_categories = set()
        for rec in candidates:
            item = self.ITEM_CATALOG.get(rec["item_id"], {})
            cat = item.get("category", "unknown")
            diversity_bonus = diversity_weight if cat not in seen_categories else 0
            rec["diversified_score"] = round(rec["score"] + diversity_bonus, 4)
            selected.append(rec)
            seen_categories.add(cat)
            if len(selected) >= top_k:
                break
        selected.sort(key=lambda x: x["diversified_score"], reverse=True)
        return {"user_id": user_id, "recommendations": selected[:top_k], "method": "diversity-aware", "categories_covered": list(seen_categories)}

    # ── Idea 30: Context-Aware Recommendations ──────────────────────
    def context_aware_recommend(self, user_id: str, context: dict | None = None, top_k: int = 5) -> dict:
        """Recommend based on time, location, and other context."""
        if context is None:
            context = {}
        time_of_day = context.get("time_of_day", "day")
        day_type = context.get("day_type", "weekday")
        mood = context.get("mood", "neutral")
        base = self.hybrid_recommend(user_id, top_k=top_k * 2)
        recs = base.get("recommendations", [])
        boosted = []
        for rec in recs:
            item = self.ITEM_CATALOG.get(rec["item_id"], {})
            tags = set(item.get("tags", []))
            context_boost = 0
            if time_of_day == "evening" and ("reading" in tags or "books" in item.get("category", "")):
                context_boost += 0.1
            if day_type == "weekend" and ("entertainment" in tags or "fun" in tags):
                context_boost += 0.1
            if mood == "focused" and ("programming" in tags or "data-science" in tags):
                context_boost += 0.1
            if mood == "curious" and ("ai" in tags or "machine-learning" in tags):
                context_boost += 0.1
            rec["context_score"] = round(rec["score"] + context_boost, 4)
            boosted.append(rec)
        boosted.sort(key=lambda x: x["context_score"], reverse=True)
        return {
            "user_id": user_id,
            "recommendations": boosted[:top_k],
            "method": "context-aware",
            "context": context,
        }
