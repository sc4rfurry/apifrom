"""
Plugin system for APIFromAnything.

This module provides a plugin system for extending the functionality of
the APIFromAnything library.
"""

from apifrom.plugins.base import Plugin, PluginManager
from apifrom.plugins.logging import LoggingPlugin

__all__ = ["Plugin", "PluginManager", "LoggingPlugin"] 