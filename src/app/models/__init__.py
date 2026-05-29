"""Persistence model package.

Import concrete ORM entities from their module paths to avoid coupling
lightweight runtime imports to SQLAlchemy at package import time.
"""
