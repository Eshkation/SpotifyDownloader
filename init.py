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
		self.save_directory = ''
		self.include_dump_file_name = True

		self.process_start_time = 0
		self.get_given_params()

	def get_given_params(self):
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
			self.save_directory = params.folder
			console.config('Save directory set to =={0}=='.format(self.save_directory))

		if (params.nofilename):
			self.include_dump_file_name = False
			console.config('Save directory will not include dump file name')

		if (params.source):
			console.config('given source is =={0}==, identifying url type'.format(params.source))
			self.identify_given_source(params.source)

		elif (params.download):
			console.config('starting download from =={0}=='.format(params.download))
			self.prepare_download(params.download)

	def prepare_download(self, dump_file):
		self.process_start_time = time.time()

		contents = open(dump_file, 'r').read()
		content_lines = contents.split('\n')
		if (self.include_dump_file_name):
			save_directory = os.path.join(self.save_directory, os.path.basename(dump_file).rsplit('.', 1)[0])
		else:
			save_directory = self.save_directory
		console.config('saving tracks to =={0}=='.format(save_directory))

		while content_lines:
			line = content_lines.pop(0)
			if (line.startswith('http')):
				track_id = re.match('http(s|)://open.spotify.com/track/([^##]+)', line)
				if (track_id):
					track_id = track_id.group(2).strip()
					track = LoadTrack(track_id)

					console.success('Found track in dump file: =={0}== by =={1}==, starting youtube search'.format(track.metadata.name, track.metadata.artist))
					file_path_name = os.path.join(save_directory, '{0} - {1}.%(ext)s'.format(track.metadata.artist, track.metadata.name))
					file_path_name = file_path_name.replace('/', '_')
					if (os.path.exists(file_path_name.replace('%(ext)s', 'mp3'))):
						console.warning('Audio file for =={0} - {1}== already exists, skipping download'.format(track.metadata.artist, track.metadata.name))
					else:
						youtube_video = SearchSong(track)
						if (youtube_video.metadata):
							download = DownloadVideo(track, youtube_video, save_directory)
							if (not download.SUCCESS):
								console.warning('Could not successfully process =={0}=='.format(track_id))
								with open(dump_file+'.errors', 'a') as stream:
									stream.write('{0} ## {1}\n'.format(line, download.EXCEPTION))

			with open(dump_file, 'w+') as stream:
				stream.write('\n'.join(content_lines))
		total_seconds = int(time.time() - self.process_start_time)
		console.debug('Total process time was =={0:>08}=='.format(str(datetime.timedelta(seconds = total_seconds))))

	def identify_given_source(self, source_url):
		private_playlist = re.match('http(s|)://open.spotify.com/user/(.*?)/playlist/(.*)', source_url)
		public_playlist = re.match('http(s|)://open.spotify.com/playlist/(.*)', source_url)
		album = re.match('http(s|)://open.spotify.com/album/(.*)', source_url)

		if (private_playlist):
			username, playlist_id = private_playlist.group(2), private_playlist.group(3)
			console.config('Private playlist request found, username is =={0}== and playlist id is =={1}=='.format(username, playlist_id))
			LoadPlaylist(username, playlist_id, self.save_directory)

		elif (public_playlist):
			playlist_id = public_playlist.group(2)
			console.config('Playlist request found, id is =={0}=='.format(playlist_id))
			LoadPlaylist('', playlist_id, self.save_directory)

		elif (album):
			album_id = album.group(2)
			console.config('Album request found, id is =={0}=='.format(album_id))
			LoadAlbum(album_id, self.save_directory)


MainProcessor()
