import requests
from bs4 import BeautifulSoup
import json

# Make a request to the website
r = requests.get("https://www.officialcharts.com/charts/singles-chart/20110313/7501/")
r.content

# Use the 'html.parser' to parse the page
soup = BeautifulSoup(r.content, 'html.parser')

# Find all the div tags with class 'description block'
divs = soup.find_all('div', class_='description block')

# Create a list to store the song data
songs = []

# Extract and print the song name, artist, and chart information
for div in divs:
    song_name_tag = div.find('a', class_='chart-name font-bold inline-block')
    song_name_elements = song_name_tag.find_all('span')
    re_new = song_name_elements[0].get_text(strip=True).upper() if len(song_name_elements) > 1 else ''
    song_name = song_name_elements[-1].get_text(strip=True)
    artist = div.find('a', class_='chart-artist text-lg inline-block').get_text(strip=True)
    lw = div.find('li', class_='movement px-2 py-1 rounded-md inline-block mr-1 sm:mr-2').get_text(strip=True).split(':')[1].replace(',', '')
    peak = div.find('li', class_='peak px-2 py-1 rounded-md inline-block mr-1 sm:mr-2').get_text(strip=True).split(':')[1].replace(',', '')
    weeks = div.find('li', class_='weeks px-2 py-1 rounded-md inline-block mr-1 sm:mr-2').get_text(strip=True).split(':')[1]

    # Create a dictionary for the song
    song = {
        're_new': re_new,
        'song_name': song_name,
        'artist': artist,
        'lw': lw,
        'peak': peak,
        'weeks': weeks
    }
    
    # Add the song to the list
    songs.append(song)

# Convert the list to a JSON string
json_songs = json.dumps(songs, indent=4)

# Print the JSON string
print(json_songs)