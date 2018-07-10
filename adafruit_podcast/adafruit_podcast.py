"""
AdafruitPodcast - build a collection of playlists from metadata, retrieve
them, and generate feeds.
"""

import glob
import json
import os
import pprint
import re
import subprocess
import lxml.builder
import lxml.etree
from feedgen.feed import FeedGenerator
from jinja2 import Environment, PackageLoader, select_autoescape

JINJA_ENV = Environment(
    loader=PackageLoader('adafruit_podcast', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

# YouTube download commands:
# Note: -s is for simulate, remove to get anything real done, add to avoid downloading videos
PODCAST_COMMAND = ['youtube-dl', '--ignore-errors', '--print-json',
                   '--write-thumbnail', '--no-overwrites', '--max-downloads', '1',
                   '--merge-output-format', 'mp4', '--restrict-filenames',
                   '--sleep-interval', '10', '--format', '134+140']

APPLETV_COMMAND = ['youtube-dl', '--ignore-errors', '--print-json',
                   '--write-thumbnail', '--no-overwrites', '--max-downloads', '1',
                   '--merge-output-format', 'mp4', '--restrict-filenames',
                   '--sleep-interval', '10', '--format', '137+140,136+140']

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

            self.playlists.append(AdafruitPlaylist(self, playlist_desc))

    def run_all_rss(self):
        """Fetch playlists, write podcast data."""
        for playlist in self.playlists:
            print(playlist.info['title'])
            playlist.fetch(PODCAST_COMMAND)
            playlist.write_rss()

    def run_all_appletv(self):
        """Fetch playlists, write podcast data."""
        for playlist in self.playlists:
            print(playlist.info['title'])
            playlist.fetch(APPLETV_COMMAND)
            playlist.write_appletv()
        self.write_toplevel_appletv()

    def write_toplevel_appletv(self):
        """Write a top-level appletv.js template for Apple TV."""
        em = lxml.builder.ElementMaker()

        # Build list of playlists:
        playlist_section = lxml.etree.Element('section')

        for playlist in self.playlists:
            playlist_url = self.base_url + playlist.folder + '/appletv.js'
            image_url = self.base_url + playlist.folder + '/appletv.jpg'
            playlist_section.append(
                em.lockup(
                    em.relatedContent(
                        em.lockup(
                            em.img(
                                src=image_url,
                                width="350",
                                height="350"
                            ),
                            em.title(playlist.info['title']),
                        )
                    ),
                    {'is': 'true', 'template': playlist_url}
                )
            )

        # Build overall TVML document:
        tvml = em.document(
            em.stackTemplate(
                em.identityBanner(
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
        js_template = JINJA_ENV.get_template('appletv.js')

        js_template.stream({'markup': markup}).dump(
            os.path.join(self.output_dir, 'appletv.js')
        )

    def toplevel_rss(self):
        print("toplevel_rss isn't implemented yet.")

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
        self.video_ids = []
        self.videos = []

    def output_template(self):
        """Return an output template for youtube-dl based on output dir."""
        return os.path.join(
            self.controller.output_dir,
            self.output_template_basedir,
            self.output_template_name
        )

    def fetch(self, command):
        """Fetch the playlist's videos and metadata."""
        source = self.url
        # If we have a list of source URLs, turn them into a string:
        if isinstance(source, list):
            source = source.join(' ')

        result = subprocess.run(
            command + ["--output", self.output_template(), source],
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

    def write_rss(self):
        """Write podcast feeds to files."""

        print("playlist self.info")
        pp.pprint(self.info)

        feed_url = self.controller.base_url + self.folder + '/podcast.xml'

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

        for vid in self.videos:
            vid_url = self.video_url(vid['_filename'])

            # Size of enclosed file in bytes:
            vid_size = os.path.getsize(vid['_filename'])

            print("vid:\n")
            pp.pprint(vid)

            entry = feedgen.add_entry()
            entry.id(vid_url)
            entry.title(vid['fulltitle'])
            for category in vid['categories']:
                entry.category(term=category)
            entry.description(vid['description'])
            entry.enclosure(vid_url, str(vid_size), 'video/mp4')

            entry.podcast.itunes_author(self.info['author'])
            entry.podcast.itunes_summary(vid['description'])
            entry.podcast.itunes_duration(vid['duration'])

        feedgen.rss_str(pretty=True)

        # Ensure output folder for this podcast exists:
        os.makedirs(os.path.join(self.controller.output_dir, self.folder), exist_ok=True)

        # Generate RSS file in output folder:
        feedgen.rss_file(os.path.join(self.controller.output_dir, self.folder, 'podcast.xml'))

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
            episodesSection.append(
                em.listItemLockup(
                    em.title(vid['fulltitle']),
                    em.relatedContent(
                        em.lockup(
                            em.img(),
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
                            src='https://s3.amazonaws.com/adafruit-apple-tv/images/FeaturedBannerMain.jpg',
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

        # Ensure output folder for this podcast exists:
        os.makedirs(os.path.join(self.controller.output_dir, self.folder), exist_ok=True)

        js_template = JINJA_ENV.get_template('appletv.js')

        js_template.stream({'markup': markup}).dump(
            os.path.join(self.controller.output_dir, self.folder, 'appletv.js')
        )
