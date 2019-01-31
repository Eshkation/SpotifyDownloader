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


class SpotifySearch:
	def __init__(self, query, query_type, save_dir = ''):
		self.console = power_console('spotify.search')

		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)
		self.query = query
		self.query_type = query_type
		self.save_dir = save_dir

		self.console.info('Searching for <LC>{0}<W> (<LC>{1}<W>)'.format(query, query_type))
		self.begin_search()

	def begin_search(self):
		results = self.SPClient.search(self.query, limit = 15, type = self.query_type)
		index = 1
		creator_type = 'owner' if (self.query_type == 'playlist') else 'artists'
		if (len(results[self.query_type+'s']['items']) > 0):
			self.console.info('<M>{0:>2} {1:>35} {2:>45} {3:>25}'.format('no.', creator_type, self.query_type+' name', 'release date'), True)
			for data in results[self.query_type+'s']['items']:
				item = objectify(data)
				artist_name = ''
				if (creator_type == 'owner'):
					artist_name = item[creator_type].display_name
				else:
					artist_name = item[creator_type][0]['name']
				self.console.info('#{0:>02d} {1:>35} {2:>45} {3:>25}'.format(
					index,
					artist_name[:32].strip()+'...' if len(artist_name) > 35 else artist_name.strip(),
					item.name[:32].strip()+'...'  if len(item.name) > 35 else item.name.strip(),
					item.release_date.split('-')[0] if ('release_date' in item) else '-'
				), True)
				index += 1
			selected_number = int(input('\nSelect search item number:\n> #'))-1
			if (selected_number >= 0 and selected_number <= index):
				selected_item = objectify(results[self.query_type+'s']['items'][selected_number])
				artist_name = ''
				if (creator_type == 'owner'):
					artist_name = selected_item[creator_type].display_name
				else:
					artist_name = selected_item[creator_type][0]['name']
				uri_id = selected_item.id
				self.console.success('Selected {0} is <G>{1} - {2}<W>, uri id is {3}'.format(self.query_type, artist_name, selected_item.name, uri_id))
				if (self.query_type == 'album'):
					LoadAlbum(uri_id, self.save_dir)

				elif (self.query_type == 'playlist'):
					LoadPlaylist(artist_name, uri_id)

				elif (self.query_type == 'track'):
					with open(os.path.join(self.save_dir, validate.file_name(selected_item.name+'.txt')), 'w') as stream:
						stream.write('https://open.spotipy.com/track/'+uri_id)
			else:
				self.console.error('Invalid item number')
		else:
			self.console.error('Search did not return results')


class LoadTrack:
	def __init__(self, track_id, save = False, save_dir = ''):
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
		self.console = power_console('loader.playlist')

		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)
		self.save_path = save_path
		self.username = username
		self.playlist_id = playlist_id
		self.tracks = []
		self.metadata = objectify({})

		self.console.info('Requesting playlist metadata')
		self.request_playlist_info()
		self.request_playlist_tracks()
		self.console.success('finished loading playlist, {0} songs were found'.format(len(self.tracks)))
		self.dump_file()

	def request_playlist_info(self):
		playlist = objectify(self.SPClient.user_playlist(self.username, self.playlist_id))

		self.metadata.name = playlist.name
		self.metadata.owner = playlist.owner.display_name
		self.metadata.cover = playlist.images[0]['url']
		self.metadata.desc = playlist.description
		self.console.success('Playlist is <G>{0}<W> by <G>{1}'.format(self.metadata.name, self.metadata.owner))

	def request_playlist_tracks(self):
		results = self.SPClient.user_playlist_tracks(self.username, self.playlist_id)
		if ('items' in results):
			for data in results['items']:
				data = objectify(data)
				self.tracks.append(objectify({
					'duration': data.track.duration_ms / 1e3,
					'link': data.track.external_urls.spotify,
					'name': data.track.name,
					'number': data.track.track_number
				}))
		while 'next' in results:
			results = self.SPClient.next(results)
			if (results):
				for data in results['items']:
					data = objectify(data)
					self.tracks.append(objectify({
						'duration': data.track.duration_ms / 1e3,
						'link': data.track.external_urls.spotify,
						'name': data.track.name,
						'number': data.track.track_number
					}))
			else:
				break

	def dump_file(self):
		file_path = os.path.join(self.save_path, self.metadata.name+'.txt')
		self.console.info('Saving dump file to <LC>{0}'.format(file_path))

		contents = '#playlist\n@name {0}\n@description {1}\n@owner {2}\n@cover {3}\n\n'.format(self.metadata.name, self.metadata.desc, self.metadata.owner, self.metadata.cover)
		for track in self.tracks:
			contents += '{0}\n'.format(track.link, track.name, )

		if (len(os.path.dirname(file_path)) > 0):
			os.makedirs(os.path.dirname(file_path), exist_ok=True)
		with open(file_path, 'w') as stream:
			stream.write(contents)

		self.console.success('Dump file successfully generated')

class LoadAlbum:
	def __init__(self, album_id, save_path = ''):
		self.console = power_console('loader.album')

		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)
		self.save_path = save_path

		self.console.info('Gathering album data (<LC>ID_{0}<W>)'.format(album_id))

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

		self.console.success('Album <G>{0}<W> by <G>{1}'.format(self.metadata.name, self.metadata.artist))
		self.console.success('<G>{0}<W> tracks were found'.format(album.tracks.total))

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
		self.console.success('finished loading tracks, ready to dump file')

	def dump_file(self):
		file_path = os.path.join(self.save_path, self.metadata.name+'.txt')
		self.console.info('Writing dump file to directory <LC>{0}'.format(file_path))

		contents = '#album\n@name {0}\n@artist {1}\n@cover {2}\n\n'.format(self.metadata.name, self.metadata.artist, self.metadata.cover)
		for track in self.tracks:
			contents += '{0}\n'.format(track.link, track.name)

		if (len(os.path.dirname(file_path)) > 0):
			os.makedirs(os.path.dirname(file_path), exist_ok=True)

		with open(file_path, 'w') as stream:
			stream.write(contents)

		self.console.success('Dump file generated')
