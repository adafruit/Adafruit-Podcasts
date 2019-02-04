"""
AdafruitPodcast - build a collection of playlists from metadata, retrieve
them, and generate feeds.
"""

import glob
import json
import os
import pprint
import pytz
import re
import subprocess
import datetime
import lxml.builder
import lxml.etree
from feedgen.feed import FeedGenerator

# YouTube download commands:
# Note: -s is for simulate, remove to get anything real done, add to avoid downloading videos
PODCAST_COMMAND = ['youtube-dl', '--ignore-errors', '--print-json',
                   '--write-thumbnail', '--no-overwrites',
                   '--merge-output-format', 'mp4', '--restrict-filenames',
                   '--sleep-interval', '10', '--format', '134+140']

APPLETV_COMMAND = ['youtube-dl', '--ignore-errors', '--print-json',
                   '--write-thumbnail', '--no-overwrites',
                   '--merge-output-format', 'mp4', '--restrict-filenames',
                   '--sleep-interval', '10', '--format', '137+140,136+140']

AUDIOPODCAST_COMMAND = ['youtube-dl', '--ignore-errors', '--print-json',
                        '--write-thumbnail', '--no-overwrites', '--keep-video',
                        '--merge-output-format', 'mp4',
                        '--no-post-overwrites', '--extract-audio',
                        '--audio-format', 'mp3', '--restrict-filenames',
                        '--sleep-interval', '10', '--format', '140']

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

        print("podcast self.base_info\n", flush=True)
        pp.pprint(self.base_info)

        # Get individual playlist info from *.playlist.json files in the playlist dir:
        for playlist in glob.glob(os.path.join(self.playlist_dir, '*.playlist.json')):
            playlist_desc = json.load(open(playlist, encoding="utf-8"))

            # Merge base info into playlist info:
            for key in self.base_info:
                if not key in playlist_desc['_info']:
                    playlist_desc['_info'][key] = self.base_info[key]

            self.playlists.append(AdafruitPlaylist(self, playlist_desc))

        # Order playlists by title string:
        self.playlists = sorted(self.playlists, key=lambda playlist: playlist.info['title'])

    def run_all_rss(self):
        """Fetch playlists, write podcast data."""
        for playlist in self.playlists:
            if playlist.include_audio_version:
                print('(AUDIO EDITION) ' + playlist.info['title'], flush=True)
                playlist.fetch(AUDIOPODCAST_COMMAND, 1)
                playlist.write_rss(audio=True)

        for playlist in self.playlists:
            if not playlist.include_audio_version:
                print(playlist.info['title'], flush=True)
                playlist.fetch(PODCAST_COMMAND, 1)
                playlist.write_rss()

    def run_all_appletv(self):
        """Fetch playlists, write podcast data."""
        for playlist in self.playlists:
            if playlist.include_in_appletv:
                print('writing ' + playlist.info['title'] + ' appletv', flush=True)
                playlist.fetch(APPLETV_COMMAND, 2)
                playlist.write_appletv()
            else:
                print(playlist.info['title'] + ' excluded from appletv', flush=True)
        self.write_toplevel_appletv()

    def write_toplevel_appletv(self):
        """Write a top-level appletv.js template for Apple TV."""
        em = lxml.builder.ElementMaker()

        # Build list of playlists:
        playlist_section = lxml.etree.Element('section')

        for playlist in self.playlists:
            if not playlist.include_in_appletv:
                continue

            playlist_url = self.base_url + playlist.folder + '/appletv.js'
            image_url = self.base_url + playlist.folder + '/appletv.jpg'
            playlist_section.append(
                em.lockup(
                    em.img(
                        src=image_url,
                        width="350",
                        height="350"
                    ),
                    em.title(
                        # re.sub("'", '&#x27;s', playlist.info['title'])
                        playlist.info['title']
                    ),
                    {'is': 'true', 'template': playlist_url}
                )
            )

        # Build overall TVML document:
        tvml = em.document(
            em.stackTemplate(
                em.banner(
                    em.background(
                        em.img(
                            src='https://s3.amazonaws.com/adafruit-apple-tv/images/FeaturedBannerMain.jpg',
                            width='1920',
                            height='360'
                        )
                    )
                ),
                em.collectionList(
                    em.grid(
                        playlist_section
                    )
                ),
                {'class': 'lightBackgroundColor'}
            ),
        )
        # markup = lxml.etree.tostring(tvml, pretty_print=True)
        markup = lxml.etree.tostring(tvml, encoding='unicode')
        markup = 'var Template = function() { return `<?xml version="1.0" encoding="UTF-8" ?>' + markup + '`;};'
        with open(os.path.join(self.output_dir, 'appletv.js'), 'w') as f:
            f.write(markup)

    def toplevel_rss(self):
        """Print a top-level RSS feed pointing at other feeds for monitoring purposes."""
        print("toplevel_rss isn't implemented yet.", flush=True)

# pylint: disable=too-many-instance-attributes
class AdafruitPlaylist:
    """AdafruitPlayist - model an individual playlist."""

    output_template_basedir = 'media'
    output_template_name = '%(id)s_%(height)s.%(ext)s'


    def __init__(self, controller, description):
        self.controller = controller
        self.info = description['_info']
        self.url = description['url']
        self.track = description['track']
        self.folder = description['folder']

        self.max_downloads = 0
        if 'max_downloads' in description:
            self.max_downloads = description['max_downloads']

        self.include_in_appletv = True
        if 'include_in_appletv' in description:
            self.include_in_appletv = description['include_in_appletv']

        self.include_audio_version = False
        if 'include_audio_version' in description:
            self.include_audio_version = description['include_audio_version']

        self.video_ids = []
        self.videos = []

    def output_template(self):
        """Return an output template for youtube-dl based on output dir."""
        return os.path.join(
            self.controller.output_dir,
            self.output_template_basedir,
            self.output_template_name
        )

    def fetch(self, command, fetch_multiplier):
        """Fetch the playlist's videos and metadata."""
        source = self.url
        # If we have a list of source URLs, turn them into a string:
        if isinstance(source, list):
            source = ' '.join(source)

        if self.max_downloads > 0:
            max_dl = str(fetch_multiplier * self.max_downloads)
            command = command + ['--max-downloads', max_dl]

        fetch_command = command + ['--output', self.output_template(), source]
        pp.pprint(fetch_command)

        result = subprocess.run(
            fetch_command,
            stdout=subprocess.PIPE,
            universal_newlines=True
        )
        vids = result.stdout.split("\n")

        for vid in vids:
            if vid:
                vid_data = json.loads(vid)

            # Check some conditions that should prevent a video from being included:
            if not vid_data:
                continue
            if vid_data['is_live']:
                continue
            if re.match('theta', vid_data['title'], re.I):
                continue
            if re.match('hugvr', vid_data['title'], re.I):
                continue
            if re.match('360', vid_data['title']):
                continue

            # To make sure we don't already have this id, add to id list:
            if not vid_data['id'] in self.video_ids:
                self.video_ids.append(vid_data['id'])
                self.videos.append(vid_data)

    def video_url(self, video_filename):
        """Get a URL for the given filename."""
        return self.controller.base_url + \
            self.output_template_basedir + \
            '/' + \
            os.path.basename(video_filename)

    def video_image_url(self, video_filename):
        """Get a thumbnail path for the given filename."""
        return self.controller.base_url + \
            self.output_template_basedir + \
            '/' + \
            re.sub('mp[34]$', 'jpg', os.path.basename(video_filename))

    def write_rss(self, audio=False):
        """Write podcast feeds to files."""

        print("playlist self.info", flush=True)
        pp.pprint(self.info)

        prefix = "audio-" if audio else ""

        feed_url = self.controller.base_url + self.folder + '/' + prefix + 'podcast.xml'

        feedgen = FeedGenerator()
        feedgen.load_extension('podcast')

        feedgen.generator('Adafruit-Podcast')
        feedgen.id(feed_url)
        feedgen.title(self.info['title'])
        feedgen.subtitle(self.info['itunesSubtitle'])
        feedgen.author({'name': self.info['author']})
        for category in self.info['categories']:
            feedgen.category(term=category)
        feedgen.webMaster(self.info['webMaster'])
        feedgen.managingEditor(self.info['managingEditor'])
        feedgen.link(href=feed_url, rel='self')

        # Link to the original YouTube playlist as an alternate:
        if isinstance(self.url, list):
            for url in self.url:
                feedgen.link(href=url, rel='alternate')
        else:
            feedgen.link(href=self.url, rel='alternate')
        feedgen.language('en')

        # feedgen.logo('http://ex.com/logo.jpg')

        # pylint: disable=no-member
        feedgen.podcast.itunes_category(self.info['itunesCategory']['text'])
        feedgen.podcast.itunes_subtitle(self.info['itunesSubtitle'])
        feedgen.podcast.itunes_summary(self.info['description'])
        feedgen.podcast.itunes_owner(
            email=self.info['itunesOwner']['email'],
            name=self.info['itunesOwner']['name']
        )
        feedgen.podcast.itunes_author(self.info['itunesOwner']['name'])
        feedgen.podcast.itunes_image(self.controller.base_url + self.folder + '/image.jpg')

        for vid in self.videos:
            print("vid:\n", flush=True)
            pp.pprint(vid)
            print("\n", flush=True)

            vid_filename = vid['_filename'].split('.')[0] + (".mp3" if audio else ".mp4")

            vid_url = self.video_url(vid_filename)

            # Size of enclosed file in bytes:
            vid_size = os.path.getsize(vid_filename)

            # Date of upload (from the youtube-dl JSON data)
            vid_date = datetime.datetime.strptime(vid['upload_date'], '%Y%m%d').replace(tzinfo=pytz.timezone('US/Eastern'))

            entry = feedgen.add_entry()
            entry.id(vid_url)
            entry.title(vid['fulltitle'])
            entry.published(vid_date)
            for category in vid['categories']:
                entry.category(term=category)
            entry.description(vid['description'])
            entry.enclosure(vid_url, str(vid_size), ('audio/mp3' if audio else 'video/mp4'))
            entry.podcast.itunes_image(self.controller.base_url + self.folder + '/image.jpg')

            entry.podcast.itunes_author(self.info['author'])
            entry.podcast.itunes_summary(vid['description'])
            entry.podcast.itunes_duration(vid['duration'])

        feedgen.rss_str(pretty=True)

        # Ensure output folder for this podcast exists:
        os.makedirs(os.path.join(self.controller.output_dir, self.folder), exist_ok=True)

        # Generate RSS file in output folder:
        feedgen.rss_file(os.path.join(self.controller.output_dir, self.folder, prefix + 'podcast.xml'))

    def write_appletv(self):
        """Write appletv.js files."""

        pp.pprint(self.videos)
        pp.pprint(self.video_ids)

        em = lxml.builder.ElementMaker()

        # Build list of videos:
        episodesSection = lxml.etree.Element('section')
        episodesSection.append(em.header(em.title('Episodes')))

        for vid in self.videos:
            vid_url = self.video_url(vid['_filename'])
            vid_image_url = self.video_image_url(vid['_filename'])
            episodesSection.append(
                em.listItemLockup(
                    em.title(vid['fulltitle']),
                    em.relatedContent(
                        em.lockup(
                            em.img(
                                src=vid_image_url,
                                width="857",
                                height="482"
                            ),
                            em.title(vid['fulltitle']),
                            em.description(vid['description'])
                        )
                    ),
                    {'is': "true", 'videoURL': vid_url}
                )
            )

        # Build overall TVML document:
        tvml = em.document(
            em.listTemplate(
                em.banner(
                    em.background(
                        em.img(
                            src='https://s3.amazonaws.com/adafruit-apple-tv/images/EpisodeBanner.jpg',
                            width='1920',
                            height='360'
                        )
                    )
                ),
                em.list(
                    em.header(em.title(self.info['title'])),
                    episodesSection
                )
            ),
        )
        # markup = lxml.etree.tostring(tvml, pretty_print=True)
        markup = lxml.etree.tostring(tvml, encoding='unicode')
        markup = 'var Template = function() { return `<?xml version="1.0" encoding="UTF-8" ?>' + markup + '`;};'

        # Ensure output folder for this podcast exists:
        os.makedirs(os.path.join(self.controller.output_dir, self.folder), exist_ok=True)

        with open(os.path.join(self.controller.output_dir, self.folder, 'appletv.js'), 'w') as f:
            f.write(markup)
