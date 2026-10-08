"""Flask server for UX Engine - port 9830."""

from flask import Flask, jsonify, request

from .accessibility import (
    AltTextGenerator,
    ColorContrastChecker,
    FocusTrapManager,
    KeyboardNavigationManager,
    MotionReduction,
    ScreenReaderOptimizer,
    SkipNavigation,
    TextToSpeech,
    VoiceCommandInterface,
    WCAGComplianceChecker,
)
from .animations import (
    ConfettiAnimation,
    DragDropAnimations,
    HoverEffectLibrary,
    InfiniteScroll,
    NumberCounterAnimation,
    PageTransitions,
    ProgressBarAnimations,
    PullToRefresh,
    SkeletonLoader,
    ToastNotificationSystem,
)
from .i18n import (
    AutoTranslation,
    ContextAwareTranslations,
    DateTimeFormatting,
    LanguageFallbackChain,
    MultiLanguageSupport,
    NumberFormatting,
    PluralizationRules,
    RTLLayoutSupport,
    TranslationMemory,
    TranslationQualityScorer,
)
from .personalization import (
    AchievementSystem,
    ContentRecommendations,
    LayoutPersonalization,
    PersonalizedDashboard,
    ProgressTracker,
    QuickActions,
    SearchPersonalization,
    SmartNotifications,
    UserPreferenceLearning,
    WelcomeWizard,
)
from .themes import (
    AccessibilityFontControls,
    ColorBlindPalette,
    CSSVariableInjector,
    DarkLightMode,
    HighContrastMode,
    ServiceThemeOverrides,
    ThemeEngine,
    ThemeMarketplace,
    ThemePreviewAB,
    ThemeScheduler,
)

app = Flask(__name__)

# Theme instances
theme_engine = ThemeEngine()
dark_light = DarkLightMode()
high_contrast = HighContrastMode()
css_injector = CSSVariableInjector()
marketplace = ThemeMarketplace()
scheduler = ThemeScheduler()
service_overrides = ServiceThemeOverrides()
font_controls = AccessibilityFontControls()
color_blind = ColorBlindPalette()
preview_ab = ThemePreviewAB()

# Personalization instances
pref_learning = UserPreferenceLearning()
layout_personalization = LayoutPersonalization()
quick_actions = QuickActions()
smart_notifications = SmartNotifications()
content_recs = ContentRecommendations()
search_personalization = SearchPersonalization()
welcome_wizard = WelcomeWizard()
progress_tracker = ProgressTracker()
achievement_system = AchievementSystem()
dashboard = PersonalizedDashboard()

# Accessibility instances
wcag_checker = WCAGComplianceChecker()
screen_reader = ScreenReaderOptimizer()
keyboard_nav = KeyboardNavigationManager()
focus_trap = FocusTrapManager()
skip_nav = SkipNavigation()
alt_generator = AltTextGenerator()
contrast_checker = ColorContrastChecker()
motion_reduction = MotionReduction()
tts = TextToSpeech()
voice_commands = VoiceCommandInterface()

# Animation instances
skeleton = SkeletonLoader()
page_transitions = PageTransitions()
hover_effects = HoverEffectLibrary()
toasts = ToastNotificationSystem()
progress_bars = ProgressBarAnimations()
confetti = ConfettiAnimation()
pull_refresh = PullToRefresh()
infinite_scroll = InfiniteScroll()
drag_drop = DragDropAnimations()
counter_animation = NumberCounterAnimation()

# i18n instances
i18n = MultiLanguageSupport()
rtl = RTLLayoutSupport()
dt_format = DateTimeFormatting()
num_format = NumberFormatting()
pluralization = PluralizationRules()
context_translations = ContextAwareTranslations()
translation_memory = TranslationMemory()
auto_translation = AutoTranslation()
fallback_chain = LanguageFallbackChain()
quality_scorer = TranslationQualityScorer()


@app.route("/api/ux/status", methods=["GET"])
def status():
    return jsonify({
        "status": "ok",
        "engine": "ux_engine",
        "version": "1.0.0",
        "modules": {
            "themes": 10,
            "personalization": 10,
            "accessibility": 10,
            "animations": 10,
            "i18n": 10,
        },
        "total_features": 50,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ux_engine"})


@app.route("/api/ux/themes", methods=["GET"])
def list_themes():
    action = request.args.get("action", "list")
    if action == "list":
        return jsonify({
            "themes": [
                {"id": "default-light", "name": "Default Light", "mode": "light"},
                {"id": "default-dark", "name": "Default Dark", "mode": "dark"},
                {"id": "high-contrast", "name": "High Contrast", "mode": "high-contrast"},
                {"id": "color-blind-protanopia", "name": "Protanopia Friendly", "mode": "color-blind"},
            ],
            "marketplace": marketplace.list_themes(),
        })
    return jsonify({"status": "unknown action"}), 400


@app.route("/api/ux/themes", methods=["POST"])
def apply_theme():
    data = request.get_json() or {}
    action = data.get("action", "apply")
    if action == "generate":
        result = theme_engine.generate_from_brand(data.get("colors", {}))
        return jsonify({"theme": result})
    elif action == "mode":
        dark_light.set_mode(data.get("mode", "auto"))
        return jsonify({"mode": dark_light.get_mode(), "resolved": dark_light.resolve()})
    elif action == "publish":
        marketplace.publish(data.get("id", "unnamed"), data.get("theme", {}), data.get("author", "anonymous"))
        return jsonify({"status": "published"})
    return jsonify({"status": "unknown action"}), 400


@app.route("/api/ux/personalize", methods=["GET"])
def get_personalize():
    user_id = request.args.get("user_id", "default")
    return jsonify({
        "preferences": pref_learning.get_preferences(user_id),
        "layout": layout_personalization.get_layout(user_id),
        "shortcuts": quick_actions.get_suggested(user_id),
        "notifications": smart_notifications.get_notifications(user_id),
        "dashboard": dashboard.get_dashboard(user_id),
    })


@app.route("/api/ux/personalize", methods=["POST"])
def post_personalize():
    data = request.get_json() or {}
    user_id = data.get("user_id", "default")
    action = data.get("action")
    if action == "set_preference":
        pref_learning.set_preference(user_id, data.get("key", ""), data.get("value"))
        return jsonify({"status": "ok"})
    elif action == "save_layout":
        layout_personalization.save_layout(user_id, data.get("widgets", []))
        return jsonify({"status": "ok"})
    elif action == "add_shortcut":
        quick_actions.add_shortcut(user_id, data.get("shortcut", {}))
        return jsonify({"status": "ok"})
    elif action == "add_notification":
        smart_notifications.add_notification(user_id, data.get("notification", {}))
        return jsonify({"status": "ok"})
    return jsonify({"status": "unknown action"}), 400


@app.route("/api/ux/accessibility", methods=["GET"])
def get_accessibility():
    return jsonify({
        "wcag": {"aa_normal": WCAGComplianceChecker.AA_NORMAL_MIN, "aa_large": WCAGComplianceChecker.AA_LARGE_MIN},
        "motion_reduction": motion_reduction.is_global(),
        "tts_settings": tts.get_settings(),
        "voice_commands": voice_commands.get_commands(),
        "skip_links": skip_nav.get_links(),
    })


@app.route("/api/ux/accessibility", methods=["POST"])
def post_accessibility():
    data = request.get_json() or {}
    action = data.get("action")
    if action == "check_contrast":
        result = contrast_checker.check(data.get("fg", "#000000"), data.get("bg", "#ffffff"))
        return jsonify({"result": result})
    elif action == "motion_reduction":
        motion_reduction.set_global(data.get("enabled", False))
        return jsonify({"enabled": motion_reduction.is_global(), "css": motion_reduction.get_css()})
    elif action == "add_skip_link":
        skip_nav.add_link(data.get("label", ""), data.get("target", ""))
        return jsonify({"links": skip_nav.get_links()})
    elif action == "register_voice_command":
        voice_commands.register_command(data.get("phrase", ""), data.get("action", ""))
        return jsonify({"commands": voice_commands.get_commands()})
    elif action == "tts_speak":
        tts.speak(data.get("text", ""), data.get("priority", False))
        return jsonify({"queue": tts.get_queue()})
    return jsonify({"status": "unknown action"}), 400


@app.route("/api/ux/animations", methods=["GET"])
def list_animations():
    return jsonify({
        "skeleton_templates": skeleton.list_templates(),
        "hover_effects": hover_effects.list_effects(),
        "transition_presets": list(PageTransitions.PRESETS.keys()),
        "progress_bar_presets": list(ProgressBarAnimations.PRESETS.keys()),
    })


@app.route("/api/ux/animations", methods=["POST"])
def configure_animation():
    data = request.get_json() or {}
    action = data.get("action")
    if action == "define_skeleton":
        skeleton.define_template(data.get("name", "default"), data.get("blocks", []))
        return jsonify({"status": "ok", "templates": skeleton.list_templates()})
    elif action == "toast":
        toasts.show(data.get("message", ""), data.get("type", "info"))
        return jsonify({"toasts": toasts.get_toasts()})
    elif action == "confetti":
        confetti.trigger(data.get("count", 50))
        return jsonify({"particles": len(confetti.get_particles())})
    elif action == "create_counter":
        counter_animation.create(data.get("id", "c1"), data.get("target", 100))
        return jsonify({"status": "ok"})
    return jsonify({"status": "unknown action"}), 400


@app.route("/api/ux/i18n", methods=["GET"])
def get_i18n():
    locale = request.args.get("locale", "en")
    key = request.args.get("key", "")
    return jsonify({
        "available_locales": i18n.get_available(),
        "translation": i18n.t(key, locale) if key else None,
        "direction": rtl.get_direction(locale),
        "supported_auto_languages": auto_translation.get_supported_languages(),
    })


@app.route("/api/ux/i18n", methods=["POST"])
def post_i18n():
    data = request.get_json() or {}
    action = data.get("action")
    if action == "add_translation":
        i18n.add_translations(data.get("locale", "en"), data.get("translations", {}))
        return jsonify({"status": "ok", "locales": i18n.get_available()})
    elif action == "translate":
        result = auto_translation.translate(data.get("text", ""), data.get("source", "en"), data.get("target", "es"))
        return jsonify({"translation": result})
    elif action == "score":
        result = quality_scorer.score(data.get("source", ""), data.get("translation", ""), data.get("locale", "en"))
        return jsonify({"score": result})
    return jsonify({"status": "unknown action"}), 400


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "9830")), debug=False)
