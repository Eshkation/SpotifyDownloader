# handles youtube sound downloading and song search
from dotenv import load_dotenv
from library.internal import *
from mutagen.id3 import ID3, APIC, TT2, TPE1, TRCK, TALB, TYER, TIT2, TPE2, error
from urllib.request import urlopen

load_dotenv()

import isodate
import json
import os
import re
import requests
import sys
import time
import traceback
import youtube_dl

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_CLIENT_KEY', '')

class YoutubeDLLogger:
	def debug(self, msg):
		pass

	def warning(self, msg):
		console.warning(msg)

	def error(self, msg):
		console.error(msg.replace('ERROR: ', ''))

class DownloadVideo:
	def __init__(self, track, video, custom_dir = ''):
		self.track = track.metadata
		self.video = video.metadata
		self.save_path = custom_dir
		self.steps_download_velocity = []
		self.file_path = ''

		self.SUCCESS = False
		self.ALREADY_EXISTS = False
		self.EXCEPTION = ''

		self.start = time.time()
		self.start_download_time = 0
		self.steps_downloaded = 0
		self.average_velocity = 0
		self.start_download()

	def start_download(self):
		file_path_name = os.path.join(self.save_path, '{0} - {1}.%(ext)s'.format(self.track.artist, self.track.name))
		file_path_name = file_path_name.replace('/', '_')
		if (os.path.exists(file_path_name.replace('%(ext)s', 'mp3'))):
			console.warning('Audio file for =={0} - {1}== already exists, skipping download'.format(self.track.artist, self.track.name))
			self.file_path = file_path_name.replace('%(ext)s', 'mp3')
			self.SUCCESS = True
			self.ALREADY_EXISTS = True
		else:
			ydl_opts = {
				'format': 'bestaudio/best',
				'postprocessors': [{
					'key': 'FFmpegExtractAudio',
					'preferredcodec': 'mp3',
					'preferredquality': '320'
				}],
				'progress_hooks': [self.display_progress],
				'logger': YoutubeDLLogger(),
				'verbose': False,
				'outtmpl': file_path_name,
				'get-filename': True
			}
			console.info('starting youtube download')
			try:
				with youtube_dl.YoutubeDL(ydl_opts) as ydl:
					ydl.download([self.video.id.videoId])
				console.info('applying metadata to file')
				self.applyTrackMetadata()
			except Exception:
				error = traceback.format_exc().replace('\n', ' ')
				console.error(error)
				self.SUCCESS = False
				self.EXCEPTION = error
		console.debug('download process took =={0}s== to finish\n'.format(int(time.time()-self.start)))

	def applyTrackMetadata(self):
		audio_file = ID3(self.file_path)

		# album cover image
		album_cover_art = urlopen(self.track.cover)
		audio_file['APIC'] = APIC(
			encoding = 3,
			mime = 'image/jpeg',
			type = 3,
			desc = u'Cover',
			data = album_cover_art.read()
		)

		# album name
		audio_file['TALB'] = TALB(
			encoding = 3,
			text = self.track.album_name
		)

		# album release year
		audio_file['TYER'] = TYER(
			encoding = 3,
			text = self.track.release_date.split('-')[0]
		)

		# album artist
		audio_file['TPE2'] = TPE2(
			encoding = 3,
			text = self.track.album_artist.split(';')
		)

		# track name
		audio_file['TIT2'] = TIT2(
			encoding = 3,
			text = self.track.name
		)

		# track number
		audio_file['TRCK'] = TRCK(
			encoding = 3,
			text = str(self.track.number)
		)

		# track artist name
		audio_file['TPE1'] = TPE1(
			encoding = 3,
			text = self.track.featured_artists.split(';')
		)

		album_cover_art.close()
		audio_file.save(v2_version=3)
		self.SUCCESS = True

	def display_progress(self, d):
		display = objectify(d)
		if (display.status == 'downloading'):
			self.steps_downloaded += 1
			self.average_velocity += display.speed or 0
			parts = 30
			downloaded_parts = round((float(display._percent_str.replace('%', '')) * parts) / 100)
			unfinished_parts = parts-downloaded_parts

			bar_downloaded = '#' * downloaded_parts
			bar_unfinished = ' ' * unfinished_parts

			progress_bar = '[=={0}=={1}]'.format(bar_downloaded, bar_unfinished)
			text = '{0} {1} downloaded, estimated download time: =={2}== at =={3}=='.format(progress_bar, display._percent_str, display._eta_str, display._speed_str)

			if (downloaded_parts == 0):
				self.start_download_time = time.time()

			elif (downloaded_parts == parts):
				text = 'file downloaded, total download time: =={0}s==, average velocity: =={1:.2f} KiB/s=='.format(int(time.time() - self.start_download_time), (self.average_velocity/self.steps_downloaded)/1e3)
				sys.stdout.write('\033[K')
				console.info(text)
			else:
				console.info(text, end = '\r')


		elif (display.status == 'finished'):
			self.file_path, fileExtension = display.filename.rsplit('.', 1)
			self.file_path = self.file_path+'.mp3'
			console.success('finished downloading, file directory is =={0}==, starting file conversion'.format(self.file_path))

class SearchSong:
	def __init__(self, track):
		self.track = track.metadata
		self.metadata = {}

		self.request_search()

	def request_search(self):
		query = '{0} - {1}'.format(self.track.artist, self.track.name)
		api_request = requests.get('https://www.googleapis.com/youtube/v3/search', params = {
				'key': YOUTUBE_API_KEY,
				'maxResults': 50,
				'part': 'snippet,id',
				'q': re.sub(r'\((feat.|)(.*?)\)', '', query),
			}).text
		search = json.loads(api_request)
		query_ids = []

		for video in search['items']:
			video = objectify(video)
			if (video.id.kind == 'youtube#video'):
				query_ids.append(video.id.videoId)

		api_request = requests.get('https://www.googleapis.com/youtube/v3/videos', params = {
				'key': YOUTUBE_API_KEY,
				'id': ','.join(query_ids),
				'part': 'contentDetails'
			}).text

		duration = json.loads(api_request)

		selected_video = [{}, -100]
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
				video_points = self.attribute_meta_points(video)

				if (video_points > selected_video[1]):
					selected_video = [video, video_points]

		if (selected_video[1] >= 3):
			console.success('video =={0}== ranked =={1}== points (=={2}==)'.format(selected_video[0].snippet.title, selected_video[1], selected_video[0].id.videoId))
			self.metadata = selected_video[0]
		else:
			self.metadata = False
			self.SUCCESS = False
			console.error('could not find a suitable video, the highest one ranked =={0}== points and is =={1}== (=={2}==)'.format(selected_video[1], selected_video[0].snippet.title, selected_video[0].id.videoId))

	def attribute_meta_points(self, video):
		points = 0
		title = re.sub(r'[^\w\s]', '', video.snippet.title.lower())
		title = re.sub(r'\((feat.|)(.*?)\)', '', title)
		fx_artist_name = re.sub(r'[^\w\s]', '', self.track.artist.lower())
		fx_track_name = re.sub(r'[^\w\s]', '', self.track.name.lower())
		fx_track_name = re.sub(r'\((feat.|)(.*?)\)', '', fx_track_name)
		fx_channel_name = re.sub(r'[^\w\s]', '', video.snippet.channelTitle.lower())

		# either video title has track name
		if (fx_track_name in title):
			points += 3
		else:
			points -= 30

		# either video title has artist name
		if (fx_artist_name in title):
			points += 3

		# video title has "official" in it
		if (re.search(r'of(f|)ici(a|e)l', title)):
			points += 6

		if (re.search(r'unof(f|)ici(a|e)l', title)):
			points -= 6

		if (re.search(r'of(f|)ici(a|e)l audio', title)):
			if (not 'remix' in fx_track_name and 'remix' in title):
				points += 2
			else:
				points += 20

		if (re.search(r'unof(f|)ici(a|e)l audio', title)):
			points -= 9

		if (re.search(r'of(f|)ici(a|e)l music (video|)', title)):
			points += 15

		if (re.search(r'unof(f|)ici(a|e)l music (video|)', title)):
			points -= 20

		# artist name - track name
		if (re.search(r'{0}(\s|)(:|-)(\s|){1}'.format(fx_artist_name, fx_track_name), title)):
			points += 12

		# track name - artist name
		if (re.search(r'{0}(\s|)(:|-)(\s|){1}'.format(fx_track_name, fx_artist_name), title)):
			points += 12

		# video title has live in it, but track doesn't
		if (not 'live' in fx_track_name and 'live' in title):
			points -= 15

		# video title has cover in it, but track doesn't
		if (not 'cover' in fx_track_name and 'cover' in title):
			points -= 15

		# video title has edit in it, but track doesn't
		if (not 'edit' in fx_track_name and 'edit' in title):
			points -= 3

		# video title has remix in it, but track doesn't
		if (not 'remix' in fx_track_name and 'remix' in title):
			points -= 6

		if (not 'instrumental' in fx_track_name and 'instrumental' in title):
			points -= 12

		if (not 'piano sheet' in fx_track_name and 'piano sheet' in title):
			points -= 12

		if (not any(ext in fx_track_name for ext in ['glastonbury', 'lollapalooza', 'coachella'])):
			if any(ext in title for ext in ['glastonbury', 'lollapalooza', 'coachella']):
				points -= 12

		# artist name is the channel name
		if (re.sub(r'[\W]+', '', video.snippet.channelTitle.lower()) == re.sub(r'[\W]+', '', fx_artist_name)):
			points += 6

		# video was found in a youtube topic
		if (fx_channel_name == fx_artist_name+' - topic'):
			points += 9

		# video was found in a vevo channel
		if (fx_channel_name == fx_artist_name+'vevo'):
			points += 9

		points += 15-int(dur_diff)

		return points
