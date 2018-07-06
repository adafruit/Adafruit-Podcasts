import re
import os
import pprint
import subprocess
import json
from feedgen.feed import FeedGenerator

class AdafruitPlaylist:
    """AdafruitPlayist - model an individual playlist."""

    # YouTube download commands:
    # XXX: -s is for simulate, remove to get anything real done, add to avoid
    #      downloading videos
    podcast_command = ['youtube-dl', '--ignore-errors', '--print-json',
                       '--write-thumbnail', '--no-overwrites', '--max-downloads', '1',
                       '--merge-output-format', 'mp4', '--restrict-filenames',
                       '--sleep-interval', '10', '--format', '134+140']

    appletv_command = ['youtube-dl', '--ignore-errors', '--print-json',
                       '--write-thumbnail', '--no-overwrites', '--max-downloads', '1',
                       '--merge-output-format', 'mp4', '--restrict-filenames',
                       '--sleep-interval', '10', '--format', '137+140,136+140']

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

    def fetch(self):
        """Fetch the playlist's videos and metadata."""
        source = self.url
        # If we have a list of source URLs, turn them into a string:
        if isinstance(source, list):
            source = source.join(' ')

        result = subprocess.run(
            self.podcast_command + ["--output", self.output_template(), source],
            stdout=subprocess.PIPE,
            universal_newlines=True
        )
        vids = result.stdout.split("\n")

        for vid in vids:
            if vid:
                vid_data = json.loads(vid)
            else:
                # print("Empty JSON field... ?")
                continue

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

    def write(self):
        """Write podcast feeds to files."""

        pp = pprint.PrettyPrinter(indent=4)
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
            vid_url = self.controller.base_url + \
                self.output_template_basedir + \
                '/' + \
                os.path.basename(vid['_filename'])

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

# async savePodcast(playlist, videos) {
#
#   const podcast = new Podcast(playlist.info());
#
#   await this.mkdir(playlist.outputFolder());
#
#   videos.forEach((video) => {
#
#     this.logger.info(`adding video ${video.fulltitle}`);
#
#     if(video.width != 640)
#       return;
#
#     podcast.item({
#       title: video.fulltitle,
#       description: playlist.descriptionFormat(video.description),
#       enclosure: {
#         url: `${playlist.base_url}/media/${video.id}_${video.height}.mp4`,
#         file: path.normalize(`${playlist.path}/media/${video.id}_${video.height}.mp4`)
#       },
#       image_url: `${playlist.outputURL()}/image.jpg`,
#       categories: video.categories,
#       date: video.upload_date.replace(/(\d{4})(\d{2})(\d{2})/g, '$1/$2/$3'),
#       itunesAuthor: 'Adafruit Industries',
#       itunesExplicit: false,
#       itunesSubtitle: video.fulltitle,
#       itunesDuration: video.duration,
#       itunesKeywords: video.tags
#     });
#
#   });
# await this.writeFile(`${playlist.outputFolder()}/podcast.xml`, podcast.xml());
