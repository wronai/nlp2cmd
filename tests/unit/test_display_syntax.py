"""
Tests for display module syntax highlighting functionality.

Tests the enhanced display_command_result function with Rich Syntax
highlighting for bash, SQL, and YAML codeblocks.
"""

import pytest
from unittest.mock import patch, MagicMock
from rich.console import Console
from rich.syntax import Syntax

from nlp2cmd.cli.display import display_command_result


class TestDisplaySyntaxHighlighting:
    """Test cases for syntax highlighting in display module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.console = Console()
        self.sample_command = "find . -type f -mtime -7"
        self.sample_metadata = {
            "dsl": "auto",
            "query": "znajdź pliki zmodyfikowane ostatnie 7 dni",
            "status": "success",
            "confidence": 1.0,
            "generated_command": "find . -type f -mtime -7"
        }

    @patch('nlp2cmd.cli.display.console.print')
    def test_bash_syntax_highlighting(self, mock_print):
        """Test bash command syntax highlighting."""
        display_command_result(
            command=self.sample_command,
            metadata=self.sample_metadata,
            show_yaml=True
        )
        
        # Should print bash codeblock delimiter
        mock_print.assert_any_call("```bash")
        
        # Should call console.print with Syntax object for bash
        syntax_calls = [call for call in mock_print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        assert len(syntax_calls) >= 1
        bash_syntax = syntax_calls[0].args[0]
        assert bash_syntax.lexer == "bash"
        assert bash_syntax.theme == "monokai"
        assert bash_syntax.line_numbers == False

    @patch('nlp2cmd.cli.display.console.print')
    def test_yaml_syntax_highlighting(self, mock_print):
        """Test YAML metadata syntax highlighting."""
        display_command_result(
            command=self.sample_command,
            metadata=self.sample_metadata,
            show_yaml=True
        )
        
        # Should print yaml codeblock delimiter
        mock_print.assert_any_call("```yaml")
        
        # Should call console.print with Syntax object for yaml
        syntax_calls = [call for call in mock_print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        yaml_syntax_calls = [call for call in syntax_calls if call.args[0].lexer == "yaml"]
        assert len(yaml_syntax_calls) >= 1
        
        yaml_syntax = yaml_syntax_calls[0].args[0]
        assert yaml_syntax.lexer == "yaml"
        assert yaml_syntax.theme == "monokai"
        assert yaml_syntax.line_numbers == False

    @patch('nlp2cmd.cli.display.console.print')
    def test_no_command_no_highlighting(self, mock_print):
        """Test behavior with empty command."""
        display_command_result(
            command="",
            metadata=self.sample_metadata,
            show_yaml=True
        )
        
        # Should not print bash codeblock for empty command
        bash_calls = [call for call in mock_print.call_args_list 
                     if "```bash" in str(call)]
        assert len(bash_calls) == 0

    @patch('nlp2cmd.cli.display.console.print')
    def test_no_metadata_no_yaml_highlighting(self, mock_print):
        """Test behavior with no metadata."""
        display_command_result(
            command=self.sample_command,
            metadata=None,
            show_yaml=True
        )
        
        # Should not print yaml codeblock for no metadata
        yaml_calls = [call for call in mock_print.call_args_list 
                     if "```yaml" in str(call)]
        assert len(yaml_calls) == 0

    @patch('nlp2cmd.cli.display.console.print')
    def test_show_yaml_disabled(self, mock_print):
        """Test behavior when YAML display is disabled."""
        display_command_result(
            command=self.sample_command,
            metadata=self.sample_metadata,
            show_yaml=False
        )
        
        # Should print bash but not yaml
        bash_calls = [call for call in mock_print.call_args_list 
                     if "```bash" in str(call)]
        yaml_calls = [call for call in mock_print.call_args_list 
                     if "```yaml" in str(call)]
        
        assert len(bash_calls) >= 1
        assert len(yaml_calls) == 0

    @patch('nlp2cmd.cli.display.console.print')
    def test_complex_bash_command(self, mock_print):
        """Test syntax highlighting with complex bash command."""
        complex_command = "find . -type f -name '*.log' -size +10MB -exec ls -lh {} \\;"
        
        display_command_result(
            command=complex_command,
            metadata=self.sample_metadata,
            show_yaml=True
        )
        
        # Should handle complex bash syntax correctly
        syntax_calls = [call for call in mock_print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        bash_syntax_calls = [call for call in syntax_calls if call.args[0].lexer == "bash"]
        assert len(bash_syntax_calls) >= 1
        
        bash_syntax = bash_syntax_calls[0].args[0]
        assert complex_command in bash_syntax.code

    @patch('nlp2cmd.cli.display.console.print')
    def test_complex_yaml_metadata(self, mock_print):
        """Test syntax highlighting with complex YAML metadata."""
        complex_metadata = {
            "dsl": "auto",
            "query": "znajdź pliki zmodyfikowane ostatnie 7 dni",
            "status": "success",
            "confidence": 1.0,
            "generated_command": "find . -type f -mtime -7",
            "errors": [],
            "warnings": ["This is a warning"],
            "suggestions": ["Consider using -exec"],
            "resource_metrics": {
                "time_ms": 25.2,
                "cpu_percent": 0.0,
                "memory_mb": 56.8,
                "energy_mj": 0.219
            },
            "token_estimate": {
                "total": 1,
                "input": 1,
                "output": 0,
                "cost_usd": 2.0e-05,
                "model_tier": "small"
            }
        }
        
        display_command_result(
            command=self.sample_command,
            metadata=complex_metadata,
            show_yaml=True
        )
        
        # Should handle complex YAML structure correctly
        syntax_calls = [call for call in mock_print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        yaml_syntax_calls = [call for call in syntax_calls if call.args[0].lexer == "yaml"]
        assert len(yaml_syntax_calls) >= 1
        
        yaml_syntax = yaml_syntax_calls[0].args[0]
        assert "resource_metrics:" in yaml_syntax.code
        assert "token_estimate:" in yaml_syntax.code

    @patch('nlp2cmd.cli.display.console.print')
    def test_command_with_newlines(self, mock_print):
        """Test syntax highlighting with multi-line command."""
        multiline_command = "for file in *.log; do\n  echo \"Processing $file\"\n  grep \"ERROR\" \"$file\"\ndone"
        
        display_command_result(
            command=multiline_command,
            metadata=self.sample_metadata,
            show_yaml=True
        )
        
        # Should handle multi-line bash syntax correctly
        syntax_calls = [call for call in mock_print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        bash_syntax_calls = [call for call in syntax_calls if call.args[0].lexer == "bash"]
        assert len(bash_syntax_calls) >= 1
        
        bash_syntax = bash_syntax_calls[0].args[0]
        assert multiline_command in bash_syntax.code

    @patch('nlp2cmd.cli.display.console.print')
    def test_unicode_characters_in_command(self, mock_print):
        """Test syntax highlighting with Unicode characters."""
        unicode_command = "echo 'Polskie znaki: ąśćłóźć'"
        
        display_command_result(
            command=unicode_command,
            metadata=self.sample_metadata,
            show_yaml=True
        )
        
        # Should handle Unicode characters correctly
        syntax_calls = [call for call in mock_print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        bash_syntax_calls = [call for call in syntax_calls if call.args[0].lexer == "bash"]
        assert len(bash_syntax_calls) >= 1
        
        bash_syntax = bash_syntax_calls[0].args[0]
        assert unicode_command in bash_syntax.code

    @patch('nlp2cmd.cli.display.console.print')
    def test_metrics_string_without_yaml(self, mock_print):
        """Test metrics string display when YAML is disabled."""
        metrics_str = "Time: 25.2ms | CPU: 0.0% | Memory: 56.8MB"
        
        display_command_result(
            command=self.sample_command,
            metadata=None,
            metrics_str=metrics_str,
            show_yaml=False
        )
        
        # Should print metrics directly
        metrics_calls = [call for call in mock_print.call_args_list 
                        if metrics_str in str(call)]
        assert len(metrics_calls) >= 1

    @patch('nlp2cmd.cli.display.console.print')
    def test_empty_command_with_whitespace(self, mock_print):
        """Test behavior with command containing only whitespace."""
        display_command_result(
            command="   \n\t  ",
            metadata=self.sample_metadata,
            show_yaml=True
        )
        
        # Should not print bash codeblock for whitespace-only command
        bash_calls = [call for call in mock_print.call_args_list 
                     if "```bash" in str(call)]
        assert len(bash_calls) == 0

    @patch('nlp2cmd.cli.display.console.print')
    def test_title_parameter_ignored(self, mock_print):
        """Test that title parameter is ignored in new format."""
        display_command_result(
            command=self.sample_command,
            metadata=self.sample_metadata,
            show_yaml=True,
            title="Custom Title"
        )
        
        # Should not use Rich Panel with title
        # Should use simple codeblock format instead
        bash_calls = [call for call in mock_print.call_args_list 
                     if "```bash" in str(call)]
        assert len(bash_calls) >= 1


if __name__ == '__main__':
    pytest.main([__file__])
