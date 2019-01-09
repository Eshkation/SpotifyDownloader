# handles youtube sound downloading and song search
from library.internal import *

import json
import re
import requests

YOUTUBE_API_KEY = ''

class SearchSong:
	def __init__(self, track):
		self.track = track.metadata

		self.requestSearch()

	def requestSearch(self):
		query = '{0} - {1}'.format(self.track.artist, self.track.name)
		console.info('youtube search query is =={0}==, searching'.format(query))

		apiRequest = requests.get('https://www.googleapis.com/youtube/v3/search', params = {
				'key': YOUTUBE_API_KEY,
				'maxResults': 20,
				'part': 'snippet,id',
				'q': query,
			}).text
		f = open('request.json', 'w', encoding = 'utf-8')
		f.write(apiRequest)
		f.close()
		search = json.loads(apiRequest)

		choosenVideo = [{}, -100]
		for video in search['items']:
			video = objectify(video)
			videoPoints = self.attributePoints(video)

			if (videoPoints > choosenVideo[1]):
				choosenVideo = [video, videoPoints]
		if (choosenVideo[1] > 0):
			console.success('video =={0}== ranked =={1}== points, ready to download'.format(choosenVideo[0].snippet.title, choosenVideo[1]))
		else:
			console.error('could not find a suitable video, the highest one ranked =={0}== points and is =={1}=='.format(choosenVideo[1], choosenVideo[0].snippet.title))

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

		if (re.search(r'{0}(\s|)(:|-)(\s|){1}'.format(self.track.artist.lower(), self.track.name.lower()), title)):
			points += 6

		# video title has live in it, but track doesn't
		if (not 'live' in self.track.name.lower() and 'live' in title):
			points -= 6

		# video title has cover in it, but track doesn't
		if (not 'cover' in self.track.name.lower() and 'cover' in title):
			points -= 8 # fricckin' covers

		# video title has edit in it, but track doesn't
		if (not 'edit' in self.track.name.lower() and 'edit' in title):
			points -= 2

		# video title has remix in it, but track doesn't
		if (not 'remix' in self.track.name.lower() and 'remix' in title):
			points -= 3

		# artist name is the channel name
		if (video.snippet.channelTitle.lower() == self.track.artist.lower()):
			points += 6

		# video was found in a youtube topic
		if (video.snippet.channelTitle.lower() == self.track.artist.lower()+' - topic'):
			points += 3

		# video was found in a vevo channel
		if (video.snippet.channelTitle.lower() == self.track.artist.lower()+'vevo'):

			points += 9

		return points
