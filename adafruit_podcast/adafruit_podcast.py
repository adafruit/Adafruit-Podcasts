from dominate.tags import *
import dominate
import glob
import json
import os
import re
import subprocess
import traceback
from adafruit_podcast import adafruit_playlist

class AdafruitPodcast:
    """A maker of podcast feeds"""

    def __init__(self):
        # Set some defaults:
        self.playlist_dir = './playlists'
        self.output_dir = '.'
        self.base_url = ''
        self.playlists = []

    def configure(self):
        # Get base info for all podcasts:
        with open(os.path.join(self.playlist_dir, '_info.json')) as info_file:
            self.base_info = json.load(info_file)

        # Get individual playlist info from *.playlist.json files in the playlist dir:
        for playlist in glob.glob(os.path.join(self.playlist_dir, '*.playlist.json')):
            playlist_info = json.load(open(playlist))

            # Merge base info into playlist info:
            for key, value in self.base_info:
                if not key in playlist_info['_info']:
                    playlist_info['_info'][key] = value

            self.playlists.append(adafruit_playlist.AdafruitPlaylist(playlist_info))

    def run(self):
        for playlist in self.playlists:
            print(playlist.data['_info']['title'])
            playlist.fetch()
            print(playlist.video_ids)
            playlist.write()
