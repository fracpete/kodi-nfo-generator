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

# imports.py
# Copyright (C) 2020 Fracpete (fracpete at gmail dot com)

import argparse
import logging
import traceback

# logging setup
logger = logging.getLogger("kodi.import")


def import_ids(input, dir, idtype="imdb"):
    """
    Imports the IDs from the CSV file.

    :param input: the input CSV file to read from
    :type input: str
    :param dir: the top-level movie directory, in case relative paths are stored in the CSV file
    :type dir: str
    :param idtype: what type of ID files to generate (choices: 'imdb')
    :type idtype: str
    """
    pass


def main(args=None):
    """
    Performs the import.
    Use -h to see all options.

    :param args: the command-line arguments to use, uses sys.argv if None
    :type args: list
    """

    parser = argparse.ArgumentParser(
        description='Imports IDs from CSV, storing ID files in the associated directories.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="kodi-nfo-export")
    parser.add_argument("--input", metavar="CSV", dest="input", required=True, help="the CSV output file to store the collected information in")
    parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the top-level directory of the movies if relative directories are used in the CSV file")
    parser.add_argument("--type", dest="type", choices=["imdb"], default="imdb", required=False, help="what type of ID to create, ie what website the IDs are from")
    parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")
    parsed = parser.parse_args(args=args)
    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed.verbose:
        logging.basicConfig(level=logging.INFO)
    logger.debug(parsed)
    import_ids(input=parsed.input, dir=parsed.dir, idtype=parsed.type)


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
