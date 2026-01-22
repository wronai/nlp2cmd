"""
Iteration 4-5: LLM Integration Tests.

Test LLM-based generation (single domain and multi-domain).
"""

import pytest
import asyncio

from nlp2cmd.generation.llm_simple import (
    LLMConfig,
    LLMGenerationResult,
    SimpleLLMSQLGenerator,
    SimpleLLMShellGenerator,
    SimpleLLMDockerGenerator,
    SimpleLLMKubernetesGenerator,
    MockLLMClient,
)
from nlp2cmd.generation.llm_multi import (
    LLMDomainRouter,
    MultiDomainGenerator,
    RoutingResult,
    CachedMultiDomainGenerator,
)


class TestMockLLMClient:
    """Test mock LLM client."""
    
    @pytest.fixture
    def mock(self) -> MockLLMClient:
        return MockLLMClient()
    
    @pytest.mark.asyncio
    async def test_mock_returns_sql_for_users(self, mock):
        """Test mock returns SQL for user queries."""
        response = await mock.complete(user="Pokaż użytkowników")
        assert "SELECT" in response
        assert "users" in response
    
    @pytest.mark.asyncio
    async def test_mock_returns_find_for_files(self, mock):
        """Test mock returns find for file queries."""
        response = await mock.complete(user="Znajdź pliki .py")
        assert "find" in response
    
    @pytest.mark.asyncio
    async def test_mock_tracks_calls(self, mock):
        """Test mock tracks call count."""
        await mock.complete(user="test1")
        await mock.complete(user="test2")
        assert mock.call_count == 2
    
    @pytest.mark.asyncio
    async def test_mock_custom_responses(self):
        """Test mock with custom responses."""
        mock = MockLLMClient(responses={
            "custom": "SELECT custom_result;"
        })
        response = await mock.complete(user="custom query")
        assert response == "SELECT custom_result;"


class TestSimpleLLMSQLGenerator:
    """Test SQL generator."""
    
    @pytest.fixture
    def generator(self) -> SimpleLLMSQLGenerator:
        return SimpleLLMSQLGenerator(MockLLMClient())
    
    @pytest.mark.asyncio
    async def test_generate_select(self, generator):
        """Test basic SELECT generation."""
        result = await generator.generate("Pokaż wszystkich użytkowników")
        
        assert result.success
        assert "SELECT" in result.command
        assert result.latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_with_context(self, generator):
        """Test generation with schema context."""
        result = await generator.generate(
            "Pokaż zamówienia",
            context={"schema": "orders, products"}
        )
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_extract_sql_from_markdown(self, generator):
        """Test SQL extraction from markdown code blocks."""
        mock = MockLLMClient(responses={
            "test": "```sql\nSELECT * FROM test;\n```"
        })
        gen = SimpleLLMSQLGenerator(mock)
        
        result = await gen.generate("test query")
        assert result.command == "SELECT * FROM test;"
    
    def test_system_prompt_includes_tables(self):
        """Test that system prompt includes default tables."""
        generator = SimpleLLMSQLGenerator(MockLLMClient())
        prompt = generator.get_system_prompt()
        
        assert "users" in prompt
        assert "orders" in prompt
        assert "products" in prompt
    
    def test_custom_schema_in_prompt(self):
        """Test custom schema in system prompt."""
        generator = SimpleLLMSQLGenerator(
            MockLLMClient(),
            schema_context={"custom_table": ["col1", "col2"]}
        )
        prompt = generator.get_system_prompt()
        
        assert "custom_table" in prompt


class TestSimpleLLMShellGenerator:
    """Test Shell generator."""
    
    @pytest.fixture
    def generator(self) -> SimpleLLMShellGenerator:
        return SimpleLLMShellGenerator(MockLLMClient())
    
    @pytest.mark.asyncio
    async def test_generate_find(self, generator):
        """Test find command generation."""
        result = await generator.generate("Znajdź pliki Python")
        
        assert result.success
        assert "find" in result.command


class TestSimpleLLMDockerGenerator:
    """Test Docker generator."""
    
    @pytest.fixture
    def generator(self) -> SimpleLLMDockerGenerator:
        return SimpleLLMDockerGenerator(MockLLMClient())
    
    @pytest.mark.asyncio
    async def test_generate_ps(self, generator):
        """Test docker ps generation."""
        result = await generator.generate("Pokaż kontenery")
        
        assert result.success
        assert "docker" in result.command


class TestSimpleLLMKubernetesGenerator:
    """Test Kubernetes generator."""
    
    @pytest.fixture
    def generator(self) -> SimpleLLMKubernetesGenerator:
        return SimpleLLMKubernetesGenerator(MockLLMClient())
    
    @pytest.mark.asyncio
    async def test_generate_get_pods(self, generator):
        """Test kubectl get pods generation."""
        result = await generator.generate("Pokaż pody")
        
        assert result.success
        assert "kubectl" in result.command


class TestLLMDomainRouter:
    """Test domain routing."""
    
    @pytest.fixture
    def router(self) -> LLMDomainRouter:
        mock = MockLLMClient(responses={
            "użytkownik": "sql",
            "plik": "shell",
            "kontener": "docker",
            "pod": "kubernetes",
        })
        return LLMDomainRouter(mock)
    
    @pytest.mark.asyncio
    async def test_route_to_sql(self, router):
        """Test routing to SQL domain."""
        result = await router.route("Pokaż użytkowników")
        # Mock returns based on keywords
        assert result.domain in ['sql', 'unknown']
    
    @pytest.mark.asyncio
    async def test_route_returns_confidence(self, router):
        """Test that routing returns confidence."""
        result = await router.route("test query")
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1


class TestMultiDomainGenerator:
    """Test multi-domain generation."""
    
    @pytest.fixture
    def generator(self) -> MultiDomainGenerator:
        return MultiDomainGenerator(MockLLMClient())
    
    @pytest.mark.asyncio
    async def test_generate_routes_correctly(self, generator):
        """Test that generation routes to correct domain."""
        result = await generator.generate(
            "Pokaż użytkowników z tabeli",
            force_domain="sql"
        )
        
        assert result.domain == "sql"
        assert result.success
    
    @pytest.mark.asyncio
    async def test_generate_unknown_domain(self, generator):
        """Test handling of unknown domain."""
        result = await generator.generate(
            "something unknown",
            force_domain="unknown"
        )
        
        assert result.domain == "unknown"
        assert not result.success
    
    @pytest.mark.asyncio
    async def test_generate_batch(self, generator):
        """Test batch generation."""
        texts = ["query1", "query2", "query3"]
        results = await generator.generate_batch(texts)
        
        assert len(results) == 3
    
    def test_get_supported_domains(self, generator):
        """Test getting supported domains."""
        domains = generator.get_supported_domains()
        
        assert "sql" in domains
        assert "shell" in domains
        assert "docker" in domains
        assert "kubernetes" in domains


class TestCachedMultiDomainGenerator:
    """Test cached generator."""
    
    @pytest.fixture
    def generator(self) -> CachedMultiDomainGenerator:
        return CachedMultiDomainGenerator(MockLLMClient(), cache_size=10)
    
    @pytest.mark.asyncio
    async def test_caches_results(self, generator):
        """Test that results are cached."""
        # First call
        result1 = await generator.generate("test query", force_domain="sql")
        
        # Second call - should be cached
        result2 = await generator.generate("test query", force_domain="sql")
        
        assert result1.command == result2.command
        assert generator.cache_stats["size"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, generator):
        """Test cache clearing."""
        await generator.generate("test", force_domain="sql")
        assert generator.cache_stats["size"] == 1
        
        generator.clear_cache()
        assert generator.cache_stats["size"] == 0


class TestLLMGenerationResult:
    """Test generation result dataclass."""
    
    def test_success_result(self):
        """Test successful result."""
        result = LLMGenerationResult(
            command="SELECT * FROM users;",
            raw_response="SELECT * FROM users;",
            model="gpt-4",
            success=True,
        )
        
        assert result.success
        assert result.command == "SELECT * FROM users;"
    
    def test_error_result(self):
        """Test error result."""
        result = LLMGenerationResult(
            command="",
            raw_response="",
            model="gpt-4",
            success=False,
            error="API error",
        )
        
        assert not result.success
        assert result.error == "API error"


class TestLLMConfig:
    """Test LLM configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = LLMConfig()
        
        assert config.model == "gpt-4"
        assert config.max_tokens == 500
        assert config.temperature == 0.1
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.5,
        )
        
        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens == 1000
        assert config.temperature == 0.5
