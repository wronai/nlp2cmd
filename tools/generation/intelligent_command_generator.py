#!/usr/bin/env python3
"""
Intelligent Command Generator with Adaptive Strategy Selection

This module provides an intelligent generator that:
1. Automatically detects available methods
2. Selects optimal strategy per command
3. Falls back gracefully when methods fail
4. Learns from success/failure patterns
5. Provides quality scoring
"""

import sys
sys.path.insert(0, './src')

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry
from enhanced_schema_generator import EnhancedSchemaExtractor, ExtractionStrategy


class GenerationMethod(Enum):
    """Available generation methods."""
    SCHEMA_BASED = "schema_based"
    LLM_DIRECT = "llm_direct"
    TEMPLATE_MATCHING = "template_matching"
    HYBRID = "hybrid"
    FALLBACK = "fallback"


@dataclass
class GenerationResult:
    """Result of command generation."""
    command: str
    method: GenerationMethod
    confidence: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class IntelligentCommandGenerator:
    """Intelligent command generator with adaptive strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize generator with configuration."""
        self.config = config or {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.schema_registry = DynamicSchemaRegistry(
            use_per_command_storage=True,
            storage_dir="./command_schemas"
        )
        
        self.enhanced_extractor = EnhancedSchemaExtractor(
            llm_config=self.config.get("llm")
        )
        
        self.dynamic_adapter = DynamicAdapter(
            schema_registry=self.schema_registry
        )
        
        self.nlp2cmd = NLP2CMD(adapter=self.dynamic_adapter)
        
        # Performance tracking
        self.method_stats = {
            method: {"uses": 0, "successes": 0, "total_time": 0.0}
            for method in GenerationMethod
        }
        
        # Learning cache
        self.success_cache = {}
        self.failure_cache = {}
        
        # Quality thresholds
        self.min_confidence = self.config.get("min_confidence", 0.5)
        self.max_execution_time = self.config.get("max_execution_time", 5.0)
    
    def generate_command(self, prompt: str, preferred_method: Optional[GenerationMethod] = None) -> GenerationResult:
        """Generate command using best available method."""
        
        start_time = time.time()
        
        # Select method
        method = preferred_method or self._select_optimal_method(prompt)
        
        # Update stats
        self.method_stats[method]["uses"] += 1
        
        # Try generation
        result = self._generate_with_method(prompt, method)
        
        # Update execution time
        result.execution_time = time.time() - start_time
        self.method_stats[method]["total_time"] += result.execution_time
        
        # Update success stats
        if result.command and not result.command.startswith("#"):
            self.method_stats[method]["successes"] += 1
            self._cache_success(prompt, method)
        else:
            self._cache_failure(prompt, method)
            
            # Try fallback if failed
            if method != GenerationMethod.FALLBACK:
                self.logger.info(f"Primary method failed, trying fallback")
                fallback_result = self._generate_with_method(prompt, GenerationMethod.FALLBACK)
                if fallback_result.command and not fallback_result.command.startswith("#"):
                    result = fallback_result
                    result.metadata["fallback_used"] = True
        
        return result
    
    def _select_optimal_method(self, prompt: str) -> GenerationMethod:
        """Select optimal method based on prompt and history."""
        
        # Check cache
        if prompt in self.success_cache:
            return self.success_cache[prompt]
        
        # Analyze prompt complexity
        complexity = self._analyze_prompt_complexity(prompt)
        
        # Check available schemas
        has_schema = self._has_relevant_schema(prompt)
        
        # Check LLM availability
        has_llm = self.enhanced_extractor._is_llm_available()
        
        # Decision logic
        if complexity > 0.7 and has_llm:
            return GenerationMethod.LLM_DIRECT
        elif has_schema:
            return GenerationMethod.SCHEMA_BASED
        elif has_llm:
            return GenerationMethod.HYBRID
        elif complexity < 0.3:
            return GenerationMethod.TEMPLATE_MATCHING
        else:
            return GenerationMethod.FALLBACK
    
    def _generate_with_method(self, prompt: str, method: GenerationMethod) -> GenerationResult:
        """Generate command using specific method."""
        
        result = GenerationResult(method=method, command="", confidence=0.0)
        
        try:
            if method == GenerationMethod.SCHEMA_BASED:
                result = self._generate_schema_based(prompt)
            elif method == GenerationMethod.LLM_DIRECT:
                result = self._generate_llm_direct(prompt)
            elif method == GenerationMethod.TEMPLATE_MATCHING:
                result = self._generate_template_matching(prompt)
            elif method == GenerationMethod.HYBRID:
                result = self._generate_hybrid(prompt)
            elif method == GenerationMethod.FALLBACK:
                result = self._generate_fallback(prompt)
        except Exception as e:
            result.errors.append(str(e))
            self.logger.error(f"Generation failed with {method}: {e}")
        
        return result
    
    def _generate_schema_based(self, prompt: str) -> GenerationResult:
        """Generate using schema-based method."""
        result = GenerationResult(method=GenerationMethod.SCHEMA_BASED)
        
        try:
            # Transform using NLP2CMD with schema adapter
            ir = self.nlp2cmd.transform_ir(prompt)
            result.command = ir.dsl
            result.confidence = 0.8  # High confidence for schema-based
            result.metadata["ir"] = ir.to_dict()
            
        except Exception as e:
            result.errors.append(f"Schema-based generation failed: {e}")
        
        return result
    
    def _generate_llm_direct(self, prompt: str) -> GenerationResult:
        """Generate using direct LLM call."""
        result = GenerationResult(method=GenerationMethod.LLM_DIRECT)
        
        try:
            # Create prompt for LLM
            llm_prompt = f"""
Convert this natural language request to a shell command:
Request: {prompt}

Return only the command, no explanation.
"""
            
            # Call LLM
            response = self.enhanced_extractor._call_llm(llm_prompt)
            
            # Clean response
            command = response.strip().split('\n')[0]
            if command and not command.startswith("#"):
                result.command = command
                result.confidence = 0.7
                result.metadata["llm_response"] = response
            else:
                result.errors.append("LLM returned invalid command")
                
        except Exception as e:
            result.errors.append(f"LLM generation failed: {e}")
        
        return result
    
    def _generate_template_matching(self, prompt: str) -> GenerationResult:
        """Generate using template matching."""
        result = GenerationResult(method=GenerationMethod.TEMPLATE_MATCHING)
        
        # Simple pattern matching
        patterns = {
            r"list.*files": "ls -la",
            r"find.*python": "find . -name '*.py'",
            r"show.*process": "ps aux",
            r"check.*disk": "df -h",
            r"compress.*tar": "tar -czf archive.tar.gz",
            r"docker.*ps": "docker ps",
            r"git.*status": "git status",
        }
        
        import re
        for pattern, command in patterns.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                result.command = command
                result.confidence = 0.6
                result.metadata["matched_pattern"] = pattern
                break
        else:
            result.errors.append("No matching template found")
        
        return result
    
    def _generate_hybrid(self, prompt: str) -> GenerationResult:
        """Generate using hybrid approach."""
        result = GenerationResult(method=GenerationMethod.HYBRID)
        
        # Try schema-based first
        schema_result = self._generate_schema_based(prompt)
        
        if schema_result.command and not schema_result.command.startswith("#"):
            # Enhance with LLM if needed
            if self._needs_enhancement(schema_result.command):
                try:
                    enhanced = self._enhance_command(schema_result.command, prompt)
                    result.command = enhanced
                    result.confidence = 0.85
                    result.metadata["enhanced"] = True
                except:
                    result = schema_result
            else:
                result = schema_result
        else:
            # Fall back to LLM
            result = self._generate_llm_direct(prompt)
        
        return result
    
    def _generate_fallback(self, prompt: str) -> GenerationResult:
        """Generate fallback command."""
        result = GenerationResult(method=GenerationMethod.FALLBACK)
        
        # Extract keywords
        words = prompt.lower().split()
        
        # Common command mappings
        command_map = {
            "list": "ls",
            "find": "find",
            "show": "echo",
            "run": "sh",
            "execute": "sh",
            "create": "touch",
            "delete": "rm",
            "move": "mv",
            "copy": "cp",
        }
        
        for word in words:
            if word in command_map:
                result.command = f"# Could not generate exact command. Try: {command_map[word]}"
                result.confidence = 0.2
                result.metadata["fallback_reason"] = "keyword_match"
                break
        else:
            result.command = f"# No command generated for: {prompt}"
            result.confidence = 0.0
            result.metadata["fallback_reason"] = "no_match"
        
        return result
    
    def _analyze_prompt_complexity(self, prompt: str) -> float:
        """Analyze prompt complexity (0.0 to 1.0)."""
        
        complexity = 0.0
        
        # Length factor
        if len(prompt) > 50:
            complexity += 0.2
        if len(prompt) > 100:
            complexity += 0.2
        
        # Keyword complexity
        complex_keywords = [
            "recursive", "exclude", "include", "pattern", "regex",
            "permission", "owner", "group", "timestamp", "size",
            "container", "pod", "deployment", "service"
        ]
        
        for keyword in complex_keywords:
            if keyword in prompt.lower():
                complexity += 0.1
        
        # Multiple actions
        actions = ["and", "then", "after", "before", "while"]
        for action in actions:
            if action in prompt.lower():
                complexity += 0.1
        
        return min(complexity, 1.0)
    
    def _has_relevant_schema(self, prompt: str) -> bool:
        """Check if we have relevant schema for prompt."""
        
        # Extract potential command
        words = prompt.lower().split()
        
        for word in words:
            if word in self.schema_registry.schemas:
                return True
        
        return False
    
    def _needs_enhancement(self, command: str) -> bool:
        """Check if command needs LLM enhancement."""
        
        # Simple commands don't need enhancement
        simple_commands = ["ls", "ps", "df", "du", "free", "uptime"]
        
        for cmd in simple_commands:
            if command.startswith(cmd):
                return False
        
        return True
    
    def _enhance_command(self, command: str, prompt: str) -> str:
        """Enhance command with LLM."""
        
        enhancement_prompt = f"""
Improve this shell command for the request:
Request: {prompt}
Current command: {command}

Provide a better, more complete command.
Return only the command.
"""
        
        response = self.enhanced_extractor._call_llm(enhancement_prompt)
        return response.strip().split('\n')[0]
    
    def _cache_success(self, prompt: str, method: GenerationMethod):
        """Cache successful generation."""
        self.success_cache[prompt] = method
        
        # Remove from failure cache if present
        if prompt in self.failure_cache:
            del self.failure_cache[prompt]
    
    def _cache_failure(self, prompt: str, method: GenerationMethod):
        """Cache failed generation."""
        if prompt not in self.failure_cache:
            self.failure_cache[prompt] = []
        self.failure_cache[prompt].append(method)
    
    def batch_generate(self, prompts: List[str]) -> List[GenerationResult]:
        """Generate commands for multiple prompts."""
        
        results = []
        
        for prompt in prompts:
            result = self.generate_command(prompt)
            results.append(result)
            
            # Show progress
            status = "✓" if result.command and not result.command.startswith("#") else "✗"
            print(f"{status} {prompt[:40]:40} -> {result.command[:30]:30}")
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        
        stats = {
            "method_performance": {},
            "overall": {
                "total_generations": sum(m["uses"] for m in self.method_stats.values()),
                "success_rate": 0.0,
                "avg_time": 0.0
            },
            "cache_stats": {
                "success_cache_size": len(self.success_cache),
                "failure_cache_size": len(self.failure_cache)
            }
        }
        
        # Calculate per-method stats
        total_successes = 0
        total_uses = 0
        total_time = 0.0
        
        for method, data in self.method_stats.items():
            uses = data["uses"]
            successes = data["successes"]
            total_time = data["total_time"]
            
            success_rate = successes / uses if uses > 0 else 0.0
            avg_time = total_time / uses if uses > 0 else 0.0
            
            stats["method_performance"][method.value] = {
                "uses": uses,
                "successes": successes,
                "success_rate": success_rate,
                "avg_time": avg_time
            }
            
            total_successes += successes
            total_uses += uses
            total_time += total_time
        
        # Overall stats
        if total_uses > 0:
            stats["overall"]["success_rate"] = total_successes / total_uses
            stats["overall"]["avg_time"] = total_time / total_uses
        
        return stats


def main():
    """Demonstrate intelligent command generation."""
    
    print("=" * 60)
    print("INTELLIGENT COMMAND GENERATOR")
    print("=" * 60)
    
    # Initialize generator
    generator = IntelligentCommandGenerator()
    
    # Test prompts
    test_prompts = [
        "list all files in current directory",
        "find all python files recursively",
        "show running processes",
        "check disk space usage",
        "list docker containers",
        "create a backup of /home/user",
        "compress logs directory",
        "git status and commit changes",
        "deploy application to kubernetes",
        "monitor cpu usage in real time",
        "complex: find large files older than 30 days and delete them",
        "invalid command that should fail"
    ]
    
    print("\nGenerating commands...")
    print("-" * 60)
    
    # Generate commands
    results = generator.batch_generate(test_prompts)
    
    # Show statistics
    print("\n" + "=" * 60)
    print("PERFORMANCE STATISTICS")
    print("=" * 60)
    
    stats = generator.get_performance_stats()
    
    print("\nMethod Performance:")
    for method, data in stats["method_performance"].items():
        if data["uses"] > 0:
            print(f"{method:20}: {data['successes']:3}/{data['uses']:3} "
                  f"({data['success_rate']:.1%}) "
                  f"avg: {data['avg_time']:.3f}s")
    
    print(f"\nOverall:")
    print(f"  Total generations: {stats['overall']['total_generations']}")
    print(f"  Success rate: {stats['overall']['success_rate']:.1%}")
    print(f"  Average time: {stats['overall']['avg_time']:.3f}s")
    
    print(f"\nCache:")
    print(f"  Success cache: {stats['cache_stats']['success_cache_size']} entries")
    print(f"  Failure cache: {stats['cache_stats']['failure_cache_size']} entries")
    
    # Show successful generations
    print("\n" + "=" * 60)
    print("SUCCESSFUL GENERATIONS")
    print("=" * 60)
    
    for result in results:
        if result.command and not result.command.startswith("#"):
            print(f"\nPrompt: {result.metadata.get('original_prompt', 'Unknown')}")
            print(f"Command: {result.command}")
            print(f"Method: {result.method.value}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Time: {result.execution_time:.3f}s")


if __name__ == "__main__":
    main()
