#!/usr/bin/env python3
"""
Prompt Quality Validator

Analyzes prompts for quality issues and suggests improvements based on
the Prompting Canon best practices.

Usage:
    python prompt-validator.py "Your prompt here"
    python prompt-validator.py --file prompt.txt
    python prompt-validator.py --interactive
"""

import re
import sys
import argparse
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class Issue:
    """Represents a prompt quality issue."""
    severity: str  # 'error', 'warning', 'suggestion'
    category: str
    message: str
    fix: str = ""


class PromptValidator:
    """Validates prompts against best practices."""
    
    def __init__(self):
        self.issues: List[Issue] = []
        
    def validate(self, prompt: str) -> Tuple[int, List[Issue]]:
        """
        Validate a prompt and return score (0-100) and issues.
        
        Args:
            prompt: The prompt text to validate
            
        Returns:
            Tuple of (score, list of issues)
        """
        self.issues = []
        
        # Run all checks
        self._check_clarity(prompt)
        self._check_structure(prompt)
        self._check_examples(prompt)
        self._check_constraints(prompt)
        self._check_format_spec(prompt)
        self._check_anti_patterns(prompt)
        self._check_length(prompt)
        
        # Calculate score
        score = self._calculate_score()
        
        return score, self.issues
    
    def _check_clarity(self, prompt: str):
        """Check for clarity issues."""
        # Check for vague instructions
        vague_terms = ['helpful', 'accurate', 'good', 'best', 'quality', 
                       'comprehensive', 'detailed']
        found_vague = [term for term in vague_terms 
                       if term.lower() in prompt.lower()]
        
        if found_vague:
            self.issues.append(Issue(
                severity='warning',
                category='Clarity',
                message=f"Vague terms found: {', '.join(found_vague)}",
                fix="Replace with specific, measurable criteria"
            ))
        
        # Check for implicit task
        task_indicators = ['task:', 'goal:', 'objective:', 'you should']
        if not any(indicator in prompt.lower() for indicator in task_indicators):
            self.issues.append(Issue(
                severity='error',
                category='Clarity',
                message="No explicit task statement found",
                fix="Add 'Task:' or 'Goal:' section with clear objective"
            ))
    
    def _check_structure(self, prompt: str):
        """Check for structural organization."""
        # Check for delimiters/sections
        has_delimiters = bool(re.search(r'(###|##|#|\n-{3,}|\n={3,})', prompt))
        has_xml_tags = bool(re.search(r'<\w+>', prompt))
        
        if not has_delimiters and not has_xml_tags and len(prompt) > 200:
            self.issues.append(Issue(
                severity='warning',
                category='Structure',
                message="Long prompt without clear structure",
                fix="Add headers (##), delimiters (---), or XML tags (<section>)"
            ))
        
        # Check for mixed instructions and data
        if '```' in prompt or 'example' in prompt.lower():
            if not has_xml_tags and not has_delimiters:
                self.issues.append(Issue(
                    severity='suggestion',
                    category='Structure',
                    message="Consider using tags to separate instructions from examples",
                    fix="Use <instructions> and <examples> tags"
                ))
    
    def _check_examples(self, prompt: str):
        """Check for examples and few-shot patterns."""
        has_examples = 'example' in prompt.lower() or 'input:' in prompt.lower()
        
        if len(prompt) > 300 and not has_examples:
            self.issues.append(Issue(
                severity='suggestion',
                category='Examples',
                message="No examples provided for complex task",
                fix="Add 2-3 few-shot examples showing desired behavior"
            ))
        
        # Check example consistency
        if has_examples:
            input_count = prompt.lower().count('input:')
            output_count = prompt.lower().count('output:')
            
            if input_count != output_count:
                self.issues.append(Issue(
                    severity='warning',
                    category='Examples',
                    message=f"Mismatched examples: {input_count} inputs, {output_count} outputs",
                    fix="Ensure each input has corresponding output"
                ))
    
    def _check_constraints(self, prompt: str):
        """Check for constraints and boundaries."""
        constraint_indicators = [
            'constraint', 'don\'t', 'must', 'should', 'required',
            'limit', 'boundary', 'rule'
        ]
        
        has_constraints = any(ind in prompt.lower() for ind in constraint_indicators)
        
        if len(prompt) > 400 and not has_constraints:
            self.issues.append(Issue(
                severity='warning',
                category='Constraints',
                message="No explicit constraints specified",
                fix="Add section listing what to do and what to avoid"
            ))
        
        # Check for negative-only constraints
        negative_pattern = r"(don't|do not|never|avoid)\s+(\w+)"
        negatives = re.findall(negative_pattern, prompt, re.IGNORECASE)
        
        if len(negatives) > 2:
            self.issues.append(Issue(
                severity='suggestion',
                category='Constraints',
                message="Multiple negative constraints without positive alternatives",
                fix="Balance 'don't X' with 'do Y instead'"
            ))
    
    def _check_format_spec(self, prompt: str):
        """Check for output format specification."""
        format_indicators = [
            'format:', 'output:', 'response format', 'schema', 'structure',
            'json', 'markdown', 'heading'
        ]
        
        has_format = any(ind in prompt.lower() for ind in format_indicators)
        
        if len(prompt) > 200 and not has_format:
            self.issues.append(Issue(
                severity='error',
                category='Format',
                message="No output format specified",
                fix="Add 'Output Format:' section with example or schema"
            ))
        
        # Check for JSON without schema
        if 'json' in prompt.lower():
            has_schema = bool(re.search(r'\{[^}]*"[^"]*":\s*[^}]*\}', prompt))
            if not has_schema:
                self.issues.append(Issue(
                    severity='warning',
                    category='Format',
                    message="JSON requested but no schema provided",
                    fix="Include example JSON structure"
                ))
    
    def _check_anti_patterns(self, prompt: str):
        """Check for known anti-patterns."""
        # Check for "be helpful"
        if re.search(r'\bbe\s+(helpful|accurate|good)\b', prompt, re.IGNORECASE):
            self.issues.append(Issue(
                severity='warning',
                category='Anti-pattern',
                message="Generic instruction like 'be helpful' found",
                fix="Replace with specific behavioral guidelines"
            ))
        
        # Check for too many priorities
        priorities = re.findall(r'\d+\.\s+\w+', prompt)
        if len(priorities) > 5:
            self.issues.append(Issue(
                severity='suggestion',
                category='Anti-pattern',
                message=f"{len(priorities)} numbered items - may be too many priorities",
                fix="Reduce to 3-5 key points or organize hierarchically"
            ))
        
        # Check for absolute terms without escape hatches
        absolutes = ['always', 'never', 'must', 'cannot']
        found_absolutes = [term for term in absolutes 
                          if term.lower() in prompt.lower()]
        
        if len(found_absolutes) > 3:
            self.issues.append(Issue(
                severity='suggestion',
                category='Anti-pattern',
                message=f"Multiple absolute terms: {', '.join(found_absolutes)}",
                fix="Add escape hatches for edge cases"
            ))
    
    def _check_length(self, prompt: str):
        """Check prompt length considerations."""
        word_count = len(prompt.split())
        
        if word_count < 20:
            self.issues.append(Issue(
                severity='warning',
                category='Length',
                message=f"Very short prompt ({word_count} words)",
                fix="Add more context, constraints, and examples"
            ))
        
        if word_count > 1000:
            self.issues.append(Issue(
                severity='suggestion',
                category='Length',
                message=f"Very long prompt ({word_count} words)",
                fix="Consider prompt chaining or moving references to separate context"
            ))
    
    def _calculate_score(self) -> int:
        """Calculate overall prompt quality score."""
        base_score = 100
        
        # Deduct points based on issues
        for issue in self.issues:
            if issue.severity == 'error':
                base_score -= 15
            elif issue.severity == 'warning':
                base_score -= 8
            elif issue.severity == 'suggestion':
                base_score -= 3
        
        return max(0, min(100, base_score))


def print_report(score: int, issues: List[Issue], prompt: str):
    """Print validation report."""
    print("=" * 70)
    print("PROMPT QUALITY REPORT")
    print("=" * 70)
    
    # Score and grade
    if score >= 90:
        grade = "EXCELLENT"
        emoji = "🌟"
    elif score >= 75:
        grade = "GOOD"
        emoji = "✅"
    elif score >= 60:
        grade = "FAIR"
        emoji = "⚠️"
    else:
        grade = "NEEDS IMPROVEMENT"
        emoji = "❌"
    
    print(f"\nOverall Score: {score}/100 - {grade} {emoji}\n")
    
    # Prompt stats
    word_count = len(prompt.split())
    char_count = len(prompt)
    print(f"Prompt Length: {word_count} words, {char_count} characters\n")
    
    # Issues by severity
    errors = [i for i in issues if i.severity == 'error']
    warnings = [i for i in issues if i.severity == 'warning']
    suggestions = [i for i in issues if i.severity == 'suggestion']
    
    if errors:
        print(f"❌ ERRORS ({len(errors)}):")
        for issue in errors:
            print(f"  [{issue.category}] {issue.message}")
            if issue.fix:
                print(f"    → Fix: {issue.fix}")
        print()
    
    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        for issue in warnings:
            print(f"  [{issue.category}] {issue.message}")
            if issue.fix:
                print(f"    → Fix: {issue.fix}")
        print()
    
    if suggestions:
        print(f"💡 SUGGESTIONS ({len(suggestions)}):")
        for issue in suggestions:
            print(f"  [{issue.category}] {issue.message}")
            if issue.fix:
                print(f"    → Fix: {issue.fix}")
        print()
    
    if not issues:
        print("✨ No issues found! This prompt follows best practices.\n")
    
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate prompt quality against best practices"
    )
    parser.add_argument(
        'prompt',
        nargs='?',
        help='Prompt text to validate'
    )
    parser.add_argument(
        '--file', '-f',
        help='Read prompt from file'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode'
    )
    
    args = parser.parse_args()
    
    # Get prompt text
    if args.interactive:
        print("Enter your prompt (Ctrl+D or Ctrl+Z when done):")
        prompt = sys.stdin.read()
    elif args.file:
        with open(args.file, 'r') as f:
            prompt = f.read()
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        return 1
    
    # Validate
    validator = PromptValidator()
    score, issues = validator.validate(prompt)
    
    # Print report
    print_report(score, issues, prompt)
    
    # Return exit code based on score
    if score >= 75:
        return 0
    elif score >= 60:
        return 1
    else:
        return 2


if __name__ == '__main__':
    sys.exit(main())
