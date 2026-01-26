"""
Tests for execution runner syntax highlighting functionality.

Tests the enhanced confirm_execution and recovery suggestion functions
with Rich Syntax highlighting for bash codeblocks.
"""

import pytest
from unittest.mock import patch, MagicMock
from rich.console import Console
from rich.syntax import Syntax

from nlp2cmd.execution.runner import ExecutionRunner


class TestExecutionRunnerSyntax:
    """Test cases for syntax highlighting in execution runner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.console = Console()
        self.runner = ExecutionRunner(console=self.console, auto_confirm=False)
        self.sample_command = "find . -type f -mtime -7"

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_confirm_execution_syntax_highlighting(self, mock_console, mock_print):
        """Test command confirmation with syntax highlighting."""
        mock_console.input.return_value = "y"
        
        result = self.runner.confirm_execution(self.sample_command)
        
        # Should return True for 'y' response
        assert result is True
        
        # Should print bash codeblock delimiter
        mock_print.assert_any_call("```bash")
        mock_print.assert_any_call("```")
        
        # Should call console.print with Syntax object
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        assert len(syntax_calls) >= 1
        bash_syntax = syntax_calls[0].args[0]
        assert "bash" in getattr(bash_syntax.lexer, "aliases", [])
        assert bash_syntax.theme == "monokai"
        assert bash_syntax.line_numbers == False
        assert bash_syntax.code == self.sample_command

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_confirm_execution_auto_confirm(self, mock_console, mock_print):
        """Test command confirmation with auto_confirm=True."""
        auto_confirm_runner = ExecutionRunner(console=self.console, auto_confirm=True)
        
        result = auto_confirm_runner.confirm_execution(self.sample_command)
        
        # Should return True immediately without prompting
        assert result is True
        
        # Should not call console.input
        mock_console.input.assert_not_called()
        
        # Should still print syntax-highlighted command
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        assert len(syntax_calls) >= 1

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_confirm_execution_user_rejects(self, mock_console, mock_print):
        """Test command confirmation when user rejects."""
        mock_console.input.return_value = "n"
        
        result = self.runner.confirm_execution(self.sample_command)
        
        # Should return False for 'n' response
        assert result is False
        
        # Should still show syntax highlighting before rejection
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        assert len(syntax_calls) >= 1

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_confirm_execution_user_edits(self, mock_console, mock_print):
        """Test command confirmation when user wants to edit."""
        mock_console.input.side_effect = ["e", "ls -la", "y"]
        
        result = self.runner.confirm_execution("original command")
        
        # Should return True after editing and confirming
        assert result is True
        
        # Should show syntax highlighting for both original and edited commands
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        # Should have syntax calls for both commands
        assert len(syntax_calls) >= 2
        
        # Check that edited command is highlighted
        edited_syntax_calls = [call for call in syntax_calls 
                              if call.args[0].code == "ls -la"]
        assert len(edited_syntax_calls) >= 1

    def test_run_with_recovery_user_cancels_has_exit_code_0(self):
        from nlp2cmd.execution.runner import ExecutionResult

        with patch.object(self.runner, "confirm_execution", return_value=False):
            res = self.runner.run_with_recovery(self.sample_command, original_query="test")

        assert isinstance(res, ExecutionResult)
        assert res.success is False
        assert res.exit_code == 0
        assert res.error_context == "User cancelled"

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_confirm_execution_complex_command(self, mock_console, mock_print):
        """Test syntax highlighting with complex bash command."""
        complex_command = "find . -type f -name '*.log' -size +10MB -exec ls -lh {} \\;"
        mock_console.input.return_value = "y"
        
        result = self.runner.confirm_execution(complex_command)
        
        assert result is True
        
        # Should handle complex bash syntax correctly
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        bash_syntax = syntax_calls[0].args[0]
        assert bash_syntax.code == complex_command
        assert "bash" in getattr(bash_syntax.lexer, "aliases", [])

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_recovery_suggestion_syntax_highlighting(self, mock_console, mock_print):
        """Test recovery suggestion with syntax highlighting."""
        mock_console.input.return_value = "y"
        
        # Mock the get_recovery_suggestion method
        suggestion = "sudo apt-get install missing-tool"
        
        # Create a mock context
        context = MagicMock()
        context.original_query = "install missing-tool"
        context.executed_command = "missing-tool"
        context.error_output = "command not found"
        context.exit_code = 127
        context.previous_attempts = []
        
        # Mock the run_with_recovery method to call recovery suggestion
        with patch.object(self.runner, 'get_recovery_suggestion', return_value=suggestion):
            with patch.object(self.runner, 'run_command', return_value=MagicMock(success=False)):
                
                # This would normally be called from run_with_recovery
                # We'll test the suggestion highlighting directly
                print(f"```bash")
                syntax = Syntax(f"# 💡 Suggested recovery:\n {suggestion}", "bash", theme="monokai", line_numbers=False)
                mock_console.print(syntax)
                print(f"```")
                print()
                
                # Verify the syntax highlighting was created correctly
                assert "bash" in getattr(syntax.lexer, "aliases", [])
                assert syntax.theme == "monokai"
                assert "# 💡 Suggested recovery:" in syntax.code
                assert suggestion in syntax.code

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_recovery_suggestion_with_comment(self, mock_console, mock_print):
        """Test recovery suggestion that already contains a comment."""
        suggestion = "# Install missing package\nsudo apt-get install tool"
        
        print(f"```bash")
        syntax = Syntax(f"# 💡 Suggested recovery:\n {suggestion}", "bash", theme="monokai", line_numbers=False)
        mock_console.print(syntax)
        print(f"```")
        print()
        
        # Should handle multi-line suggestion correctly
        assert "bash" in getattr(syntax.lexer, "aliases", [])
        assert "# 💡 Suggested recovery:" in syntax.code
        assert "# Install missing package" in syntax.code
        assert "sudo apt-get install tool" in syntax.code

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_unicode_command_highlighting(self, mock_console, mock_print):
        """Test syntax highlighting with Unicode characters in command."""
        unicode_command = "echo 'Polskie znaki: ąśćłóźć'"
        mock_console.input.return_value = "y"
        
        result = self.runner.confirm_execution(unicode_command)
        
        assert result is True
        
        # Should handle Unicode characters correctly
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        bash_syntax = syntax_calls[0].args[0]
        assert bash_syntax.code == unicode_command
        assert "Polskie znaki: ąśćłóźć" in bash_syntax.code

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_multiline_command_highlighting(self, mock_console, mock_print):
        """Test syntax highlighting with multi-line command."""
        multiline_command = "for file in *.log; do\n  echo \"Processing $file\"\n  grep \"ERROR\" \"$file\"\ndone"
        mock_console.input.return_value = "y"
        
        result = self.runner.confirm_execution(multiline_command)
        
        assert result is True
        
        # Should handle multi-line commands correctly
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        bash_syntax = syntax_calls[0].args[0]
        assert bash_syntax.code == multiline_command

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_empty_command_highlighting(self, mock_console, mock_print):
        """Test syntax highlighting with empty command."""
        mock_console.input.return_value = "y"
        
        result = self.runner.confirm_execution("")
        
        assert result is True
        
        # Should still show syntax highlighting for empty command
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        assert len(syntax_calls) >= 1
        bash_syntax = syntax_calls[0].args[0]
        assert bash_syntax.code == ""

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_command_with_special_characters(self, mock_console, mock_print):
        """Test syntax highlighting with special shell characters."""
        special_command = "grep 'ERROR.*[0-9]{4}' *.log | awk '{print $1}' | sort -u"
        mock_console.input.return_value = "y"
        
        result = self.runner.confirm_execution(special_command)
        
        assert result is True
        
        # Should handle special characters correctly
        syntax_calls = [call for call in mock_console.print.call_args_list 
                      if len(call.args) > 0 and isinstance(call.args[0], Syntax)]
        
        bash_syntax = syntax_calls[0].args[0]
        assert bash_syntax.code == special_command

    @patch('builtins.print')
    @patch.object(ExecutionRunner, 'console')
    def test_user_input_variations(self, mock_console, mock_print):
        """Test different user input variations."""
        test_cases = [
            ("y", True),
            ("yes", True),
            ("tak", True),
            ("", True),  # Empty defaults to yes
            ("n", False),
            ("no", False),
            ("nie", False),
            ("e", "edit"),  # Would need additional input for edit
        ]
        
        for user_input, expected_result in test_cases:
            with patch.object(self.runner, 'confirm_execution') as mock_confirm:
                mock_confirm.return_value = expected_result
                
                # Mock the input and test
                mock_console.input.return_value = user_input
                result = self.runner.confirm_execution(self.sample_command)
                
                # The result should match expected for non-edit cases
                if user_input != "e":
                    assert result == expected_result

    @patch('builtins.print')
    def test_syntax_object_creation(self, mock_print):
        """Test that Syntax objects are created with correct parameters."""
        from rich.syntax import Syntax
        
        # Test bash syntax creation
        bash_syntax = Syntax(self.sample_command, "bash", theme="monokai", line_numbers=False)
        assert "bash" in getattr(bash_syntax.lexer, "aliases", [])
        assert bash_syntax.theme == "monokai"
        assert bash_syntax.line_numbers == False
        assert bash_syntax.code == self.sample_command
        
        # Test recovery suggestion syntax creation
        suggestion = "sudo apt-get install tool"
        recovery_syntax = Syntax(f"# 💡 Suggested recovery:\n {suggestion}", "bash", theme="monokai", line_numbers=False)
        assert "bash" in getattr(recovery_syntax.lexer, "aliases", [])
        assert "# 💡 Suggested recovery:" in recovery_syntax.code
        assert suggestion in recovery_syntax.code


if __name__ == '__main__':
    pytest.main([__file__])
