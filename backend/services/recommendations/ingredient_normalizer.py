"""Conservative ingredient normalization for pantry-to-recipe comparison.

This module creates one backend vocabulary for pantry and recipe ingredients.
It deliberately avoids ranking, expiration, profile, and nutrition decisions.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Optional, Sequence, Tuple

# Measurement words are removed only when they appear as standalone tokens.
UNITS = {
    "tsp", "teaspoon", "teaspoons", "tbsp", "tablespoon", "tablespoons",
    "cup", "cups", "c", "oz", "ounce", "ounces", "lb", "lbs", "pound",
    "pounds", "g", "gram", "grams", "kg", "kilogram", "kilograms", "ml",
    "milliliter", "milliliters", "l", "liter", "liters", "pinch", "dash",
    "slice", "slices", "piece", "pieces", "clove", "cloves", "can", "cans",
    "jar", "jars", "package", "packages", "packet", "packets", "bunch",
    "bunches", "head", "heads", "stalk", "stalks", "sprig", "sprigs",
}

PREPARATION_WORDS = {
    "fresh", "frozen", "thawed", "cooked", "uncooked", "raw", "diced",
    "chopped", "minced", "sliced", "shredded", "grated", "crushed", "ground",
    "peeled", "seeded", "rinsed", "drained", "trimmed", "divided", "softened",
    "melted", "beaten", "packed", "heaping", "rounded", "finely", "roughly",
    "thinly", "coarsely", "small", "medium", "large", "extra", "optional",
    "to", "taste", "plus", "more", "for", "serving", "garnish",
    "organic", "original", "angus", "premium", "perfect", "portions",
}

# Canonicalization is intentionally explicit. Broad substitutions such as
# "milk" -> any milk or "chicken" -> any chicken product are not performed.
ALIASES = {
    "chicken breasts": "chicken breast",
    "boneless chicken breast": "chicken breast",
    "boneless skinless chicken breast": "chicken breast",
    "skinless chicken breast": "chicken breast",
    "chicken breast fillet": "chicken breast",
    "chicken breast fillets": "chicken breast",
    "chicken thighs": "chicken thigh",
    "boneless chicken thigh": "chicken thigh",
    "boneless skinless chicken thigh": "chicken thigh",
    "skinless chicken thigh": "chicken thigh",
    "eggs": "egg",
    "egg whites": "egg white",
    "egg yolks": "egg yolk",
    "tomatoes": "tomato",
    "roma tomatoes": "roma tomato",
    "cherry tomatoes": "cherry tomato",
    "potatoes": "potato",
    "beef patty": "ground beef",
    "beef patties": "ground beef",
    "ground beef patty": "ground beef",
    "ground beef patties": "ground beef",
    "yukon gold potato": "potato",
    "yukon gold potatoes": "potato",
    "gold potato": "potato",
    "gold potatoes": "potato",
    "russet potato": "potato",
    "russet potatoes": "potato",
    "red potato": "potato",
    "red potatoes": "potato",
    "sweet potatoes": "sweet potato",
    "onions": "onion",
    "red onions": "red onion",
    "green onions": "green onion",
    "spring onions": "green onion",
    "scallions": "green onion",
    "garlic cloves": "garlic",
    "clove garlic": "garlic",
    "bell peppers": "bell pepper",
    "red bell peppers": "red bell pepper",
    "green bell peppers": "green bell pepper",
    "carrots": "carrot",
    "mushrooms": "mushroom",
    "zucchinis": "zucchini",
    "courgette": "zucchini",
    "courgettes": "zucchini",
    "aubergine": "eggplant",
    "aubergines": "eggplant",
    "black beans": "black bean",
    "kidney beans": "kidney bean",
    "chickpeas": "chickpea",
    "garbanzo beans": "chickpea",
    "lentils": "lentil",
    "tortillas": "tortilla",
    "hamburger buns": "hamburger bun",
    "burger buns": "hamburger bun",
    "bread crumbs": "breadcrumb",
    "breadcrumbs": "breadcrumb",
    "panko breadcrumbs": "panko breadcrumb",
    "spaghetti noodles": "spaghetti",
    "pasta noodles": "pasta",
    "macaroni noodles": "macaroni",
    "rolled oats": "oat",
    "old fashioned oats": "oat",
    "oats": "oat",
    "all purpose flour": "all purpose flour",
    "plain flour": "all purpose flour",
    "granulated sugar": "sugar",
    "white sugar": "sugar",
    "confectioners sugar": "powdered sugar",
    "confectioner sugar": "powdered sugar",
    "icing sugar": "powdered sugar",
    "olive oils": "olive oil",
    "vegetable oils": "vegetable oil",
    "cheddar cheese": "cheddar",
    "shredded cheddar cheese": "cheddar",
    "mozzarella cheese": "mozzarella",
    "parmesan cheese": "parmesan",
    "cream cheese spread": "cream cheese",
    "greek yoghurt": "greek yogurt",
    "yoghurt": "yogurt",
}

# Tokens that mark ingredients as distinct even when another token overlaps.
# This prevents unsafe or semantically wrong fuzzy matches.
DISTINGUISHING_TOKENS = {
    "stock", "broth", "sauce", "paste", "powder", "oil", "milk", "cream",
    "flour", "butter", "cheese", "juice", "vinegar", "syrup", "extract",
    "seed", "seeds", "nut", "nuts", "buttermilk", "yogurt", "wine",
}

STOPWORDS = {"and", "or", "of", "the", "a", "an", "with", "without"}

FRACTION_RE = re.compile(r"(?:\d+\s+)?\d+\s*/\s*\d+|[¼½¾⅓⅔⅛⅜⅝⅞]")
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
PAREN_RE = re.compile(r"\([^)]*\)")
NON_WORD_RE = re.compile(r"[^a-z0-9\s-]")
SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedIngredient:
    original: str
    canonical: str
    tokens: Tuple[str, ...]


@lru_cache(maxsize=8192)
def normalize_ingredient(value: str | None) -> NormalizedIngredient:
    original = " ".join(str(value or "").strip().split())
    text = unicodedata.normalize("NFKD", original).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("&", " and ")
    text = PAREN_RE.sub(" ", text)
    text = FRACTION_RE.sub(" ", text)
    text = NUMBER_RE.sub(" ", text)
    text = text.replace("-", " ")
    text = NON_WORD_RE.sub(" ", text)

    tokens = [
        token
        for token in SPACE_RE.sub(" ", text).strip().split()
        if token not in UNITS and token not in PREPARATION_WORDS and token not in STOPWORDS
    ]
    phrase = " ".join(tokens)
    canonical = ALIASES.get(phrase, phrase)

    # Apply alias one more time after conservative trailing plural cleanup.
    if canonical not in ALIASES and canonical.endswith("ies") and len(canonical) > 4:
        singular = canonical[:-3] + "y"
        canonical = ALIASES.get(singular, singular)
    elif canonical not in ALIASES and canonical.endswith("s") and not canonical.endswith("ss"):
        singular = canonical[:-1]
        canonical = ALIASES.get(singular, singular)

    canonical = ALIASES.get(canonical, canonical)
    return NormalizedIngredient(
        original=original,
        canonical=canonical,
        tokens=tuple(canonical.split()),
    )


def _distinguishing_tokens(tokens: Iterable[str]) -> set[str]:
    return set(tokens) & DISTINGUISHING_TOKENS


def _generic_food_equivalent(a: NormalizedIngredient, b: NormalizedIngredient) -> bool:
    """Allow a generic pantry/recipe concept to match a specific variety.

    Specific varieties do not match each other here: elbow macaroni is not
    angel-hair pasta, but either can satisfy a recipe that only asks for pasta.
    """
    generic_groups = {
        "pasta": {"pasta", "spaghetti", "macaroni", "penne", "linguine", "fettuccine", "noodle", "angel hair pasta"},
        "rice": {"rice", "brown rice", "white rice", "jasmine rice", "basmati rice"},
        "cheese": {"cheese", "cheddar", "mozzarella", "parmesan", "gouda", "monterey jack", "colby jack"},
        "bell pepper": {"bell pepper", "red bell pepper", "green bell pepper", "yellow bell pepper", "orange bell pepper"},
        "ground beef": {"ground beef", "beef patty"},
        "flour": {"flour", "all purpose flour", "plain flour", "wheat flour"},
    }
    for generic, members in generic_groups.items():
        if a.canonical == generic and b.canonical in members:
            return True
        if b.canonical == generic and a.canonical in members:
            return True
    return False


def ingredients_equivalent(left: str | None, right: str | None) -> bool:
    """Return True only for exact or explicitly normalized equivalents.

    This intentionally rejects substring matching. For example, "chicken stock"
    does not match "chicken breast", and "coconut milk" does not match "milk".
    """
    a = normalize_ingredient(left)
    b = normalize_ingredient(right)
    if not a.canonical or not b.canonical:
        return False
    if a.canonical == b.canonical:
        return True
    if _generic_food_equivalent(a, b):
        return True

    a_tokens, b_tokens = set(a.tokens), set(b.tokens)
    if _distinguishing_tokens(a_tokens) != _distinguishing_tokens(b_tokens):
        return False

    # Conservative containment supports brand/preparation descriptors that
    # survive cleanup, but only for multi-token concepts with the same head.
    if len(a_tokens) >= 2 and len(b_tokens) >= 2:
        smaller, larger = (a_tokens, b_tokens) if len(a_tokens) <= len(b_tokens) else (b_tokens, a_tokens)
        if smaller.issubset(larger) and a.tokens[-1] == b.tokens[-1]:
            return True
    return False


def best_equivalent_index(target: str, candidates: Sequence[str]) -> Optional[int]:
    """Return the first exact/alias-equivalent candidate index, if any."""
    target_norm = normalize_ingredient(target)
    if not target_norm.canonical:
        return None
    exact: list[int] = []
    equivalent: list[int] = []
    for index, candidate in enumerate(candidates):
        candidate_norm = normalize_ingredient(candidate)
        if target_norm.canonical == candidate_norm.canonical:
            exact.append(index)
        elif ingredients_equivalent(target, candidate):
            equivalent.append(index)
    return exact[0] if exact else (equivalent[0] if equivalent else None)
