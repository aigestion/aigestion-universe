"""
aig Intel Engine - 50 Epic AI Intelligence Ideas
=====================================================

A modular AI intelligence platform providing NLP, Computer Vision,
Recommendations, Predictions, and Automation capabilities.

Modules:
    - nlp_engine: Natural Language Processing (ideas 1-10)
    - vision_engine: Computer Vision (ideas 11-20)
    - recommendation: Recommendation Engine (ideas 21-30)
    - prediction: Prediction Engine (ideas 31-40)
    - automation: AI Automation (ideas 41-50)
    - server: Flask API server (port 9850)

Usage:
    from intel_engine import NLPEngine, VisionEngine, RecommendationEngine

    nlp = NLPEngine()
    result = nlp.sentiment_analysis("This is amazing!")
"""

__version__ = "1.0.0"
__author__ = "aig"

from .automation import AutomationEngine
from .nlp_engine import NLPEngine
from .prediction import PredictionEngine
from .recommendation import RecommendationEngine
from .vision_engine import VisionEngine

__all__ = [
    "NLPEngine",
    "VisionEngine",
    "RecommendationEngine",
    "PredictionEngine",
    "AutomationEngine",
]
