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
# Copyright (C) 2023 Fracpete (fracpete at gmail dot com)

import argparse
import fnmatch
import logging
import os
import traceback
from kodi.imdb import guess_imdb
from kodi.io_utils import determine_dirs

# logging setup
logger = logging.getLogger("kodi.guess")


def guess(dir, idtype="imdb", recursive=True, pattern="*.imdb", dry_run=False, overwrite=False,
          language="en", ua="Mozilla"):
    """
    Traverses the directory and generates the .nfo files.

    :param dir: the directory to traverse
    :type dir: str
    :param idtype: how to interpret the ID files (choices: 'imdb')
    :type idtype: str
    :param recursive: whether to search recursively
    :type recursive: bool
    :param pattern: the file pattern (glob) to use for identifying the files with the IDs
    :type pattern: str
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    :param overwrite: whether to overwrite existing .nfo files (ie recreating them)
    :type overwrite: bool
    :param language: the preferred language for the titles
    :type language: str
    :param ua: User agent for requests
    :type ua: str
    """

    dirs = []
    determine_dirs(dir, recursive, dirs)
    dirs.sort()
    logger.info("# dirs: %d" % len(dirs))

    for d in dirs:
        logger.info("Current dir: %s" % d)
        if (not overwrite) and (len(fnmatch.filter(os.listdir(d), pattern)) > 0):
            continue

        dname = os.path.basename(d)
        print("\n%s\n%s" % (dname, "=" * len(dname)))

        try:
            if idtype == "imdb":
                meta_path = os.path.join(d, dname + ".imdb")
                guess_imdb(dname, meta_path, language=language, dry_run=dry_run, ua=ua)
            else:
                logger.critical("Unhandled ID type: %s" % idtype)
                return
        except Exception:
            logger.info(traceback.format_exc())


def main(args=None):
    """
    Runs the .nfo generation.
    Use -h/--help to see all options.

    :param args: the command-line arguments to use, uses sys.argv if None
    :type args: list
    """

    parser = argparse.ArgumentParser(
        description='Generates output files for the kodi-nfo-gen tool.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="kodi-nfo-guess")
    parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
    parser.add_argument("--type", dest="type", choices=["imdb"], default="imdb", required=False, help="what type of ID the movie ID files represent, ie the website they are from")
    parser.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
    parser.add_argument("--pattern", metavar="GLOB", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie IDs")
    parser.add_argument("--preferred_language", metavar="LANG", dest="language", required=False, default="en", help="the preferred language for the titles (ISO 639-1, see https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)")
    parser.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
    parser.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite existing .nfo files, ie recreating them with freshly retrieved data")
    parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")
    parser.add_argument("--user-agent", "--ua", type=str, required=False, default="Mozilla", help="User agent for HTTP requests")
    parsed = parser.parse_args(args=args)
    # configure logging
    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed.verbose:
        logging.basicConfig(level=logging.INFO)
    logger.debug(parsed)
    guess(dir=parsed.dir, idtype=parsed.type, recursive=parsed.recursive, pattern=parsed.pattern,
          dry_run=parsed.dry_run, overwrite=parsed.overwrite, language=parsed.language,
          ua=parsed.user_agent)


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
