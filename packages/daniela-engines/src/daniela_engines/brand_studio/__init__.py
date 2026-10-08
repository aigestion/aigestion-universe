"""Brand Studio engine — storyboard JSON -> render plan -> MP4.

Consolidates prototypes/build_brand_vids_studio.py,
prototypes/assembler_ffmpeg.py and
prototypes/brand_studio/VIDEO_STORYBOARD.json into one service.
No LLM, no network: deterministic storyboard validation plus real
ffmpeg rendering (lavfi color cards per scene; honest placeholder
visuals, real durations and concat).
"""
__version__ = "1.0.0"
