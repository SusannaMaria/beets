"""Calculate acoustic information and submit to AcousticBrainz.
"""

from __future__ import division, absolute_import, print_function

import hashlib
import json
import os
import subprocess
import tempfile

import distutils
import requests

from beets import plugins
from beets import util
from beets import ui


class ABSubmitError(Exception):
    """Raised when failing to analyse file with extractor."""


def call(args):
    """Execute the command and return its output.

    Raise a AnalysisABSubmitError on failure.
    """
    try:
        return util.command_output(args)
    except subprocess.CalledProcessError as e:
        raise ABSubmitError(
            u'{0} exited with status {1}'.format(args[0], e.returncode)
        )


class AcousticBrainzSubmitPlugin(plugins.BeetsPlugin):

    def __init__(self):
        super(AcousticBrainzSubmitPlugin, self).__init__()

        self.config.add({'extractor': u'','force': False})
        self.extractor = self.config['extractor'].as_str()
        if self.extractor:
            self.extractor = util.normpath(self.extractor)
            # Expicit path to extractor
            if not os.path.isfile(self.extractor):
                raise ui.UserError(
                    u'Extractor command does not exist: {0}.'.
                    format(self.extractor)
                )
        else:
            # Implicit path to extractor, search for it in path
            # TODO how to check for on Windows?
            self.extractor = 'streaming_extractor_music'
            try:
                call([self.extractor])
            except OSError:
                raise ui.UserError(
                    u'No extractor command found: please install the '
                    u'extractor binary from http://acousticbrainz.org/download'
                )
            except ABSubmitError:
                # Extractor found, will exit with an error if not called with
                # the correct amount of arguments.
                pass
            # Get the executable location on the system,
            # needed to calculate the sha1 hash.
            self.extractor = distutils.spawn.find_executable(self.extractor)

        # Calculate extractor hash.
        self.extractor_sha = hashlib.sha1()
        with open(self.extractor, 'rb') as extractor:
            self.extractor_sha.update(extractor.read())
        self.extractor_sha = self.extractor_sha.hexdigest()

    supported_formats = {'mp3', 'ogg', 'oga', 'flac', 'mp4', 'm4a', 'm4r',
                         'm4b', 'm4p', 'aac', 'wma', 'asf', 'mpc', 'wv',
                         'spx', 'tta', '3g2', 'aif', 'aiff', 'ape'}

    base_url = 'https://acousticbrainz.org/api/v1/{mbid}/low-level'

    def commands(self):
        cmd = ui.Subcommand(
            'absubmit',
            help=u'calculate and submit AcousticBrainz analysis'
        )

        cmd.parser.add_option(
            u'-f', u'--force', dest='force_refetch',
            action='store_true', default=False,
            help=u're-analyse data when already present'
        )

        cmd.func = self.command
        return [cmd]

    def command(self, lib, opts, args):
        # Get items from arguments
        items = lib.items(ui.decargs(args))
        for item in items:
            analysis = self._get_analysis(item,opts.force_refetch or self.config['force'])
            if analysis:
                self._submit_data(item, analysis)

    def _get_analysis(self, item,force):

        if not force:
            mood_str = item.get('mood_acoustic', u'')
            if mood_str:
                self._log.info(u'Already acousticbrainz tags available for {} ', item)
                return None
                
        mbid = item['mb_trackid']
        # If file has no mbid skip it.
        if not mbid:
            self._log.info(u'Not analysing {}, missing '
                           u'musicbrainz track id.', item)
            return None
        # If file format is not supported skip it.
        if item['format'].lower() not in self.supported_formats:
            self._log.info(u'Not analysing {}, file not in '
                           u'supported format.', item)
            return None

        # Temporary file to save extractor output to, extractor only works
        # if an output file is given. Here we use a temporary file to copy
        # the data into a python object and then remove the file from the
        # system.
        tmp_file, filename = tempfile.mkstemp(suffix='.json')
        try:
            # Close the file, so the extractor can overwrite it.
            try:
                call([self.extractor, util.syspath(item.path), filename])
            except ABSubmitError as e:
                self._log.error(
                    u'Failed to analyse {item} for AcousticBrainz: {error}',
                    item=item, error=e
                )
                return None
            with open(filename) as tmp_file:
                analysis = json.loads(tmp_file.read())
            # Add the hash to the output.
            analysis['metadata']['version']['essentia_build_sha'] = \
                self.extractor_sha
            return analysis
        finally:
            try:
                os.remove(filename)
            except OSError as e:
                # errno 2 means file does not exist, just ignore this error.
                if e.errno != 2:
                    raise

    def _submit_data(self, item, data):
        mbid = item['mb_trackid']
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.base_url.format(mbid=mbid),
                                 json=data, headers=headers)
        # Test that request was successful and raise an error on failure.
        if response.status_code != 200:
            try:
                message = response.json()['message']
            except (ValueError, KeyError) as e:
                message = u'unable to get error message: {}'.format(e)
            self._log.error(
                u'Failed to submit AcousticBrainz analysis of {item}: '
                u'{message}).', item=item, message=message
            )
        else:
            self._log.debug(u'Successfully submitted AcousticBrainz analysis '
                            u'for {}.', item)
