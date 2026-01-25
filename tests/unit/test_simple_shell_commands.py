"""
Simple Shell Command Test
Test basic shell commands to ensure NLP2CMD is working
"""

import subprocess
import sys
import time
from pathlib import Path

def test_shell_command(command_input, timeout=10):
    """Test a single shell command"""
    try:
        # Try to run nlp2cmd
        result = subprocess.run(
            [sys.executable, "-m", "nlp2cmd.cli.main", command_input],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        
        return {
            'input': command_input,
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'input': command_input,
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out',
            'returncode': -1
        }
    except Exception as e:
        return {
            'input': command_input,
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -2
        }

def main():
    """Test basic shell commands"""
    print("=== Simple Shell Command Test ===")
    print("Testing basic NLP2CMD functionality\n")
    
    # Test commands
    test_commands = [
        "list files",
        "show current directory",
        "git status",
        "find python files",
        "show processes"
    ]
    
    results = []
    
    for cmd in test_commands:
        print(f"Testing: {cmd}")
        start_time = time.time()
        
        result = test_shell_command(cmd)
        execution_time = time.time() - start_time
        
        results.append({
            **result,
            'execution_time': execution_time
        })
        
        if result['success']:
            print(f"  ✅ PASSED ({execution_time:.2f}s)")
        else:
            print(f"  ❌ FAILED: {result['stderr'][:100]}...")
    
    # Summary
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n=== SUMMARY ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All commands working!")
    elif passed >= total * 0.8:
        print("✅ Most commands working")
    else:
        print("❌ Many commands failed")
    
    print("\nFailed commands:")
    for r in results:
        if not r['success']:
            print(f"  - {r['input']}: {r['stderr'][:50]}...")

if __name__ == "__main__":
    main()
