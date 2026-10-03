"""Templates for every repository a research project needs.

Examples:
    >>> isinstance(__version__, str)
    True
"""

from importlib.metadata import version

__version__ = version("research-foundry")
