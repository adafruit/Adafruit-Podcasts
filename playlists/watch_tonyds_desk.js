import Playlist from '../lib/playlist';

export default class WatchTonyDsDesk extends Playlist {

  folder = 'tonyds_desk';
  url = 'https://www.youtube.com/playlist?list=PLjF7R1fz_OOUmgpmVDTyX85Z8OO142eia';
  track = 'http://www.adafruit.com/?utm_source=podcast&utm_medium=videodescrip&utm_campaign=tonyds_desk';

  _child_info = {
    title: 'Watch Tony D\'s Desk',
    description: 'Archive of live streams from Tony DiCola covering topics from Arduino to Raspberry Pi and more. Watch live on http://twitch.tv/adafruit!',
    itunesSubtitle: 'Archive of live streams from Tony DiCola covering topics from Arduino to Raspberry Pi and more. Watch live on http://twitch.tv/adafruit!'
  };

  constructor(base_url, base_output) {
    super(base_url, base_output);
    Object.assign(this._info, this._child_info);
  }

  descriptionFormat(description) {
    return description + this.trackLink();
  }

}
