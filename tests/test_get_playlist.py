import pytest
from my_app.toptastic_api import get_playlist_from_db


from my_app.toptastic_api import get_playlist_from_db
def test_get_playlist_from_db():
    # Test that the function returns a list
    playlist = get_playlist_from_db('20210924')
    assert type(playlist) == list

    # Test that the function returns the correct number of songs
    assert len(playlist) == 100

    # Test that the function returns the correct song
    assert playlist[0]['song_name'] == 'SHIVERS'