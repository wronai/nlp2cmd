#!/usr/bin/env python3
"""
NLP2CMD Feedback Loop Example

Demonstrates the interactive feedback loop with:
- Error detection and analysis
- Automatic corrections
- User-guided refinement
- Confidence-based decisions
"""

from nlp2cmd import NLP2CMD, SQLAdapter, FeedbackAnalyzer
from nlp2cmd.feedback import CorrectionEngine, FeedbackType
from nlp2cmd.validators import SQLValidator


def simulate_interactive_session():
    """Simulate an interactive session with feedback loop."""

    print("=" * 70)
    print("NLP2CMD Feedback Loop Demonstration")
    print("=" * 70)

    # Setup
    adapter = SQLAdapter(
        dialect="postgresql",
        schema_context={
            "tables": ["users", "orders", "products"],
            "columns": {
                "users": ["id", "name", "email", "status"],
                "orders": ["id", "user_id", "total", "status"],
                "products": ["id", "name", "price", "stock"],
            }
        }
    )

    analyzer = FeedbackAnalyzer()
    validator = SQLValidator()
    correction_engine = CorrectionEngine()

    nlp = NLP2CMD(
        adapter=adapter,
        feedback_analyzer=analyzer,
        validator=validator,
    )

    # Scenario 1: Successful transformation
    print("\n" + "─" * 70)
    print("Scenario 1: Successful Transformation")
    print("─" * 70)

    query1 = "Show all active users"
    plan1 = {
        "intent": "select",
        "entities": {
            "table": "users",
            "columns": "*",
            "filters": [{"field": "status", "operator": "=", "value": "active"}]
        }
    }

    command1 = adapter.generate(plan1)
    validation1 = validator.validate(command1)

    feedback1 = analyzer.analyze(
        original_input=query1,
        generated_output=command1,
        validation_errors=validation1.errors,
        validation_warnings=validation1.warnings,
        dsl_type="sql"
    )

    print(f"\n📝 Input: {query1}")
    print(f"📤 Generated: {command1}")
    print(f"📊 Status: {feedback1.type.value}")
    print(f"🎯 Confidence: {feedback1.confidence:.0%}")

    if feedback1.is_success:
        print("✅ Transformation successful!")

    # Scenario 2: Transformation with warnings
    print("\n" + "─" * 70)
    print("Scenario 2: Transformation with Warnings")
    print("─" * 70)

    query2 = "Update all users to premium"
    plan2 = {
        "intent": "update",
        "entities": {
            "table": "users",
            "values": {"status": "premium"},
            "filters": []  # No WHERE clause!
        }
    }

    command2 = adapter.generate(plan2)
    validation2 = validator.validate(command2)

    feedback2 = analyzer.analyze(
        original_input=query2,
        generated_output=command2,
        validation_errors=validation2.errors,
        validation_warnings=validation2.warnings,
        dsl_type="sql"
    )

    print(f"\n📝 Input: {query2}")
    print(f"📤 Generated: {command2}")
    print(f"📊 Status: {feedback2.type.value}")
    print(f"🎯 Confidence: {feedback2.confidence:.0%}")

    if feedback2.warnings:
        print("\n⚠️  Warnings:")
        for warning in feedback2.warnings:
            print(f"   - {warning}")

    if feedback2.suggestions:
        print("\n💡 Suggestions:")
        for suggestion in feedback2.suggestions:
            print(f"   - {suggestion}")

    # Scenario 3: Syntax error with auto-correction
    print("\n" + "─" * 70)
    print("Scenario 3: Syntax Error with Auto-Correction")
    print("─" * 70)

    # Simulate a command with syntax error
    bad_command = "SELECT * FROM users WHERE (status = 'active'"  # Missing )

    syntax_check = analyzer.check_syntax(bad_command, "sql")

    print(f"\n📝 Command: {bad_command}")
    print(f"✓ Valid: {syntax_check['valid']}")

    if syntax_check['errors']:
        print("\n❌ Errors:")
        for error in syntax_check['errors']:
            print(f"   - {error}")

            # Try to get correction
            correction = correction_engine.suggest(error, bad_command, {"dsl_type": "sql"})

            if correction.get("fix"):
                print(f"\n🔧 Suggested fix (confidence: {correction['confidence']:.0%}):")
                print(f"   {correction['fix']}")

                if correction['confidence'] >= 0.8:
                    print("   ✅ Auto-applying fix...")
                    corrected = correction_engine.apply_correction(bad_command, correction)
                    print(f"   Corrected: {corrected}")

    # Scenario 4: Ambiguous input requiring clarification
    print("\n" + "─" * 70)
    print("Scenario 4: Ambiguous Input")
    print("─" * 70)

    query4 = "Delete that thing"

    feedback4 = analyzer.analyze(
        original_input=query4,
        generated_output="",
        dsl_type="sql",
        context=None  # No context
    )

    print(f"\n📝 Input: {query4}")
    print(f"📊 Status: {feedback4.type.value}")

    if feedback4.requires_user_input:
        print("\n❓ Clarification needed:")
        for question in feedback4.clarification_questions:
            print(f"   - {question}")

    # Scenario 5: Exception handling
    print("\n" + "─" * 70)
    print("Scenario 5: Exception Analysis")
    print("─" * 70)

    exceptions = [
        FileNotFoundError("Table 'customers' does not exist"),
        PermissionError("Access denied for user 'readonly'@'localhost'"),
        ConnectionError("Could not connect to database server"),
        TimeoutError("Query execution timed out after 30s"),
    ]

    for exc in exceptions:
        analysis = analyzer.analyze_exception(exc)

        print(f"\n❌ Exception: {analysis['error_type']}")
        print(f"   Message: {analysis['error_message']}")

        if analysis['suggestions']:
            print("   💡 Suggestions:")
            for s in analysis['suggestions']:
                print(f"      - {s}")

    # Scenario 6: Feedback-driven refinement loop
    print("\n" + "─" * 70)
    print("Scenario 6: Iterative Refinement")
    print("─" * 70)

    print("\nSimulating iterative refinement process:")

    iterations = [
        {
            "input": "Show sales",
            "feedback": "Ambiguous - which table?",
            "refined": "Show sales from orders"
        },
        {
            "input": "Show sales from orders",
            "feedback": "Missing time filter",
            "refined": "Show sales from orders this month"
        },
        {
            "input": "Show sales from orders this month",
            "feedback": "Success!",
            "refined": None
        }
    ]

    for i, iteration in enumerate(iterations, 1):
        print(f"\n   Iteration {i}:")
        print(f"   Input: {iteration['input']}")
        print(f"   Feedback: {iteration['feedback']}")
        if iteration['refined']:
            print(f"   → Refined: {iteration['refined']}")
        else:
            print("   ✅ Final result achieved!")

    # Summary
    print("\n" + "=" * 70)
    print("FEEDBACK LOOP SUMMARY")
    print("=" * 70)

    print("""
The NLP2CMD Feedback Loop provides:

1. 📊 Status Classification:
   - SUCCESS: Transformation completed without issues
   - PARTIAL_SUCCESS: Completed with warnings
   - SYNTAX_ERROR: Syntax issues detected
   - SCHEMA_MISMATCH: Schema-related problems
   - AMBIGUOUS_INPUT: Needs user clarification
   - SECURITY_VIOLATION: Blocked by safety policy

2. 🔧 Auto-Correction:
   - Pattern-based fixes (typos, missing tokens)
   - Confidence-based auto-apply (>80% confidence)
   - User confirmation for lower confidence

3. 💡 Suggestions:
   - Syntax improvements
   - Security recommendations
   - Performance hints

4. ❓ Clarification:
   - Generates targeted questions
   - Guides users to provide missing information

5. 🎯 Confidence Scoring:
   - Based on validation results
   - Considers error count and severity
   - Helps prioritize review needs

Usage:
    from nlp2cmd import FeedbackAnalyzer

    analyzer = FeedbackAnalyzer()
    feedback = analyzer.analyze(
        original_input="user query",
        generated_output="generated command",
        validation_errors=[],
        validation_warnings=[],
        dsl_type="sql"
    )

    if feedback.can_auto_fix:
        # Apply automatic corrections
        pass
    elif feedback.requires_user_input:
        # Ask clarification questions
        pass
""")


if __name__ == "__main__":
    simulate_interactive_session()
