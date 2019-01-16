# this file handles all spotify related requests

from library.internal import *
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
load_dotenv()

import os
import spotipy
import time
import json

SPCredentials = SpotifyClientCredentials(
	client_id = os.environ.get('SPOTIFY_CLIENT_ID', ''),
	client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET', '')
)


class LoadTrack:
	def __init__(self, track_id):
		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)

		self.track_id = track_id
		self.metadata = objectify({})
		self.request_track_info()

	def request_track_info(self):
		track = objectify(self.SPClient.track(self.track_id))

		self.metadata.name = track.name
		self.metadata.number = track.track_number
		self.metadata.duration = track.duration_ms / 1e3
		self.metadata.cover = track.album.images[0]['url']
		self.metadata.release_date = track.album.release_date
		track_artists = []
		for artist in track.artists:
			track_artists.append(artist['name'])
		self.metadata.featured_artists = ';'.join(track_artists)
		self.metadata.artist = self.metadata.featured_artists.split(';')[0]

		self.metadata.album_name = track.album.name
		album_artists = []
		for artist in track.album.artists:
			album_artists.append(artist['name'])
		self.metadata.album_artist = ';'.join(album_artists)


class LoadPlaylist:
	def __init__(self, username, playlist_id, save_path = ''):
		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)
		self.save_path = save_path
		self.username = username
		self.playlist_id = playlist_id
		self.tracks = []
		self.metadata = objectify({})

		console.info('Requesting playlist metadata, given username is =={0}== and playlist id is =={1}=='.format(username or 'none', playlist_id))
		self.request_playlist_info()
		self.request_playlist_tracks()
		console.success('finished loading playlist, =={0}== songs were found'.format(len(self.tracks)))
		self.dump_file()

	def request_playlist_info(self):
		playlist = objectify(self.SPClient.user_playlist(self.username, self.playlist_id))

		self.metadata.name = playlist.name
		self.metadata.owner = playlist.owner.display_name
		self.metadata.cover = playlist.images[0]['url']
		self.metadata.desc = playlist.description
		console.success('Playlist name is =={0}== by =={1}=='.format(self.metadata.name, self.metadata.owner))

	def request_playlist_tracks(self):
		results = self.SPClient.user_playlist_tracks(self.username, self.playlist_id)
		self.add_playlist_results(results)
		if 'next' in results:
			while results['next']:
				results = self.SPClient.next(results)
				self.add_playlist_results(results)

	def add_playlist_results(self, results):
		if 'tracks' not in results:
			console.warning('No tracks in playlist found!')
			return
		for data in results['tracks']['items']:
			data = objectify(data)
			self.tracks.append(objectify({
				'duration': data.track.duration_ms / 1e3,
				'link': data.track.external_urls.spotify,
				'name': data.track.name,
				'number': data.track.track_number
			}))

	def dump_file(self):
		file_path = os.path.join(self.save_path, self.metadata.name+'.txt')
		console.info('saving dump file to =={0}=='.format(file_path))

		contents = '#playlist\n@name {0}\n@description {1}\n@owner {2}\n@cover {3}\n\n'.format(self.metadata.name, self.metadata.desc, self.metadata.owner, self.metadata.cover)
		for track in self.tracks:
			contents += '{0}\n'.format(track.link, track.name, )

		if (len(os.path.dirname(file_path)) > 0):
			os.makedirs(os.path.dirname(file_path), exist_ok=True)
		with open(file_path, 'w') as stream:
			stream.write(contents)

		console.success('dump file created')

class LoadAlbum:
	def __init__(self, album_id, save_path = ''):
		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)
		self.save_path = save_path

		console.info('gathering album data, given id is =={0}=='.format(album_id))

		self.album_id = album_id
		self.tracks = []
		self.metadata = objectify({})

		self.request_album_info()

	def request_album_info(self):
		album = objectify(self.SPClient.album(self.album_id))

		album_artists = []
		for artist in album.artists:
			album_artists.append(artist['name'])

		self.metadata.artist = ' & '.join(album_artists)
		self.metadata.name = album.name
		self.metadata.cover = album.images[0]['url']

		console.success('album name is =={0}== by =={1}=='.format(self.metadata.name, self.metadata.artist))
		console.success('number of tracks in the album is =={0}==, loading them now'.format(album.tracks.total))

		self.load_album_tracks(album.tracks)
		self.dump_file()

	def load_album_tracks(self, tracks):
		for data in tracks.items:
			data = objectify(data)
			self.tracks.append(objectify({
				'duration': data.duration_ms / 1e3,
				'link': data.external_urls.spotify,
				'name': data.name,
				'number': data.track_number
			}))
		console.success('finished loading tracks, ready to dump file')

	def dump_file(self):
		file_path = os.path.join(self.save_path, self.metadata.name+'.txt')
		console.info('saving dump file to =={0}=='.format(file_path))

		contents = '#album\n@name {0}\n@artist {1}\n@cover {2}\n\n'.format(self.metadata.name, self.metadata.artist, self.metadata.cover)
		for track in self.tracks:
			contents += '{0}\n'.format(track.link, track.name)

		if (len(os.path.dirname(file_path)) > 0):
			os.makedirs(os.path.dirname(file_path), exist_ok=True)

		with open(file_path, 'w') as stream:
			stream.write(contents)

		console.success('dump file created')
