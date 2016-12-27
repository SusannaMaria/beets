AcousticBrainz Submit Plugin
============================

The `absubmit` plugin uses the `streaming_extractor_music`_ program to analyse an audio file and calculate different acoustic properties of the audio, the plugin then uploads this metadata to the AcousticBrainz server. The plugin does this when calling the ``beet absumbit [QUERY]`` command or on importing if the `auto` configuration options is set to ``yes``.

$ beet absubmit [-f] [QUERY]

By default, the command will only analyse for acousticbrainz data when the tracks doesn't
already have it; the ``-f`` or ``--force`` switch makes it analyse the tracks for acousticbrainz. 
If you specify a query, only matching tracks will be processed; 
otherwise, the command processes every track in your library.

Installation
------------

The `absubmit` plugin requires the the `streaming_extractor_music`_ program to run. Its source can be found on `github`_, and while it is possible to compile the extractor from source, AcousticBrainz would prefer if you used thier binary (see the AcousticBrainz `FAQ`_).

The `absubmit` also plugin requires `requests`_, which you can install using `pip_` by typing:

    pip install requests

After installing both the extractor binary and request you can enable the plgin ``absubmit`` in your configuration (see :ref:`using-plugins`).

Configuration
-------------

To configute the plugin, make a ``absubmit:`` section in your configuration file. The available options are:

- **auto**: Analyze every file on import. Otherwise, you need to use the ``beet absubmit`` command explicitly.
  Default: ``no``
- **extractor**: The path to the `streaming_extractor_music`_ binary.
  Default: search for the program in your ``$PATH``
- **force**: By default, beets will not analyse Tracks if it have already acousticbrainz data. To instead analyse tracks and send json to acousticbrainz, 
  set the ``force`` option to ``yes``.
  Default: ``no``.

.. _streaming_extractor_music: http://acousticbrainz.org/download
.. _FAQ: http://acousticbrainz.org/faq
.. _pip: http://www.pip-installer.org/
.. _requests: http://docs.python-requests.org/en/master/
.. _github: https://github.com/MTG/essentia
