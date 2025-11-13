"""Offline evaluation using LLM judges"""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI


client = OpenAI()


def evaluate_output_with_llm_judge(
    input_text: str,
    output_text: str,
    criteria: str = "clarity and usefulness",
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Use an LLM as a judge to score output quality.
    
    Args:
        input_text: Original input
        output_text: LLM output to evaluate
        criteria: Evaluation criteria
        model: Model to use as judge
    
    Returns:
        Dictionary with scores and reasoning
    """
    prompt = f"""Evaluate this LLM interaction:

Input: {input_text}
Output: {output_text}

Criteria: {criteria}

Rate the output on a scale of 1-10 for:
1. Clarity: Is the output clear and easy to understand?
2. Usefulness: Does the output help solve the problem?
3. Accuracy: Is the output factually correct?

Return JSON: {{
    "clarity": 1-10,
    "usefulness": 1-10,
    "accuracy": 1-10,
    "overall": 1-10,
    "reason": "brief explanation"
}}
"""
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    return json.loads(response.choices[0].message.content)


def evaluate_prompt_version(
    logged_interactions: List[Dict[str, Any]],
    prompt_version: str,
    criteria: str = "clarity and usefulness"
) -> Dict[str, Any]:
    """
    Evaluate all interactions for a prompt version.
    
    Args:
        logged_interactions: List of logged interactions
        prompt_version: Prompt version to evaluate
        criteria: Evaluation criteria
    
    Returns:
        Aggregated metrics for the prompt version
    """
    version_interactions = [
        i for i in logged_interactions
        if i.get("prompt_version") == prompt_version
    ]
    
    if not version_interactions:
        return {}
    
    scores = []
    for interaction in version_interactions:
        try:
            score = evaluate_output_with_llm_judge(
                input_text=interaction.get("input", ""),
                output_text=interaction.get("output", ""),
                criteria=criteria
            )
            scores.append(score)
        except Exception as e:
            print(f"Error evaluating interaction: {e}")
            continue
    
    if not scores:
        return {}
    
    return {
        "prompt_version": prompt_version,
        "sample_size": len(scores),
        "avg_clarity": sum(s["clarity"] for s in scores) / len(scores),
        "avg_usefulness": sum(s["usefulness"] for s in scores) / len(scores),
        "avg_accuracy": sum(s["accuracy"] for s in scores) / len(scores),
        "avg_overall": sum(s["overall"] for s in scores) / len(scores)
    }


def compare_prompt_versions(
    logged_interactions: List[Dict[str, Any]],
    criteria: str = "clarity and usefulness"
) -> Dict[str, Dict[str, Any]]:
    """
    Compare multiple prompt versions.
    
    Args:
        logged_interactions: List of logged interactions
        criteria: Evaluation criteria
    
    Returns:
        Dictionary mapping prompt versions to their metrics
    """
    versions = set(i.get("prompt_version") for i in logged_interactions)
    
    results = {}
    for version in versions:
        results[version] = evaluate_prompt_version(
            logged_interactions,
            version,
            criteria
        )
    
    return results


def load_logged_interactions(
    file_path: Optional[str] = None,
    prompt_version: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load logged interactions from file or database.
    
    Args:
        file_path: Path to JSON file (if loading from file)
        prompt_version: Filter by prompt version (if loading from DB)
    
    Returns:
        List of logged interactions
    """
    if file_path:
        # Load from file
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        # Load from database
        from src.feedback import get_feedback_data
        feedback_data = get_feedback_data(prompt_version=prompt_version)
        
        # Convert to interaction format
        return [
            {
                "input": f.get("input", ""),
                "output": f.get("output", ""),
                "prompt_version": f.get("prompt_version", "unknown"),
                "model": f.get("model", "unknown")
            }
            for f in feedback_data
        ]

