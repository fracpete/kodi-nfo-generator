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

import os


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