# Copyright (C) 2016 Aratelia Limited - Juan A. Rubio
#
# This file is part of Tizonia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""@package tizyoutubeproxy
Simple YouTube proxy/wrapper.

Access YouTube to retrieve audio stream URLs and create a playback queue.

"""

from __future__ import unicode_literals

import pafy
import sys
import logging
import random
import unicodedata
from collections import namedtuple

# For use during debugging
# import pprint
# from traceback import print_exception

logging.captureWarnings(True)
# logging.getLogger().addHandler(logging.NullHandler())
logging.getLogger().setLevel(logging.DEBUG)

class _Colors:
    """A trivial class that defines various ANSI color codes.

    """
    BOLD = '\033[1m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def pretty_print(color, msg=""):
    """Print message with color.

    """
    print color + msg + _Colors.ENDC

def print_msg(msg=""):
    """Print a normal message.

    """
    pretty_print(_Colors.OKGREEN + msg + _Colors.ENDC)

def print_nfo(msg=""):
    """Print an info message.

    """
    pretty_print(_Colors.OKBLUE + msg + _Colors.ENDC)

def print_wrn(msg=""):
    """Print a warning message.

    """
    pretty_print(_Colors.WARNING + msg + _Colors.ENDC)

def print_err(msg=""):
    """Print an error message.

    """
    pretty_print(_Colors.FAIL + msg + _Colors.ENDC)

def exception_handler(exception_type, exception, traceback):
    """A simple exception handler that prints the excetion message.

    """

    print_err("[YouTube] (%s) : %s" % (exception_type.__name__, exception))
    del traceback # unused
    # print_exception(exception_type, exception, traceback)

sys.excepthook = exception_handler

class TizEnumeration(set):
    """A simple enumeration class.

    """
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

def to_ascii(msg):
    """Unicode to ascii helper.

    """

    return unicodedata.normalize('NFKD', unicode(msg)).encode('ASCII', 'ignore')

class tizyoutubeproxy(object):
    """A class that accesses YouTube, retrieves stream URLs and creates and manages
    a playback queue.

    """

    Stream = namedtuple("Stream", "title url filesize quality bitrate rawbitrate mediatype notes duration author viewcount description")

    def __init__(self):
        self.queue = list()
        self.queue_index = -1
        self.play_queue_order = list()
        self.play_modes = TizEnumeration(["NORMAL", "SHUFFLE"])
        self.current_play_mode = self.play_modes.NORMAL
        self.now_playing_stream = None

    def set_play_mode(self, mode):
        """ Set the playback mode.

        :param mode: current valid values are "NORMAL" and "SHUFFLE"

        """
        self.current_play_mode = getattr(self.play_modes, mode)
        self.__update_play_queue_order()

    def enqueue_audio_stream(self, arg):
        """Search YouTube for a stream and add all matches to the
        playback queue.

        :param arg: a search string

        """
        logging.info('enqueue_audio_stream : %s', arg)
        try:
            count = len(self.queue)

            video = pafy.new(arg)
            audio = video.getbestaudio(preftype="webm")
            if not audio:
                raise ValueError(str("No WebM audio stream for : %s" % arg))

            self.add_to_playback_queue(audio, video)

            self.__update_play_queue_order()

        except ValueError:
            raise ValueError(str("Video not found : %s" % arg))

    def enqueue_audio_playlist(self, arg):
        """Search YouTube for a playlist and add all matches to the
        playback queue.

        :param arg: a search string

        """
        logging.info('enqueue_audio_playlist : %s', arg)
        try:
            count = len(self.queue)

            playlist = pafy.get_playlist(arg)
            for video in playlist:
                audio = video.getbestaudio(preftype="webm")
                if audio:
                    self.add_to_playback_queue(audio, video)

            if count == len(self.queue):
                raise ValueError

            self.__update_play_queue_order()

        except ValueError:
            raise ValueError(str("Playlist not found : %s" % arg))

    def current_audio_stream_title(self):
        """ Retrieve the current stream's title.

        """
        logging.info("current_audio_stream_title")
        stream = self.now_playing_stream
        title = ''
        if stream:
            title = to_ascii(stream.title).encode("utf-8")
        return title

    def current_audio_stream_author(self):
        """ Retrieve the current stream's author.

        """
        logging.info("current_audio_stream_author")
        stream = self.now_playing_stream
        author = ''
        if stream:
            author = to_ascii(stream.author).encode("utf-8")
        return author

    def current_audio_stream_file_size(self):
        """ Retrieve the current stream's file size.

        """
        logging.info("current_audio_stream_file_size")
        stream = self.now_playing_stream
        size = 0
        if stream:
            size = stream.filesize
        return size

    def current_audio_stream_duration(self):
        """ Retrieve the current stream's duration.

        """
        logging.info("current_audio_stream_duration")
        stream = self.now_playing_stream
        duration = ''
        if stream:
            duration = to_ascii(stream.duration).encode("utf-8")
        return duration

    def current_audio_stream_bitrate(self):
        """ Retrieve the current stream's bitrate.

        """
        logging.info("current_audio_stream_bitrate")
        stream = self.now_playing_stream
        bitrate = ''
        if stream:
            bitrate = stream.bitrate
        return bitrate

    def current_audio_stream_view_count(self):
        """ Retrieve the current stream's view count.

        """
        logging.info("current_audio_stream_view_count")
        stream = self.now_playing_stream
        viewcount = 0
        if stream:
            viewcount = stream.viewcount
        return viewcount

    def current_audio_stream_description(self):
        """ Retrieve the current stream's description.

        """
        logging.info("current_audio_stream_description")
        stream = self.now_playing_stream
        description = ''
        if stream:
            description = to_ascii(stream.description).encode("utf-8")
        return description

    def clear_queue(self):
        """ Clears the playback queue.

        """
        self.queue = list()
        self.queue_index = -1

    def remove_current_url(self):
        """Remove the currently active url from the playback queue.

        """
        logging.info("remove_current_url")
        if len(self.queue) and self.queue_index:
            stream = self.queue[self.queue_index]
            print_nfo("[YouTube] [Stream] '{0}' removed." \
                      .format(to_ascii(stream.title).encode("utf-8")))
            del self.queue[self.queue_index]
            self.queue_index -= 1
            if self.queue_index < 0:
                self.queue_index = 0
            self.__update_play_queue_order()

    def next_url(self):
        """ Retrieve the url of the next stream in the playback queue.

        """
        logging.info("next_url")
        try:
            if len(self.queue):
                self.queue_index += 1
                if (self.queue_index < len(self.queue)) \
                   and (self.queue_index >= 0):
                    next_stream = self.queue[self.play_queue_order \
                                            [self.queue_index]]
                    return self.__retrieve_stream_url(next_stream).rstrip()
                else:
                    self.queue_index = -1
                    return self.next_url()
            else:
                return ''
        except (KeyError, AttributeError):
            del self.queue[self.queue_index]
            return self.next_url()

    def prev_url(self):
        """ Retrieve the url of the previous stream in the playback queue.

        """
        logging.info("prev_url")
        try:
            if len(self.queue):
                self.queue_index -= 1
                if (self.queue_index < len(self.queue)) \
                   and (self.queue_index >= 0):
                    prev_stream = self.queue[self.play_queue_order \
                                            [self.queue_index]]
                    return self.__retrieve_stream_url(prev_stream).rstrip()
                else:
                    self.queue_index = len(self.queue)
                    return self.prev_url()
            else:
                return ''
        except (KeyError, AttributeError):
            del self.queue[self.queue_index]
            return self.prev_url()

    def __update_play_queue_order(self):
        """ Update the queue playback order.

        A sequential order is applied if the current play mode is "NORMAL" or a
        random order if current play mode is "SHUFFLE"

        """
        total_streams = len(self.queue)
        if total_streams:
            if not len(self.play_queue_order):
                # Create a sequential play order, if empty
                self.play_queue_order = range(total_streams)
            if self.current_play_mode == self.play_modes.SHUFFLE:
                random.shuffle(self.play_queue_order)
            print_nfo("[YouTube] [Streams in queue] '{0}'." \
                      .format(total_streams))

    def __retrieve_stream_url(self, stream):
        """ Retrieve a stream url

        """
        try:
            self.now_playing_stream = stream
            logging.info("__retrieve_stream_url url : {0}".format(stream.url))
            logging.info("__retrieve_stream_url bitrate   : {0}".format(stream.bitrate))
            logging.info("__retrieve_stream_url mediatype: {0}".format(stream.mediatype))
            return stream.url.encode("utf-8")
        except AttributeError:
            logging.info("Could not retrieve the stream url!")
            raise

    def add_to_playback_queue(self, audio, video):

        # pprint.pprint(audio.title)
        # pprint.pprint(audio.url)
        # pprint.pprint(audio.get_filesize())
        # pprint.pprint(audio.quality)
        # pprint.pprint(audio.bitrate)
        # pprint.pprint(audio.rawbitrate)
        # pprint.pprint(audio.mediatype)
        # pprint.pprint(audio.notes)
        # pprint.pprint(video.duration)
        # pprint.pprint(video.author)
        # pprint.pprint(video.viewcount)
        # pprint.pprint(video.description)

        print_nfo("[YouTube] [Stream] '{0}' [{1}]." \
                  .format(to_ascii(audio.title).encode("utf-8"), \
                          to_ascii(audio.mediatype)))
        self.queue.append(
            tizyoutubeproxy.Stream(audio.title, \
                                   audio.url, \
                                   audio.get_filesize(), \
                                   audio.quality, \
                                   audio.bitrate, \
                                   audio.rawbitrate, \
                                   audio.mediatype,
                                   audio.notes,
                                   video.duration,
                                   video.author,
                                   video.viewcount,
                                   video.description))

if __name__ == "__main__":
    tizyoutubeproxy()
