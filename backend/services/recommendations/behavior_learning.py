"""Conservative Phase 17 behavior-learning signals.

The recommendation engine records Save, Made, and Skip actions. This module
turns those events into small, explainable ranking adjustments without hiding
whole food groups or creating a filter bubble.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import re
from typing import Any, Dict, Iterable, Mapping

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP = {
    "recipe", "recipes", "easy", "best", "homemade", "with", "and", "the",
    "a", "an", "of", "for", "style", "classic", "simple", "quick",
}
POSITIVE = {"made": 2.0, "saved": 1.0}
NEGATIVE = {"skipped": -1.25, "not_used": -1.25, "disliked": -2.0}


def _tokens(value: Any) -> set[str]:
    return {t for t in TOKEN_RE.findall(str(value or "").lower()) if len(t) > 2 and t not in STOP}


def _parse_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def build_behavior_profile(actions: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    exact = defaultdict(float)
    token_scores: Counter[str] = Counter()
    made_dates: Dict[str, datetime] = {}
    counts: Counter[str] = Counter()

    for row in actions or []:
        action = str(row.get("action") or "").lower().strip()
        weight = POSITIVE.get(action, NEGATIVE.get(action, 0.0))
        if not weight:
            continue
        counts[action] += 1
        rid = str(row.get("recipe_id") or "").strip()
        name = str(row.get("recipe_name") or "").strip()
        key = rid or name.lower()
        if key:
            exact[key] += weight
        for token in _tokens(name):
            # Token preferences are deliberately weaker than exact-recipe signals.
            token_scores[token] += weight * 0.35
        if action == "made" and key:
            created = _parse_date(row.get("created_at"))
            if created and (key not in made_dates or created > made_dates[key]):
                made_dates[key] = created

    return {
        "exact_scores": dict(exact),
        "token_scores": dict(token_scores),
        "last_made": made_dates,
        "action_counts": dict(counts),
        "action_count": sum(counts.values()),
    }


def score_behavior(candidate: Mapping[str, Any], profile: Mapping[str, Any] | None) -> tuple[float, Dict[str, Any]]:
    actions = list((profile or {}).get("_behavior_actions") or [])
    learned = build_behavior_profile(actions)
    rid = str(candidate.get("recipe_id") or "").strip()
    name = str(candidate.get("recipe_name") or "").strip()
    key = rid or name.lower()

    exact_raw = float(learned["exact_scores"].get(key, 0.0))
    token_raw = sum(float(learned["token_scores"].get(t, 0.0)) for t in _tokens(name))
    token_raw = max(-2.0, min(2.0, token_raw))

    fatigue_penalty = 0.0
    last_made = learned["last_made"].get(key)
    days_since_made = None
    if last_made:
        days_since_made = max(0, (datetime.now(timezone.utc) - last_made).days)
        if days_since_made <= 7:
            fatigue_penalty = 4.0
        elif days_since_made <= 21:
            fatigue_penalty = 2.5
        elif days_since_made <= 45:
            fatigue_penalty = 1.0

    # Neutral starts in the middle. Behavior may move the score, but only by a
    # few points so pantry evidence and safety remain dominant.
    points = 5.0 + max(-3.0, min(3.0, exact_raw)) + token_raw - fatigue_penalty
    points = round(max(0.0, min(10.0, points)), 1)

    reasons = []
    if exact_raw > 0:
        reasons.append("Positive history with this recipe")
    elif exact_raw < 0:
        reasons.append("Previously skipped or disliked")
    if token_raw >= 0.75:
        reasons.append("Similar to recipes previously saved or made")
    elif token_raw <= -0.75:
        reasons.append("Similar to recipes frequently skipped")
    if fatigue_penalty:
        reasons.append("Recently made, so repeat priority was reduced")
    if not reasons:
        reasons.append("No strong behavior signal yet")

    return points, {
        "action_count": learned["action_count"],
        "exact_signal": round(exact_raw, 2),
        "similar_recipe_signal": round(token_raw, 2),
        "fatigue_penalty": fatigue_penalty,
        "days_since_last_made": days_since_made,
        "explanations": reasons,
    }
