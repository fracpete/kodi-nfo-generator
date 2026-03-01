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

# Copyright (C) 2026 Fracpete (fracpete at gmail dot com)

def extract_id(tid: str) -> str:
    """
    Extracts the title ID.

    :param tid: the ID or URL
    :type tid: str
    :return: the ID
    :rtype: str
    """
    result = tid
    if "/title/" in result:
        result = result[result.index("/title/")+7:]
        if "/" in result:
            result = result[0:result.index("/")]
    return result
