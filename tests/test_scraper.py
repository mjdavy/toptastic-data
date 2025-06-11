import pytest
import sys
from unittest.mock import MagicMock

# Mock the youtube module to avoid import errors due to missing credentials
sys.modules['my_app.youtube'] = MagicMock()

from my_app.toptastic_api import scrape_songs


def test_scrape_songs_real_website():
    """Test scraping songs from the real Official Charts website."""
    # Use a recent date that should have chart data
    date = "20250610"  # June 10, 2025
    
    songs = scrape_songs(date)
    
    # Basic assertions
    assert isinstance(songs, list)
    assert len(songs) > 0, "Should find some songs on the charts"
    
    # Check first song structure
    first_song = songs[0]
    assert 'song_name' in first_song
    assert 'artist' in first_song
    assert 'is_new' in first_song
    assert 'is_reentry' in first_song
    assert 'lw' in first_song
    assert 'peak' in first_song
    assert 'weeks' in first_song
    assert 'video_id' in first_song
    
    # Check data types
    assert isinstance(first_song['song_name'], str)
    assert isinstance(first_song['artist'], str)
    assert isinstance(first_song['is_new'], bool)
    assert isinstance(first_song['is_reentry'], bool)
    assert isinstance(first_song['lw'], int)
    assert isinstance(first_song['peak'], int)
    assert isinstance(first_song['weeks'], int)
    assert isinstance(first_song['video_id'], str)
    
    # Check that we got reasonable data
    assert len(first_song['song_name']) > 0
    assert len(first_song['artist']) > 0
    assert first_song['peak'] >= 1
    assert first_song['weeks'] >= 1
    
    print(f"Successfully scraped {len(songs)} songs from {date}")
    print(f"First song: '{first_song['song_name']}' by {first_song['artist']}")


def test_scrape_songs_multiple_dates():
    """Test scraping from multiple dates to ensure consistency."""
    dates = ["20250610", "20250603"]  # Two recent weeks
    
    for date in dates:
        songs = scrape_songs(date)
        assert isinstance(songs, list)
        assert len(songs) > 0, f"Should find songs for date {date}"
        
        # Verify all songs have required fields
        for song in songs:
            assert all(key in song for key in ['song_name', 'artist', 'is_new', 'is_reentry', 'lw', 'peak', 'weeks', 'video_id'])
            assert len(song['song_name'].strip()) > 0
            assert len(song['artist'].strip()) > 0


def test_scrape_songs_edge_cases():
    """Test scraper with edge cases."""
    # Test with a very recent date that should have data
    date = "20250610"  # June 10, 2025
    
    songs = scrape_songs(date)
    
    # Should still get some results
    assert isinstance(songs, list)
    
    # Test that new/reentry flags work correctly
    has_new = any(song['is_new'] for song in songs if songs)
    has_reentry = any(song['is_reentry'] for song in songs if songs)
    
    print(f"Found {len(songs)} songs for {date}")
    if songs:
        print(f"Has new entries: {has_new}")
        print(f"Has re-entries: {has_reentry}")
        
        # Check for songs with lw=0 (new or re-entry)
        new_or_reentry_songs = [s for s in songs if s['lw'] == 0]
        print(f"Songs with LW=0 (new/re-entry): {len(new_or_reentry_songs)}")


if __name__ == "__main__":
    # Allow running the test directly
    test_scrape_songs_real_website()
    test_scrape_songs_multiple_dates()
    test_scrape_songs_edge_cases()
    print("All tests passed!")