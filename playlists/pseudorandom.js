import Playlist from '../lib/playlist';

export default class PseudoRandom extends Playlist {

  folder = 'pseudorandom';
  url = 'https://www.youtube.com/playlist?list=PLjF7R1fz_OOWClkhJ7WcBQdR0QnKBUAj5';
  track = 'http://www.adafruit.com/?utm_source=podcast&utm_medium=videodescrip&utm_campaign=pseudorandom';

  _child_info = {
    title: 'pseudorandom',
    description: 'apples.',
    itunesSubtitle: 'apples.'
  };

  constructor(base_url, base_output) {
    super(base_url, base_output);
    Object.assign(this._info, this._child_info);
  }

  descriptionFormat(description) {
    return description + this.trackLink();
  }

}
