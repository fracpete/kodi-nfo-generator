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

# api.py
# Copyright (C) 2026 Fracpete (fracpete at gmail dot com)

import abc
from seppl import Plugin


class MediaAPI(Plugin, abc.ABC):
    """
    Interface for command-line tools (sub-parsers)
    """

    def iterate(self, sub_parsers):
        """
        Adds the argument sub-parser for the API that iterates
        over directories looking for media to update.

        Tool: kodi-nfo-gen

        :param sub_parsers: the sub-parsers to append
        """
        pass

    def guess(self, sub_parsers):
        """
        Adds the argument sub-parser for the API that iterates
        over directories looking for media to update.

        Tool: kodi-nfo-guess

        :param sub_parsers: the sub-parsers to append
        """
        pass
