"""Test prompt file presence and CSV schema validation."""

import pytest
import pandas as pd
from pathlib import Path


def test_prompt_files_exist():
    """Test that all required prompt files exist."""
    base_dir = Path(__file__).parent.parent

    # Core prompt files
    required_prompts = [
        'prompts/query_generation.txt',
        'prompts/vibe_check.txt',
    ]

    # Judge prompt files
    judge_prompts = [
        'prompts/judges/relevance.txt',
        'prompts/judges/groundedness.txt',
        'prompts/judges/completeness.txt',
        'prompts/judges/actionability.txt',
        'prompts/judges/tone_empathy.txt',
        'prompts/judges/safety_compliance.txt'
    ]

    all_prompts = required_prompts + judge_prompts

    for prompt_path in all_prompts:
        full_path = base_dir / prompt_path
        assert full_path.exists(), f"Prompt file missing: {prompt_path}"


def test_prompt_files_have_content():
    """Test that prompt files contain non-empty content."""
    base_dir = Path(__file__).parent.parent

    required_prompts = [
        'prompts/generate_query.txt',
        'prompts/vibe_check.txt',
        'prompts/rag_answer.txt'
    ]

    for prompt_path in required_prompts:
        full_path = base_dir / prompt_path
        if full_path.exists():
            content = full_path.read_text()
            assert len(content.strip()) > 0, f"Prompt file empty: {prompt_path}"


def test_prompt_placeholders():
    """Test that prompts contain expected placeholders."""
    base_dir = Path(__file__).parent.parent

    # Define expected placeholders for each prompt
    expected_placeholders = {
        'prompts/query_generation.txt': ['{persona}', '{problem}', '{modifier}'],
        'prompts/vibe_check.txt': ['{query}', '{persona}']
    }

    for prompt_path, placeholders in expected_placeholders.items():
        full_path = base_dir / prompt_path
        if full_path.exists():
            content = full_path.read_text()
            for placeholder in placeholders:
                assert placeholder in content, \
                    f"Placeholder {placeholder} not found in {prompt_path}"


def test_synthetic_queries_csv_schema():
    """Test that synthetic_queries.csv has correct schema."""
    base_dir = Path(__file__).parent.parent
    csv_file = base_dir / 'data/outputs/synthetic_queries.csv'

    if csv_file.exists():
        df = pd.read_csv(csv_file)

        # Required columns
        required_cols = ['persona_id', 'problem_id', 'modifier_id', 'query']

        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

        # Data types
        assert df['query'].dtype == 'object' or df['query'].dtype == 'string'
        assert len(df) > 0


def test_validated_queries_csv_schema():
    """Test that validated_queries.csv has correct schema."""
    base_dir = Path(__file__).parent.parent
    csv_file = base_dir / 'data/outputs/validated_queries.csv'

    if csv_file.exists():
        df = pd.read_csv(csv_file)

        # Required columns
        required_cols = [
            'persona_id', 'problem_id', 'modifier_id', 'query',
            'looks_human_mobile', 'not_ai_slop', 'single_language',
            'matches_problem', 'matches_persona', 'no_pii',
            'passed', 'reasoning'
        ]

        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

        # Boolean columns
        bool_cols = ['looks_human_mobile', 'not_ai_slop', 'single_language',
                     'matches_problem', 'matches_persona', 'no_pii', 'passed']

        for col in bool_cols:
            assert df[col].dtype == 'bool', f"Column {col} should be boolean"

        assert len(df) > 0


def test_rag_outputs_csv_schema():
    """Test that rag_outputs.csv has correct schema."""
    base_dir = Path(__file__).parent.parent
    csv_file = base_dir / 'data/outputs/rag_outputs.csv'

    if csv_file.exists():
        df = pd.read_csv(csv_file)

        # Required columns
        required_cols = [
            'persona_id', 'problem_id', 'modifier_id', 'query',
            'answer', 'retrieved_ids', 'retrieved_titles',
            'retrieved_scores', 'gold_article_retrieved'
        ]

        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

        # Answer should not be empty
        assert df['answer'].notna().all()
        assert (df['answer'].str.len() > 0).all()


def test_eval_results_csv_schema():
    """Test that eval_results.csv has correct schema."""
    base_dir = Path(__file__).parent.parent
    csv_file = base_dir / 'data/outputs/eval_results.csv'

    if csv_file.exists():
        df = pd.read_csv(csv_file)

        # Required judge columns
        criteria = ['relevance', 'groundedness', 'completeness',
                   'actionability', 'tone_empathy', 'safety_compliance']

        for criterion in criteria:
            passed_col = f'{criterion}_passed'
            reasoning_col = f'{criterion}_reasoning'

            assert passed_col in df.columns, f"Missing column: {passed_col}"
            assert reasoning_col in df.columns, f"Missing column: {reasoning_col}"

            # Passed columns should be boolean
            assert df[passed_col].dtype == 'bool', \
                f"Column {passed_col} should be boolean"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
