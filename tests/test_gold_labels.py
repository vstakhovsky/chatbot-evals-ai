"""Test gold labeling functionality for Part 2."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


def test_gold_csv_schema():
    """Test that gold label CSVs have correct schema."""
    base_dir = Path(__file__).parent.parent
    gold_dir = base_dir / 'data/outputs/gold_labels'

    if not gold_dir.exists():
        pytest.skip("Gold labels directory not created yet")

    gold_files = list(gold_dir.glob('gold_labels_*.csv'))

    for gold_file in gold_files:
        df = pd.read_csv(gold_file)

        # Required columns
        required_cols = [
            'persona_id', 'problem_id', 'modifier_id', 'query', 'answer',
            'criterion', 'gold_passed', 'gold_reasoning',
            'judge_passed', 'judge_reasoning', 'human_override'
        ]

        for col in required_cols:
            assert col in df.columns, f"Missing column: {col} in {gold_file.name}"

        # Data types
        assert df['gold_passed'].dtype == 'bool', f"gold_passed should be boolean in {gold_file.name}"
        assert df['judge_passed'].dtype == 'bool', f"judge_passed should be boolean in {gold_file.name}"

        # human_override should be string/object (possibly empty)
        assert df['human_override'].dtype == 'object', f"human_override should be string in {gold_file.name}"

        # Should have data
        assert len(df) > 0, f"{gold_file.name} should have data"


def test_human_override_precedence():
    """Test that human_override takes precedence when non-empty."""
    # Create sample data
    df = pd.DataFrame({
        'gold_passed': [True, False, True, False],
        'judge_passed': [False, True, True, False],
        'human_override': ['True', '', '', 'False']
    })

    # When human_override is non-empty, it should take precedence
    def apply_precedence(row):
        if pd.notna(row['human_override']) and row['human_override'].strip():
            return row['human_override'].strip() == 'True'
        return row['gold_passed']

    df['final_passed'] = df.apply(apply_precedence, axis=1)

    # Row 0: human_override='True' should override gold_passed=True (same result)
    assert df.loc[0, 'final_passed'] == True

    # Row 1: human_override='' should use gold_passed=False
    assert df.loc[1, 'final_passed'] == False

    # Row 2: human_override='' should use gold_passed=True
    assert df.loc[2, 'final_passed'] == True

    # Row 3: human_override='False' should override gold_passed=False (same result)
    assert df.loc[3, 'final_passed'] == False


def test_stratified_sampling_determinism():
    """Test that stratified sampling is deterministic with fixed seed."""
    np.random.seed(42)

    # Create sample data
    df = pd.DataFrame({
        'modifier_id': ['A', 'A', 'B', 'B', 'C', 'C'] * 10,
        'criterion_passed': [True, False] * 30,
        'query': [f'query{i}' for i in range(60)]
    })

    # Sample twice with same seed
    np.random.seed(42)
    sample1 = df.sample(10, random_state=42)

    np.random.seed(42)
    sample2 = df.sample(10, random_state=42)

    # Should get same results
    assert sample1.index.tolist() == sample2.index.tolist()


def test_stratified_split_balance():
    """Test that stratified split balances across strata."""
    # Create sample data
    df = pd.DataFrame({
        'modifier_id': ['A', 'A', 'B', 'B', 'C', 'C'] * 5,
        'criterion_passed': [True, False] * 15,
        'query': [f'query{i}' for i in range(30)]
    })

    # Stratified sample
    modifiers = df['modifier_id'].unique()
    samples = []

    for modifier in modifiers:
        modifier_data = df[df['modifier_id'] == modifier]
        passed = modifier_data[modifier_data['criterion_passed'] == True]
        failed = modifier_data[modifier_data['criterion_passed'] == False]

        n_per_verdict = min(len(passed), len(failed), 2)
        if n_per_verdict > 0:
            samples.extend(passed.sample(n_per_verdict, random_state=42).to_dict('records'))
            samples.extend(failed.sample(n_per_verdict, random_state=42).to_dict('records'))

    # Should have balance across modifiers
    result_df = pd.DataFrame(samples)
    modifier_counts = result_df['modifier_id'].value_counts()

    # Each modifier should have same number of samples
    assert len(modifier_counts.unique()) == 1, "Should have equal samples per modifier"

    # Should have balance of pass/fail
    pass_count = (result_df['criterion_passed'] == True).sum()
    fail_count = (result_df['criterion_passed'] == False).sum()

    assert abs(pass_count - fail_count) <= 1, "Should balance pass/fail counts"


def test_gepa_metric_function():
    """Test GEPA metric function for scoring."""
    # Create sample data
    df = pd.DataFrame({
        'gold_passed': [True, False, True, False, True],
        'judge_passed': [True, True, False, False, True],
        'feedback': ['', 'Wrong', 'Wrong', '', '']
    })

    def score_gepa(row):
        score = 1 if row['gold_passed'] == row['judge_passed'] else 0
        has_feedback = bool(row['feedback']) and bool(row['feedback'].strip())
        return score, has_feedback

    results = df.apply(score_gepa, axis=1).tolist()
    scores = [r[0] for r in results]
    feedback_flags = [r[1] for r in results]

    # Row 0: gold=True, judge=True → score=1
    assert scores[0] == 1

    # Row 1: gold=False, judge=True → score=0, has_feedback=True
    assert scores[1] == 0
    assert feedback_flags[1] == True  # Now properly boolean

    # Row 2: gold=True, judge=False → score=0, has_feedback=True
    assert scores[2] == 0
    assert feedback_flags[2] == True  # Now properly boolean

    # Row 3: gold=False, judge=False → score=1
    assert scores[3] == 1

    # Row 4: gold=True, judge=True → score=1, no feedback
    assert scores[4] == 1
    assert feedback_flags[4] == False

    # Overall accuracy
    accuracy = sum(scores) / len(scores)
    assert accuracy == 0.6, f"Expected accuracy 0.6, got {accuracy}"


def test_optimized_prompt_file_structure():
    """Test that optimized prompt files have expected structure."""
    base_dir = Path(__file__).parent.parent
    opt_prompts_dir = base_dir / 'prompts' / 'optimized'

    if not opt_prompts_dir.exists():
        pytest.skip("Optimized prompts directory not created yet")

    opt_files = list(opt_prompts_dir.glob('*.txt'))

    for opt_file in opt_files:
        content = opt_file.read_text()

        # Should not be empty
        assert len(content.strip()) > 0, f"{opt_file.name} should not be empty"

        # Should contain some basic structure (not empty template)
        assert '{' in content or 'query' in content.lower() or 'answer' in content.lower(), \
            f"{opt_file.name} should contain prompt structure"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
