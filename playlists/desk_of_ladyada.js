import Playlist from '../lib/playlist';

export default class DeskOfLadyada extends Playlist {

  folder = 'desk_of_ladyada';
  url = 'https://www.youtube.com/playlist?list=PLjF7R1fz_OOXUtaFu7-_D1UCugC8OecKv';
  track = 'http://www.adafruit.com/?utm_source=podcast&utm_medium=videodescrip&utm_campaign=deskofladyada';

  _child_info = {
    title: 'Live from the Desk of Ladyada',
    description: 'Join Ladyada streaming live for circuit board layout design, code writing, surface mount soldering and more fresh engineering and even some gaming! If Ladyada’s working on it, you’ll find it here first.',
    itunesSubtitle: 'Join Ladyada streaming live!'
  };

  constructor(base_url, base_output) {
    super(base_url, base_output);
    Object.assign(this._info, this._child_info);
  }

}
