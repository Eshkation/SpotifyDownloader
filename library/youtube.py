# handles youtube sound downloading and song search
from dotenv import load_dotenv
from library.internal import *
from mutagen.id3 import ID3, APIC, TT2, TPE1, TRCK, TALB, TYER, TIT2, TPE2, error
from urllib.request import urlopen

load_dotenv()

import json
import os
import re
import requests
import youtube_dl
import isodate

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_CLIENT_KEY', '')

class YoutubeDLLogger:
	def debug(self, msg):
		pass

	def warning(self, msg):
		console.warning(msg)

	def error(self, msg):
		console.error(msg.replace('ERROR: ', ''))

class DownloadVideo:
	def __init__(self, track, video, customDir = ''):
		self.track = track.metadata
		self.video = video.metadata
		self.savePath = customDir
		self.downloadVelocity = []
		self.filePath = ''

		self.SUCCESS = False
		self.startDownload()

	def startDownload(self):
		filePathName = os.path.join(self.savePath, '{0} - {1}.%(ext)s'.format(self.track.artist, self.track.name))
		if (os.path.exists(filePathName.replace('%(ext)s', 'mp3'))):
			console.warning('Audio file for =={0} - {1}== already exists, skipping download'.format(self.track.artist, self.track.name))
			self.filePath = filePathName.replace('%(ext)s', 'mp3')
			self.SUCCESS = True
		else:
			ydl_opts = {
				'format': 'bestaudio/best',
				'postprocessors': [{
					'key': 'FFmpegExtractAudio',
					'preferredcodec': 'mp3',
					'preferredquality': '320'
				}],
				'progress_hooks': [self.displayProgress],
				'logger': YoutubeDLLogger(),
				'verbose': False,
				'outtmpl': filePathName,
				'get-filename': True
			}
			console.info('starting youtube download')
			try:
				with youtube_dl.YoutubeDL(ydl_opts) as ydl:
					ydl.download([self.video.id.videoId])
				console.info('applying metadata to file')
				self.applyTrackMetadata()
			except Exception as error:
				self.SUCCESS = False

	def applyTrackMetadata(self):
		audioFile = ID3(self.filePath)

		# album cover image
		albumCoverArt = urlopen(self.track.cover)
		audioFile['APIC'] = APIC(
			encoding = 3,
			mime = 'image/jpeg',
			type = 3,
			desc = u'Cover',
			data = albumCoverArt.read()
		)

		# album name
		audioFile['TALB'] = TALB(
			encoding = 3,
			text = self.track.albumName
		)

		# album release year
		audioFile['TYER'] = TYER(
			encoding = 3,
			text = self.track.releaseDate.split('-')[0]
		)

		# album artist
		audioFile['TPE2'] = TPE2(
			encoding = 3,
			text = self.track.albumArtist.split(';')
		)

		# track name
		audioFile['TIT2'] = TIT2(
			encoding = 3,
			text = self.track.name
		)

		# track number
		audioFile['TRCK'] = TRCK(
			encoding = 3,
			text = str(self.track.number)
		)

		# track artist name
		audioFile['TPE1'] = TPE1(
			encoding = 3,
			text = self.track.featuredArtists.split(';')
		)

		albumCoverArt.close()
		audioFile.save(v2_version=3)
		self.SUCCESS = True

	def displayProgress(self, d):
		display = objectify(d)
		if (display.status == 'downloading'):
			parts = 30
			downloadedPercent = round((float(display._percent_str.replace('%', '')) * parts) / 100)
			unfinishedPercent = parts-downloadedPercent

			downloadedBar = '#' * downloadedPercent
			unfinishedBar = ' ' * unfinishedPercent

			progressBar = '[=={0}=={1}]'.format(downloadedBar, unfinishedBar)
			text = '{0} {1} downloaded, estimated download time: =={2}== at =={3}=='.format(progressBar, display._percent_str, display._eta_str, display._speed_str)

			if (downloadedPercent == parts):
				console.info(text)
			else:
				console.info(text, end = '\r')

		elif (display.status == 'finished'):
			console.success('finished downloading, file directory is =={0}==, starting file conversion'.format(display.filename))
			self.filePath = display.filename.replace('.webm', '.mp3')

class SearchSong:
	def __init__(self, track):
		self.track = track.metadata
		self.metadata = {}

		self.requestSearch()

	def requestSearch(self):
		query = '{0} - {1} audio'.format(self.track.artist, self.track.name)
		apiRequest = requests.get('https://www.googleapis.com/youtube/v3/search', params = {
				'key': YOUTUBE_API_KEY,
				'maxResults': 50,
				'part': 'snippet,id',
				'q': query,
			}).text
		search = json.loads(apiRequest)
		queryIds = []

		for video in search['items']:
			video = objectify(video)
			if (video.id.kind == 'youtube#video'):
				queryIds.append(video.id.videoId)

		apiRequest = requests.get('https://www.googleapis.com/youtube/v3/videos', params = {
				'key': YOUTUBE_API_KEY,
				'id': ','.join(queryIds),
				'part': 'contentDetails'
			}).text

		duration = json.loads(apiRequest)

		choosenVideo = [{}, -100]
		for video in search['items']:
			video = objectify(video)
			if (video.id.kind == 'youtube#video'):
				for ytv in duration['items']:
					ytv = objectify(ytv)
					try:
						if (ytv.id == video.id.videoId):
							video.duration = ytv.contentDetails.duration
							video.duration = isodate.parse_duration(video.duration).total_seconds()
							break
					except:
						video.duration = 0
				videoPoints = self.attributePoints(video)

				if (videoPoints > choosenVideo[1]):
					choosenVideo = [video, videoPoints]

		if (choosenVideo[1] >= 3):
			console.success('video =={0}== ranked =={1}== points (=={2}==)'.format(choosenVideo[0].snippet.title, choosenVideo[1], choosenVideo[0].id.videoId))
			self.metadata = choosenVideo[0]
		else:
			self.metadata = False
			self.SUCCESS = False
			console.error('could not find a suitable video, the highest one ranked =={0}== points and is =={1}== (=={2}==)'.format(choosenVideo[1], choosenVideo[0].snippet.title, choosenVideo[0].id.videoId))

	def attributePoints(self, video):
		points = 0
		title = video.snippet.title.lower()

		# either video title has track name
		if (self.track.name.lower() in title):
			points += 3
		else:
			points -= 9

		# either video title has artist name
		if (self.track.artist.lower() in title):
			points += 3

		# video title has "official" in it
		if (re.search(r'of(f|)ici(a|e)l', title)):
			points += 6

		if (re.search(r'of(f|)ici(a|e)l audio', title)):
			if ('remix' in title):
				points += 2
			else:
				points += 12

		if (re.search(r'{0}(\s|)(:|-)(\s|){1}'.format(self.track.artist.lower(), self.track.name.lower()), title)):
			points += 6

		# video title has live in it, but track doesn't
		if (not 'live' in self.track.name.lower() and 'live' in title):
			points -= 9

		# video title has cover in it, but track doesn't
		if (not 'cover' in self.track.name.lower() and 'cover' in title):
			points -= 9

		# video title has edit in it, but track doesn't
		if (not 'edit' in self.track.name.lower() and 'edit' in title):
			points -= 3

		# video title has remix in it, but track doesn't
		if (not 'remix' in self.track.name.lower() and 'remix' in title):
			points -= 6

		# artist name is the channel name
		if (re.sub(r'[\W]+', '', video.snippet.channelTitle.lower()) == re.sub(r'[\W]+', '', self.track.artist.lower())):
			points += 6

		# video was found in a youtube topic
		if (video.snippet.channelTitle.lower() == self.track.artist.lower()+' - topic'):
			points += 9

		# video was found in a vevo channel
		if (video.snippet.channelTitle.lower() == self.track.artist.lower()+'vevo'):
			points += 9

		dur_diff = abs(video.duration - self.track.duration)
		if (dur_diff < 10):
			points += 15-int(dur_diff)

		return points
