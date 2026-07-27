"""Public recommendation-engine API.

Routes import ``generate_recommendations`` from this package.  Keep that
stable public import pointed at the current orchestration engine rather than
the legacy recommendation_service module.
"""

from .engine import generate_recommendations

__all__ = ["generate_recommendations"]
