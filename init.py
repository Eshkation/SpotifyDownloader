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
        self.console = power_console('main')
        print(getattr(colorama.Fore, 'LIGHTGREEN_EX') + r"""

                     . ........
                 . ................
              ........................
             ............................
           ...............................                                                        . .     .
          ..... .               .  ........        ......... .                            . ..     ...   .....
          .....     ........        . .....       .....  ....                             .....    . .  ... ..
         ......................... .   ......     ...          ... ......     . ......    ....... .... .........     ....
        . ......             .  ............       ....... .   ............  ....... ... .....   ..... . ..   ....   ....
        . .......   ........ ..      .......        .. ......  ...      ... ....     . .. .....   ....   ..   ....   ...
         .........................   ........      .      .... ...      ...  ...     .... .....   ....   ..     ... ...
         ........            .. ............      ..  .  . ... .....  . ..........   .........    ....   ..      .....
          ......................   ........       ...........  .......... .  . .........    ..... ....   ..       ...
           ...............................              .      ...                ..                             ....
             ............................                      ....                                           ......
              ........................
                  ....................
                     . ........



""")
        self.save_directory = ''
        self.include_dump_file_name = True
        self.include_album_name = False

        self.process_start_time = 0
        self.download_low_score = False

        self.get_given_params()

    def get_given_params(self):
        parser = argparse.ArgumentParser(description='Process some integers.')
        parser.add_argument('-s', '--source',
                            help='The source link (can either be a spotify album or playlist link)'
                            )
        parser.add_argument('-d', '--download',
                            help='The source dump file to download tracks from'
                            )
        parser.add_argument('-f', '--folder',
                            help='Directory choosen to write the files'
                            )
        parser.add_argument('-l', '--lookup',
                            help='Spotify search'
                            )
        parser.add_argument('-nf', '--nofilename',
                            help='Include dump file name in the save directory',
                            action='store_true'
                            )
        parser.add_argument('-ia', '--includealbumname',
                            help='Include track album name in the save directory',
                            action='store_true'
                            )
        parser.add_argument('-fd', '--forcedownload',
                            help='Allow downloading of low scored videos',
                            action='store_true'
                            )
        params, _ = parser.parse_known_args()
        params = objectify(vars(params))

        self.console.info('Reading served parameters')
        if (params.folder):
            self.save_directory = params.folder
            self.console.info('Save directory set to <LC>{0}'.format(
                self.save_directory), True)

        if (params.nofilename):
            self.include_dump_file_name = False
            self.console.info(
                'Save directory will not include dump file name', True)

        if (params.includealbumname):
            self.include_album_name = True
            self.console.info(
                'Save directory will include track\'s album name', True)

        if (params.forcedownload):
            self.download_low_score = True
            self.console.info('Low scored videos will be downloaded', True)

        if (params.source):
            self.console.info(
                'Given source is <LC>{0}<W>, identifying url type'.format(
                    params.source))
            self.identify_given_source(params.source)

        elif (params.download):
            self.console.info(
                'Downloading tracks from <LC>{0}'.format(params.download))
            self.prepare_download(params.download)

        elif (params.lookup):
            self.identify_search(params.lookup)

    def identify_search(self, query):
        if (':' in query):
            search_type, search_query = query.split(':', 1)
            search_type = search_type.lower()
            if (search_type in ['album', 'playlist', 'track']):
                SpotifySearch(search_query, search_type, self.save_directory)
                return
        self.console.error(
            'Search must be (album:|track:|playlist:)name')

    def prepare_download(self, dump_file):
        self.process_start_time = time.time()

        contents = open(dump_file, 'r').read()
        content_lines = contents.split('\n')
        if (self.include_dump_file_name):
            save_directory = os.path.join(
                self.save_directory,
                os.path.basename(dump_file).rsplit('.', 1)[0])
        else:
            save_directory = self.save_directory
        self.console.info('saving tracks to <LC>{0}'.format(save_directory))

        while content_lines:
            line = content_lines.pop(0)
            print(line)
            if (line.startswith('http')):
                track_id = re.search(
                    'http(s|)://open.spotify.com/track/([^##]+)', line)
                if (track_id):
                    track_id = track_id.group(2).strip()
                    track = LoadTrack(track_id)

                    self.console.success(
                        'Found track: <G>{0}<W> by <G>{1}<W>'.format(
                            track.metadata.name, track.metadata.artist))
                    final_save_dir = save_directory
                    if (self.include_album_name):
                        final_save_dir = os.path.join(
                            final_save_dir,
                            validate.file_name(track.metadata.album_name))

                    file_path_name = os.path.join(
                        final_save_dir, '{0} - {1}.%(ext)s'.format(
                            validate.file_name(track.metadata.artist),
                            validate.file_name(track.metadata.name)))
                    file_path_name = file_path_name.replace('/', '_')
                    if (
                        os.path.exists(
                            file_path_name.replace('%(ext)s', 'mp3'))):
                        self.console.warning(
                            'Audio file already exists, skipping download')
                    else:
                        youtube_video = SearchSong(
                            track, self.download_low_score)
                        if (youtube_video.metadata):
                            download = DownloadVideo(
                                track, youtube_video, final_save_dir)
                            if (not download.SUCCESS):
                                self.console.warning(
                                    'Could not process track <R>ID_{0}'.format(
                                        track_id))
                                with open(dump_file + '.error', 'a') as stream:
                                    stream.write('{0} ## {1}\n'.format(
                                        line, download.EXCEPTION))

            with open(dump_file, 'w+') as stream:
                stream.write('\n'.join(content_lines))
        total_seconds = int(time.time() - self.process_start_time)
        self.console.info('Total process time == <LC>{0:>08}'.format(
            str(datetime.timedelta(seconds=total_seconds))))

    def identify_given_source(self, source_url):
        private_playlist = re.match(
            'http(s|)://open.spotify.com/user/(.*?)/playlist/(.*)', source_url)
        public_playlist = re.match(
            'http(s|)://open.spotify.com/playlist/(.*)', source_url)
        album = re.match('http(s|)://open.spotify.com/album/(.*)', source_url)

        if (private_playlist):
            username, playlist_id = private_playlist.group(
                2), private_playlist.group(3)
            LoadPlaylist(username, playlist_id, self.save_directory)

        elif (public_playlist):
            playlist_id = public_playlist.group(2)
            LoadPlaylist('', playlist_id, self.save_directory)

        elif (album):
            album_id = album.group(2)
            LoadAlbum(album_id, self.save_directory)

        else:
            self.console.error(
                'Could not identify source url: =={0}=='.format(source_url))


MainProcessor()
