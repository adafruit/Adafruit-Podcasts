import Playlist from '../lib/playlist';

export default class RaspberryPi extends Playlist {

  folder = 'raspberry_pi';
  url = 'https://www.youtube.com/playlist?list=PL1A011279DBD4EB7E';
  track = 'http://www.adafruit.com/?utm_source=podcast&utm_medium=videodescrip&utm_campaign=raspi';

  _child_info = {
    title: 'Raspberry Pi',
    description: 'Adafruit\'s goal to help the world learn & share electronics and computer programming continues with our line of products made just for the Raspberry Pi®. What is the Raspberry Pi® ? A low-cost ARM GNU/Linux box.',
    itunesSubtitle: 'Delicious Pi projects'
  };

  constructor(base_url, base_output) {
    super(base_url, base_output);
    Object.assign(this._info, this._child_info);
  }

}
