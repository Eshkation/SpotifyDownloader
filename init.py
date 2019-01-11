from library.internal import *
from library.spotify import *
from library.youtube import *

import argparse
import colorama
import datetime
import os
import re
import time

class MainProcessor:
	def __init__(self):
		print(getattr(colorama.Fore, 'CYAN')+"""
   ____          __  _ ___     ___                  __             __
  / __/__  ___  / /_(_) _/_ __/ _ \___ _    _____  / /__  ___ ____/ /__ ____
 _\ \/ _ \/ _ \/ __/ / _/ // / // / _ \ |/|/ / _ \/ / _ \/ _ `/ _  / -_) __/
/___/ .__/\___/\__/_/_/ \_, /____/\___/__,__/_//_/_/\___/\_,_/\_,_/\__/_/
   /_/                 /___/
""")
		self.saveDir = ''
		self.includeDumpFileName = True

		self.processStart = 0
		self.getGivenParams()

	def getGivenParams(self):
		parser = argparse.ArgumentParser(description='Process some integers.')
		parser.add_argument('-s', '--source',
			help = 'The source link (can either be a spotify album or playlist link)'
		)
		parser.add_argument('-d', '--download',
			help = 'The source dump file to download tracks from'
		)
		parser.add_argument('-f', '--folder',
			help = 'Directory choosen to write the files'
		)
		parser.add_argument('-nf', '--nofilename',
			help = 'Include dump file name in the save directory',
			action = 'store_true'
		)
		params, _ = parser.parse_known_args()
		params = objectify(vars(params))

		if (params.folder):
			self.saveDir = params.folder
			console.config('Save directory set to =={0}=='.format(self.saveDir))

		if (params.nofilename):
			self.includeDumpFileName = False
			console.config('Save directory will not include dump file name')

		if (params.source):
			console.config('given source is =={0}==, identifying url type'.format(params.source))
			self.identifyGivenSource(params.source)

		elif (params.download):
			console.config('starting download from =={0}=='.format(params.download))
			self.prepareDownload(params.download)

	def prepareDownload(self, dumpFile):
		self.processStart = time.time()

		contents = open(dumpFile, 'r').read()
		contentLines = contents.split('\n')
		if (self.includeDumpFileName):
			saveDir = os.path.join(self.saveDir, os.path.basename(dumpFile).rsplit('.', 1)[0])
		else:
			saveDir = self.saveDir
		console.config('saving tracks to =={0}=='.format(saveDir))

		while contentLines:
			line = contentLines.pop(0)
			if (line.startswith('http')):
				trackId = re.match('http(s|)://open.spotify.com/track/([^##]+)', line)
				if (trackId):
					trackId = trackId.group(2).strip()
					track = LoadTrack(trackId)

					console.success('Found track in dump file: =={0}== by =={1}==, starting youtube search'.format(track.metadata.name, track.metadata.artist))
					youtubeVideo = SearchSong(track)
					if (youtubeVideo.metadata):
						download = DownloadVideo(track, youtubeVideo, saveDir)
						if (not download.SUCCESS):
							console.warning('Could not successfully process =={0}=='.format(trackId))
							with open(dumpFile+'.errors', 'a') as stream:
								stream.write('{0} ## {1}\n'.format(line, download.EXCEPTION))

			with open(dumpFile, 'w+') as stream:
				stream.write('\n'.join(contentLines))
		totalSeconds = int(time.time() - self.processStart)
		console.debug('Total process time was =={0:>08}=='.format(str(datetime.timedelta(seconds = totalSeconds))))

	def identifyGivenSource(self, urlSource):
		privatePlaylist = re.match('http(s|)://open.spotify.com/user/(.*?)/playlist/(.*)', urlSource)
		publicPlaylist = re.match('http(s|)://open.spotify.com/playlist/(.*)', urlSource)
		album = re.match('http(s|)://open.spotify.com/album/(.*)', urlSource)

		if (privatePlaylist):
			username, playlistId = privatePlaylist.group(2), privatePlaylist.group(3)
			console.config('Private playlist request found, username is =={0}== and playlist id is =={1}=='.format(username, playlistId))
			LoadPlaylist(username, playlistId, self.saveDir)

		elif (publicPlaylist):
			playlistId = publicPlaylist.group(2)
			console.config('Playlist request found, id is =={0}=='.format(playlistId))
			LoadPlaylist('', playlistId, self.saveDir)

		elif (album):
			albumId = album.group(2)
			console.config('Album request found, id is =={0}=='.format(albumId))
			LoadAlbum(albumId, self.saveDir)


MainProcessor()
