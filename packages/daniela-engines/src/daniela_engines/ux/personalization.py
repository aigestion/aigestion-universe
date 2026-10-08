"""Personalization: 11-20."""

from typing import Any


class UserPreferenceLearning:
    """11. User preference learning."""

    def __init__(self):
        self._preferences: dict[str, dict[str, Any]] = {}
        self._interactions: dict[str, list[dict]] = {}

    def record_interaction(self, user_id: str, action: str, context: dict):
        if user_id not in self._interactions:
            self._interactions[user_id] = []
        self._interactions[user_id].append({"action": action, **context})

    def get_preferences(self, user_id: str) -> dict:
        return self._preferences.get(user_id, {})

    def set_preference(self, user_id: str, key: str, value: Any):
        if user_id not in self._preferences:
            self._preferences[user_id] = {}
        self._preferences[user_id][key] = value

    def get_top_actions(self, user_id: str, limit: int = 5) -> list[str]:
        interactions = self._interactions.get(user_id, [])
        counts: dict[str, int] = {}
        for i in interactions:
            counts[i["action"]] = counts.get(i["action"], 0) + 1
        sorted_actions = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [a[0] for a in sorted_actions[:limit]]


class LayoutPersonalization:
    """12. Layout personalization (drag & drop)."""

    def __init__(self):
        self._layouts: dict[str, list[dict]] = {}

    def save_layout(self, user_id: str, widgets: list[dict]):
        self._layouts[user_id] = sorted(widgets, key=lambda w: w.get("order", 0))

    def get_layout(self, user_id: str) -> list[dict]:
        return self._layouts.get(user_id, [])

    def move_widget(self, user_id: str, widget_id: str, new_order: int):
        layout = self._layouts.get(user_id, [])
        for w in layout:
            if w["id"] == widget_id:
                w["order"] = new_order
        self._layouts[user_id] = sorted(layout, key=lambda w: w.get("order", 0))

    def remove_widget(self, user_id: str, widget_id: str):
        if user_id in self._layouts:
            self._layouts[user_id] = [w for w in self._layouts[user_id] if w["id"] != widget_id]


class QuickActions:
    """13. Quick actions (personalized shortcuts)."""

    def __init__(self):
        self._shortcuts: dict[str, list[dict]] = {}
        self._usage: dict[str, dict[str, int]] = {}

    def add_shortcut(self, user_id: str, action: dict):
        if user_id not in self._shortcuts:
            self._shortcuts[user_id] = []
        self._shortcuts[user_id].append(action)

    def remove_shortcut(self, user_id: str, action_id: str):
        if user_id in self._shortcuts:
            self._shortcuts[user_id] = [a for a in self._shortcuts[user_id] if a.get("id") != action_id]

    def record_usage(self, user_id: str, action_id: str):
        if user_id not in self._usage:
            self._usage[user_id] = {}
        self._usage[user_id][action_id] = self._usage[user_id].get(action_id, 0) + 1

    def get_suggested(self, user_id: str, limit: int = 5) -> list[str]:
        usage = self._usage.get(user_id, {})
        sorted_usage = sorted(usage.items(), key=lambda x: x[1], reverse=True)
        return [a[0] for a in sorted_usage[:limit]]


class SmartNotifications:
    """14. Smart notifications (priority-based)."""

    PRIORITY_LEVELS = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

    def __init__(self):
        self._queues: dict[str, list[dict]] = {}
        self._settings: dict[str, dict] = {}

    def configure(self, user_id: str, settings: dict):
        self._settings[user_id] = settings

    def add_notification(self, user_id: str, notification: dict):
        if user_id not in self._queues:
            self._queues[user_id] = []
        notification["priority"] = self.PRIORITY_LEVELS.get(notification.get("level", "medium"), 2)
        self._queues[user_id].append(notification)
        self._queues[user_id].sort(key=lambda n: n["priority"], reverse=True)

    def get_notifications(self, user_id: str, limit: int = 10) -> list[dict]:
        return self._queues.get(user_id, [])[:limit]

    def dismiss(self, user_id: str, notification_id: str):
        if user_id in self._queues:
            self._queues[user_id] = [n for n in self._queues[user_id] if n.get("id") != notification_id]

    def clear_all(self, user_id: str):
        self._queues.pop(user_id, None)


class ContentRecommendations:
    """15. Content recommendations (dashboard widgets)."""

    def __init__(self):
        self._history: dict[str, list[str]] = {}
        self._widgets: dict[str, dict] = {}

    def register_widget(self, widget_id: str, metadata: dict):
        self._widgets[widget_id] = metadata

    def record_view(self, user_id: str, widget_id: str):
        if user_id not in self._history:
            self._history[user_id] = []
        self._history[user_id].append(widget_id)

    def recommend(self, user_id: str, limit: int = 5) -> list[str]:
        history = self._history.get(user_id, [])
        counts: dict[str, int] = {}
        for w in history:
            counts[w] = counts.get(w, 0) + 1
        sorted_widgets = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_widgets[:limit]]


class SearchPersonalization:
    """16. Search personalization."""

    def __init__(self):
        self._history: dict[str, list[str]] = {}
        self._saved: dict[str, list[dict]] = {}

    def record_search(self, user_id: str, query: str):
        if user_id not in self._history:
            self._history[user_id] = []
        self._history[user_id].append(query)

    def get_recent(self, user_id: str, limit: int = 10) -> list[str]:
        history = self._history.get(user_id, [])
        return list(reversed(history[-limit:]))

    def save_search(self, user_id: str, search: dict):
        if user_id not in self._saved:
            self._saved[user_id] = []
        self._saved[user_id].append(search)

    def get_saved(self, user_id: str) -> list[dict]:
        return self._saved.get(user_id, [])


class WelcomeWizard:
    """17. Welcome wizard (first-time user)."""

    def __init__(self):
        self._completed: set[str] = set()
        self._steps = ["welcome", "profile", "preferences", "tour", "finish"]

    def is_first_time(self, user_id: str) -> bool:
        return user_id not in self._completed

    def get_current_step(self, user_id: str, current: int = 0) -> str:
        return self._steps[min(current, len(self._steps) - 1)]

    def get_total_steps(self) -> int:
        return len(self._steps)

    def complete(self, user_id: str):
        self._completed.add(user_id)

    def get_all_steps(self) -> list[str]:
        return list(self._steps)


class ProgressTracker:
    """18. Progress tracker (onboarding)."""

    def __init__(self):
        self._progress: dict[str, dict] = {}

    def start(self, user_id: str, checklist: list[str]):
        self._progress[user_id] = dict.fromkeys(checklist, False)

    def complete_item(self, user_id: str, item: str):
        if user_id in self._progress and item in self._progress[user_id]:
            self._progress[user_id][item] = True

    def get_progress(self, user_id: str) -> dict:
        return self._progress.get(user_id, {})

    def get_percentage(self, user_id: str) -> float:
        items = self._progress.get(user_id, {})
        if not items:
            return 0.0
        done = sum(1 for v in items.values() if v)
        return (done / len(items)) * 100

    def is_complete(self, user_id: str) -> bool:
        items = self._progress.get(user_id, {})
        return bool(items) and all(items.values())


class AchievementSystem:
    """19. Achievement system (gamification)."""

    def __init__(self):
        self._achievements: dict[str, dict] = {}
        self._user_badges: dict[str, set[str]] = {}
        self._points: dict[str, int] = {}

    def define_achievement(self, ach_id: str, name: str, points: int, description: str = ""):
        self._achievements[ach_id] = {"name": name, "points": points, "description": description}

    def award(self, user_id: str, ach_id: str) -> bool:
        if ach_id not in self._achievements:
            return False
        if user_id not in self._user_badges:
            self._user_badges[user_id] = set()
        if ach_id in self._user_badges[user_id]:
            return False
        self._user_badges[user_id].add(ach_id)
        self._points[user_id] = self._points.get(user_id, 0) + self._achievements[ach_id]["points"]
        return True

    def get_badges(self, user_id: str) -> list[str]:
        return list(self._user_badges.get(user_id, set()))

    def get_points(self, user_id: str) -> int:
        return self._points.get(user_id, 0)

    def get_all_achievements(self) -> list[dict]:
        return [{"id": k, **v} for k, v in self._achievements.items()]


class PersonalizedDashboard:
    """20. Personalized analytics dashboard."""

    def __init__(self):
        self._dashboards: dict[str, dict] = {}
        self._metrics: dict[str, list[dict]] = {}

    def create_dashboard(self, user_id: str, config: dict):
        self._dashboards[user_id] = config

    def get_dashboard(self, user_id: str) -> dict:
        return self._dashboards.get(user_id, {})

    def add_metric(self, user_id: str, metric: dict):
        if user_id not in self._metrics:
            self._metrics[user_id] = []
        self._metrics[user_id].append(metric)

    def get_metrics(self, user_id: str, limit: int = 20) -> list[dict]:
        return self._metrics.get(user_id, [])[:limit]

    def update_widget(self, user_id: str, widget_id: str, data: dict):
        dash = self._dashboards.get(user_id, {})
        if "widgets" not in dash:
            dash["widgets"] = {}
        dash["widgets"][widget_id] = data
        self._dashboards[user_id] = dash
