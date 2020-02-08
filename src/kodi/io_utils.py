# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# io_utils.py
# Copyright (C) 2020 Fracpete (fracpete at gmail dot com)

import fnmatch
import os
from xml.dom import minidom


def determine_dirs(dir, recursive, result):
    """
    Determines all the directories to inspect.

    :param dir: the top-level directory
    :type dir: str
    :param recursive: whether to look for directories recursively
    :type recursive: bool
    :param result: for storing the located dirs
    :type param: list
    """

    result.append(dir)
    if recursive:
        files = os.listdir(dir)
        for f in files:
            full = os.path.join(dir, f)
            if os.path.isdir(full):
                determine_dirs(full, True, result)


def read_id(id_path):
    """
    Reads the ID from the specified ID file.

    :param id_path: the ID file to read
    :type id_path: str
    :return: the ID
    """

    with open(id_path, "r") as id_file:
        id = id_file.readline()
        return id.strip()


def read_id_from_nfo(nfo_path, idtype):
    """
    Reads the ID from the specified .nfo file.

    :param nfo_path: the .nfo file to read
    :type nfo_path: str
    :param idtype: what type of IDs to extract from .nfo files (choices: 'imdb')
    :type idtype: str
    :return: the ID
    :rtype: str
    """

    id = ""
    doc = minidom.parse(nfo_path)
    items = doc.getElementsByTagName('uniqueid')
    for item in items:
        if "type" in item.attributes and item.attributes["type"].value == idtype:
            id = item.firstChild.data
            break

    return id.strip()


def guess_file_name(dir):
    """
    Tries to determine the filename (excl extension) for the specified directory.
    Looks for .nfo file, then video files (mp4, mkv, avi) and finally the base name
    of the directory itself.

    :param dir: the directory to guess the file name for
    :type dir: str
    :return: the guessed file name (excl path)
    :rtype: str
    """

    result = None

    # nfo or video file?
    exts = ["nfo", "mp4", "mkv", "avi"]
    for ext in exts:
        filenames = fnmatch.filter(os.listdir(dir), "*." + ext)
        if len(filenames) == 1:
            result = os.path.splitext(os.path.basename(filenames[0]))[0]
            break

    # directory
    if result is None:
        result = os.path.basename(dir)

    return result


def prompt(msg="Proceed (%s)? ", choices=["y", "n"]):
    """
    Prompts user in the console with a message with specific choices to select from.

    :param msg: the message to display, use %s for inserting the allowed choices (format: a/b/c/...)
    :type msg: str
    :param choices: the list of allowed choices (must be strings)
    :type choices: list
    :return: the selected choice
    :rtype: str
    """

    act_msg = msg
    if "%s" in act_msg:
        act_msg = act_msg % ("/".join(choices))
    while True:
        retval = input(act_msg)
        if retval in choices:
            result = retval
            break

    return result


def proceed():
    """
    Prompts user whether to proceed (y/n).

    :return: whether to proceed
    :rtype: bool
    """

    return prompt(msg="Proceed (%s)? ", choices=["y", "n"]) == "y"


def skip():
    """
    Prompts user whether to skip (y/n).

    :return: whether to skip
    :rtype: bool
    """

    return prompt(msg="Skip (%s)? ", choices=["y", "n"]) == "y"
