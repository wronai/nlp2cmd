#!/usr/bin/env python3
"""
Simple E2E Test Runner for NLP2CMD Service Mode

This script runs end-to-end tests for the service mode without requiring pytest.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

import requests


class SimpleE2ETester:
    """Simple E2E test runner for NLP2CMD service."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8001):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.process = None
        self.test_results = []
        
    def start_service(self) -> bool:
        """Start NLP2CMD service."""
        print(f"🚀 Starting NLP2CMD service on {self.host}:{self.port}")
        
        cmd = [
            sys.executable, "-m", "nlp2cmd", "service",
            "--host", self.host,
            "--port", str(self.port),
            "--debug",
            "--log-level", "debug"
        ]
        
        try:
            # Set environment with PYTHONPATH
            env = os.environ.copy()
            src_path = str(Path(__file__).parent / "src")
            env["PYTHONPATH"] = src_path + ":" + env.get("PYTHONPATH", "")
            
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to be ready
            if self.wait_for_ready():
                print(f"✅ Service started successfully")
                return True
            else:
                print(f"❌ Service failed to start")
                self.stop_service()
                return False
                
        except Exception as e:
            print(f"❌ Failed to start service: {e}")
            return False
    
    def wait_for_ready(self, timeout: int = 30) -> bool:
        """Wait for service to be ready."""
        print(f"⏳ Waiting for service to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.5)
            print(".", end="", flush=True)
        
        print()
        return False
    
    def stop_service(self):
        """Stop the service."""
        if self.process:
            print("🛑 Stopping service...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            print("✅ Service stopped")
    
    def run_test(self, name: str, test_func) -> bool:
        """Run a single test."""
        print(f"🧪 Running test: {name}")
        try:
            result = test_func()
            if result:
                print(f"✅ {name}: PASSED")
                self.test_results.append({"name": name, "status": "passed"})
                return True
            else:
                print(f"❌ {name}: FAILED")
                self.test_results.append({"name": name, "status": "failed"})
                return False
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            self.test_results.append({"name": name, "status": "error", "error": str(e)})
            return False
    
    def test_health_check(self) -> bool:
        """Test health check endpoint."""
        response = requests.get(f"{self.base_url}/health")
        if response.status_code != 200:
            return False
        
        data = response.json()
        return data.get("status") == "healthy" and data.get("service") == "nlp2cmd"
    
    def test_service_info(self) -> bool:
        """Test service info endpoint."""
        response = requests.get(f"{self.base_url}/")
        if response.status_code != 200:
            return False
        
        data = response.json()
        required_fields = ["service", "version", "status", "config"]
        return all(field in data for field in required_fields)
    
    def test_basic_query(self) -> bool:
        """Test basic query processing."""
        payload = {
            "query": "list files in current directory",
            "dsl": "shell"
        }
        
        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        return (
            data.get("success") is True and
            data.get("command") is not None and
            isinstance(data.get("confidence"), (int, float)) and
            data.get("domain") == "shell"
        )
    
    def test_polish_queries(self) -> bool:
        """Test Polish language queries."""
        polish_queries = [
            {"query": "znajdź pliki większe niż 100MB", "dsl": "shell"},
            {"query": "uruchom usługę nginx", "dsl": "shell"},
            {"query": "pokaż wszystkie procesy", "dsl": "shell"}
        ]
        
        for query_data in polish_queries:
            response = requests.post(f"{self.base_url}/query", json=query_data)
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            if not data.get("success") or not data.get("command"):
                return False
        
        return True
    
    def test_query_with_explanation(self) -> bool:
        """Test query with explanation."""
        payload = {
            "query": "find all python files",
            "dsl": "shell",
            "explain": True
        }
        
        response = requests.post(f"{self.base_url}/query", json=payload)
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        return (
            data.get("success") is True and
            data.get("explanation") is not None and
            "RuleBasedPipeline" in data.get("explanation", "")
        )
    
    def test_config_management(self) -> bool:
        """Test configuration management."""
        # Get current config
        response = requests.get(f"{self.base_url}/config")
        if response.status_code != 200:
            return False
        
        original_config = response.json()
        
        # Update config
        update_payload = {"log_level": "warning"}
        response = requests.post(f"{self.base_url}/config", json=update_payload)
        
        if response.status_code != 200:
            return False
        
        # Verify update
        response = requests.get(f"{self.base_url}/config")
        if response.status_code != 200:
            return False
        
        updated_config = response.json()
        return updated_config.get("log_level") == "warning"
    
    def test_error_handling(self) -> bool:
        """Test error handling."""
        # Test invalid JSON
        response = requests.post(
            f"{self.base_url}/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 4xx status
        if response.status_code < 400 or response.status_code >= 500:
            return False
        
        # Test missing required fields
        response = requests.post(
            f"{self.base_url}/query",
            json={"dsl": "shell"}  # Missing query
        )
        
        return response.status_code >= 400
    
    def test_concurrent_requests(self) -> bool:
        """Test concurrent requests."""
        import threading
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    json={"query": "list files", "dsl": "shell"},
                    timeout=10
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Make 5 concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        return len(errors) == 0 and all(status == 200 for status in results)
    
    def run_all_tests(self) -> bool:
        """Run all E2E tests."""
        print("🎯 Starting E2E Tests for NLP2CMD Service Mode")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Service Info", self.test_service_info),
            ("Basic Query", self.test_basic_query),
            ("Polish Queries", self.test_polish_queries),
            ("Query with Explanation", self.test_query_with_explanation),
            ("Config Management", self.test_config_management),
            ("Error Handling", self.test_error_handling),
            ("Concurrent Requests", self.test_concurrent_requests),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            print()
        
        # Print summary
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("💥 Some tests failed:")
            for result in self.test_results:
                if result["status"] != "passed":
                    error_msg = result.get("error", "Test failed")
                    print(f"  ❌ {result['name']}: {error_msg}")
            return False
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_service()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run E2E tests for NLP2CMD service")
    parser.add_argument("--host", default="127.0.0.1", help="Host for test service")
    parser.add_argument("--port", type=int, default=8001, help="Port for test service")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    tester = SimpleE2ETester(host=args.host, port=args.port)
    
    try:
        # Start service
        if not tester.start_service():
            sys.exit(1)
        
        # Run tests
        success = tester.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
