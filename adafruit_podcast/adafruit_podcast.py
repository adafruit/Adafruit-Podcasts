"""
AdafruitPodcast - build a collection of playlists from metadata, retrieve
them, and generate feeds.
"""

import glob
import json
import os
import pprint
from adafruit_podcast import adafruit_playlist

pp = pprint.PrettyPrinter(indent=4)

class AdafruitPodcast:
    """A maker of podcast feeds"""

    def __init__(self):
        # Set some defaults:
        self.playlist_dir = './playlists'
        self.output_dir = '.'
        self.base_url = ''
        self.base_info = {}
        self.playlists = []

    def configure(self):
        """Collect playlists from configuration data in playlist_dir."""
        # Get base info for all podcasts:
        with open(os.path.join(self.playlist_dir, '_info.json')) as info_file:
            self.base_info = json.load(info_file)

        print("podcast self.base_info\n")
        pp.pprint(self.base_info)

        # Get individual playlist info from *.playlist.json files in the playlist dir:
        for playlist in glob.glob(os.path.join(self.playlist_dir, '*.playlist.json')):
            playlist_desc = json.load(open(playlist))

            # Merge base info into playlist info:
            for key in self.base_info:
                if not key in playlist_desc['_info']:
                    playlist_desc['_info'][key] = self.base_info[key]

            self.playlists.append(adafruit_playlist.AdafruitPlaylist(self, playlist_desc))

    def run(self):
        """Fetch playlists, write podcast data."""
        for playlist in self.playlists:
            print(playlist.info['title'])
            playlist.fetch()
            playlist.write()
