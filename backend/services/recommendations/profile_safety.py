"""Hard profile safety filtering for the rebuilt recommendation engine.

Safety rules run before pantry eligibility, expiration discovery, Nutrition Fit,
preferences, or Smart Score. A recipe that conflicts with an allergy, avoided
food, or dietary restriction is excluded rather than merely penalized.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from .ingredient_normalizer import normalize_ingredient
from .recipe_repository import RecipeRecord

_SPLIT_RE = re.compile(r"[,;|/\n]+")
_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class SafetyDecision:
    safe: bool
    reasons: Tuple[str, ...]
    matched_terms: Tuple[str, ...]


@dataclass(frozen=True)
class ProfileSafetyRules:
    allergies: Tuple[str, ...]
    avoided_foods: Tuple[str, ...]
    restrictions: Tuple[str, ...]


# Ingredient groups are explicit so broad substring matching is avoided.
ALLERGEN_GROUPS: Mapping[str, Set[str]] = {
    "peanut": {"peanut", "peanut butter", "peanut flour", "groundnut"},
    "tree nut": {
        "almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut",
        "macadamia", "brazil nut", "pine nut", "chestnut", "marzipan",
    },
    "dairy": {
        "milk", "butter", "cheese", "cream", "yogurt", "whey", "casein",
        "ghee", "buttermilk", "sour cream", "cream cheese", "mozzarella",
        "cheddar", "parmesan", "ricotta", "feta",
    },
    "egg": {"egg", "egg white", "egg yolk", "mayonnaise"},
    "soy": {"soy", "soybean", "tofu", "tempeh", "edamame", "miso", "soy sauce"},
    "wheat": {"wheat", "wheat flour", "all purpose flour", "bread", "pasta", "couscous", "bulgur", "seitan"},
    "gluten": {
        "wheat", "wheat flour", "all purpose flour", "barley", "rye", "malt",
        "bread", "pasta", "couscous", "bulgur", "seitan", "breadcrumb",
    },
    "fish": {
        "fish", "salmon", "tuna", "cod", "tilapia", "trout", "halibut",
        "sardine", "anchovy", "mackerel", "haddock", "swordfish",
    },
    "shellfish": {
        "shrimp", "prawn", "crab", "lobster", "crayfish", "scallop", "clam",
        "mussel", "oyster", "squid", "octopus",
    },
    "sesame": {"sesame", "sesame seed", "sesame oil", "tahini"},
}

MEAT_TERMS = {
    "beef", "steak", "ground beef", "veal", "lamb", "mutton", "pork", "ham",
    "bacon", "sausage", "prosciutto", "pepperoni", "salami", "chorizo",
    "chicken", "chicken breast", "chicken thigh", "turkey", "duck", "goose",
    "venison", "rabbit", "gelatin", "lard",
}

POULTRY_TERMS = {"chicken", "chicken breast", "chicken thigh", "turkey", "duck", "goose"}
PORK_TERMS = {"pork", "ham", "bacon", "prosciutto", "pepperoni", "salami", "chorizo", "pancetta", "lard"}
FISH_TERMS = ALLERGEN_GROUPS["fish"]
SHELLFISH_TERMS = ALLERGEN_GROUPS["shellfish"]
ANIMAL_SEAFOOD_TERMS = MEAT_TERMS | FISH_TERMS | SHELLFISH_TERMS
DAIRY_TERMS = ALLERGEN_GROUPS["dairy"]
EGG_TERMS = ALLERGEN_GROUPS["egg"]
GLUTEN_TERMS = ALLERGEN_GROUPS["gluten"]
NUT_TERMS = ALLERGEN_GROUPS["tree nut"] | ALLERGEN_GROUPS["peanut"]

RESTRICTION_ALIASES = {
    "vegetarian": "vegetarian",
    "vegetarian diet": "vegetarian",
    "veggie": "vegetarian",
    "vegan": "vegan",
    "plant based": "vegan",
    "plant-based": "vegan",
    "pescatarian": "pescatarian",
    "pescetarian": "pescatarian",
    "gluten free": "gluten_free",
    "gluten-free": "gluten_free",
    "celiac": "gluten_free",
    "dairy free": "dairy_free",
    "dairy-free": "dairy_free",
    "lactose free": "dairy_free",
    "lactose-free": "dairy_free",
    "nut free": "nut_free",
    "nut-free": "nut_free",
    "peanut free": "nut_free",
    "peanut-free": "nut_free",
    "pork free": "pork_free",
    "pork-free": "pork_free",
    "no pork": "pork_free",
    "egg free": "egg_free",
    "egg-free": "egg_free",
    "soy free": "soy_free",
    "soy-free": "soy_free",
    "shellfish free": "shellfish_free",
    "shellfish-free": "shellfish_free",
}


def _clean_phrase(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _split_profile_terms(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = _SPLIT_RE.split(str(value))
    terms: List[str] = []
    for raw in raw_values:
        term = _clean_phrase(raw)
        if term and term not in {"none", "n/a", "na", "no", "null"} and term not in terms:
            terms.append(term)
    return terms


def build_profile_safety_rules(profile: Mapping[str, Any] | None) -> ProfileSafetyRules:
    profile = profile or {}
    allergies = tuple(_split_profile_terms(profile.get("allergies")))
    avoided = tuple(_split_profile_terms(profile.get("avoid_foods")))

    restrictions: List[str] = []
    for term in _split_profile_terms(profile.get("dietary_restrictions")):
        canonical = RESTRICTION_ALIASES.get(term)
        if canonical and canonical not in restrictions:
            restrictions.append(canonical)
    return ProfileSafetyRules(
        allergies=allergies,
        avoided_foods=avoided,
        restrictions=tuple(restrictions),
    )


def _recipe_phrases(recipe: RecipeRecord) -> Set[str]:
    phrases: Set[str] = set()
    values: List[str] = [recipe.recipe_name, recipe.clean_recipe_name, *recipe.main_ingredients]
    for ingredient in recipe.ingredients:
        values.extend([ingredient.food, ingredient.text])
    for value in values:
        normalized = normalize_ingredient(value).canonical
        if normalized:
            phrases.add(normalized)
    return phrases


def _phrase_tokens(phrase: str) -> Set[str]:
    return set(_WORD_RE.findall(phrase.lower()))


def _contains_concept(recipe_phrases: Set[str], concept: str) -> bool:
    target = normalize_ingredient(concept).canonical
    if not target:
        return False
    target_tokens = _phrase_tokens(target)
    for phrase in recipe_phrases:
        phrase_tokens = _phrase_tokens(phrase)
        if phrase == target:
            return True
        # Multi-word concepts may be embedded in a detailed ingredient phrase.
        # Single-token matching still requires a complete token, never substring.
        if target_tokens and target_tokens.issubset(phrase_tokens):
            return True
    return False


def _matches_group(recipe_phrases: Set[str], terms: Iterable[str]) -> bool:
    return any(_contains_concept(recipe_phrases, term) for term in terms)


def _allergy_group(term: str) -> Tuple[str, Set[str]] | None:
    cleaned = _clean_phrase(term)
    aliases = {
        "nuts": "tree nut", "nut": "tree nut", "tree nuts": "tree nut",
        "peanuts": "peanut", "milk": "dairy", "lactose": "dairy",
        "eggs": "egg", "soybean": "soy", "soybeans": "soy",
        "wheat allergy": "wheat", "gluten allergy": "gluten",
        "seafood": "shellfish",
    }
    key = aliases.get(cleaned, cleaned)
    terms = ALLERGEN_GROUPS.get(key)
    return (key, terms) if terms else None


def evaluate_recipe_safety(recipe: RecipeRecord, rules: ProfileSafetyRules) -> SafetyDecision:
    phrases = _recipe_phrases(recipe)
    reasons: List[str] = []
    matched_terms: List[str] = []

    for allergy in rules.allergies:
        group = _allergy_group(allergy)
        if group:
            group_name, terms = group
            if _matches_group(phrases, terms):
                reasons.append(f"Contains a declared allergen: {allergy}")
                matched_terms.append(group_name)
        elif _contains_concept(phrases, allergy):
            reasons.append(f"Contains a declared allergen: {allergy}")
            matched_terms.append(allergy)

    for avoided in rules.avoided_foods:
        if _contains_concept(phrases, avoided):
            reasons.append(f"Contains an avoided food: {avoided}")
            matched_terms.append(avoided)

    restrictions = set(rules.restrictions)
    if "vegetarian" in restrictions and _matches_group(phrases, ANIMAL_SEAFOOD_TERMS):
        reasons.append("Conflicts with vegetarian restriction")
        matched_terms.append("vegetarian")
    if "vegan" in restrictions and (
        _matches_group(phrases, ANIMAL_SEAFOOD_TERMS)
        or _matches_group(phrases, DAIRY_TERMS)
        or _matches_group(phrases, EGG_TERMS)
    ):
        reasons.append("Conflicts with vegan restriction")
        matched_terms.append("vegan")
    if "pescatarian" in restrictions and _matches_group(phrases, MEAT_TERMS):
        reasons.append("Conflicts with pescatarian restriction")
        matched_terms.append("pescatarian")
    if "gluten_free" in restrictions and _matches_group(phrases, GLUTEN_TERMS):
        reasons.append("Conflicts with gluten-free restriction")
        matched_terms.append("gluten_free")
    if "dairy_free" in restrictions and _matches_group(phrases, DAIRY_TERMS):
        reasons.append("Conflicts with dairy-free restriction")
        matched_terms.append("dairy_free")
    if "nut_free" in restrictions and _matches_group(phrases, NUT_TERMS):
        reasons.append("Conflicts with nut-free restriction")
        matched_terms.append("nut_free")
    if "pork_free" in restrictions and _matches_group(phrases, PORK_TERMS):
        reasons.append("Conflicts with pork-free restriction")
        matched_terms.append("pork_free")
    if "egg_free" in restrictions and _matches_group(phrases, EGG_TERMS):
        reasons.append("Conflicts with egg-free restriction")
        matched_terms.append("egg_free")
    if "soy_free" in restrictions and _matches_group(phrases, ALLERGEN_GROUPS["soy"]):
        reasons.append("Conflicts with soy-free restriction")
        matched_terms.append("soy_free")
    if "shellfish_free" in restrictions and _matches_group(phrases, SHELLFISH_TERMS):
        reasons.append("Conflicts with shellfish-free restriction")
        matched_terms.append("shellfish_free")

    # Stable, deduplicated explanations make logs and tests deterministic.
    unique_reasons = tuple(dict.fromkeys(reasons))
    unique_terms = tuple(dict.fromkeys(matched_terms))
    return SafetyDecision(safe=not unique_reasons, reasons=unique_reasons, matched_terms=unique_terms)


def filter_safe_recipes(
    recipes: Sequence[RecipeRecord],
    profile: Mapping[str, Any] | None,
) -> Tuple[List[RecipeRecord], Dict[str, Any]]:
    rules = build_profile_safety_rules(profile)
    safe: List[RecipeRecord] = []
    excluded_reason_counts: Counter[str] = Counter()

    for recipe in recipes:
        decision = evaluate_recipe_safety(recipe, rules)
        if decision.safe:
            safe.append(recipe)
            continue
        for term in decision.matched_terms:
            excluded_reason_counts[term] += 1

    metadata = {
        "profile_safety_applied": True,
        "profile_allergy_terms": list(rules.allergies),
        "profile_avoided_food_terms": list(rules.avoided_foods),
        "profile_dietary_restrictions": list(rules.restrictions),
        "recipes_before_safety_filter": len(recipes),
        "recipes_after_safety_filter": len(safe),
        "recipes_excluded_by_safety": len(recipes) - len(safe),
        "safety_exclusion_counts": dict(sorted(excluded_reason_counts.items())),
    }
    return safe, metadata
