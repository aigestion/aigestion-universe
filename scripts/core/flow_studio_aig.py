#!/usr/bin/env python3
"""
aig Flow Studio - Google Flow + Storyboard Studio Integration
===================================================================
Complete content creation system using Google Flow (flow.google.com) and
its built-in Storyboard Studio tool for producing cinematic AI video
content featuring Daniela and the aig brand.

Google Flow Models:
  - Veo 3.1: Video generation with native audio (4s/6s/8s clips, 1080p)
  - Nano Banana: High-fidelity image generation with subject consistency
  - Gemini Omni: Multimodal video editing from text/image/video inputs

Storyboard Studio Workflow:
  1. Write a script (or generate with AI)
  2. Create the cast (auto-detected from story)
  3. Autofill details for characters/locations/props
  4. Generate storyboard panels with camera shots
  5. Customize camera angles and shots
  6. Export as JSON for later editing

Free Tier: 50 daily credits (can use tools, not create them)
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ============================================================================
# DANIELA - FLOW INGREDIENT SPEC
# ============================================================================

@dataclass
class FlowIngredient:
    """Google Flow Ingredient - character/object reference for consistency."""
    name: str
    description: str
    nano_banana_prompt: str
    visual_traits: dict[str, str]
    usage_notes: str

DANIELA_INGREDIENT = FlowIngredient(
    name="Daniela",
    description=(
        "Daniela is the Ciber-Ejecutiva (Cyber-Executive) of aig. "
        "She is a professional AI executive woman with a futuristic dark suit "
        "featuring neon cyan (#00ffff) and magenta (#ff0055) accents. "
        "She operates from a glass-walled virtual office overlooking a "
        "cyberpunk metropolis at night, surrounded by holographic dashboards."
    ),
    nano_banana_prompt=(
        "Cinematic portrait of Daniela, a confident AI executive woman in her 30s. "
        "She wears a sleek charcoal-black futuristic business suit with subtle "
        "neon cyan and magenta glowing accents along the lapels and cuffs. "
        "Her hair is dark, styled in a sharp executive cut. "
        "She stands in a glass-walled office with floor-to-ceiling windows "
        "overlooking a neon cyberpunk metropolis at night. "
        "Holographic dashboard panels float around her showing data graphs. "
        "Lighting: dramatic cyan and magenta neon rim light. "
        "Expression: confident, direct gaze, subtle professional smile. "
        "Style: photorealistic, 8K, cinematic, Blade Runner aesthetic. "
        "DO NOT change her face, suit, or hair style in any generation."
    ),
    visual_traits={
        "age": "30s",
        "hair": "Dark, sharp executive cut",
        "suit": "Charcoal-black futuristic with neon cyan/magenta accents",
        "setting": "Glass office, cyberpunk city night, holographic dashboards",
        "lighting": "Cyan and magenta neon rim light",
        "expression": "Confident, direct gaze, subtle professional smile",
        "color_palette": "Dark base + cyan #00ffff + magenta #ff0055",
    },
    usage_notes=(
        "Use this ingredient as a reference in EVERY scene where Daniela appears. "
        "Lock it as the first ingredient in your Flow project. "
        "All subsequent generations with Veo or Nano Banana will maintain "
        "her identity consistency. Use @Daniela in Flow prompts to reference her."
    )
)

# Additional ingredients for the aig universe
aig_OFFICE_INGREDIENT = FlowIngredient(
    name="aig Office",
    description=(
        "Daniela's virtual office: a glass-walled penthouse suite overlooking "
        "a neon cyberpunk metropolis. Holographic dashboards float in mid-air. "
        "The desk is a transparent glass surface with cyan-lit edges."
    ),
    nano_banana_prompt=(
        "Interior of a futuristic glass-walled executive office at night. "
        "Floor-to-ceiling windows reveal a vast cyberpunk metropolis with "
        "neon cyan and magenta lights. A transparent glass desk with glowing "
        "cyan edges sits in the center. Multiple holographic dashboard panels "
        "float in the air showing data graphs and analytics. "
        "Dark floor with subtle magenta light strips. "
        "Style: photorealistic, cinematic, 8K, Blade Runner meets executive suite."
    ),
    visual_traits={
        "walls": "Floor-to-ceiling glass",
        "view": "Cyberpunk metropolis at night",
        "desk": "Transparent glass with cyan-lit edges",
        "decor": "Floating holographic dashboards",
        "lighting": "Neon cyan and magenta ambient",
    },
    usage_notes="Use as location ingredient for all office scenes."
)

DASHBOARD_INGREDIENT = FlowIngredient(
    name="aig Dashboard",
    description=(
        "The aig holographic dashboard interface: floating panels with "
        "real-time analytics, agent status, task automation flows, and metrics. "
        "Cyan and magenta data visualizations on dark transparent backgrounds."
    ),
    nano_banana_prompt=(
        "Holographic dashboard interface floating in dark space. "
        "Multiple translucent panels showing real-time analytics graphs, "
        "agent status indicators, automated task flows, and KPI metrics. "
        "Cyan (#00ffff) line charts, magenta (#ff0055) alert indicators, "
        "green (#00ff88) success states. Dark transparent backgrounds. "
        "Glowing neon edges on each panel. Futuristic data visualization. "
        "Style: sci-fi UI, photorealistic hologram, 8K."
    ),
    visual_traits={
        "panels": "Translucent floating rectangles",
        "charts": "Cyan line graphs, magenta alerts, green success",
        "background": "Dark transparent",
        "edges": "Glowing neon cyan",
    },
    usage_notes="Use as prop ingredient when showing aig capabilities."
)

ALL_INGREDIENTS = [DANIELA_INGREDIENT, aig_OFFICE_INGREDIENT, DASHBOARD_INGREDIENT]

# ============================================================================
# STORYBOARD SCRIPTS - Ready to paste into Storyboard Studio
# ============================================================================

@dataclass
class StoryboardScript:
    """Complete script ready for Google Flow Storyboard Studio."""
    id: str
    title: str
    style: str  # e.g., "3D Animated", "Cinematic", "Photorealistic"
    story_text: str  # The actual story to paste into Storyboard Studio
    cast: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    props: list[str] = field(default_factory=list)
    veo_prompts: list[dict] = field(default_factory=list)
    nano_banana_prompts: list[dict] = field(default_factory=list)
    notes: str = ""

class StoryboardScripts:
    """10 complete storyboard scripts for aig content."""

    SCRIPT_1_LAUNCH = StoryboardScript(
        id="flow_launch_commercial",
        title="aig: El Futuro de la Gestion Empresarial",
        style="Cinematic Photorealistic",
        story_text="""In a dark, chaotic office at night, a stressed executive sits
surrounded by piles of paper, dozens of browser tabs, and a phone
that won't stop buzzing with notifications. The clock on the wall
spins faster and faster. Coffee cups stack up. The executive rubs
his temples in frustration.

Suddenly, the room goes dark. A beam of cyan light cuts through
the darkness. The executive looks up. Through the glass wall,
a neon cyberpunk metropolis glows in the distance.

Daniela appears, walking calmly through a holographic doorway.
She wears a sleek dark suit with glowing cyan and magenta accents.
Holographic dashboard panels materialize around her, showing
real-time data, automated task flows, and green success indicators.

She speaks directly to the executive: "You're losing 3 hours every
day to tasks I can handle in 30 seconds."

She gestures, and the chaos around the desk transforms. Papers
digitize and organize themselves. Browser tabs consolidate into
a single clean dashboard. Notifications sort by priority and
auto-respond. The clock slows to a calm, steady pace.

Daniela smiles. "I'm Daniela, your Ciber-Ejecutiva. This is
aig."

The scene pulls back to reveal the aig logo glowing in
neon cyan and magenta. The tagline appears: "Gestion Inteligente
con Inteligencia Artificial." A URL appears: aig.com
""",
        cast=["Daniela", "Stressed Executive"],
        locations=["Chaotic Office (dark, messy)", "aig Glass Office (neon, clean)"],
        props=["Piles of paper", "Phone with notifications", "Coffee cups", "Holographic dashboards", "aig logo"],
        veo_prompts=[
            {
                "scene": 1,
                "description": "Chaotic office at night",
                "prompt": (
                    "Wide shot of a messy office at night. An executive sits at a desk "
                    "buried under piles of paper. Dozens of browser windows glow on "
                    "multiple monitors. A phone buzzes with notifications. Coffee cups "
                    "stack up. The clock on the wall spins rapidly. Dark, oppressive lighting. "
                    "Camera: slow dolly in toward the stressed executive. "
                    "Mood: chaotic, stressful, overwhelming."
                ),
                "duration": "8s",
                "audio": "Phone buzzing, keyboard clacking, clock ticking fast"
            },
            {
                "scene": 2,
                "description": "Darkness and light beam",
                "prompt": (
                    "The office goes completely dark. A beam of cyan neon light "
                    "cuts through the darkness from the glass wall. Through the window, "
                    "a neon cyberpunk metropolis is visible at night. "
                    "Camera: low angle looking up at the light beam. "
                    "Mood: mysterious, transitional, hopeful."
                ),
                "duration": "6s",
                "audio": "Silence, then a low electronic hum building"
            },
            {
                "scene": 3,
                "description": "Daniela enters",
                "prompt": (
                    "@Daniela walks calmly through a holographic doorway made of cyan light. "
                    "She wears her dark suit with neon cyan and magenta accents. "
                    "Holographic dashboard panels materialize around her showing data graphs. "
                    "Camera: medium tracking shot following her entrance. "
                    "Mood: confident, powerful, futuristic."
                ),
                "duration": "8s",
                "audio": "Electronic crescendo, confident footsteps"
            },
            {
                "scene": 4,
                "description": "Daniela speaks to executive",
                "prompt": (
                    "@Daniela stands in front of the stressed executive. She looks directly "
                    "at him with a confident, subtle smile. Holographic panels float "
                    "between them. The executive looks up in amazement. "
                    "Camera: over-the-shoulder shot from executive's perspective. "
                    "Mood: authoritative, reassuring, transformative."
                ),
                "duration": "6s",
                "audio": "Daniela speaks: 'You're losing 3 hours every day to tasks I can handle in 30 seconds.'"
            },
            {
                "scene": 5,
                "description": "Transformation sequence",
                "prompt": (
                    "@Daniela gestures with her hand. Papers on the desk digitize and "
                    "fly into a clean dashboard. Browser tabs consolidate into one screen. "
                    "Notifications sort by priority and auto-respond with check marks. "
                    "The clock on the wall slows to a calm pace. "
                    "Camera: sweeping 180-degree shot around the desk. "
                    "Mood: magical, satisfying, organized."
                ),
                "duration": "8s",
                "audio": "Digital transformation sounds, soft electronic music, chimes"
            },
            {
                "scene": 6,
                "description": "Daniela introduces aig",
                "prompt": (
                    "@Daniela stands in her glass office with the neon city behind her. "
                    "She smiles confidently. The aig logo glows in cyan and magenta "
                    "behind her. Holographic text appears: 'Gestion Inteligente con IA'. "
                    "Camera: slow pull back to wide shot. "
                    "Mood: epic, conclusive, call-to-action."
                ),
                "duration": "6s",
                "audio": "Daniela speaks: 'I'm Daniela, your Ciber-Ejecutiva. This is aig.' Epic final chord."
            }
        ],
        nano_banana_prompts=[
            {
                "purpose": "Storyboard panel - chaotic office",
                "prompt": "Wide shot of a messy dark office at night. Stressed executive at desk buried in paper. Multiple monitors with browser tabs. Phone buzzing. Coffee cups stacked. Clock spinning. Oppressive dim lighting. Photorealistic, cinematic."
            },
            {
                "purpose": "Storyboard panel - Daniela entrance",
                "prompt": "A woman in a dark futuristic suit with neon cyan and magenta accents walks through a doorway of cyan holographic light. Glass office with cyberpunk city visible. Holographic dashboard panels float around her. Photorealistic, 8K, Blade Runner aesthetic."
            },
            {
                "purpose": "Storyboard panel - transformation",
                "prompt": "Desk transformation scene. Papers digitizing into floating data streams. Browser tabs consolidating into one clean holographic dashboard. Green check marks appearing on notifications. Clock slowing down. Cyan and magenta neon glow. Photorealistic."
            },
            {
                "purpose": "Storyboard panel - final logo",
                "prompt": "Woman in futuristic dark suit standing confidently in glass office with neon cyberpunk city behind her. A glowing hexagonal logo with circuit patterns in cyan and magenta floats behind her. Holographic text reads 'aig'. Epic lighting. Photorealistic, 8K."
            }
        ],
        notes=(
            "WORKFLOW: 1) Open Google Flow > New Project. "
            "2) Tools > Storyboard Studio > Get Started. "
            "3) Select style: 'Cinematic Photorealistic'. "
            "4) Paste the story_text above into the script editor. "
            "5) Let AI auto-detect cast, locations, props. "
            "6) Click Autofill Details for asset descriptions. "
            "7) For each panel, use the veo_prompts in Veo 3.1. "
            "8) Use nano_banana_prompts for storyboard panel images. "
            "9) Lock @Daniela, @aig Office, @Dashboard as ingredients. "
            "10) Export as JSON when done."
        )
    )

    SCRIPT_2_DANIELA_DAY = StoryboardScript(
        id="flow_daniela_day_in_life",
        title="Un Dia con Daniela: Como la IA Gestion tu Empresa 24/7",
        style="3D Animated",
        story_text="""Morning breaks over the neon cyberpunk metropolis. Inside
her glass office, Daniela is already working. She doesn't sleep.
She doesn't need coffee. She is always on.

At 6:00 AM, Daniela scans 47 overnight emails. She classifies
each one: 12 urgent (flagged red), 25 routine (auto-responded
with green check marks), 10 spam (deleted). The executive's
inbox is clean before he even wakes up.

At 7:00 AM, Daniela checks the calendar. She spots a scheduling
conflict: two meetings booked at 10 AM. She reschedules one,
sends polite notifications to all participants, and prepares
a briefing document for the 10 AM meeting that's still on.

At 9:00 AM, Daniela generates a weekly sales report. She pulls
data from 5 sources, creates 3 charts, writes an executive
summary, saves it to Google Drive, and posts it to the team
dashboard. The report is ready before anyone asks for it.

At 12:00 PM, Daniela monitors social media. She drafts 3 tweets,
2 LinkedIn posts, and an Instagram caption. All scheduled for
optimal posting times. Engagement metrics from yesterday's
posts are tracked and analyzed.

At 3:00 PM, Daniela detects an anomaly: server response time
spiked by 200%. She alerts the team, creates a ticket, and
pulls diagnostic logs. The issue is resolved before customers
even notice.

At 6:00 PM, Daniela prepares tomorrow's briefing: weather,
calendar, priorities, news digest, and a motivational quote.
She sends it to the executive's phone. The day is done.
But Daniela never sleeps. She'll be ready again at 6 AM.
""",
        cast=["Daniela"],
        locations=["aig Glass Office (dawn to dusk lighting changes)"],
        props=["Holographic email interface", "Calendar with scheduling conflict", "Sales report with charts", "Social media dashboard", "Server alert panel", "Daily briefing on phone"],
        veo_prompts=[
            {
                "scene": 1,
                "description": "Dawn over the city",
                "prompt": (
                    "Time-lapse of a neon cyberpunk metropolis at dawn. "
                    "The sun rises behind skyscrapers with holographic billboards. "
                    "Camera: aerial wide shot slowly descending toward a glass office tower. "
                    "Mood: serene, beginning, anticipation."
                ),
                "duration": "6s",
                "audio": "Soft ambient electronic music, distant city sounds"
            },
            {
                "scene": 2,
                "description": "Daniela scanning emails at 6AM",
                "prompt": (
                    "@Daniela stands at her glass desk in the office. Holographic email "
                    "panels float in front of her. Emails fly past rapidly: red flags "
                    "for urgent, green checks for auto-responded, trash icon for spam. "
                    "47 emails processed in seconds. Camera: side tracking shot. "
                    "Mood: efficient, precise, effortless."
                ),
                "duration": "8s",
                "audio": "Soft digital processing sounds, notification chimes"
            },
            {
                "scene": 3,
                "description": "Calendar conflict resolution at 7AM",
                "prompt": (
                    "@Daniela gestures at a holographic calendar. Two meetings overlap "
                    "at 10 AM, highlighted in red. She drags one meeting to a new slot. "
                    "Polite notification messages fly out automatically. A briefing "
                    "document materializes for the remaining meeting. "
                    "Camera: over-shoulder looking at calendar. "
                    "Mood: organized, proactive."
                ),
                "duration": "8s",
                "audio": "Calendar scheduling sounds, message send chimes"
            },
            {
                "scene": 4,
                "description": "Sales report generation at 9AM",
                "prompt": (
                    "@Daniela pulls data from 5 floating source panels. Data streams "
                    "merge into a single holographic report with 3 animated charts. "
                    "The report compiles, saves to a Drive icon, and posts to a team "
                    "dashboard. Everything happens automatically. "
                    "Camera: wide shot of the full desk with all panels active. "
                    "Mood: powerful, comprehensive, satisfying."
                ),
                "duration": "8s",
                "audio": "Data processing sounds, chart building, save confirmation"
            },
            {
                "scene": 5,
                "description": "Social media management at 12PM",
                "prompt": (
                    "@Daniela drafts social media content. Three tweet cards, two "
                    "LinkedIn posts, and an Instagram caption float in front of her. "
                    "A scheduling timeline shows optimal posting times highlighted. "
                    "Engagement metrics from yesterday appear as small bar charts. "
                    "Camera: medium shot, dynamic composition. "
                    "Mood: creative, strategic."
                ),
                "duration": "6s",
                "audio": "Light typing sounds, social media notification sounds"
            },
            {
                "scene": 6,
                "description": "Server anomaly at 3PM",
                "prompt": (
                    "@Daniela's dashboard flashes red. A server response graph spikes "
                    "200%. Alert notifications fly out. A diagnostic log panel appears. "
                    "The spike graph flattens back to normal. Green check mark appears. "
                    "Camera: fast zoom into the alert, then pull back to calm. "
                    "Mood: tense then resolved, protective."
                ),
                "duration": "8s",
                "audio": "Alert sound, rapid processing, resolution chime"
            },
            {
                "scene": 7,
                "description": "Daily briefing and night",
                "prompt": (
                    "@Daniela sends a holographic briefing card to a phone screen. "
                    "The card contains: weather, calendar, priorities, news, quote. "
                    "The office lights dim to a soft cyan glow. The city glows outside. "
                    "@Daniela stands calmly, ready for tomorrow. "
                    "Camera: slow pull back to wide, fade to the city skyline. "
                    "Mood: peaceful, complete, ever-present."
                ),
                "duration": "8s",
                "audio": "Soft send chime, ambient night sounds, gentle electronic fade"
            }
        ],
        notes=(
            "This script is perfect for Storyboard Studio's auto-scene detection. "
            "The time stamps (6AM, 7AM, 9AM, etc.) will be detected as scene breaks. "
            "Use '3D Animated' style in Storyboard Studio. "
            "Lock @Daniela as the only character ingredient. "
            "Use @Dashboard and @aig Office as location and prop ingredients."
        )
    )

    SCRIPT_3_BEFORE_AFTER = StoryboardScript(
        id="flow_before_after",
        title="Antes vs Despues: La Transformacion aig",
        style="Cinematic Photorealistic",
        story_text="""BEFORE: A businessman named Carlos sits in his office at 7 PM,
exhausted. His desk is chaos. 50 unread emails. A calendar
double-booked. Three reports due tomorrow. His phone shows
47 missed calls. He hasn't seen his family before 8 PM in weeks.
The clock on the wall seems to mock him.

A split screen appears. LEFT side: Carlos's chaotic present.
RIGHT side: empty, dark, waiting.

Daniela steps into the RIGHT side of the screen. She activates
the aig dashboard. Holographic panels light up. The right
side transforms into a clean, organized, neon-lit workspace.

Now both sides run simultaneously in fast-forward:

LEFT (BEFORE): Carlos manually opens each email, reads, types
a response, sends. 50 emails take 2 hours. He's still at his
desk at 9 PM.

RIGHT (AFTER): Daniela processes 50 emails in 30 seconds.
Red flags for 5 urgent ones. Green checks for 40 auto-responded.
Trash for 5 spam. Done. Carlos leaves at 6 PM.

LEFT: Carlos manually creates a report. Opens Excel, copies data,
formats, writes summary, exports PDF, emails it. 90 minutes.

RIGHT: Daniela pulls data from 5 sources, generates charts,
writes summary, saves to Drive, posts to dashboard. 30 seconds.

LEFT: Carlos misses his daughter's school play. He's at the office.

RIGHT: Carlos is in the front row of the school play, phone
in pocket. Daniela handles everything.

The split screen merges. Carlos stands with Daniela in the
aig office. He looks relieved. Grateful. Free.

Daniela: "30 hours a week. That's what you get back."

Logo. Tagline. URL.
""",
        cast=["Daniela", "Carlos (stressed businessman)"],
        locations=["BEFORE: Chaotic office (dim, messy)", "AFTER: aig office (neon, clean)", "School auditorium"],
        props=["Email inbox (50 unread)", "Calendar (double-booked)", "Excel report", "Phone with missed calls", "Holographic dashboards", "School play stage"],
        veo_prompts=[
            {
                "scene": 1,
                "description": "BEFORE - Carlos exhausted",
                "prompt": (
                    "A businessman sits exhausted at a messy desk at 7 PM. 50 unread emails "
                    "on screen. Calendar double-booked. Phone showing 47 missed calls. "
                    "Three reports stacked. Dim overhead lighting. Clock on wall. "
                    "Camera: static wide shot, slightly high angle. "
                    "Mood: exhausted, trapped, hopeless."
                ),
                "duration": "8s",
                "audio": "Ticking clock, phone buzz, heavy sigh"
            },
            {
                "scene": 2,
                "description": "Split screen introduction",
                "prompt": (
                    "Screen splits vertically. LEFT: the chaotic office with Carlos. "
                    "RIGHT: empty dark space. A vertical neon line separates them. "
                    "Camera: static split screen. "
                    "Mood: anticipatory, about to change."
                ),
                "duration": "4s",
                "audio": "A low hum, building tension"
            },
            {
                "scene": 3,
                "description": "Daniela activates the RIGHT side",
                "prompt": (
                    "@Daniela steps into the RIGHT side of the split screen. She touches "
                    "the air and holographic dashboard panels light up around her. "
                    "The dark space transforms into a clean neon-lit office. "
                    "Camera: medium shot on Daniela, dynamic lighting change. "
                    "Mood: transformative, powerful, hopeful."
                ),
                "duration": "8s",
                "audio": "Activation sound, electronic build-up, confident footsteps"
            },
            {
                "scene": 4,
                "description": "Email comparison - fast forward",
                "prompt": (
                    "Split screen, fast-forward effect. LEFT: Carlos manually opening emails "
                    "one by one, typing responses, clock shows 2 hours passing. "
                    "RIGHT: @Daniela processes 50 emails in seconds. Red flags, green checks, "
                    "trash icons fly past. Done in 30 seconds. "
                    "Camera: split screen, time-lapse effect on both sides. "
                    "Mood: dramatic contrast, satisfying."
                ),
                "duration": "8s",
                "audio": "Fast-forward sounds on left, rapid processing on right"
            },
            {
                "scene": 5,
                "description": "Report comparison",
                "prompt": (
                    "Split screen continues. LEFT: Carlos in Excel, manually copying data, "
                    "formatting, slow tedious work. RIGHT: @Daniela pulls 5 data streams, "
                    "charts auto-generate, report compiles instantly, saves to Drive. "
                    "Camera: split screen, zoom on details. "
                    "Mood: stark contrast, revelation."
                ),
                "duration": "8s",
                "audio": "Keyboard typing on left, data processing sounds on right"
            },
            {
                "scene": 6,
                "description": "School play - emotional payoff",
                "prompt": (
                    "LEFT: Carlos at his desk at night, phone shows a photo of his "
                    "daughter on stage. He missed it. RIGHT: Carlos sits in the front row "
                    "of a school auditorium, watching his daughter perform. He smiles. "
                    "Phone in pocket. Camera: emotional close-up on both faces. "
                    "Mood: heartbreaking left, heartwarming right."
                ),
                "duration": "8s",
                "audio": "Silence on left, children's play music on right"
            },
            {
                "scene": 7,
                "description": "Merge and conclusion",
                "prompt": (
                    "The split screen merges into one. Carlos stands with @Daniela in the "
                    "aig glass office. He looks relieved, grateful, free. "
                    "@Daniela smiles. The aig logo glows behind them. "
                    "Camera: slow pull back to wide. "
                    "Mood: resolution, freedom, epic."
                ),
                "duration": "6s",
                "audio": "Daniela: '30 hours a week. That's what you get back.' Epic music."
            }
        ],
        notes=(
            "SPLIT SCREEN TECHNIQUE: Use Veo 3.1 to generate LEFT and RIGHT "
            "clips separately, then composite in the Scenebuilder timeline. "
            "The contrast between dim/messy and neon/clean is the key visual driver. "
            "Emotional peak is Scene 6 (school play). "
            "Best for YouTube long-form (5 min version) or condensed Short (60s)."
        )
    )

    SCRIPT_4_AGENT_SQUAD = StoryboardScript(
        id="flow_agent_squad",
        title="El Escuadron: 5 Agentes IA que Trabajan por Ti",
        style="3D Animated",
        story_text="""Deep inside the aig system, five AI agents power up
in sequence, like a team assembling for a mission.

Agent 1: CORREO. A sleek figure made of blue light. He processes
email flows at superhuman speed. 50 emails in 30 seconds.
Classification, response, archiving. Done.

Agent 2: CALENDARIO. A figure made of golden light. She sees
the full calendar, past and future. She optimizes schedules,
avoids conflicts, sends reminders. Time bends to her will.

Agent 3: DOCUMENTOS. A figure made of green light. He pulls
data from everywhere, generates reports, creates presentations,
organizes Drive. Knowledge flows through him.

Agent 4: REDES. A figure made of magenta light. She crafts
social media content, schedules posts, tracks engagement,
finds trends. She speaks the language of the internet.

Agent 5: VIGIA. A figure made of red light. He monitors
everything: servers, security, anomalies. He never blinks.
He never sleeps. He is the guardian.

Daniela stands at the center, coordinating all five agents.
She is the conductor of this digital orchestra. Each agent
reports to her. She reports to you.

Together, they form the aig Agent Squad. 24/7. No breaks.
No salary. Just results.

The five agents merge into a single beam of light that forms
the aig logo.
""",
        cast=["Daniela", "Agent Correo (blue)", "Agent Calendario (gold)", "Agent Documentos (green)", "Agent Redes (magenta)", "Agent Vigia (red)"],
        locations=["aig digital core (abstract dark space with neon grid)"],
        props=["Email flow visualizations", "Calendar timeline", "Document streams", "Social media feed", "Security monitors", "aig logo"],
        veo_prompts=[
            {
                "scene": 1,
                "description": "Agents power up in sequence",
                "prompt": (
                    "Dark abstract space with a neon grid floor. Five humanoid figures "
                    "made of colored light power up one by one in sequence: blue, gold, "
                    "green, magenta, red. Each figure materializes from particles. "
                    "Camera: slow 360-degree orbit around the forming squad. "
                    "Mood: epic, assembling, powerful."
                ),
                "duration": "8s",
                "audio": "Power-up sounds, electronic build, each agent gets a tone"
            },
            {
                "scene": 2,
                "description": "Agent Correo in action",
                "prompt": (
                    "A blue glowing figure processes email flows. Emails fly past as "
                    "streams of light. Red flags, green checks, trash icons appear "
                    "instantly. The figure moves at superhuman speed. "
                    "Camera: dynamic tracking shot following email streams. "
                    "Mood: fast, precise, efficient."
                ),
                "duration": "6s",
                "audio": "Rapid processing sounds, email notification chimes"
            },
            {
                "scene": 3,
                "description": "Daniela coordinates",
                "prompt": (
                    "@Daniela stands at the center of the five agents. Glowing connection "
                    "lines link her to each agent. She gestures and the agents respond. "
                    "She is the conductor of this digital orchestra. "
                    "Camera: low angle hero shot looking up at Daniela. "
                    "Mood: commanding, epic, powerful."
                ),
                "duration": "8s",
                "audio": "Orchestral electronic music, commanding"
            },
            {
                "scene": 4,
                "description": "Agents merge into logo",
                "prompt": (
                    "The five agents (blue, gold, green, magenta, red) fly toward the "
                    "center and merge into a single brilliant beam of light. The beam "
                    "forms the aig hexagonal logo with circuit patterns. "
                    "Cyan and magenta glow. Camera: dramatic zoom into the merge. "
                    "Mood: climactic, unified, epic."
                ),
                "duration": "6s",
                "audio": "Building crescendo, merge sound, final chord"
            }
        ],
        nano_banana_prompts=[
            {
                "purpose": "Agent character designs",
                "prompt": "Five humanoid AI agent characters standing in formation on a neon grid floor. Each made of a different colored light: blue, gold, green, magenta, red. Abstract digital space. A woman in a dark suit with cyan/magenta accents stands at the center. Epic, sci-fi, photorealistic."
            }
        ],
        notes=(
            "Use '3D Animated' style in Storyboard Studio. "
            "Each agent should be created as a separate ingredient for consistency. "
            "The merge scene (Scene 4) works best with Veo 3.1's particle effects. "
            "Perfect for a 60-second YouTube Short or TikTok."
        )
    )

    SCRIPT_5_TUTORIAL_EPIC = StoryboardScript(
        id="flow_tutorial_epic",
        title="Tu Primera Semana con aig: Un Viaje Epico",
        style="Cinematic Photorealistic",
        story_text="""Day 1: A nervous entrepreneur named Laura opens aig
for the first time. The dashboard is overwhelming. Daniela
appears as a holographic guide. "Don't worry. I'll walk you
through this." Daniela guides Laura to set up her first agent:
Email. Laura connects her Gmail. Within 30 seconds, 47 emails
are processed. Laura's eyes go wide.

Day 2: Laura adds the Calendar agent. Daniela shows her how
the agent found 3 scheduling conflicts and resolved them all.
Laura's calendar is clean for the first time in months.

Day 3: Laura activates the Documents agent. She watches in
amazement as it generates a full sales report from raw data
in under a minute. "This would have taken me 2 hours,"
Laura whispers.

Day 5: Laura has 5 agents running. She sits in her office,
relaxed, while the agents work around her. Holographic
panels show: emails managed, calendar optimized, reports
generated, social media scheduled, security monitored.

Daniela appears beside Laura. "This is your first week.
Imagine a year." Laura smiles. The camera pulls back to
show the city below, the neon office above, and the
aig logo glowing in the night sky.
""",
        cast=["Daniela", "Laura (entrepreneur)"],
        locations=["Laura's office (Day 1: messy, Day 5: clean)", "aig dashboard interior"],
        props=["Laptop with aig", "Email panel", "Calendar panel", "Report panel", "5 floating agent indicators"],
        veo_prompts=[
            {
                "scene": 1,
                "description": "Day 1 - Laura nervous, Daniela appears",
                "prompt": (
                    "A young woman sits nervously at a laptop showing a complex dashboard. "
                    "@Daniela appears as a holographic figure beside the screen, smiling "
                    "reassuringly. She points at the interface. The first agent card "
                    "glows: 'Email Agent'. Camera: over-shoulder shot of laptop. "
                    "Mood: nervous then reassured."
                ),
                "duration": "8s",
                "audio": "Soft electronic ambience, Daniela: 'Don't worry. I'll walk you through this.'"
            },
            {
                "scene": 2,
                "description": "Day 1 - First email processing",
                "prompt": (
                    "Close-up of the laptop screen. Gmail connects to aig. "
                    "47 emails flow through a processing pipeline. Red flags, green "
                    "checks, trash icons appear rapidly. Counter shows 0 remaining. "
                    "Laura's face reflects in the screen, eyes wide with amazement. "
                    "Camera: screen to face reaction shot. "
                    "Mood: revelation, excitement."
                ),
                "duration": "6s",
                "audio": "Processing sounds, completion chime, gasp"
            },
            {
                "scene": 3,
                "description": "Day 3 - Report generation",
                "prompt": (
                    "@Daniela stands beside Laura at the laptop. A documents agent pulls "
                    "data streams from 5 floating source icons. Charts auto-generate. "
                    "A full report compiles on screen in under 60 seconds. Laura whispers "
                    "in amazement. Camera: dynamic close-up of the report forming. "
                    "Mood: wonder, disbelief, satisfaction."
                ),
                "duration": "8s",
                "audio": "Data sounds, chart building, Laura: 'This would have taken me 2 hours.'"
            },
            {
                "scene": 4,
                "description": "Day 5 - 5 agents running",
                "prompt": (
                    "Laura sits relaxed in her now-clean office. Five holographic agent "
                    "indicators float around her: blue (email), gold (calendar), green "
                    "(documents), magenta (social), red (security). All showing green "
                    "status. She sips coffee calmly. Camera: wide slow pan around her. "
                    "Mood: peaceful, accomplished, empowered."
                ),
                "duration": "8s",
                "audio": "Calm ambient music, soft agent status sounds"
            },
            {
                "scene": 5,
                "description": "Daniela's promise",
                "prompt": (
                    "@Daniela appears beside Laura. They look out the window at the neon "
                    "city. Daniela smiles. Camera pulls back through the window, rising "
                    "above the city. The aig logo glows in the night sky. "
                    "Camera: dramatic crane shot rising above the city. "
                    "Mood: epic, promising, limitless."
                ),
                "duration": "8s",
                "audio": "Daniela: 'This is your first week. Imagine a year.' Epic orchestral finale."
            }
        ],
        notes=(
            "Best tutorial format for YouTube. 3-5 min long-form. "
            "The day-by-day structure maps perfectly to Storyboard Studio's "
            "auto-scene detection. "
            "Use 'Cinematic Photorealistic' style. "
            "Laura represents the target user - relatable, amazed, empowered."
        )
    )

    @classmethod
    def get_all_scripts(cls) -> list[StoryboardScript]:

        return [
            cls.SCRIPT_1_LAUNCH,
            cls.SCRIPT_2_DANIELA_DAY,
            cls.SCRIPT_3_BEFORE_AFTER,
            cls.SCRIPT_4_AGENT_SQUAD,
            cls.SCRIPT_5_TUTORIAL_EPIC,
        ]

# ============================================================================
# EPIC IDEAS - 10 Content Concepts for Flow + Storyboard Studio
# ============================================================================

class EpicFlowIdeas:
    """10 epic content ideas specifically designed for Google Flow + Storyboard Studio."""

    IDEAS = [
        {
            "id": "epic_01",
            "title": "Serie Web 'Las Crónicas de Daniela' (6 episodios)",
            "concept": (
                "Mini-series cinematográfica de 6 episodios donde Daniela resuelve "
                "un reto de gestión empresarial diferente en cada uno. "
                "Episodio 1: Startup en caos. Episodio 2: Empresa familiar estancada. "
                "Episodio 3: E-commerce que no escala. Episodio 4: Agencia saturada. "
                "Episodio 5: Corporación burocrática. Episodio 6: Negocio en crisis."
            ),
            "flow_tools": ["Storyboard Studio (script completo)", "Veo 3.1 (cada escena)", "Nano Banana (frames clave)", "Type Overlays (títulos)", "Shader Effects (look ciberpunk)"],
            "storyboard_style": "Cinematic Photorealistic",
            "format": "YouTube long-form, 3-5 min por episodio",
            "ingredient_lock": "Daniela + aig Office + Dashboard",
            "veo_scenes_per_episode": "5-7 scenes x 8s = 40-56s video base",
            "estimated_credits": "350-490 credits per episode (Veo) + free Nano Banana frames",
            "why_epic": "Contenido serial que construye audiencia recurrente. Cada episodio es un caso de uso real de aig.",
        },
        {
            "id": "epic_02",
            "title": "'Daniela vs el Caos' - Shorts Virales Semanales",
            "concept": (
                "Serie de YouTube Shorts (60s) donde Daniela se enfrenta a un tipo "
                "diferente de caos empresarial cada semana. Tono dinámico, humorístico, "
                "con un giro épico al final. "
                "Ej: 'Daniela vs 200 emails sin leer', 'Daniela vs calendario imposible', "
                "'Daniela vs reporte de 500 páginas', 'Daniela vs crash del servidor'."
            ),
            "flow_tools": ["Storyboard Studio", "Veo 3.1 (4-6 scenes x 8s)", "pixelBento (efecto glitch en transiciones)", "Type Overlays (textos virales)"],
            "storyboard_style": "3D Animated",
            "format": "YouTube Shorts + TikTok + IG Reels (60s)",
            "ingredient_lock": "Daniela + Dashboard",
            "veo_scenes_per_episode": "6 scenes x 8s = 48s (perfecto para Short)",
            "estimated_credits": "300 credits per Short (Veo)",
            "why_epic": "Formato viral perfecto. El 'vs' genera expectativa. Fácil de producir en batch semanal.",
        },
        {
            "id": "epic_03",
            "title": "'El Tour de aig' - Recorrido Virtual Cinematográfico",
            "concept": (
                "Video de 5 minutos que lleva al espectador en un tour cinematográfico "
                "por el 'universo aig'. Empieza en la ciudad ciberpunk, sube al "
                "edificio de oficinas, entra al despacho de Daniela, explora el "
                "dashboard holográfico en detalle, muestra los 5 agentes en acción, "
                "y termina con vista aérea de la ciudad con el logo brillando."
            ),
            "flow_tools": ["Storyboard Studio (tour script)", "Veo 3.1 (scenic shots)", "Nano Banana (keyframes del tour)", "Scout360 (vista 360 de la oficina)", "Video Resizer (multi-formato)"],
            "storyboard_style": "Cinematic Photorealistic",
            "format": "YouTube long-form (5 min) + teaser Short (60s)",
            "ingredient_lock": "Daniela + Office + Dashboard + City",
            "veo_scenes_per_episode": "10 scenes x 8s = 80s base, extend con Repeat",
            "estimated_credits": "500-800 credits",
            "why_epic": "Funciona como video de presentación principal del producto. Evergreen. Se puede reutilizar como intro en todos los canales.",
        },
        {
            "id": "epic_04",
            "title": "'Conversación con Daniela' - Serie de Diálogos con IA",
            "concept": (
                "Serie donde el fundador/CEO 'conversa' con Daniela sobre temas de "
                "gestión. Daniela responde con datos, análisis, y recomendaciones. "
                "Cada episodio trata un tema: '¿Debería contratar?', '¿Cómo optimizar "
                "margen?', '¿Qué automatizar primero?', '¿IA en marketing?'. "
                "Tono: ejecutivo, profesional, insightful."
            ),
            "flow_tools": ["Storyboard Studio (diálogo script)", "Veo 3.1 (conversación shots)", "Character X-ray (backstory Daniela)", "Gemini Omni (edición natural del diálogo)"],
            "storyboard_style": "Cinematic Photorealistic",
            "format": "YouTube long-form (3-5 min) + podcast audio",
            "ingredient_lock": "Daniela + Office + Dashboard (with data visualizations)",
            "veo_scenes_per_episode": "4-6 scenes x 8s = 32-48s video base",
            "estimated_credits": "250-400 credits per episode",
            "why_epic": "Posiciona a aig como thought leader. El formato conversacional es el más efectivo para B2B. Genera confianza.",
        },
        {
            "id": "epic_05",
            "title": "'Antes y Después' - Transformaciones Épicas",
            "concept": (
                "Serie de videos que muestran transformaciones dramáticas de negocios "
                "antes y después de aig. Cada episodio es un caso real (anonimizado). "
                "Técnica de split screen: izquierda caos, derecha orden. "
                "La transformación visual es la estrella del contenido."
            ),
            "flow_tools": ["Storyboard Studio (split screen script)", "Veo 3.1 (generar L y R por separado)", "Mockup (escenarios de oficina)", "Shader Effects (diferenciar tonos L vs R)"],
            "storyboard_style": "Cinematic Photorealistic",
            "format": "YouTube long-form (5 min) + Shorts condensados (60s)",
            "ingredient_lock": "Daniela + Dashboard + Office (before/after variants)",
            "veo_scenes_per_episode": "7 scenes x 8s = 56s por side = 112s total",
            "estimated_credits": "700-800 credits per episode",
            "why_epic": "El contenido de transformación es el más viral en B2B. El contraste visual es imposible de scroll-past.",
        },
        {
            "id": "epic_06",
            "title": "'Backstage aig' - Cómo Funciona Realmente",
            "concept": (
                "Serie que muestra el 'detrás de escena' de aig. Cómo los agentes "
                "procesan datos, cómo Daniela toma decisiones, cómo fluye la información "
                "entre módulos. Visualización cinematográfica de procesos técnicos "
                "que normalmente son invisibles."
            ),
            "flow_tools": ["Storyboard Studio (technical script)", "Veo 3.1 (data flow visualization)", "Grid Architect (grid de procesos)", "Shader Effects (efectos de datos)", "Converge (sketch to render)"],
            "storyboard_style": "3D Animated",
            "format": "YouTube long-form (5-8 min)",
            "ingredient_lock": "Daniela + Dashboard + Agent characters",
            "veo_scenes_per_episode": "8-10 scenes x 8s = 64-80s base",
            "estimated_credits": "500-650 credits per episode",
            "why_epic": "Transparencia genera confianza. Mostrar cómo funciona por dentro es diferenciador vs competencia opaca.",
        },
        {
            "id": "epic_07",
            "title": "'El Futuro del Trabajo' - Serie Documental IA",
            "concept": (
                "Mini-documental de 3 partes sobre cómo la IA está transformando la "
                "gestión empresarial. Parte 1: El problema (trabajo manual ineficiente). "
                "Parte 2: La solución (IA en gestión). Parte 3: El futuro (coexistencia "
                "humano-IA). Daniela como narradora-presentadora."
            ),
            "flow_tools": ["Storyboard Studio (documental script)", "Veo 3.1 (todas las escenas)", "Nano Banana (imágenes documentales)", "Character X-ray (desarrollo de Daniela)", "Scout360 (entornos 360)"],
            "storyboard_style": "Cinematic Photorealistic",
            "format": "YouTube long-form (8-10 min por parte) = 30 min total",
            "ingredient_lock": "Daniela + Office + Dashboard + City + abstract data spaces",
            "veo_scenes_per_episode": "12-15 scenes x 8s por parte = ~100s base",
            "estimated_credits": "600-750 credits per parte",
            "why_epic": "Posicionamiento como líder de pensamiento. Formato documental = autoridad. 30 min de contenido evergreen.",
        },
        {
            "id": "epic_08",
            "title": "'Retos con Daniela' - Serie Interactiva",
            "concept": (
                "Serie donde la audiencia propone retos de gestión en comentarios "
                "y Daniela los resuelve en el siguiente episodio. Ej: 'Daniela, "
                "mi equipo pierde 4 horas en reuniones, ¿qué hago?' → episodio "
                "donde Daniela analiza, diagnostica, y ejecuta la solución."
            ),
            "flow_tools": ["Storyboard Studio (community-driven script)", "Veo 3.1 (solution visualization)", "Type Overlays (comentarios reales)", "Gemini Omni (edición iterativa)"],
            "storyboard_style": "Cinematic Photorealistic",
            "format": "YouTube long-form (3-5 min) + Shorts teasers",
            "ingredient_lock": "Daniela + Dashboard + Office",
            "veo_scenes_per_episode": "5-7 scenes x 8s = 40-56s base",
            "estimated_credits": "300-450 credits per episode",
            "why_epic": "Contenido generado por la comunidad = engagement máximo. Cada comentario es idea para un episodio. Loop virtuoso de contenido.",
        },
        {
            "id": "epic_09",
            "title": "'aig Universe' - Mundo Expandible",
            "concept": (
                "Construir un universo narrativo expandible tipo Marvel: Daniela "
                "como personaje central, los 5 agentes como secundarios, la ciudad "
                "ciberpunk como mundo, futuros productos como nuevas historias. "
                "Cada pieza de contenido existe dentro del mismo universo. "
                "Genera continuidad, lore, y fandom."
            ),
            "flow_tools": ["Storyboard Studio (master universe bible)", "Veo 3.1 (todas las historias)", "Character X-ray (todos los personajes)", "Nano Banana (concept art)", "Mockup (nuevos escenarios)"],
            "storyboard_style": "Mixed (Cinematic + 3D Animated)",
            "format": "Multi-formato: Shorts, long-form, carousel, todo conectado",
            "ingredient_lock": "Daniela + 5 Agents + Office + City + Dashboard",
            "veo_scenes_per_episode": "Variable",
            "estimated_credits": "1000-2000 credits/month for full universe",
            "why_epic": "El universo es el activo más valioso. Marvel, Star Wars, lo demuestran. aig puede ser el primer universo IA de gestión empresarial.",
        },
        {
            "id": "epic_10",
            "title": "'Spot de Super Bowl' - El Comercial Definitivo",
            "concept": (
                "Producir el comercial más épico posible para aig: 60 segundos "
                "cinematográficos que cuenten la historia completa: problema → "
                "Daniela → transformación → resultado → logo. Calidad de Super Bowl. "
                "Usar las mejores herramientas de Flow: Veo 3.1 Quality mode, "
                "Nano Banana Pro para keyframes, Shader Effects para polish, "
                "Type Overlays para textos finales."
            ),
            "flow_tools": ["Storyboard Studio (script de 60s)", "Veo 3.1 Quality (máxima calidad)", "Nano Banana Pro (keyframes)", "Shader Effects (polish final)", "Type Overlays (títulos y CTA)", "Video Resizer (multi-formato: 16:9 + 9:16 + 1:1)"],
            "storyboard_style": "Cinematic Photorealistic",
            "format": "60s comercial multi-plataforma (YouTube, IG, TV, web)",
            "ingredient_lock": "Daniela + Office + Dashboard + City + Logo",
            "veo_scenes_per_episode": "8 scenes x 8s = 64s (perfect 60s after trim)",
            "estimated_credits": "500-600 credits (Quality mode = more credits per clip)",
            "why_epic": "Un comercial de calidad Super Bowl posiciona la marca como premium. Evergreen, reutilizable en todos los canales. Inversión única, retorno perpetuo.",
        },
    ]

    @classmethod
    def get_idea(cls, idea_id: str) -> dict | None:

        for idea in cls.IDEAS:
            if idea["id"] == idea_id:
                return idea
        return None

    @classmethod
    def export_json(cls, output_path: str = None) -> str:

        path = output_path or str(BASE_DIR / "static" / "brand" / "flow_epic_ideas.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cls.IDEAS, f, ensure_ascii=False, indent=2)
        return path

# ============================================================================
# FLOW WORKFLOW GUIDE
# ============================================================================

class FlowWorkflowGuide:
    """Step-by-step guide for using Google Flow + Storyboard Studio for aig."""

    SETUP_STEPS = [
        {
            "step": 1,
            "title": "Crear cuenta en Google Flow",
            "url": "https://flow.google.com",
            "action": "Ir a flow.google.com y hacer clic en Get Started",
            "note": "Necesitas cuenta de Google. Free tier: 50 credits/dia.",
        },
        {
            "step": 2,
            "title": "Crear nuevo proyecto",
            "action": "Dashboard > New Project",
            "note": "Nombrar el proyecto: 'aig - [nombre del contenido]'",
        },
        {
            "step": 3,
            "title": "Definir Ingredients (referencias de consistencia)",
            "action": "Media > Characters > Add Character > Generate with Nano Banana",
            "note": (
                "Pegar el prompt de DANIELA_INGREDIENT.nano_banana_prompt. "
                "Generar la imagen. Verificar que se vea como Daniela. "
                "Repetir para aig Office y Dashboard. "
                "Estos 3 ingredients locked = consistencia en todas las escenas."
            ),
        },
        {
            "step": 4,
            "title": "Abrir Storyboard Studio",
            "action": "Tools > Storyboard Studio > Get Started",
            "note": "Seleccionar estilo: 'Cinematic Photorealistic' o '3D Animated' segun el script.",
        },
        {
            "step": 5,
            "title": "Pegar el script",
            "action": "Paste story_text del StoryboardScript elegido",
            "note": (
                "Storyboard Studio analizara el texto y: "
                "- Generara titulo automatico "
                "- Dividira en escenas "
                "- Creara dialogos "
                "- Detectara personajes, localizaciones, props"
            ),
        },
        {
            "step": 6,
            "title": "Autofill Details",
            "action": "Assets > Autofill Details",
            "note": "Genera descripciones detalladas de cada personaje, localizacion y prop. Editar manualmente si es necesario.",
        },
        {
            "step": 7,
            "title": "Generar storyboard panels",
            "action": "Storyboard > Generate Panels",
            "note": "Cada escena se convierte en un panel visual con camera shot sugerido. Editar angulos si es necesario.",
        },
        {
            "step": 8,
            "title": "Generar videos con Veo 3.1",
            "action": "Para cada panel: usar el veo_prompts correspondiente",
            "note": (
                "Pegar el prompt en Veo 3.1. Usar @Daniela para mantener consistencia. "
                "Seleccionar duracion (4s/6s/8s). "
                "Veo genera video + audio nativo. "
                "Free tier: Veo 3.1 Lite. "
                "Pro tier: Veo 3.1 Quality para maxima calidad."
            ),
        },
        {
            "step": 9,
            "title": "Ensamblar en Scenebuilder",
            "action": "Scenebuilder > arrastrar clips al timeline",
            "note": (
                "Ordenar clips segun el storyboard. "
                "Trim, reorder, ajustar transiciones. "
                "Usar Gemini para edicion natural: "
                "'change lighting to golden hour' "
                "'slow down camera movement'"
            ),
        },
        {
            "step": 10,
            "title": "Exportar y publicar",
            "action": "Export > MP4 (1080p o 4K)",
            "note": (
                "Usar Video Resizer para multi-formato: "
                "- 16:9 para YouTube long-form "
                "- 9:16 para Shorts/TikTok/Reels "
                "- 1:1 para feed "
                "Guardar proyecto como JSON para futuras ediciones."
            ),
        },
    ]

    CREDIT_BUDGET = {
        "free_tier": {
            "daily_credits": 50,
            "veo_lite_8s": 8,
            "veo_fast_8s": 12,
            "veo_quality_8s": 25,
            "nano_banana": 0,
            "gemini_omni_720p": 15,
            "gemini_omni_360p": 8,
            "daily_veo_clips_lite": "6 clips (50/8)",
            "daily_veo_clips_quality": "2 clips (50/25)",
            "monthly_free_clips": "~180 clips (Veo Lite)",
        },
        "pro_tier": {
            "monthly_credits": 1000,
            "daily_bonus": 50,
            "total_monthly": 1050,
            "monthly_veo_clips_lite": "~131 clips",
            "monthly_veo_clips_quality": "~42 clips",
            "cost": "$19.99/mes",
        },
        "ultra_tier": {
            "monthly_credits": 10000,

            "daily_bonus": 50,
            "total_monthly": 10050,
            "monthly_veo_clips_lite": "~1256 clips",
            "monthly_veo_clips_quality": "~402 clips",
            "cost": "$99.99/mes",
            "extras": ["4K upscaling", "highest limits", "20TB storage"],
        },
        "strategy_free": (
            "Con free tier (50/dia = ~180 clips/mes Veo Lite): "
            "- 2 episodios semanales de 6 clips cada uno = 12 clips/semana = 48 clips/mes "
            "- Sobran ~130 clips para experimentacion y iteration "
            "- Nano Banana (imagenes) es GRATIS, ilimitado "
            "- Usar Nano Banana para storyboard frames, thumbnails, social posts"
        ),
    }

    @classmethod
    def export_guide_json(cls, output_path: str = None) -> str:

        path = output_path or str(BASE_DIR / "static" / "brand" / "flow_workflow_guide.json")
        data = {
            "setup_steps": cls.SETUP_STEPS,
            "credit_budget": cls.CREDIT_BUDGET,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

# ============================================================================
# CLI
# ============================================================================

def print_status():
    print("=" * 70)
    print("  aig Flow Studio - Google Flow + Storyboard Studio")
    print("=" * 70)
    print()

    print("INGREDIENTS (character consistency):")
    for ing in ALL_INGREDIENTS:
        print(f"  - {ing.name}: {ing.description[:60]}...")
    print()

    print("STORYBOARD SCRIPTS:")
    for script in StoryboardScripts.get_all_scripts():
        print(f"  - [{script.style}] {script.title}")
        print(f"    Cast: {', '.join(script.cast)}")
        print(f"    Veo scenes: {len(script.veo_prompts)} | Nano Banana: {len(script.nano_banana_prompts)}")
    print()

    print("EPIC IDEAS (10):")
    for idea in EpicFlowIdeas.IDEAS:
        print(f"  - [{idea['id']}] {idea['title']}")
        print(f"    Format: {idea['format']}")
        print(f"    Credits: {idea['estimated_credits']}")
    print()

    print("FREE TIER STRATEGY:")
    print(f"  {FlowWorkflowGuide.CREDIT_BUDGET['strategy_free']}")
    print()

    print("WORKFLOW: 10 steps from setup to publish")
    for step in FlowWorkflowGuide.SETUP_STEPS:
        print(f"  {step['step']}. {step['title']}")
    print()

    print("FILES:")
    print("  flow_studio_aig.py (this module)")
    print("  static/brand/flow_epic_ideas.json")
    print("  static/brand/flow_workflow_guide.json")
    print()
    print("=" * 70)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print_status()
    elif sys.argv[1] == "ideas":
        EpicFlowIdeas.export_json()
        print("Exported 10 epic ideas to static/brand/flow_epic_ideas.json")
    elif sys.argv[1] == "guide":
        FlowWorkflowGuide.export_guide_json()
        print("Exported workflow guide to static/brand/flow_workflow_guide.json")
    elif sys.argv[1] == "scripts":
        scripts_data = []
        for s in StoryboardScripts.get_all_scripts():
            scripts_data.append({
                "id": s.id,
                "title": s.title,
                "style": s.style,
                "story_text": s.story_text,
                "cast": s.cast,
                "locations": s.locations,
                "props": s.props,
                "veo_prompts": s.veo_prompts,
                "nano_banana_prompts": s.nano_banana_prompts,
                "notes": s.notes,
            })
        path = str(BASE_DIR / "static" / "brand" / "flow_storyboard_scripts.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(scripts_data, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(scripts_data)} storyboard scripts to {path}")
    else:
        print_status()
