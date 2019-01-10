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
	def __init__(self, trackId):
		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)

		self.trackId = trackId
		self.metadata = objectify({})
		console.info('requesting track data, given id is =={0}=='.format(self.trackId))

		self.requestTrackInfo()

	def requestTrackInfo(self):
		track = objectify(self.SPClient.track(self.trackId))

		self.metadata.name = track.name
		self.metadata.number = track.track_number
		self.metadata.duration = track.duration_ms / 1e3
		self.metadata.cover = track.album.images[0]['url']
		self.metadata.releaseDate = track.album.release_date
		trackArtists = []
		for artist in track.artists:
			trackArtists.append(artist['name'])
		self.metadata.featuredArtists = ';'.join(trackArtists)
		self.metadata.artist = self.metadata.featuredArtists.split(';')[0]

		self.metadata.albumName = track.album.name
		albumArtist = []
		for artist in track.album.artists:
			albumArtist.append(artist['name'])
		self.metadata.albumArtist = ';'.join(albumArtist)


class LoadPlaylist:
	def __init__(self, username, playlistId, savePath = ''):
		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)
		self.savePath = savePath
		self.username = username
		self.playlistId = playlistId
		self.tracks = []
		self.metadata = objectify({})

		console.info('Requesting playlist metadata, given username is =={0}== and playlist id is =={1}=='.format(username or 'none', playlistId))
		self.requestPlaylistInfo()
		console.info('requesting playlist tracks')
		self.requestPlaylistTracks()
		console.success('finished loading playlist, =={0}== songs were found'.format(len(self.tracks)))
		self.dumpFile()

	def requestPlaylistInfo(self):
		playlist = objectify(self.SPClient.user_playlist(self.username, self.playlistId))

		self.metadata.name = playlist.name
		self.metadata.owner = playlist.owner.display_name
		self.metadata.cover = playlist.images[0]['url']
		self.metadata.desc = playlist.description
		console.success('Playlist name is =={0}== by =={1}=='.format(self.metadata.name, self.metadata.owner))

	def requestPlaylistTracks(self):
		results = self.SPClient.user_playlist_tracks(self.username, self.playlistId)
		while results['next']:
			results = self.SPClient.next(results)
			for data in results['items']:
				data = objectify(data)
				self.tracks.append(objectify({
					'duration': data.track.duration_ms / 1e3,
					'link': data.track.external_urls.spotify,
					'name': data.track.name,
					'number': data.track.track_number
				}))

	def dumpFile(self):
		filePath = os.path.join(self.savePath, self.metadata.name+'.txt')
		console.info('saving dump file to =={0}=='.format(filePath))

		contents = '#playlist\n@name {0}\n@description {1}\n@owner {2}\n@cover {3}\n\n'.format(self.metadata.name, self.metadata.desc, self.metadata.owner, self.metadata.cover)
		for track in self.tracks:
			contents += '{0}\n'.format(track.link, track.name, )

		stream = open(filePath, 'w')
		stream.write(contents)
		stream.close()

		console.success('dump file created')

class LoadAlbum:
	def __init__(self, albumId, savePath = ''):
		self.SPClient = spotipy.Spotify(
			client_credentials_manager = SPCredentials
		)
		self.savePath = savePath

		console.info('gathering album data, given id is =={0}=='.format(albumId))

		self.albumId = albumId
		self.tracks = []
		self.metadata = objectify({})

		self.requestAlbumInfo()

	def requestAlbumInfo(self):
		album = objectify(self.SPClient.album(self.albumId))

		albumArtist = []
		for artist in album.artists:
			albumArtist.append(artist['name'])

		self.metadata.artist = ' & '.join(albumArtist)
		self.metadata.name = album.name
		self.metadata.cover = album.images[0]['url']

		console.info('album name is =={0}== by =={1}=='.format(self.metadata.name, self.metadata.artist))
		console.info('number of tracks in the album is =={0}==, loading them now'.format(album.tracks.total))

		self.loadAlbumTracks(album.tracks)
		self.dumpFile()

	def loadAlbumTracks(self, tracks):
		for data in tracks.items:
			data = objectify(data)
			self.tracks.append(objectify({
				'duration': data.duration_ms / 1e3,
				'link': data.external_urls.spotify,
				'name': data.name,
				'number': data.track_number
			}))
		console.success('finished loading tracks, ready to dump file')

	def dumpFile(self):
		filePath = os.path.join(self.savePath, self.metadata.name+'.txt')
		console.info('saving dump file to =={0}=='.format(filePath))

		contents = '#album\n@name {0}\n@artist {1}\n@cover {2}\n\n'.format(self.metadata.name, self.metadata.artist, self.metadata.cover)
		for track in self.tracks:
			contents += '{0}\n'.format(track.link, track.name, )

		stream = open(filePath, 'w')
		stream.write(contents)
		stream.close()

		console.success('dump file created')
