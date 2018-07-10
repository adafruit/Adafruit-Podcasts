import Playlist from '../lib/playlist';

export default class ShowAndTell extends Playlist {

  folder = 'show_and_tell';
  url = 'https://www.youtube.com/playlist?list=PL7E1FAA9E63A32FDC';
  track = 'http://www.adafruit.com/?utm_source=podcast&utm_medium=videodescrip&utm_campaign=aae';

  _child_info = {
    title: 'Show and Tell',
    description: 'Electronics show and tell with G+ On-Air hangouts every Wednesday at 7:30pm ET. Want to show a project on an upcoming show and tell? Leave a comment on the show and tell announcement on Adafruit\'s G+ page: http://google.com/+adafruit',
    itunesSubtitle: 'Electronics show and tell with G+ On-Air hangouts every Wednesday at 7:30pm ET.'
  };

  constructor(base_url, base_output) {
    super(base_url, base_output);
    Object.assign(this._info, this._child_info);
  }

  descriptionFormat(description) {
    return description + this.trackLink();
  }

}
