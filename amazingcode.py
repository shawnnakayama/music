import requests
import base64

#getting API keys

client_id = '14a1a0b9ca5a403e87d397a551c93528'
client_secret = 'c3ac18a968e64f7e94e0e56681c7596b'

access_token = None

def get_access_token():
    global access_token
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode()).decode()
    }
    data = {
        'grant_type': 'client_credentials'
    }
    
    response = requests.post(url, headers=headers, data=data)
    response_data = response.json()
    access_token = response_data['access_token']

get_access_token()


#_______________________________________________________________________

#authorization

headers = {
    'Authorization': 'Bearer ' + access_token
}

params = {
    'market': 'US',
    'fields': 'tracks.items(track(name))'
}

url = 'https://api.spotify.com/v1/playlists/2YRe7HRKNRvXdJBp9nXFza'
    


#_______________________________________________________________________________

import spotipy  #spotify module for analyzing data
import pandas as pd #good old pandas
from tqdm import tqdm #this is the funky progress bar module ahaha

get_access_token()
sp = spotipy.Spotify(auth = access_token)

#this is the playlist that has the top 700 songs. 
#since spotify does not release their top songs in an official 
#source or playlist, the users of spotify have stepped up to fill the gap.
#this is the most popular and credible one I could find, so I'm using this one.
#Of course, you can use this code for any playlist, not just this one.
#just adjust the username and playlist id.

username = 'Ray Fontaine'
playlist_id = '2YRe7HRKNRvXdJBp9nXFza'

def analyze_playlist_tracks(username, playlist_id):
    
    # Convert key values from numerals to readable keys
    def convert_key(key_value):
        keys = {
            0: 'C',
            1: 'C#/Db', # enharmonics are important
            2: 'D',
            3: 'D#/Eb',
            4: 'E',
            5: 'F',
            6: 'F#/Gb',
            7: 'G',
            8: 'G#/Ab',
            9: 'A',
            10: 'A#/Bb',
            11: 'B'
        }

        if key_value in keys:
            return keys[key_value]
        else:
            return 'Unknown' 

    results = sp.user_playlist_tracks(username, playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    results = tracks    

    playlist_tracks_ids = []
    playlist_tracks_titles = []
    playlist_tracks_artists = []
    playlist_tracks_first_release_dates = []
    playlist_tracks_popularity = []

    print('Currently running... Please stay tuned!')
    progress_bar = tqdm(total=len(results), ncols=80)
    
    for i in range(len(results)):
        progress_bar.update(1)

        # This data isn't all being used in the graph, but it is in the CSV file if you want to further analyze it!
        if i == 0:
            playlist_tracks_ids = results[i]['track']['id']
            playlist_tracks_titles = results[i]['track']['name']
            playlist_tracks_first_release_dates = results[i]['track']['album']['release_date']
            playlist_tracks_popularity = results[i]['track']['popularity']

            artist_list = []
            for artist in results[i]['track']['artists']:
                artist_list.append(artist['name'])
            playlist_tracks_artists = artist_list

            features = sp.audio_features(playlist_tracks_ids)
            features_df = pd.DataFrame(data=features, columns=features[0].keys())
            features_df['title'] = playlist_tracks_titles
            features_df['all_artists'] = playlist_tracks_artists
            features_df['popularity'] = playlist_tracks_popularity
            features_df['release_date'] = playlist_tracks_first_release_dates
            features_df = features_df[['id', 'title', 'all_artists', 'release_date',
                                       'key', 'tempo', 'duration_ms', 'time_signature']]
            features_df['duration_sec'] = features_df['duration_ms'] / 1000
            features_df['key'] = features_df['key'].apply(convert_key) 
            continue
        else:
            try:
                playlist_tracks_ids = results[i]['track']['id']
                playlist_tracks_titles = results[i]['track']['name']
                playlist_tracks_first_release_dates = results[i]['track']['album']['release_date']
                playlist_tracks_popularity = results[i]['track']['popularity']
                artist_list = []
                for artist in results[i]['track']['artists']:
                    artist_list.append(artist['name'])
                playlist_tracks_artists = artist_list
                features = sp.audio_features(playlist_tracks_ids)
                new_row = {
                    'id': [playlist_tracks_ids],
                    'title': [playlist_tracks_titles],
                    'all_artists': [playlist_tracks_artists],
                    'release_date': [playlist_tracks_first_release_dates],
                    'key': [convert_key(features[0]['key'])],
                    'tempo': [features[0]['tempo']],
                    'duration_ms': [features[0]['duration_ms']],
                    'duration_sec': [features[0]['duration_ms'] / 1000],
                    'time_signature': [features[0]['time_signature']]
                }
                features_df = pd.concat([features_df, pd.DataFrame(new_row)], ignore_index=True)
                
            except:
                continue
    
    # Plotting key distribution
    import matplotlib.pyplot as plt
    key_counts = features_df['key'].value_counts()
    plt.figure(figsize=(8, 6))
    plt.pie(key_counts, labels=key_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Key Distribution')
    plt.axis('equal') 
    plt.show()
    
    # Plotting tempo distribution
    tempo_values = features_df['tempo']
    plt.figure(figsize=(8, 6))
    plt.hist(tempo_values, bins=range(50, 220, 10), edgecolor='black')
    plt.title('Tempo Distribution')
    plt.xlabel('Tempo (BPM)')
    plt.ylabel('Count')
    plt.show()
    
    # Plotting time signature distribution
    time_signature_counts = features_df['time_signature'].value_counts()
    labels = time_signature_counts.index.astype(str) + '/4'
    plt.figure(figsize=(8, 6))
    plt.pie(time_signature_counts, labels=labels, startangle=90)
    plt.title('Time Signature Distribution')
    plt.axis('equal')
    plt.show()
    
    # Plotting song release year distribution
    features_df['release_year'] = pd.to_datetime(features_df['release_date']).dt.year
    plt.figure(figsize=(8, 6))
    plt.hist(features_df['release_year'], bins=range(1960, 2025, 5), edgecolor='black')
    plt.xlabel('Release Year')
    plt.ylabel('Count')
    plt.title('Song Release Year Distribution')
    plt.show()

    return features_df
    

playlist_tracks_df = analyze_playlist_tracks(username, playlist_id)

playlist_tracks_df.to_csv('playlist_tracks.csv', index=False)

print('Completed! Have fun with the data!')
