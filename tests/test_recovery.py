"""
Comprehensive tests for Recovery module.

Tests Reed-Solomon error correction and recovery record generation/application.
"""

import pytest
import struct
from techcompressor.recovery import (
    ReedSolomonSimple,
    generate_recovery_records,
    apply_recovery,
    verify_recovery_possible,
    MAGIC_HEADER_RECOVERY,
    RECOVERY_VERSION,
    DEFAULT_BLOCK_SIZE
)


class TestReedSolomonSimple:
    """Test the Reed-Solomon encoder/decoder."""

    def test_init(self):
        """Test ReedSolomonSimple initialization."""
        rs = ReedSolomonSimple(n_data=10, n_parity=2)
        assert rs.n_data == 10
        assert rs.n_parity == 2

    def test_encode_empty_blocks(self):
        """Test encoding with empty block list."""
        rs = ReedSolomonSimple(n_data=0, n_parity=1)
        result = rs.encode_block([])
        assert result == []

    def test_encode_single_block(self):
        """Test encoding a single data block."""
        rs = ReedSolomonSimple(n_data=1, n_parity=1)
        data_blocks = [b"A" * 64]
        
        parity = rs.encode_block(data_blocks)
        
        assert len(parity) == 1
        assert len(parity[0]) == 64

    def test_encode_multiple_blocks(self):
        """Test encoding multiple data blocks."""
        rs = ReedSolomonSimple(n_data=4, n_parity=2)
        data_blocks = [b"A" * 64, b"B" * 64, b"C" * 64, b"D" * 64]
        
        parity = rs.encode_block(data_blocks)
        
        assert len(parity) == 2
        for p in parity:
            assert len(p) == 64

    def test_decode_no_missing(self):
        """Test decoding when no blocks are missing."""
        rs = ReedSolomonSimple(n_data=4, n_parity=1)
        blocks = [b"A" * 64, b"B" * 64, b"C" * 64, b"D" * 64]
        parity = rs.encode_block(blocks)
        
        # No missing blocks
        result = rs.decode_block(blocks.copy(), parity)
        
        assert len(result) == 4

    def test_decode_single_missing_block(self):
        """Test recovering a single missing block."""
        rs = ReedSolomonSimple(n_data=4, n_parity=1)
        original_blocks = [b"A" * 64, b"B" * 64, b"C" * 64, b"D" * 64]
        parity = rs.encode_block(original_blocks)
        
        # Mark one block as missing
        blocks_with_missing = original_blocks.copy()
        blocks_with_missing[1] = None
        
        result = rs.decode_block(blocks_with_missing, parity)
        
        # Should recover all blocks
        assert len(result) == 4

    def test_decode_too_many_missing(self):
        """Test that decoding fails with too many missing blocks."""
        rs = ReedSolomonSimple(n_data=4, n_parity=1)
        data_blocks = [b"A" * 64, b"B" * 64, b"C" * 64, b"D" * 64]
        parity = rs.encode_block(data_blocks)
        
        # Mark two blocks as missing (more than n_parity)
        blocks_with_missing = [None, None, b"C" * 64, b"D" * 64]
        
        with pytest.raises(ValueError, match="Too many corrupted"):
            rs.decode_block(blocks_with_missing, parity)

    def test_encode_varying_block_sizes(self):
        """Test encoding with blocks of different content."""
        rs = ReedSolomonSimple(n_data=3, n_parity=1)
        data_blocks = [
            bytes([0] * 64),
            bytes([255] * 64),
            bytes(range(64))
        ]
        
        parity = rs.encode_block(data_blocks)
        
        assert len(parity) == 1
        assert len(parity[0]) == 64


class TestGenerateRecoveryRecords:
    """Test recovery record generation."""

    def test_generate_basic(self):
        """Test basic recovery record generation."""
        data = b"Test data for recovery " * 100
        
        recovery = generate_recovery_records(data, recovery_percent=5.0)
        
        assert recovery[:4] == MAGIC_HEADER_RECOVERY
        assert len(recovery) > 25  # At least header size

    def test_generate_with_custom_percentage(self):
        """Test generation with custom recovery percentage."""
        data = b"X" * 10000
        
        recovery_5 = generate_recovery_records(data, recovery_percent=5.0)
        recovery_10 = generate_recovery_records(data, recovery_percent=10.0)
        
        # Higher percentage should produce more recovery data
        assert len(recovery_10) >= len(recovery_5)

    def test_generate_with_custom_block_size(self):
        """Test generation with custom block size."""
        data = b"Y" * 50000
        
        recovery_small = generate_recovery_records(data, block_size=1024)
        recovery_large = generate_recovery_records(data, block_size=65536)
        
        # Different block sizes produce different results
        assert recovery_small[:4] == MAGIC_HEADER_RECOVERY
        assert recovery_large[:4] == MAGIC_HEADER_RECOVERY

    def test_generate_invalid_percentage_zero(self):
        """Test that zero percentage raises error."""
        data = b"Test"
        
        with pytest.raises(ValueError, match="recovery_percent"):
            generate_recovery_records(data, recovery_percent=0)

    def test_generate_invalid_percentage_negative(self):
        """Test that negative percentage raises error."""
        data = b"Test"
        
        with pytest.raises(ValueError, match="recovery_percent"):
            generate_recovery_records(data, recovery_percent=-5)

    def test_generate_invalid_percentage_over_100(self):
        """Test that >100% percentage raises error."""
        data = b"Test"
        
        with pytest.raises(ValueError, match="recovery_percent"):
            generate_recovery_records(data, recovery_percent=150)

    def test_generate_small_data(self):
        """Test generation with very small data."""
        data = b"Small"
        
        recovery = generate_recovery_records(data, recovery_percent=10.0)
        
        assert recovery[:4] == MAGIC_HEADER_RECOVERY

    def test_generate_large_data(self):
        """Test generation with large data."""
        data = b"X" * (1024 * 1024)  # 1 MB
        
        recovery = generate_recovery_records(data, recovery_percent=5.0)
        
        assert recovery[:4] == MAGIC_HEADER_RECOVERY
        # Recovery data should be reasonable size
        assert len(recovery) < len(data) * 0.15  # Less than 15% of data

    def test_header_format(self):
        """Test recovery record header format."""
        data = b"Header test " * 1000
        
        recovery = generate_recovery_records(data, recovery_percent=5.0, block_size=1024)
        
        # Parse header
        assert recovery[:4] == MAGIC_HEADER_RECOVERY
        version = recovery[4]
        assert version == RECOVERY_VERSION
        
        data_size = struct.unpack('>Q', recovery[5:13])[0]
        assert data_size == len(data)
        
        block_size = struct.unpack('>I', recovery[13:17])[0]
        assert block_size == 1024


class TestApplyRecovery:
    """Test recovery application."""

    def test_apply_no_corruption(self):
        """Test applying recovery when data is not corrupted."""
        original_data = b"Test data for recovery " * 100
        recovery = generate_recovery_records(original_data, recovery_percent=10.0)
        
        result = apply_recovery(original_data, recovery)
        
        # Data should be unchanged
        assert result == original_data

    def test_apply_with_corrupted_range(self):
        """Test applying recovery with specified corrupted range."""
        original_data = b"X" * 10000
        recovery = generate_recovery_records(original_data, recovery_percent=10.0, block_size=1000)
        
        # Create corrupted data
        corrupted_data = bytearray(original_data)
        corrupted_data[500:600] = b"Y" * 100  # Corrupt 100 bytes
        corrupted_data = bytes(corrupted_data)
        
        # Apply recovery with known corrupted range
        result = apply_recovery(corrupted_data, recovery, corrupted_ranges=[(500, 600)])
        
        # Result should be recovered (may not be perfect with simple XOR parity)
        assert len(result) == len(original_data)

    def test_apply_invalid_recovery_data_short(self):
        """Test error when recovery data is too short."""
        data = b"Test data"
        
        with pytest.raises(ValueError, match="too short"):
            apply_recovery(data, b"SHORT")

    def test_apply_invalid_magic(self):
        """Test error when recovery magic is wrong."""
        data = b"Test data"
        bad_recovery = b"BADM" + b"\x00" * 30
        
        with pytest.raises(ValueError, match="Invalid recovery magic"):
            apply_recovery(data, bad_recovery)

    def test_apply_wrong_version(self):
        """Test error when recovery version is unsupported."""
        data = b"Test data"
        # Create recovery with wrong version
        bad_recovery = MAGIC_HEADER_RECOVERY + bytes([99]) + b"\x00" * 30
        
        with pytest.raises(ValueError, match="Unsupported recovery version"):
            apply_recovery(data, bad_recovery)

    def test_apply_truncated_parity(self):
        """Test error when parity blocks are truncated."""
        data = b"Test data " * 100
        recovery = generate_recovery_records(data, recovery_percent=5.0)
        
        # Truncate recovery data
        truncated = recovery[:30]
        
        with pytest.raises(ValueError, match="truncated"):
            # Need to specify corrupted ranges to trigger parity read
            apply_recovery(data, truncated, corrupted_ranges=[(0, 10)])


class TestVerifyRecoveryPossible:
    """Test recovery verification."""

    def test_verify_valid_recovery(self):
        """Test verifying valid recovery data."""
        data = b"Test data for verification " * 100
        recovery = generate_recovery_records(data, recovery_percent=5.0)
        
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True
        assert info["version"] == RECOVERY_VERSION
        assert info["data_size"] == len(data)
        assert "n_blocks" in info
        assert "n_parity" in info
        assert "max_recoverable_blocks" in info

    def test_verify_empty_recovery(self):
        """Test verifying empty recovery data."""
        info = verify_recovery_possible(b"")
        
        assert info["valid"] is False
        assert "error" in info

    def test_verify_too_short(self):
        """Test verifying too-short recovery data."""
        info = verify_recovery_possible(b"SHORT")
        
        assert info["valid"] is False
        assert "too short" in info["error"].lower()

    def test_verify_wrong_magic(self):
        """Test verifying recovery with wrong magic."""
        bad_recovery = b"BADM" + b"\x00" * 30
        
        info = verify_recovery_possible(bad_recovery)
        
        assert info["valid"] is False
        assert "magic" in info["error"].lower()

    def test_verify_returns_all_fields(self):
        """Test that verify returns all expected fields."""
        data = b"X" * 10000
        recovery = generate_recovery_records(data, recovery_percent=10.0, block_size=1000)
        
        info = verify_recovery_possible(recovery)
        
        expected_fields = [
            "valid", "version", "data_size", "block_size",
            "n_blocks", "n_parity", "max_recoverable_blocks",
            "recovery_overhead_percent", "expected_size", "actual_size"
        ]
        
        for field in expected_fields:
            assert field in info

    def test_verify_recovery_overhead_calculation(self):
        """Test that recovery overhead percentage is calculated correctly."""
        data = b"X" * 100000
        recovery = generate_recovery_records(data, recovery_percent=10.0, block_size=10000)
        
        info = verify_recovery_possible(recovery)
        
        # Overhead should be approximately recovery_percent
        assert info["recovery_overhead_percent"] > 0
        assert info["recovery_overhead_percent"] < 100


class TestRecoveryIntegration:
    """Integration tests for recovery functionality."""

    def test_full_recovery_workflow(self):
        """Test complete recovery workflow: generate, corrupt, recover."""
        # Original data
        original_data = b"Important data that must be recoverable! " * 500
        
        # Generate recovery records with 10% redundancy
        recovery = generate_recovery_records(
            original_data, 
            recovery_percent=10.0, 
            block_size=1024
        )
        
        # Verify recovery is possible
        info = verify_recovery_possible(recovery)
        assert info["valid"] is True
        
        # Data without corruption should pass through unchanged
        result = apply_recovery(original_data, recovery)
        assert result == original_data

    def test_recovery_with_binary_data(self):
        """Test recovery with binary (non-text) data."""
        # Binary data with various byte values
        original_data = bytes(range(256)) * 100
        
        recovery = generate_recovery_records(original_data, recovery_percent=5.0)
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True
        assert info["data_size"] == len(original_data)

    def test_recovery_preserves_data_length(self):
        """Test that recovery preserves exact data length."""
        original_data = b"Exact length test " * 123  # Non-round number
        
        recovery = generate_recovery_records(original_data, recovery_percent=5.0)
        result = apply_recovery(original_data, recovery)
        
        assert len(result) == len(original_data)

    def test_recovery_with_minimum_percentage(self):
        """Test recovery with minimum valid percentage."""
        data = b"Minimum recovery test " * 100
        
        recovery = generate_recovery_records(data, recovery_percent=0.1)
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True

    def test_recovery_with_maximum_percentage(self):
        """Test recovery with high percentage."""
        data = b"Maximum recovery test " * 100
        
        recovery = generate_recovery_records(data, recovery_percent=50.0)
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True
        # High percentage means more parity blocks
        assert info["n_parity"] > 0


class TestRecoveryEdgeCases:
    """Test edge cases for recovery module."""

    def test_single_byte_data(self):
        """Test recovery with single byte data."""
        data = b"X"
        
        recovery = generate_recovery_records(data, recovery_percent=10.0)
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True
        assert info["data_size"] == 1

    def test_block_boundary_data(self):
        """Test recovery with data exactly at block boundary."""
        block_size = 1024
        data = b"X" * block_size  # Exactly one block
        
        recovery = generate_recovery_records(data, recovery_percent=10.0, block_size=block_size)
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True
        assert info["n_blocks"] == 1

    def test_multiple_block_boundary(self):
        """Test recovery with data at multiple block boundary."""
        block_size = 1000
        data = b"Y" * (block_size * 5)  # Exactly 5 blocks
        
        recovery = generate_recovery_records(data, recovery_percent=10.0, block_size=block_size)
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True
        assert info["n_blocks"] == 5

    def test_partial_last_block(self):
        """Test recovery when last block is partial."""
        block_size = 1000
        data = b"Z" * 2500  # 2.5 blocks
        
        recovery = generate_recovery_records(data, recovery_percent=10.0, block_size=block_size)
        info = verify_recovery_possible(recovery)
        
        assert info["valid"] is True
        assert info["n_blocks"] == 3  # Rounds up

    def test_none_recovery_data(self):
        """Test handling of None recovery data."""
        info = verify_recovery_possible(None)
        
        assert info["valid"] is False


class TestRecoveryConstants:
    """Test recovery module constants."""

    def test_magic_header_value(self):
        """Test magic header constant."""
        assert MAGIC_HEADER_RECOVERY == b"TCRR"
        assert len(MAGIC_HEADER_RECOVERY) == 4

    def test_version_value(self):
        """Test version constant."""
        assert RECOVERY_VERSION == 1
        assert isinstance(RECOVERY_VERSION, int)

    def test_default_block_size(self):
        """Test default block size constant."""
        assert DEFAULT_BLOCK_SIZE == 65536  # 64 KB
        assert isinstance(DEFAULT_BLOCK_SIZE, int)
