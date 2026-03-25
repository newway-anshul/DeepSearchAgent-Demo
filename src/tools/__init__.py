"""
Tool invocation module.
Provides external tool interfaces, such as web search.
"""

from .search import tavily_search, SearchResult

__all__ = ["tavily_search", "SearchResult"]
