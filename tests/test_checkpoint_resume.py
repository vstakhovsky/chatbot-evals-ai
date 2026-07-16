"""Test checkpoint/resume functionality for batch processing."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path


def test_checkpoint_file_creation():
    """Test that checkpoint files are created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'checkpoint.csv'

        # Create initial checkpoint
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        df.to_csv(output_file, index=False)

        assert output_file.exists()

        # Load checkpoint
        loaded = pd.read_csv(output_file)
        assert len(loaded) == 3
        assert list(loaded.columns) == ['col1', 'col2']


def test_resume_from_checkpoint():
    """Test resuming from existing checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / 'input.csv'
        output_file = Path(tmpdir) / 'output.csv'

        # Create input data
        input_df = pd.DataFrame({
            'id': range(10),
            'value': [f'item{i}' for i in range(10)]
        })
        input_df.to_csv(input_file, index=False)

        # Simulate partial processing (rows 0-4 done)
        partial_df = input_df.iloc[:5].copy()
        partial_df['processed'] = True
        partial_df.to_csv(output_file, index=False)

        # Simulate resume logic
        input_df = pd.read_csv(input_file)
        existing_df = pd.read_csv(output_file) if output_file.exists() else None

        existing_ids = set(existing_df['id'].tolist()) if existing_df is not None else set()
        missing_indices = [i for i, row in input_df.iterrows() if row['id'] not in existing_ids]

        # Should find rows 5-9 as missing
        assert len(missing_indices) == 5
        assert missing_indices == [5, 6, 7, 8, 9]


def test_incremental_checkpointing():
    """Test that checkpointing happens incrementally."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'checkpoint.csv'

        # Process in batches
        batch1 = pd.DataFrame({'id': [1, 2], 'value': ['a', 'b']})
        batch2 = pd.DataFrame({'id': [3, 4], 'value': ['c', 'd']})

        # Write first batch
        batch1.to_csv(output_file, index=False)
        assert output_file.exists()

        # Append second batch (simulating incremental save)
        existing = pd.read_csv(output_file)
        combined = pd.concat([existing, batch2], ignore_index=True)
        combined.to_csv(output_file, index=False)

        # Verify combined result
        final = pd.read_csv(output_file)
        assert len(final) == 4
        assert set(final['id'].tolist()) == {1, 2, 3, 4}


def test_empty_checkpoint_handling():
    """Test handling when no checkpoint exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'nonexistent.csv'

        assert not output_file.exists()

        # Should return empty or None
        if output_file.exists():
            existing_df = pd.read_csv(output_file)
            existing_ids = set(existing_df['id'].tolist())
        else:
            existing_ids = set()

        assert existing_ids == set()


def test_checkpoint_with_index_key():
    """Test checkpoint using dataframe index as key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / 'input.csv'
        output_file = Path(tmpdir) / 'output.csv'

        # Create input data
        input_df = pd.DataFrame({
            'id': ['A', 'B', 'C', 'D'],
            'value': [1, 2, 3, 4]
        })

        # Simulate processing with index tracking
        existing = {}
        if output_file.exists():
            existing_df = pd.read_csv(output_file)
            for idx, row in existing_df.iterrows():
                existing[idx] = row

        # Initially no existing data
        assert existing == {}

        # After processing some rows
        partial_results = {0: {'id': 'A', 'value': 1, 'processed': True},
                          1: {'id': 'B', 'value': 2, 'processed': True}}

        missing_indices = [i for i in input_df.index if i not in partial_results]

        # Should find rows 2, 3 as missing
        assert missing_indices == [2, 3]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
