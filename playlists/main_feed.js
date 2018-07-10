import Playlist from '../lib/playlist';

export default class MainFeed extends Playlist {

  folder = 'main_feed';
  url = 'https://www.youtube.com/channel/UCpOlOeQjj7EsVnDh3zuCgsA';
  track = 'http://www.adafruit.com/?utm_source=podcast&utm_medium=videodescrip&utm_campaign=allvideos';

  _child_info = {
    title: 'Adafruit Industries',
    description: 'Welcome to Adafruit! We bring do-it-yourself electronics to life here at our factory in New York City. Our videos showcase hundreds of unique open source projects you can build at home.',
    itunesSubtitle: 'DIY electronics projects & much more'
  };

  constructor(base_url, base_output) {
    super(base_url, base_output);
    Object.assign(this._info, this._child_info);
  }

}
