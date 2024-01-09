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
        'songs': [
            {'title': 'Houdini', 'artist': 'Dua Lipa'},
            {'title': 'Run for the hills', 'artist': 'Tate McRae', 'videoId': 'NGAW-DGkXuM'}
        ]
    }

    # Send a POST request to the create_playlist endpoint
    response = client.post('/create_playlist', data=json.dumps(playlist), content_type='application/json')
    print(response.data)

    # Check that the response status code is 200
    assert response.status_code == 200

    # Check that the response data contains a success status and a playlist ID
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'playlist_id' in data