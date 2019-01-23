# SpotifyDownloader
A python script to download spotify playlists and albums from youtube.

## About
This code downloads tracks in the best quality possible [mp3/320kpbs] and uses an algorithm to compare videos and track metadata to choose the most similar to download.

## Requirements
All modules that are needed by this project are found in the `requirements.txt` file. The code requires **ffmpeg** to convert the .webm and .m4a files to .mp3, you can download ffmpeg [here](http://ffmpeg.org/download.html).

`colorama` is used to color the command prompt.

`isodate` is used to format youtube timestamps (ISO 8601).

`mutagen` has an powerful ID3 tags editor, it is used to add track metadata (cover art, track number, ...) to mp3 files.

`youtube_dl` is used to download youtube videos.

`spotipy` is a spotify api python wrapper.

`requests` is used to quickly make youtube api calls.

`python-dotenv` reads the api keys in the project .env file

**To properly use this code, make sure to supply valid youtube api and spotify api credentials in the .env file**

## Usage
Open `init.py` on cmd suplying the needed arguments.

`init.py --source https://open.spotify.com/..`creates a dump file with the album/playlist tracks.

`init.py --download file_path.txt` downloads the tracks in the dump file.

`init.py --lookup (album:|track:|playlist:)query` searchs the query on spotify and generates a dump file.


You can also provide these arguments in the command line:

`init.py --folder path --source ...` changes the files destination path.

`init.py --nofilename` removes the dump file name from the destination path.

`init.py --includealbumname` include the track album name in the destination path.

### Example
`init.py -s "https://open.spotify.com/album/0cjMGmZKB9ZWzcb0VcASpf"` Will create a dump file with the album name in the origin folder.
`init.py -d "After the Disco.txt" -f "downloads/Favorites" -nf` will download the tracks found in `After the Disco.txt` to folder `downloads/Favorites`, the `-nf` param makes so the directory `/After the Disco` is not included in the save path.
***
