#!/usr/bin/env python3
"""
Prompt 5 - Unit Tests for assetsSelected
Fast tests for model validation and persistence
"""
import sys
import pytest
sys.path.insert(0, '/app/backend')

from models import (
    LeagueCreate, 
    League,
    validate_assets_selected,
    validate_assets_selection_size
)


class TestAssetsSelectedValidation:
    """Test validate_assets_selected helper function"""
    
    def test_none_input_returns_none(self):
        """None input should return None"""
        result = validate_assets_selected(None)
        assert result is None
    
    def test_empty_list_returns_none(self):
        """Empty list should return None (means 'all')"""
        result = validate_assets_selected([])
        assert result is None
    
    def test_deduplication_preserves_order(self):
        """Should deduplicate while preserving first occurrence order"""
        result = validate_assets_selected(["a", "b", "a", "c", "b"])
        assert result == ["a", "b", "c"]
    
    def test_whitespace_trimming(self):
        """Should trim whitespace from asset IDs"""
        result = validate_assets_selected([" a ", "b ", " c"])
        assert result == ["a", "b", "c"]
    
    def test_empty_strings_filtered_out(self):
        """Should filter out empty strings"""
        result = validate_assets_selected(["a", "", "  ", "b"])
        assert result == ["a", "b"]
    
    def test_max_size_enforcement(self):
        """Should raise error for more than 200 items"""
        with pytest.raises(ValueError, match="200"):
            validate_assets_selected([str(i) for i in range(201)])
    
    def test_non_string_items_rejected(self):
        """Should raise error for non-string items"""
        with pytest.raises(ValueError, match="string"):
            validate_assets_selected([1, 2, 3])


class TestLeagueCreateModel:
    """Test LeagueCreate Pydantic model with assetsSelected"""
    
    def test_accepts_assets_selected(self):
        """LeagueCreate should accept assetsSelected field"""
        league_data = {
            "name": "Test League",
            "commissionerId": "user-123",
            "sportKey": "football",
            "assetsSelected": ["club-1", "club-2", "club-3"]
        }
        
        league = LeagueCreate(**league_data)
        assert league.assetsSelected == ["club-1", "club-2", "club-3"]
    
    def test_validates_and_cleans_assets(self):
        """LeagueCreate should validate and clean assetsSelected"""
        league_data = {
            "name": "Test League",
            "commissionerId": "user-123",
            "sportKey": "football",
            "assetsSelected": [" club-1 ", "club-2", "club-1", " club-3 "]
        }
        
        league = LeagueCreate(**league_data)
        # Should deduplicate and trim
        assert league.assetsSelected == ["club-1", "club-2", "club-3"]
    
    def test_allows_missing_assets_selected(self):
        """LeagueCreate should allow missing assetsSelected (optional)"""
        league_data = {
            "name": "Test League",
            "commissionerId": "user-123",
            "sportKey": "football"
        }
        
        league = LeagueCreate(**league_data)
        assert league.assetsSelected is None
    
    def test_converts_empty_list_to_none(self):
        """LeagueCreate should convert empty list to None"""
        league_data = {
            "name": "Test League",
            "commissionerId": "user-123",
            "sportKey": "football",
            "assetsSelected": []
        }
        
        league = LeagueCreate(**league_data)
        assert league.assetsSelected is None


class TestLeagueModel:
    """Test League model includes assetsSelected"""
    
    def test_league_has_assets_selected_field(self):
        """League model should have assetsSelected field"""
        league_data = {
            "id": "league-123",
            "name": "Test League",
            "commissionerId": "user-123",
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 3,
            "sportKey": "football",
            "assetsSelected": ["club-1", "club-2"]
        }
        
        league = League(**league_data)
        assert league.assetsSelected == ["club-1", "club-2"]
    
    def test_league_allows_none_assets_selected(self):
        """League model should allow None for assetsSelected"""
        league_data = {
            "id": "league-123",
            "name": "Test League",
            "commissionerId": "user-123",
            "budget": 500000000.0,
            "minManagers": 2,
            "maxManagers": 8,
            "clubSlots": 3,
            "sportKey": "football"
        }
        
        league = League(**league_data)
        assert league.assetsSelected is None


class TestAssetsSelectionSizeValidation:
    """Test validate_assets_selection_size helper (Prompt 4)"""
    
    def test_none_selection_passes(self):
        """None selection should pass (means 'all')"""
        # Should not raise
        validate_assets_selection_size(None, 3, 2, None)
    
    def test_empty_selection_passes(self):
        """Empty selection should pass (means 'all')"""
        # Should not raise
        validate_assets_selection_size([], 3, 2, None)
    
    def test_insufficient_selection_fails(self):
        """Selection less than clubSlots should fail"""
        with pytest.raises(ValueError, match="slots per manager"):
            validate_assets_selection_size(["a", "b"], 3, 2, None)
    
    def test_exact_minimum_passes(self):
        """Selection equal to clubSlots should pass"""
        # Should not raise
        validate_assets_selection_size(["a", "b", "c"], 3, 2, None)
    
    def test_more_than_minimum_passes(self):
        """Selection more than clubSlots should pass"""
        # Should not raise
        validate_assets_selection_size(["a", "b", "c", "d"], 3, 2, None)
    
    def test_suboptimal_logs_warning(self):
        """Selection less than optimal should log warning"""
        # Create a mock logger to capture warnings
        warnings = []
        
        class MockLogger:
            def warning(self, msg, extra=None):
                warnings.append((msg, extra))
        
        logger = MockLogger()
        
        # 6 selected, but 12 recommended (3 slots * 4 managers)
        validate_assets_selection_size(
            ["a", "b", "c", "d", "e", "f"], 
            3, 
            4, 
            logger
        )
        
        # Should have logged warning
        assert len(warnings) == 1
        assert warnings[0][0] == "assets_selection.insufficient"
        assert warnings[0][1]["recommended_minimum"] == 12


if __name__ == "__main__":
    # Run tests with pytest
    print("=" * 70)
    print("PROMPT 5 - UNIT TESTS")
    print("=" * 70)
    print("\nRunning fast unit tests for assetsSelected validation...\n")
    
    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ ALL UNIT TESTS PASSED")
        print("=" * 70)
    
    sys.exit(exit_code)
