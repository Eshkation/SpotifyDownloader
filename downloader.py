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
		file = open(self.dumpFilePath, 'r').read()
		lines = file.split('\n')
		saveDir = self.dumpFilePath.replace('.txt', '')

		while lines:
			line = lines.pop(0)
			if (line.startswith('http')):
				trackId = re.match('http(s|)://open.spotify.com/track/(.*)', line)
				if (trackId):
					trackId = trackId.group(2)
					track = LoadTrack(trackId)

					console.success('Found track in dump file: =={0}== by =={1}==, starting youtube search'.format(track.metadata.name, track.metadata.artist))
					youtubeVideo = SearchSong(track)
					if (youtubeVideo.metadata):
						download = DownloadVideo(track, youtubeVideo, saveDir)
						if (not download.SUCCESS):
							console.warning('Could not successfully process =={0}=='.format(trackId))
							f = open(saveDir+'.errors.txt', 'a')
							f.write(line+'\n')
							f.close()

			elif (line.startswith('##')):
				pass

			f = open(self.dumpFilePath, 'w')
			f.write('\n'.join(lines))
			f.close()

Downloader('Favorites.txt')
