"""
Search tool implementation.
Supports multiple search engines, primarily using Tavily search.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from tavily import TavilyClient


@dataclass
class SearchResult:
    """Search result data model."""
    title: str
    url: str
    content: str
    score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score
        }


class TavilySearch:
    """Wrapper for the Tavily search client."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Tavily search client.
        
        Args:
            api_key: Tavily API key. If not provided, read from environment variable.
        """
        if api_key is None:
            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                raise ValueError("Tavily API key not found! Set TAVILY_API_KEY or provide it during initialization.")
        
        self.client = TavilyClient(api_key=api_key)
    
    def search(self, query: str, max_results: int = 5, include_raw_content: bool = True, 
               timeout: int = 240) -> List[SearchResult]:
        """
        Execute a search.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            include_raw_content: Whether to include raw content.
            timeout: Timeout in seconds.
            
        Returns:
            List of search results.
        """
        try:
            # Call Tavily API
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                timeout=timeout
            )
            
            # Parse results
            results = []
            if 'results' in response:
                for item in response['results']:
                    result = SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        content=item.get('content', ''),
                        score=item.get('score')
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []


# Global search client instance
_tavily_client = None


def get_tavily_client() -> TavilySearch:
    """Get the global Tavily client instance."""
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilySearch()
    return _tavily_client


def tavily_search(query: str, max_results: int = 5, include_raw_content: bool = True, 
                  timeout: int = 240, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenient Tavily search function.
    
    Args:
        query: Search query.
        max_results: Maximum number of results.
        include_raw_content: Whether to include raw content.
        timeout: Timeout in seconds.
        api_key: Tavily API key. If provided, use this key; otherwise use the global client.
        
    Returns:
        List of result dictionaries, kept in a format compatible with the original implementation.
    """
    try:
        if api_key:
            # Create a temporary client with the provided API key
            client = TavilySearch(api_key)
        else:
            # Use the global client
            client = get_tavily_client()
        
        results = client.search(query, max_results, include_raw_content, timeout)
        
        # Convert to dictionary format for compatibility
        return [result.to_dict() for result in results]
        
    except Exception as e:
        print(f"Search function call error: {str(e)}")
        return []


def test_search(query: str = "AI development trends 2025", max_results: int = 3):
    """
    Test search functionality.
    
    Args:
        query: Test query.
        max_results: Maximum number of results.
    """
    print(f"\n=== Testing Tavily Search ===")
    print(f"Search query: {query}")
    print(f"Maximum results: {max_results}")
    
    try:
        results = tavily_search(query, max_results=max_results)
        
        if results:
            print(f"\nFound {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Title: {result['title']}")
                print(f"URL: {result['url']}")
                print(f"Content summary: {result['content'][:200]}...")
                if result.get('score'):
                    print(f"Relevance score: {result['score']}")
        else:
            print("No search results found")
            
    except Exception as e:
        print(f"Search test failed: {str(e)}")


if __name__ == "__main__":
    # Run test
    test_search()
