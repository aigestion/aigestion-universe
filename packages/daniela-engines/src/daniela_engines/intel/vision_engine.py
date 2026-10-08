"""
Vision Engine - Ideas 11-20
===========================

11. Image classification (ResNet)
12. Object detection (YOLO-style)
13. Face detection + recognition
14. OCR (Optical Character Recognition)
15. Image similarity search
16. Color palette extraction
17. Image quality assessment
18. Background removal
19. Scene classification (indoor/outdoor/urban)
20. Image captioning
"""

import hashlib
import math
import random


class VisionEngine:
    """Core Computer Vision engine with 10 powerful image analysis capabilities."""

    IMAGENET_CLASSES = [
        "airplane", "automobile", "bird", "cat", "deer", "dog", "frog",
        "horse", "ship", "truck", "person", "bicycle", "motorcycle", "bus",
        "train", "boat", "bottle", "chair", "couch", "potted plant",
        "bed", "dining table", "toilet", "tv", "laptop", "mouse",
        "remote", "keyboard", "cell phone", "microwave", "oven", "toaster",
    ]

    SCENE_LABELS = [
        "indoor", "outdoor", "urban", "rural", "beach", "mountain",
        "forest", "desert", "office", "kitchen", "bedroom", "bathroom",
        "street", "park", "garden", "garage", "classroom", "hospital",
    ]

    OBJECT_CLASSES = [
        "person", "car", "dog", "cat", "chair", "table", "bottle",
        "laptop", "phone", "book", "bag", "shoe", "hat", "glasses",
        "bicycle", "motorcycle", "bus", "truck", "traffic light",
        "stop sign", "bench", "plant", "tv", "remote", "keyboard",
    ]

    QUALITY_METRICS = {
        "excellent": (85, 100),
        "good": (70, 84),
        "fair": (50, 69),
        "poor": (30, 49),
        "bad": (0, 29),
    }

    def __init__(self):
        self.image_store: dict[str, dict] = {}
        self.gallery: list[dict] = []

    def _simulate_feature_vector(self, image_id: str, dims: int = 128) -> list[float]:
        """Generate deterministic feature vector from image_id for consistent results."""
        h = hashlib.md5(image_id.encode()).hexdigest()
        random.seed(h[:8])
        vec = [random.gauss(0, 1) for _ in range(dims)]
        norm = math.sqrt(sum(v ** 2 for v in vec)) or 1
        return [round(v / norm, 6) for v in vec]

    # ── Idea 11: Image Classification ───────────────────────────────
    def classify_image(self, image_id: str, top_k: int = 5) -> dict:
        """Classify image into categories (simulated ResNet)."""
        self._simulate_feature_vector(image_id)
        random.seed(hash(image_id) % (2**32))
        scores = [round(random.random(), 3) for _ in self.IMAGENET_CLASSES]
        total = sum(scores)
        scores = [round(s / total, 3) for s in scores]
        ranked = sorted(zip(self.IMAGENET_CLASSES, scores), key=lambda x: x[1], reverse=True)
        return {
            "top_classes": [{"class": c, "confidence": s} for c, s in ranked[:top_k]],
            "predicted_class": ranked[0][0],
            "confidence": ranked[0][1],
        }

    # ── Idea 12: Object Detection (YOLO-style) ─────────────────────
    def detect_objects(self, image_id: str, threshold: float = 0.5) -> dict:
        """Detect objects with bounding boxes (simulated YOLO)."""
        random.seed(hash(image_id) % (2**32))
        num_objects = random.randint(1, 8)
        detections = []
        for _i in range(num_objects):
            cls = random.choice(self.OBJECT_CLASSES)
            conf = round(random.uniform(threshold, 1.0), 3)
            x1 = round(random.uniform(0, 0.7), 3)
            y1 = round(random.uniform(0, 0.7), 3)
            w = round(random.uniform(0.1, 0.3), 3)
            h = round(random.uniform(0.1, 0.3), 3)
            detections.append({
                "class": cls,
                "confidence": conf,
                "bbox": {"x1": x1, "y1": y1, "x2": round(x1 + w, 3), "y2": round(y1 + h, 3)},
            })
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return {"detections": detections, "count": len(detections), "threshold": threshold}

    # ── Idea 13: Face Detection + Recognition ───────────────────────
    def detect_faces(self, image_id: str) -> dict:
        """Detect and recognize faces (simulated)."""
        random.seed(hash(image_id) % (2**32))
        num_faces = random.randint(0, 6)
        faces = []
        known_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
        for i in range(num_faces):
            x1 = round(random.uniform(0.1, 0.6), 3)
            y1 = round(random.uniform(0.1, 0.6), 3)
            is_known = random.random() > 0.3
            face = {
                "face_id": i,
                "bbox": {"x1": x1, "y1": y1, "x2": round(x1 + 0.2, 3), "y2": round(y1 + 0.25, 3)},
                "confidence": round(random.uniform(0.85, 0.99), 3),
                "recognized": is_known,
                "identity": random.choice(known_names) if is_known else None,
                "landmarks": {
                    "left_eye": [round(x1 + 0.07, 3), round(y1 + 0.08, 3)],
                    "right_eye": [round(x1 + 0.13, 3), round(y1 + 0.08, 3)],
                    "nose": [round(x1 + 0.1, 3), round(y1 + 0.13, 3)],
                    "mouth": [round(x1 + 0.1, 3), round(y1 + 0.17, 3)],
                },
            }
            faces.append(face)
        return {"faces": faces, "count": len(faces), "image_id": image_id}

    # ── Idea 14: OCR ────────────────────────────────────────────────
    def ocr(self, image_id: str, lang: str = "en") -> dict:
        """Extract text from image (simulated OCR)."""
        random.seed(hash(image_id) % (2**32))
        sample_texts = {
            "en": [
                "Invoice #2024-001 Total: $1,234.56",
                "Meeting at 3pm Conference Room B",
                "WARNING: Do not operate without training",
                "OPEN MON-FRI 9AM-5PM",
                "Exit this way ->",
            ],
            "es": [
                "Factura #2024-001 Total: 1.234,56 EUR",
                "Reunion a las 3pm Sala de Conferencias B",
                "ADVERTENCIA: No operar sin capacitacion",
                "ABIERTO LUN-VIE 9AM-5PM",
                "Salida por aqui ->",
            ],
        }
        texts = sample_texts.get(lang, sample_texts["en"])
        detected_text = random.choice(texts)
        words = detected_text.split()
        boxes = []
        x_pos = 0.05
        for word in words:
            w = len(word) * 0.02
            boxes.append({
                "text": word,
                "confidence": round(random.uniform(0.9, 1.0), 3),
                "bbox": {"x1": round(x_pos, 3), "y1": 0.4, "x2": round(x_pos + w, 3), "y2": 0.48},
            })
            x_pos += w + 0.01
        return {
            "text": detected_text,
            "language": lang,
            "words": len(words),
            "character_boxes": boxes,
            "confidence": round(random.uniform(0.92, 0.99), 3),
        }

    # ── Idea 15: Image Similarity Search ────────────────────────────
    def image_similarity(self, query_id: str, candidate_ids: list[str], top_k: int = 5) -> dict:
        """Find similar images using feature vectors."""
        query_vec = self._simulate_feature_vector(query_id)
        results = []
        for cid in candidate_ids:
            cand_vec = self._simulate_feature_vector(cid)
            dot = sum(a * b for a, b in zip(query_vec, cand_vec))
            results.append({"image_id": cid, "similarity": round(dot, 4)})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return {"query": query_id, "similar_images": results[:top_k], "candidates_searched": len(candidate_ids)}

    # ── Idea 16: Color Palette Extraction ───────────────────────────
    def extract_colors(self, image_id: str, num_colors: int = 5) -> dict:
        """Extract dominant color palette from image."""
        random.seed(hash(image_id) % (2**32))
        colors = []
        for _ in range(num_colors):
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            pct = round(random.uniform(5, 40), 1)
            colors.append({
                "rgb": (r, g, b),
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "percentage": pct,
                "name": self._color_name(r, g, b),
            })
        total = sum(c["percentage"] for c in colors)
        for c in colors:
            c["percentage"] = round(c["percentage"] / total * 100, 1)
        colors.sort(key=lambda c: c["percentage"], reverse=True)
        return {"colors": colors, "image_id": image_id}

    def _color_name(self, r: int, g: int, b: int) -> str:
        color_map = [
            ((200, 255), (200, 255), (200, 255), "white"),
            ((0, 50), (0, 50), (0, 50), "black"),
            ((150, 255), (0, 80), (0, 80), "red"),
            ((0, 80), (150, 255), (0, 80), "blue"),
            ((0, 80), (0, 80), (150, 255), "green"),
            ((200, 255), (150, 220), (0, 80), "yellow"),
            ((200, 255), (100, 180), (0, 80), "orange"),
            ((150, 200), (0, 80), (150, 200), "purple"),
            ((200, 255), (180, 230), (180, 230), "pink"),
            ((100, 180), (100, 180), (100, 180), "gray"),
        ]
        for (r_lo, r_hi), (g_lo, g_hi), (b_lo, b_hi), name in color_map:
            if r_lo <= r <= r_hi and g_lo <= g <= g_hi and b_lo <= b <= b_hi:
                return name
        return "mixed"

    # ── Idea 17: Image Quality Assessment ───────────────────────────
    def assess_quality(self, image_id: str) -> dict:
        """Assess image quality metrics."""
        random.seed(hash(image_id) % (2**32))
        sharpness = round(random.uniform(20, 100), 1)
        brightness = round(random.uniform(30, 95), 1)
        contrast = round(random.uniform(25, 90), 1)
        noise_level = round(random.uniform(1, 50), 1)
        resolution = random.choice(["480p", "720p", "1080p", "4K"])
        overall = round((sharpness * 0.3 + brightness * 0.2 + contrast * 0.25 + (100 - noise_level) * 0.25), 1)
        level = "unknown"
        for name, (lo, hi) in self.QUALITY_METRICS.items():
            if lo <= overall <= hi:
                level = name
                break
        return {
            "overall_score": overall,
            "level": level,
            "sharpness": sharpness,
            "brightness": brightness,
            "contrast": contrast,
            "noise_level": noise_level,
            "resolution": resolution,
            "recommendations": self._quality_recommendations(sharpness, brightness, noise_level),
        }

    def _quality_recommendations(self, sharpness: float, brightness: float, noise: float) -> list[str]:
        recs = []
        if sharpness < 50:
            recs.append("Apply sharpening filter")
        if brightness < 40:
            recs.append("Increase exposure/brightness")
        if brightness > 85:
            recs.append("Reduce brightness to avoid overexposure")
        if noise > 30:
            recs.append("Apply denoising filter")
        if not recs:
            recs.append("Image quality is good")
        return recs

    # ── Idea 18: Background Removal ─────────────────────────────────
    def remove_background(self, image_id: str, bg_color: str = "#ffffff") -> dict:
        """Remove background from image (simulated)."""
        random.seed(hash(image_id) % (2**32))
        mask_confidence = round(random.uniform(0.88, 0.98), 3)
        processing_time_ms = random.randint(120, 500)
        return {
            "image_id": image_id,
            "output_format": "png",
            "background_color": bg_color,
            "mask_confidence": mask_confidence,
            "processing_time_ms": processing_time_ms,
            "foreground_detected": True,
            "estimated_file_size_kb": random.randint(50, 500),
        }

    # ── Idea 19: Scene Classification ───────────────────────────────
    def classify_scene(self, image_id: str) -> dict:
        """Classify scene type (indoor/outdoor/urban)."""
        random.seed(hash(image_id) % (2**32))
        scores = {}
        for scene in self.SCENE_LABELS:
            scores[scene] = round(random.random(), 3)
        total = sum(scores.values())
        scores = {k: round(v / total, 3) for k, v in scores.items()}
        primary = max(scores, key=scores.get)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return {
            "primary_scene": primary,
            "confidence": scores[primary],
            "all_scores": dict(sorted_scores[:5]),
            "is_indoor": primary in {"indoor", "office", "kitchen", "bedroom", "bathroom", "classroom", "garage"},
            "is_outdoor": primary in {"outdoor", "urban", "rural", "beach", "mountain", "forest", "desert", "street", "park", "garden"},
        }

    # ── Idea 20: Image Captioning ───────────────────────────────────
    def generate_caption(self, image_id: str) -> dict:
        """Generate text caption for image (simulated)."""
        random.seed(hash(image_id) % (2**32))
        subjects = ["A person", "A dog", "A cat", "A group of people", "A child", "An animal"]
        actions = ["is standing", "is sitting", "is walking", "is running", "is playing", "is working"]
        locations = ["in a park", "on a street", "in an office", "at home", "in a garden", "near the water"]
        details = ["with a bright background", "during daytime", "with natural lighting", "in the evening", "with friends"]
        caption = f"{random.choice(subjects)} {random.choice(actions)} {random.choice(locations)} {random.choice(details)}."
        return {
            "caption": caption,
            "confidence": round(random.uniform(0.65, 0.92), 3),
            "image_id": image_id,
        }
