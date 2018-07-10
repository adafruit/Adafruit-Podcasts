import Playlist from '../lib/playlist';

export default class NewProducts extends Playlist {

  folder = 'new_products';
  url = 'https://www.youtube.com/playlist?list=PL028933C9CA644CFB';
  track = 'http://www.adafruit.com/?utm_source=podcast&utm_medium=videodescrip&utm_campaign=newproducts';

  _child_info = {
    title: 'New Products',
    description: 'Each week Ladyada shows the newest great electronics at Adafruit!',
    itunesSubtitle: 'Each week Ladyada shows the newest great electronics at Adafruit!'
  };

  constructor(base_url, base_output) {
    super(base_url, base_output);
    Object.assign(this._info, this._child_info);
  }

  descriptionFormat(description) {
    return description + this.trackLink();
  }

}
