import pytest
from my_app import toptastic_api, get_playlist_from_db, scrape_songs

def test_get_playlist_from_db_and_scrape_songs():
    # Test that the function returns a list
    assert type(get_playlist_from_db('2021-09-25')) == list

    # Test that the function returns the correct number of songs
    assert len(get_playlist_from_db('2021-09-25')) == 100

    # Test that the function returns the correct song
    assert get_playlist_from_db('2021-09-25')[0]['song_name'] == 'STAY'