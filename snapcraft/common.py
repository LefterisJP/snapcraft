# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2015 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Data/methods shared between plugins and snapcraft

import os
import platform
import subprocess
import tempfile
import urllib


SNAPCRAFT_FILES = ['snapcraft.yaml', 'parts', 'stage', 'snap']
COMMAND_ORDER = ['pull', 'build', 'stage', 'strip']
_DEFAULT_PLUGINDIR = '/usr/share/snapcraft/plugins'
_plugindir = _DEFAULT_PLUGINDIR
_DEFAULT_SCHEMADIR = '/usr/share/snapcraft/schema'
_schemadir = _DEFAULT_SCHEMADIR
_arch = None

env = []


def assemble_env():
    return '\n'.join(['export ' + e for e in env])


def run(cmd, **kwargs):
    assert isinstance(cmd, list), 'run command must be a list'
    # FIXME: This is gross to keep writing this, even when env is the same
    with tempfile.NamedTemporaryFile(mode='w+') as f:
        f.write(assemble_env())
        f.write('\n')
        f.write('exec $*')
        f.flush()
        subprocess.check_call(['/bin/sh', f.name] + cmd, **kwargs)


def run_output(cmd, **kwargs):
    assert isinstance(cmd, list), 'run command must be a list'
    # FIXME: This is gross to keep writing this, even when env is the same
    with tempfile.NamedTemporaryFile(mode='w+') as f:
        f.write(assemble_env())
        f.write('\n')
        f.write('exec $*')
        f.flush()
        return subprocess.check_output(['/bin/sh', f.name] + cmd,
                                       **kwargs).decode('utf8').strip()


_DEB_TRANSLATIONS = {
    'armv7l': {
        'arch': 'armhf',
        'triplet': 'arm-linux-gnueabihf',
    },
    'aarch64': {
        'arch': 'arm64',
        'triplet': 'aarch64-linux-gnu',
    },
    'i686': {
        'arch': 'i386',
        'triplet': 'i386-linux-gnu',
    },
    'ppc64le': {
        'arch': 'ppc64el',
        'triplet': 'powerpc64le-linux-gnu',
    },
    'x86_64': {
        'arch': 'amd64',
        'triplet': 'x86_64-linux-gnu',
    }
}


def get_arch():
    try:
        return _DEB_TRANSLATIONS[platform.machine()]['arch']
    except KeyError:
        raise EnvironmentError(
            '{} is not supported, please log a bug at'
            'https://bugs.launchpad.net/snapcraft'.format(platform.machine()))


def get_arch_triplet():
    try:
        return _DEB_TRANSLATIONS[platform.machine()]['triplet']
    except KeyError:
        raise EnvironmentError(
            '{} is not supported, please log a bug at'
            'https://bugs.launchpad.net/snapcraft'.format(platform.machine()))


def get_partsdir():
    return os.path.join(os.getcwd(), 'parts')


def get_stagedir():
    return os.path.join(os.getcwd(), 'stage')


def get_snapdir():
    return os.path.join(os.getcwd(), 'snap')


def set_plugindir(plugindir):
    global _plugindir
    _plugindir = plugindir


def get_plugindir():
    return _plugindir


def set_schemadir(schemadir):
    global _schemadir
    _schemadir = schemadir


def get_schemadir():
    return _schemadir


def isurl(url):
    return urllib.parse.urlparse(url).scheme != ''


def reset_env():
    global env
    env = []


def replace_in_file(directory, file_pattern, search_pattern, replacement):
    """Searches and replaces patterns that match a file pattern.
    :param str directory: The directory to look for files.
    :param str file_pattern: The file pattern to match inside directory.
    :param search_pattern: A re.compile'd pattern to search for within
                           matching files.
    :param str replacement: The string to replace the matching search_pattern
                            with.
    """
    for root, directories, files in os.walk(directory):
        for file_name in files:
            if file_pattern.match(file_name):
                _search_and_replace_contents(os.path.join(root, file_name),
                                             search_pattern, replacement)


def _search_and_replace_contents(file_path, search_pattern, replacement):
    with open(file_path, 'r+') as f:
        try:
            original = f.read()
        except UnicodeDecodeError:
            # This was probably a binary file. Skip it.
            return

        replaced = search_pattern.sub(replacement, original)
        if replaced != original:
            f.seek(0)
            f.truncate()
            f.write(replaced)
