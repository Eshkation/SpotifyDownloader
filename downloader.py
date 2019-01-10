# this is purely an example folder

from library.internal import *
from library.spotify import LoadTrack, LoadAlbum
from library.youtube import SearchSong, DownloadVideo
import re

class Downloader:
	def __init__(self, dumpFile):
		self.dumpFilePath = dumpFile

		self.readFile()

	def readFile(self):
		console.info('opening file =={0}=='.format(self.dumpFilePath))
		file = open(self.dumpFilePath).readlines()
		saveDir = self.dumpFilePath.replace('.txt', '')

		for i, line in enumerate(file[:]):
			if (line.startswith('http')):
				trackId = re.match('http(s|)://open.spotify.com/track/(.*)', line)
				if (trackId):
					trackId = trackId.group(2)
					track = LoadTrack(trackId)

					console.success('Found track in dump file: =={0}== by =={1}==, starting youtube search'.format(track.metadata.name, track.metadata.artist))
					youtubeVideo = SearchSong(track)
					if (youtubeVideo.metadata):
						download = DownloadVideo(track, youtubeVideo, saveDir)
						if (download.SUCCESS):
							del file[i]

						else:
							console.warning('Could not successfully process =={0}==, keeping it in file'.format(trackId))
							file[i] = '## '+file[i]

					print('\n' * 40)
			open(self.dumpFilePath, 'w').writelines(file)



Downloader('Favorites.txt')
