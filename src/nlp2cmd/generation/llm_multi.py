"""
Iteration 5: Multi-Domain LLM with Router.

Extends LLM generation to all domains with intelligent routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from nlp2cmd.generation.llm_simple import (
    LLMClient,
    LLMConfig,
    LLMGenerationResult,
    BaseLLMGenerator,
    SimpleLLMSQLGenerator,
    SimpleLLMShellGenerator,
    SimpleLLMDockerGenerator,
    SimpleLLMKubernetesGenerator,
)


@dataclass
class RoutingResult:
    """Result of domain routing."""
    
    domain: str
    confidence: float
    reasoning: Optional[str] = None


class LLMDomainRouter:
    """
    Route queries to correct domain using LLM classification.
    
    Example:
        router = LLMDomainRouter(llm_client)
        result = await router.route("Pokaż użytkowników z tabeli")
        # result.domain == 'sql'
    """
    
    CLASSIFICATION_PROMPT = """Sklasyfikuj poniższe zapytanie do jednej z kategorii:
- sql: zapytania do bazy danych, tabele, rekordy, SELECT, INSERT, UPDATE
- shell: operacje na plikach, systemie, procesy, find, grep, ls
- docker: kontenery, obrazy, docker-compose, Dockerfile
- kubernetes: pody, deploymenty, serwisy, kubectl, k8s
- unknown: nie pasuje do żadnej kategorii

Odpowiedz TYLKO nazwą kategorii (jedno słowo, małe litery).

Zapytanie: {query}"""
    
    VALID_DOMAINS = {'sql', 'shell', 'docker', 'kubernetes', 'unknown'}
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[LLMConfig] = None,
    ):
        self.llm = llm_client
        self.config = config or LLMConfig(max_tokens=20, temperature=0.0)
    
    async def route(self, text: str) -> RoutingResult:
        """
        Classify query to a domain.
        
        Args:
            text: Natural language input
            
        Returns:
            RoutingResult with domain and confidence
        """
        try:
            prompt = self.CLASSIFICATION_PROMPT.format(query=text)
            
            response = await self.llm.complete(
                user=prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            
            domain = response.strip().lower()
            
            # Validate domain
            if domain not in self.VALID_DOMAINS:
                # Try to extract first word
                domain = domain.split()[0] if domain else 'unknown'
                if domain not in self.VALID_DOMAINS:
                    domain = 'unknown'
            
            return RoutingResult(
                domain=domain,
                confidence=0.9 if domain != 'unknown' else 0.0,
            )
            
        except Exception as e:
            return RoutingResult(
                domain='unknown',
                confidence=0.0,
                reasoning=str(e),
            )


@dataclass 
class MultiDomainResult:
    """Result of multi-domain generation."""
    
    domain: str
    command: str
    raw_response: str
    routing_confidence: float
    generation_result: LLMGenerationResult
    success: bool
    error: Optional[str] = None


class MultiDomainGenerator:
    """
    Generate DSL for any domain using LLM routing.
    
    Example:
        generator = MultiDomainGenerator(llm_client)
        result = await generator.generate("Pokaż użytkowników")
        # result.domain == 'sql', result.command == 'SELECT * FROM users;'
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[LLMConfig] = None,
        custom_generators: Optional[dict[str, BaseLLMGenerator]] = None,
    ):
        self.llm = llm_client
        self.config = config or LLMConfig()
        self.router = LLMDomainRouter(llm_client, config)
        
        # Initialize domain generators
        self.generators: dict[str, BaseLLMGenerator] = custom_generators or {
            'sql': SimpleLLMSQLGenerator(llm_client, config),
            'shell': SimpleLLMShellGenerator(llm_client, config),
            'docker': SimpleLLMDockerGenerator(llm_client, config),
            'kubernetes': SimpleLLMKubernetesGenerator(llm_client, config),
        }
    
    async def generate(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
        force_domain: Optional[str] = None,
    ) -> MultiDomainResult:
        """
        Generate DSL command for any domain.
        
        Args:
            text: Natural language input
            context: Additional context
            force_domain: Skip routing, use this domain
            
        Returns:
            MultiDomainResult with domain and generated command
        """
        # Route to domain
        if force_domain:
            routing = RoutingResult(domain=force_domain, confidence=1.0)
        else:
            routing = await self.router.route(text)
        
        if routing.domain == 'unknown' or routing.domain not in self.generators:
            return MultiDomainResult(
                domain=routing.domain,
                command=f"# Unknown domain: {routing.domain}",
                raw_response="",
                routing_confidence=routing.confidence,
                generation_result=LLMGenerationResult(
                    command="",
                    raw_response="",
                    model=self.config.model,
                    success=False,
                    error=f"Unknown domain: {routing.domain}",
                ),
                success=False,
                error=f"Cannot generate for domain: {routing.domain}",
            )
        
        # Generate with domain-specific generator
        generator = self.generators[routing.domain]
        result = await generator.generate(text, context)
        
        return MultiDomainResult(
            domain=routing.domain,
            command=result.command,
            raw_response=result.raw_response,
            routing_confidence=routing.confidence,
            generation_result=result,
            success=result.success,
            error=result.error,
        )
    
    async def generate_batch(
        self,
        texts: list[str],
        context: Optional[dict[str, Any]] = None,
    ) -> list[MultiDomainResult]:
        """Generate for multiple inputs."""
        import asyncio
        tasks = [self.generate(text, context) for text in texts]
        return await asyncio.gather(*tasks)
    
    def add_generator(self, domain: str, generator: BaseLLMGenerator) -> None:
        """Add custom domain generator."""
        self.generators[domain] = generator
        self.router.VALID_DOMAINS.add(domain)
    
    def get_supported_domains(self) -> list[str]:
        """Get list of supported domains."""
        return list(self.generators.keys())


class CachedMultiDomainGenerator(MultiDomainGenerator):
    """Multi-domain generator with response caching."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[LLMConfig] = None,
        cache_size: int = 100,
    ):
        super().__init__(llm_client, config)
        self._cache: dict[str, MultiDomainResult] = {}
        self._cache_size = cache_size
    
    async def generate(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
        force_domain: Optional[str] = None,
    ) -> MultiDomainResult:
        """Generate with caching."""
        # Create cache key
        cache_key = f"{text}:{force_domain}:{hash(str(context))}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().generate(text, context, force_domain)
        
        # Add to cache
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        
        self._cache[cache_key] = result
        return result
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
    
    @property
    def cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._cache_size,
        }
