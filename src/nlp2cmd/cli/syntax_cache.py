"""
Syntax highlighting cache for improved performance.

Caches Rich Syntax objects to avoid recreating them repeatedly
for the same code content and language combinations.
"""

from typing import Dict, Optional
from rich.syntax import Syntax


class SyntaxCache:
    """Cache for Rich Syntax objects to improve performance."""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize the syntax cache.
        
        Args:
            max_size: Maximum number of cached syntax objects
        """
        self._cache: Dict[str, Syntax] = {}
        self._max_size = max_size
        self._access_order: list[str] = []
    
    def get_syntax(self, code: str, lexer: str, theme: str = "monokai", line_numbers: bool = False) -> Syntax:
        """
        Get a cached Syntax object or create a new one.
        
        Args:
            code: The code to highlight
            lexer: The lexer to use (bash, yaml, sql, etc.)
            theme: The theme to use
            line_numbers: Whether to show line numbers
            
        Returns:
            Syntax object for the given code and lexer
        """
        # Create cache key
        cache_key = f"{lexer}:{theme}:{line_numbers}:{hash(code)}"
        
        # Check cache first
        if cache_key in self._cache:
            # Move to end of access order (LRU)
            self._access_order.remove(cache_key)
            self._access_order.append(cache_key)
            return self._cache[cache_key]
        
        # Create new Syntax object
        syntax = Syntax(code, lexer, theme=theme, line_numbers=line_numbers)
        
        # Add to cache
        self._cache[cache_key] = syntax
        self._access_order.append(cache_key)
        
        # Remove oldest if cache is full
        if len(self._cache) > self._max_size:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        return syntax
    
    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._access_order.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "utilization": len(self._cache) / self._max_size
        }


# Global cache instance
_global_cache: Optional[SyntaxCache] = None


def get_syntax_cache() -> SyntaxCache:
    """Get the global syntax cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = SyntaxCache()
    return _global_cache


def get_cached_syntax(code: str, lexer: str, theme: str = "monokai", line_numbers: bool = False) -> Syntax:
    """
    Get a cached Syntax object using the global cache.
    
    Args:
        code: The code to highlight
        lexer: The lexer to use (bash, yaml, sql, etc.)
        theme: The theme to use
        line_numbers: Whether to show line numbers
        
    Returns:
        Syntax object for the given code and lexer
    """
    cache = get_syntax_cache()
    return cache.get_syntax(code, lexer, theme, line_numbers)


def clear_syntax_cache() -> None:
    """Clear the global syntax cache."""
    cache = get_syntax_cache()
    cache.clear()


def get_cache_stats() -> Dict[str, int]:
    """Get global cache statistics."""
    cache = get_syntax_cache()
    return cache.get_stats()
