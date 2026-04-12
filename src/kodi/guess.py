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

# guess.py
# Copyright (C) 2023-2026 Fracpete (fracpete at gmail dot com)

import argparse
import logging
import traceback

from kodi.registry import available_apis

# logging setup
logger = logging.getLogger("kodi.guess")


def main(args=None):
    """
    Runs the .nfo generation.
    Use -h/--help to see all options.

    :param args: the command-line arguments to use, uses sys.argv if None
    :type args: list
    """

    parser = argparse.ArgumentParser(
        description='Generates output files for the kodi-nfo-gen tool using different backends.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="kodi-nfo-guess")
    subparsers = parser.add_subparsers(help='Backend help', required=True)

    apis = available_apis()
    for api in apis:
        apis[api].guess(subparsers)

    parsed = parser.parse_args(args=args)
    parsed.func(parsed)


def sys_main():
    """
    Runs the main function using the system cli arguments, and
    returns a system error code.

    :return: 0 for success, 1 for failure.
    :rtype: int
    """

    try:
        main()
        return 0
    except Exception:
        logger.info(traceback.format_exc())
        return 1


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.info(traceback.format_exc())
