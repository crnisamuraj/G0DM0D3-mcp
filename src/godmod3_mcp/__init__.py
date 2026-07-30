"""G0DM0D3 MCP bridge package."""

from .client import Godmod3Client, Godmod3ClientError
from .config import Config
from .server import main

__all__ = ["Config", "Godmod3Client", "Godmod3ClientError", "main"]
__version__ = "0.1.0"
