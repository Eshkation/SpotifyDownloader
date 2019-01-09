# this file handles all spotify related requests

from library.internal import *
from spotipy.oauth2 import SpotifyClientCredentials

SPCredentials = SpotifyClientCredentials(
    client_id = '',
    client_secret = ''
)

import os
import spotipy
import time

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

        self.metadata.albumName = track.album.name
        albumArtist = []
        for artist in track.album.artists:
            albumArtist.append(artist['name'])

        self.metadata.artist = ' & '.join(albumArtist)

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
