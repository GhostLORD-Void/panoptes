"""Typed exception hierarchy for predictable PANOPTES error handling."""


class PanoptesError(Exception):
    """Base class for expected, user-actionable PANOPTES errors."""


class SourceError(PanoptesError):
    """A data source failed to provide observations."""


class ProbeError(PanoptesError):
    """A probe failed while checking an authorized target."""


class ConfigError(PanoptesError):
    """Configuration is invalid or cannot be loaded."""


class BudgetExceeded(PanoptesError):
    """A run attempted to exceed its configured resource budget."""
