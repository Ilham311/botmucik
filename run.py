from telethon import TelegramClient, events
import base64
import requests

API_ID = '961780'
API_HASH = 'bbbfa43f067e1e8e2fb41f334d32a6a7'
BOT_TOKEN = '7375007973:AAEDZnqXwCGmJ-fmCkT0PuHzdRLFYsKcIAg'

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def get_spotify_track_recommendations(keyword, search_type='track', limit=6):
    SPOTIFY_CLIENT_ID = 'd0c345f7c8f7437f9001583b3bdae340'
    SPOTIFY_CLIENT_SECRET = '18cf1155bba744dda945b70325ca71cc'
    client_credentials = f'{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}'
    base64_credentials = base64.b64encode(client_credentials.encode('utf-8')).decode('utf-8')
    headers = {'Authorization': f'Basic {base64_credentials}'}
    token_endpoint = 'https://accounts.spotify.com/api/token'

    token_response = requests.post(token_endpoint, headers=headers, data={'grant_type': 'client_credentials'})
    if token_response.status_code == 200:
        access_token = token_response.json().get('access_token')
        headers['Authorization'] = f'Bearer {access_token}'
        search_endpoint = 'https://api.spotify.com/v1/search'
        response = requests.get(search_endpoint, params={'q': keyword, 'type': search_type, 'limit': limit}, headers=headers)
        if response.status_code == 200:
            return response.json()
        return {'error': f"Search Error: {response.status_code} - {response.text}"}
    return {'error': f"Token Error: {token_response.status_code} - {token_response.text}"}

def download_spotify_track(track_id, track_name, artist_name=None):
    download_url = f'https://yank.g3v.co.uk/track/{track_id}'
    response = requests.get(download_url)
    if response.status_code == 200:
        filename = f"{track_name} by {artist_name}.mp3" if artist_name else f"{track_name} ({track_id}).mp3"
        with open(filename, 'wb') as file:
            file.write(response.content)
        return filename
    return None

@client.on(events.NewMessage(pattern='/song (.+)'))
async def handle_song_request(event):
    keyword = event.pattern_match.group(1)
    message = await event.respond(f"🔍 Mencari Musik '{keyword}'...")

    recommendations = get_spotify_track_recommendations(keyword)
    if 'error' in recommendations:
        await message.edit(recommendations['error'])
        return

    tracks = recommendations['tracks']['items']
    if not tracks:
        await message.edit(f"No tracks found for '{keyword}'.")
        return

    first_track = tracks[0]
    track_name = first_track['name']
    artist_name = ', '.join(artist['name'] for artist in first_track['artists']) if first_track['artists'] else None
    track_id = first_track['id']

    await message.edit(f"⬇️ Downloading: {track_name} by {artist_name if artist_name else 'Unknown Artist'}")
    filename = download_spotify_track(track_id, track_name, artist_name)
    
    if filename:
        await message.edit(f"📤 Uploading: {track_name} by {artist_name if artist_name else 'Unknown Artist'}")
        await client.send_file(event.chat_id, filename)
        
        user = await client.get_entity(event.sender_id)
        username = user.username if user.username else 'Unknown User'

        music_info = (
            f"➲ 𝙽𝙰𝙼𝙴: {track_name} {'by ' + artist_name if artist_name else ''}\n"
            f"➲ 𝙰𝚁𝚃𝙸𝚂𝚃: {artist_name if artist_name else 'Unknown Artist'}\n"
            f"➲ 𝙳𝚄𝚁𝙰𝚃𝙸𝙾𝙽: Unknown\n"
            f"➲ 𝚄𝙿𝙻𝙾𝙰𝙳𝙴𝙳 𝙱𝚈: @{username} ⚡"
        )
        await client.send_message(event.chat_id, music_info)
    else:
        await message.edit(f"Failed to download track '{track_name}'.")

client.start()
client.run_until_disconnected()
