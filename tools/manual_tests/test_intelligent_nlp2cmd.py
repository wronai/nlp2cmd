#!/usr/bin/env python3
"""Enhanced NLP2CMD with intelligent command detection."""

from typing import List, Dict, Optional
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.schema_extraction import DynamicSchemaRegistry

from nlp2cmd.intelligent.command_detector import CommandDetector
from nlp2cmd.intelligent.dynamic_generator import DynamicSchemaGenerator


class IntelligentNLP2CMD:
    """Enhanced NLP2CMD with intelligent command detection and dynamic schema generation."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """Initialize with LLM configuration."""
        self.llm_config = llm_config or {
            "model": "ollama/qwen2.5-coder:7b",
            "api_base": "http://localhost:11434",
            "temperature": 0.1,
            "max_tokens": 512,
            "timeout": 10,
        }
        
        # Initialize components
        self.command_detector = CommandDetector()
        self.schema_generator = DynamicSchemaGenerator(self.llm_config)
        self.registry = DynamicSchemaRegistry(
            auto_save_path="./intelligent_schemas.json",
            use_llm=True,
            llm_config=self.llm_config
        )
        
        # Initialize NLP2CMD
        self.adapter = DynamicAdapter(schema_registry=self.registry)
        self.nlp = NLP2CMD(adapter=self.adapter)
        
        # Cache for detected commands
        self._detection_cache = {}
    
    def transform(self, query: str, use_intelligent: bool = True):
        """
        Transform natural language to command with intelligent detection.
        
        Args:
            query: Natural language query
            use_intelligent: Whether to use intelligent detection
            
        Returns:
            Command execution result
        """
        if not use_intelligent:
            # Use standard NLP2CMD
            return self.nlp.transform(query)
        
        # Intelligent detection
        detected = self.command_detector.detect_command(query, top_k=1)
        
        if not detected:
            # Fallback to standard
            return self.nlp.transform(query)
        
        # Get the best match
        best_match = detected[0]
        
        # Generate schema if not exists
        if best_match.command not in self.registry.schemas:
            schema = self.schema_generator.generate_schema(
                best_match.command, 
                best_match.context
            )
            self.registry.schemas[schema.source] = schema
        
        # Transform with enhanced context
        enhanced_query = f"{best_match.command}: {query}"
        result = self.nlp.transform(enhanced_query)
        
        # Add detection metadata
        result.metadata.update({
            'detected_command': best_match.command,
            'confidence': best_match.confidence,
            'keywords': best_match.keywords,
            'context': best_match.context
        })
        
        return result
    
    def batch_transform(self, queries: List[str], use_intelligent: bool = True) -> List[Dict]:
        """
        Transform multiple queries.
        
        Args:
            queries: List of natural language queries
            use_intelligent: Whether to use intelligent detection
            
        Returns:
            List of results
        """
        results = []
        
        for query in queries:
            try:
                result = self.transform(query, use_intelligent)
                results.append({
                    'query': query,
                    'success': True,
                    'command': result.command,
                    'metadata': result.metadata
                })
            except Exception as e:
                results.append({
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
        
        return results


def test_intelligent_nlp2cmd():
    """Test the enhanced NLP2CMD system."""
    print("Testing Intelligent NLP2CMD")
    print("=" * 60)
    
    # Initialize system
    system = IntelligentNLP2CMD()
    
    # Test cases
    test_cases = [
        "Find files larger than 100MB",
        "Search for TODO in Python files", 
        "Compress logs directory",
        "Copy file to backup",
        "Move old files to archive",
        "Remove temporary files",
        "Show running processes",
        "Check disk usage",
        "Check memory usage",
        "Show system uptime",
        "Test connection to google.com",
        "Download file from URL",
        "Check network connections",
        "Check git status",
        "List Docker containers",
        "Check Kubernetes pods",
    ]
    
    print("\nTesting with intelligent detection:")
    print("-" * 60)
    
    results = []
    for query in test_cases:
        print(f"\nQuery: {query}")
        try:
            result = system.transform(query, use_intelligent=True)
            print(f"  Command: {result.command}")
            print(f"  Detected: {result.metadata.get('detected_command', 'N/A')}")
            print(f"  Confidence: {result.metadata.get('confidence', 0):.2f}")
            
            results.append({
                'query': query,
                'command': result.command,
                'detected': result.metadata.get('detected_command'),
                'confidence': result.metadata.get('confidence', 0)
            })
        except Exception as e:
            print(f"  Error: {e}")
            results.append({'query': query, 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    successful = sum(1 for r in results if 'error' not in r)
    avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results)
    
    print(f"  Total queries: {len(test_cases)}")
    print(f"  Successful: {successful}")
    print(f"  Average confidence: {avg_confidence:.2f}")
    
    # Save results
    import json
    with open('intelligent_nlp2cmd_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


if __name__ == "__main__":
    test_intelligent_nlp2cmd()
