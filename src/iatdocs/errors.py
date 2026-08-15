# Copyright (c) 2026 Matthew S. Novak. All rights reserved.
from __future__ import annotations


class IaTDocsError(Exception):
    """Base class for controlled, user-facing engine failures."""


class ConfigurationError(IaTDocsError):
    """Project configuration is missing, unsafe, or invalid."""


class BuildError(IaTDocsError):
    """The static site could not be built safely."""


class ValidationFailure(IaTDocsError):
    """Required validation failed."""
