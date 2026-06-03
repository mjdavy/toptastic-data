import pytest
from my_app.toptastic_api import app, json


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_playlist(client):
    # Define a sample playlist
    playlist = {
        'title': 'Toptastic Test Playlist',
        'description': 'This is a test playlist from toptastic-api',
        'tracks': [
            {'title': 'Houdini', 'artist': 'Dua Lipa', 'videoId': 'suAR1PYFNYA'},
            {'title': 'Run for the hills', 'artist': 'Tate McRae', 'videoId': 'NGAW-DGkXuM'}
        ]
    }

    # Prevent real OAuth/network calls and return predictable values.
    from my_app import youtube
    original_get_authenticated_service = youtube.get_authenticated_service
    original_create_playlist = youtube.create_playlist
    original_add_video_to_playlist = youtube.add_video_to_playlist

    youtube.get_authenticated_service = lambda: object()
    youtube.create_playlist = lambda _svc, _title, _description: 'test_playlist_id'
    youtube.add_video_to_playlist = lambda _svc, _playlist_id, _video_id: None

    try:
        # Send a POST request to the create_playlist endpoint
        response = client.post('/api/create_playlist', data=json.dumps(playlist), content_type='application/json')
        print(response.data)

        # Check that the response status code is 200
        assert response.status_code == 200

        # Check that the response data contains a success status and a playlist ID
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['playlist_id'] == 'test_playlist_id'
    finally:
        youtube.get_authenticated_service = original_get_authenticated_service
        youtube.create_playlist = original_create_playlist
        youtube.add_video_to_playlist = original_add_video_to_playlist