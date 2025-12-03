"""
LLM-as-judge module.
Uses one LLM to evaluate another LLM's outputs.
"""

from typing import Dict, Optional, Callable


def llm_judge_pairwise(
    llm: Callable[[str], str],
    input_text: str,
    output_a: str,
    output_b: str,
    criteria: str = "Which output is better?"
) -> str:
    """
    Use LLM to judge which of two outputs is better.
    
    Returns: "A" or "B"
    """
    prompt = f"""You are evaluating two LLM outputs for the same input.

Input: {input_text}

Output A:
{output_a}

Output B:
{output_b}

Criteria: {criteria}

Which output is better? Respond with only "A" or "B"."""
    
    response = llm(prompt)
    response = response.strip().upper()
    
    # Extract A or B
    if "A" in response and "B" not in response[:response.find("A")+1]:
        return "A"
    elif "B" in response:
        return "B"
    else:
        # Default to A if unclear
        return "A"


def llm_judge_score(
    llm: Callable[[str], str],
    input_text: str,
    output: str,
    criteria: str,
    scale: str = "1-5"
) -> int:
    """
    Use LLM to score an output on a scale.
    
    Returns: Score as integer
    """
    prompt = f"""You are evaluating an LLM output.

Input: {input_text}

Output:
{output}

Criteria: {criteria}

Score this output on a scale of {scale}. Respond with only the number."""
    
    response = llm(prompt)
    response = response.strip()
    
    # Extract number
    try:
        score = int(response.split()[0])
        # Clamp to scale
        if scale == "1-5":
            score = max(1, min(5, score))
        return score
    except (ValueError, IndexError):
        # Default to middle of scale
        return 3


def llm_judge_label(
    llm: Callable[[str], str],
    input_text: str,
    output: str,
    expected_behavior: Optional[str],
    label_categories: Dict[str, List[str]]
) -> Dict[str, str]:
    """
    Use LLM to label an output with multiple categories.
    
    Args:
        label_categories: Dict mapping category name to list of possible values
            e.g., {"correctness": ["correct", "partially_correct", "wrong"]}
    
    Returns: Dict of category -> label value
    """
    labels = {}
    
    for category, possible_values in label_categories.items():
        values_str = ", ".join(possible_values)
        criteria = f"Evaluate {category}"
        if expected_behavior:
            criteria += f". Expected behavior: {expected_behavior}"
        
        prompt = f"""You are evaluating an LLM output.

Input: {input_text}

Output:
{output}

Criteria: {criteria}

Categorize this output as one of: {values_str}

Respond with only the category value."""
        
        response = llm(prompt)
        response = response.strip().lower()
        
        # Find matching value
        matched_value = None
        for value in possible_values:
            if value.lower() in response or response in value.lower():
                matched_value = value
                break
        
        # Default to first value if no match
        labels[category] = matched_value or possible_values[0]
    
    return labels


class LLMJudge:
    """Wrapper for LLM-as-judge functionality."""
    
    def __init__(self, llm: Callable[[str], str]):
        """Initialize with an LLM function."""
        self.llm = llm
    
    def pairwise(
        self,
        input_text: str,
        output_a: str,
        output_b: str,
        criteria: str = "Which output is better?"
    ) -> str:
        """Judge which output is better."""
        return llm_judge_pairwise(self.llm, input_text, output_a, output_b, criteria)
    
    def score(
        self,
        input_text: str,
        output: str,
        criteria: str,
        scale: str = "1-5"
    ) -> int:
        """Score an output."""
        return llm_judge_score(self.llm, input_text, output, criteria, scale)
    
    def label(
        self,
        input_text: str,
        output: str,
        expected_behavior: Optional[str],
        label_categories: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """Label an output with multiple categories."""
        return llm_judge_label(
            self.llm,
            input_text,
            output,
            expected_behavior,
            label_categories
        )

