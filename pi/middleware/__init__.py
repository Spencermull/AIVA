"""Vision and automation layer that drives the Flask movement API."""

from middleware.hazard_middleware import run_hazard_middleware

__all__ = ["run_hazard_middleware"]
