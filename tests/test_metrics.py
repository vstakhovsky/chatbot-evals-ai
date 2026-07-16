"""Test metrics calculations for RAG evaluation."""

import pytest
import pandas as pd
import numpy as np


def test_pass_rate_calculation():
    """Test pass rate calculation for binary judges."""
    # Create sample data
    df = pd.DataFrame({
        'relevance_passed': [True, True, False, True],
        'groundedness_passed': [False, True, False, True],
        'completeness_passed': [True, True, True, True]
    })

    # Test individual pass rates
    relevance_rate = df['relevance_passed'].mean()
    assert relevance_rate == 0.75

    groundedness_rate = df['groundedness_passed'].mean()
    assert groundedness_rate == 0.5

    completeness_rate = df['completeness_passed'].mean()
    assert completeness_rate == 1.0


def test_overall_pass_rate():
    """Test overall pass rate (all judges must pass)."""
    df = pd.DataFrame({
        'judge1_passed': [True, True, False, True],
        'judge2_passed': [True, False, False, True],
        'judge3_passed': [True, True, True, True]
    })

    # Overall pass = all judges passed
    all_passed = df[[col for col in df.columns if '_passed' in col]].all(axis=1)
    overall_rate = all_passed.mean()

    # Only row 0 and 3 pass all judges
    assert overall_rate == 0.5


def test_judges_passed_distribution():
    """Test distribution of how many judges each query passed."""
    df = pd.DataFrame({
        'judge1_passed': [True, True, False, True],
        'judge2_passed': [True, False, False, True],
        'judge3_passed': [True, True, True, True]
    })

    judges_passed = df[[col for col in df.columns if '_passed' in col]].sum(axis=1)

    # Row 0: 3 judges, Row 1: 2 judges, Row 2: 1 judge, Row 3: 3 judges
    assert judges_passed.tolist() == [3, 2, 1, 3]
    assert judges_passed.mean() == 2.25


def test_slice_performance_calculation():
    """Test performance calculation for data slices."""
    df = pd.DataFrame({
        'persona_id': ['A', 'A', 'B', 'B', 'C'],
        'judge1_passed': [True, True, False, True, True],
        'judge2_passed': [True, False, False, True, True]
    })

    # Test persona A performance
    persona_a = df[df['persona_id'] == 'A']
    persona_a_pass = persona_a[[col for col in persona_a.columns if '_passed' in col]].all(axis=1).mean()

    # Persona A: row 0 passes both, row 1 passes only judge1
    assert persona_a_pass == 0.5

    # Test persona B performance
    persona_b = df[df['persona_id'] == 'B']
    persona_b_pass = persona_b[[col for col in persona_b.columns if '_passed' in col]].all(axis=1).mean()

    # Persona B: row 2 passes neither, row 3 passes both
    assert persona_b_pass == 0.5


def test_threshold_evaluation():
    """Test evaluation against target thresholds."""
    pass_rates = {
        'relevance': 0.78,
        'groundedness': 0.19,
        'completeness': 0.74
    }

    targets = {
        'relevance': 0.70,
        'groundedness': 0.70,
        'completeness': 0.70
    }

    # Test which meet targets
    passing = [judge for judge, rate in pass_rates.items() if rate >= targets[judge]]
    missing = [judge for judge, rate in pass_rates.items() if rate < targets[judge]]

    assert 'relevance' in passing
    assert 'completeness' in passing
    assert 'groundedness' in missing


def test_empty_dataframe_handling():
    """Test metrics calculation with empty dataframe."""
    df = pd.DataFrame({'judge_passed': []})

    pass_rate = df['judge_passed'].mean()
    assert pd.isna(pass_rate) or pass_rate == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
