from feedgen.feed import FeedGenerator
import re
import subprocess
import json

class AdafruitPlaylist:

    # YouTube download commands:
    # XXX: -s is for simulate, remove to get anything real done
    podcast_command = ['youtube-dl', '-s', '--ignore-errors', '--print-json',
                       '--write-thumbnail', '--no-overwrites', '--max-downloads', '10',
                       '--merge-output-format', 'mp4', '--restrict-filenames',
                       '--sleep-interval', '10', '--format', '134+140']

    appletv_command = ['youtube-dl', '-s', '--ignore-errors', '--print-json',
                       '--write-thumbnail', '--no-overwrites', '--max-downloads', '10',
                       '--merge-output-format', 'mp4', '--restrict-filenames',
                       '--sleep-interval', '10', '--format', '137+140,136+140']

    output_template = 'media/%(id)s_%(height)s.%(ext)s'

    def __init__(self, data):
        self.data = data
        self.video_ids = []
        self.videos = []

    def fetch(self):
        source = self.data['url']
        # If we have a list of source URLs, turn them into a string:
        if (isinstance(source, list)):
            source = source.join(' ')

        result = subprocess.run(
            self.podcast_command + ["--output", self.output_template, source],
            stdout=subprocess.PIPE,
            universal_newlines=True
        )
        vids = result.stdout.split("\n")

        for vid in vids:
            if (vid):
                vid_data = json.loads(vid)
            else:
                # print("Empty JSON field... ?")
                continue

            # XXX: print(vid_data)

            # Check some conditions that should prevent a video from being included:
            if (not vid_data):
                continue
            if (vid_data['is_live']):
                continue
            if (re.match('theta', vid_data['title'], re.I)):
                continue
            if (re.match('hugvr', vid_data['title'], re.I)):
                continue
            if (re.match('360', vid_data['title'])):
                continue

            # To make sure we don't already have this id, add to id list:
            if (not (vid_data['id'] in self.video_ids)):
                self.video_ids.append(vid_data['id'])

            self.videos.append(vid_data)

    def write(self):
        print("i will do output here!")
        fg = FeedGenerator()
        fg.load_extension('podcast')

        fg.podcast.itunes_category('Technology', 'Podcasting')

        fe = fg.add_entry()
        fe.id('http://lernfunk.de/media/654321/1/file.mp3')
        fe.title('The First Episode')
        fe.description('Enjoy our first episode.')
        fe.enclosure('http://lernfunk.de/media/654321/1/file.mp3', 0, 'audio/mpeg')

        fg.rss_str(pretty=True)
        fg.rss_file('podcast.xml')

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
