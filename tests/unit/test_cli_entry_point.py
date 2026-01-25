"""
Tests for CLI entry point natural language query handling.

Tests the cli_entry_point function that processes natural language queries
before passing them to Click, including Polish language support.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from nlp2cmd.cli.main import cli_entry_point


class TestCLIEntryPoint:
    """Test cases for CLI entry point functionality."""

    def test_single_polish_query(self):
        """Test single Polish language query with spaces."""
        test_args = ['nlp2cmd', 'znajdź pliki zmodyfikowane ostatnie 7 dni']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should rewrite args to include --query
            expected_args = ['--query', 'znajdź pliki zmodyfikowane ostatnie 7 dni']
            mock_main.assert_called_once()
            
            # Check that sys.argv was modified
            assert sys.argv[1:] == expected_args

    def test_single_english_query(self):
        """Test single English language query with spaces."""
        test_args = ['nlp2cmd', 'find files modified last 7 days']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should rewrite args to include --query
            expected_args = ['--query', 'find files modified last 7 days']
            mock_main.assert_called_once()
            assert sys.argv[1:] == expected_args

    def test_mixed_args_with_query(self):
        """Test mixed arguments with existing --query flag."""
        test_args = ['nlp2cmd', '--run', '--query', 'test command']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should NOT modify args since --query is already present
            mock_main.assert_called_once()
            assert sys.argv[1:] == ['--run', '--query', 'test command']

    def test_mixed_args_with_short_query(self):
        """Test mixed arguments with existing -q flag."""
        test_args = ['nlp2cmd', '-q', 'test command', '--run']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should NOT modify args since -q is already present
            mock_main.assert_called_once()
            assert sys.argv[1:] == ['-q', 'test command', '--run']

    def test_single_word_no_spaces(self):
        """Test single word without spaces - should not be treated as query."""
        test_args = ['nlp2cmd', 'help']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should NOT modify args - single word without spaces is likely a command
            mock_main.assert_called_once()
            assert sys.argv[1:] == ['help']

    def test_multiple_args_with_spaces(self):
        """Test multiple arguments where one contains spaces."""
        test_args = ['nlp2cmd', '--run', 'find large files', '--auto-confirm']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should rewrite to extract the query
            expected_args = ['--run', '--auto-confirm', '--query', 'find large files']
            mock_main.assert_called_once()
            assert sys.argv[1:] == expected_args

    def test_query_with_equals_flag(self):
        """Test query with flag that has equals sign - should not be processed."""
        test_args = ['nlp2cmd', '--format=json', 'some query']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should NOT process due to = in flag
            mock_main.assert_called_once()
            assert sys.argv[1:] == ['--format=json', 'some query']

    def test_empty_args(self):
        """Test empty arguments list."""
        test_args = ['nlp2cmd']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should not modify anything
            mock_main.assert_called_once()
            assert sys.argv[1:] == []

    def test_complex_polish_query(self):
        """Test complex Polish query with multiple entities."""
        test_args = ['nlp2cmd', 'znajdź pliki .log większe niż 10MB starsze niż 2 dni']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should rewrite args to include --query
            expected_args = ['--query', 'znajdź pliki .log większe niż 10MB starsze niż 2 dni']
            mock_main.assert_called_once()
            assert sys.argv[1:] == expected_args

    def test_query_starting_with_dash(self):
        """Test query that starts with dash but isn't a flag."""
        test_args = ['nlp2cmd', '-test-file with spaces']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should NOT process - starts with dash
            mock_main.assert_called_once()
            assert sys.argv[1:] == ['-test-file with spaces']

    def test_multiple_space_queries(self):
        """Test multiple arguments with spaces."""
        test_args = ['nlp2cmd', 'first query', 'second query']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should combine both as query text
            expected_args = ['--query', 'first query second query']
            mock_main.assert_called_once()
            assert sys.argv[1:] == expected_args

    def test_special_characters_in_query(self):
        """Test query with special characters."""
        test_args = ['nlp2cmd', 'znajdź pliki z nazwą "*.txt"']
        
        with patch('sys.argv', test_args), \
             patch('nlp2cmd.cli.main.main') as mock_main:
            
            cli_entry_point()
            
            # Should preserve special characters
            expected_args = ['--query', 'znajdź pliki z nazwą "*.txt"']
            mock_main.assert_called_once()
            assert sys.argv[1:] == expected_args

    @patch('nlp2cmd.cli.main.main')
    def test_main_exception_handling(self, mock_main):
        """Test that exceptions from main() are properly propagated."""
        test_args = ['nlp2cmd', 'test query']
        mock_main.side_effect = Exception("Test error")
        
        with patch('sys.argv', test_args):
            
            with pytest.raises(Exception, match="Test error"):
                cli_entry_point()
            
            # Args should still be rewritten before the exception
            assert sys.argv[1:] == ['--query', 'test query']


if __name__ == '__main__':
    pytest.main([__file__])
