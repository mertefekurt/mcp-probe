"""Project-specific exceptions."""


class ProbeError(Exception):
    """Base error for expected probe failures."""


class ConfigurationError(ProbeError):
    """Raised when a scenario file is invalid."""


class ProtocolError(ProbeError):
    """Raised when an MCP server violates the expected protocol."""
