"""
Resume-to-job match scoring for Karan Chandra's profile.

Scoring model (100 pts total → 75 pts = 75% threshold):
  Title match       30 pts  — is this a DS/ML/AI/Applied Scientist role?
  Level match       10 pts  — Senior/Staff/Lead level?
  Core skills       30 pts  — Python, SQL, ML frameworks, cloud, big data
  Domain bonus      20 pts  — fraud/risk/LLM/marketplace alignment
  Penalty           -10 pts — junior/internship/manager role
"""

import re
from config import MATCH_THRESHOLD

# Target role patterns
SENIOR_DS_PATTERNS = [
    # Highest priority — exactly what Karan is targeting
    r"senior data scientist", r"staff data scientist", r"principal data scientist",
    r"lead data scientist", r"senior data science",
]

SENIOR_ROLE_PATTERNS = SENIOR_DS_PATTERNS + [
    r"senior machine learning", r"staff machine learning",
    r"principal machine learning", r"senior ml engineer", r"staff ml engineer",
    r"senior ai engineer", r"staff ai engineer", r"senior applied scientist",
    r"staff applied scientist", r"principal applied scientist",
    r"senior research scientist", r"staff research scientist",
    r"senior applied research", r"staff research engineer",
    r"machine learning engineer", r"ml engineer",
    r"ai engineer", r"applied scientist", r"research scientist",
]

ANY_ROLE_PATTERNS = [
    r"data scientist", r"machine learning", r"ml engineer", r"ai engineer",
    r"applied scientist", r"research scientist", r"mlops", r"ml platform",
    r"data science", r"artificial intelligence",
]

EXCLUDE_PATTERNS = [
    r"\bintern\b", r"\binternship\b", r"\bjunior\b", r"\bentry.?level\b",
    r"\bmanager\b(?!.*individual)", r"\bdirector\b", r"\bvp\b", r"\bvice president\b",
    r"\bhead of\b", r"\bchief\b",
]

# Core skills to look for in job descriptions
CORE_SKILL_CHECKS = {
    "python": 8,
    "sql": 6,
    "machine learning|ml model|ml pipeline": 6,
    r"pytorch|tensorflow|scikit.learn|sklearn|xgboost|gradient boost|lightgbm": 5,
    r"aws|gcp|azure|sagemaker|cloud": 4,
    r"spark|pyspark|bigquery|databricks|hive|hadoop": 4,
    r"llm|large language model|generative ai|gen.?ai|rag|transformer|hugging face": 3,
    r"a/b test|experimentation|hypothesis test|statistical": 3,
    r"mlops|model monitoring|model deployment|feature store|model registry": 2,
    r"feature engineering|feature selection": 2,
    r"deep learning|neural network|cnn|rnn|lstm": 2,
}

# Domain bonuses — Karan's strongest domain alignments
DOMAIN_CHECKS = {
    r"fraud|risk|trust.?and.?safety|abuse|anti-fraud": 20,
    r"marketplace|e.?commerce|payments|fintech|financial": 15,
    r"recommendation|personalization|ranking|search": 12,
    r"autonomous|self.?driving|robotics|perception|navigation": 12,
    r"llm|language model|nlp|generative|ai platform|foundation model": 15,
    r"identity|graph|network|entity resolution|knowledge graph": 12,
    r"anomaly detection|outlier|time series|forecasting": 10,
}


def score_job(title: str, description: str) -> dict:
    """
    Score a job posting against the configured resume profile.
    Returns dict with overall_score (0-1), skill_hits, role_match, breakdown.
    """
    t = title.lower()
    d = (title + " " + description).lower()

    # ── 1. Title match (30 pts) ───────────────────────────────────────────
    title_pts = 0
    role_match = False

    # Check exclusions first
    is_excluded = any(re.search(p, t) for p in EXCLUDE_PATTERNS)

    if not is_excluded:
        if any(re.search(p, t) for p in SENIOR_DS_PATTERNS):
            # Bonus: exactly "Senior Data Scientist" — highest priority role
            title_pts = 35
            role_match = True
        elif any(re.search(p, t) for p in SENIOR_ROLE_PATTERNS):
            title_pts = 30
            role_match = True
        elif any(re.search(p, t) for p in ANY_ROLE_PATTERNS):
            title_pts = 20
            role_match = True

    if title_pts == 0:
        # Not a target role at all — return low score immediately
        return {
            "overall_score": 0.0,
            "role_match": False,
            "skill_hits": [],
            "passes_threshold": False,
        }

    # ── 2. Level match (10 pts) ──────────────────────────────────────────
    level_pts = 0
    if re.search(r"\b(senior|staff|principal|lead|sr\.?)\b", t):
        level_pts = 10
    elif re.search(r"\b(ii|iii|iv|2|3)\b", t):
        level_pts = 5
    else:
        level_pts = 3  # IC level, no explicit senior required

    # ── 3. Core skills (30 pts max) ─────────────────────────────────────
    skill_pts = 0
    skill_hits = []
    for pattern, pts in CORE_SKILL_CHECKS.items():
        if re.search(pattern, d):
            skill_pts += pts
            # Record a clean skill name for display
            skill_hits.append(pattern.split("|")[0].replace(r"\b", "").strip())
    skill_pts = min(skill_pts, 30)

    # ── 4. Domain bonus (20 pts max) ─────────────────────────────────────
    domain_pts = 0
    for pattern, pts in DOMAIN_CHECKS.items():
        if re.search(pattern, d):
            domain_pts = max(domain_pts, pts)  # take highest matching domain

    # ── Total ────────────────────────────────────────────────────────────
    raw = title_pts + level_pts + skill_pts + domain_pts
    # 100 pts max: 30 + 10 + 30 + 20 = 90... cap at 100
    overall = min(raw / 90.0, 1.0)

    return {
        "overall_score": round(overall, 3),
        "role_match": role_match,
        "skill_hits": list(dict.fromkeys(skill_hits))[:10],
        "passes_threshold": overall >= MATCH_THRESHOLD,
        "debug": {"title_pts": title_pts, "level_pts": level_pts,
                  "skill_pts": skill_pts, "domain_pts": domain_pts},
    }


def format_match_pct(score: float) -> str:
    return f"{round(score * 100)}%"
