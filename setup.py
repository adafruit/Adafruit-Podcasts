from setuptools import setup

setup(name='adafruit_podcast',
      version='0.0.1',
      description='Generate podcast feeds from YouTube downloads',
      url='http://github.com/adafruit/adafruit_podcast',
      author='Brennen Bearnes',
      author_email='brennen@adafruit.com',
      license='MIT',
      packages=['adafruit_podcast'],
      install_requires=[
          'dominate',
          'docopt',
          'feedgen',
          'pytz',
          'youtube-dl'
      ],
      scripts=['bin/podcast'],
      zip_safe=False)
