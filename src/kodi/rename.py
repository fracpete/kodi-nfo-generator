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

# rename.py
# Copyright (C) 2023 Fracpete (fracpete at gmail dot com)

import argparse
import logging
import os
import re
import traceback
from kodi.io_utils import determine_dirs

# logging setup
logger = logging.getLogger("kodi.rename")


def rename(dir, find, replace, recursive=True, dry_run=False):
    """
    Traverses the directory and renames matching files.

    :param dir: the directory to traverse
    :type dir: str
    :param find: the find pattern
    :type find: str
    :param replace: the replace pattern
    :type replace: str
    :param recursive: whether to search recursively
    :type recursive: bool
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    """

    dirs = []
    determine_dirs(dir, recursive, dirs)
    dirs.sort()
    logger.info("# dirs: %d" % len(dirs))

    findc = re.compile(find)

    for d in dirs:
        logger.info("Current dir: %s" % d)
        try:
            for f in sorted(os.listdir(d)):
                if findc.match(f) is None:
                    continue
                fnew = re.sub(find, replace, f)
                logger.debug("%s -> %s" % (f, fnew))
                if f != fnew:
                    logger.debug("renaming file")
                    os.rename(os.path.join(d, f), os.path.join(d, fnew))
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
        description='Simple renaming tool using regular expressions.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="kodi-nfo-rename")
    parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
    parser.add_argument("--find", metavar="REGEXP", dest="find", required=False, default="([0-9]?[0-9])x([0-9][0-9]).(.*)", help="the regular expression that files must match in order to be renamed (excluding path; must specify groups to identify season, episode and extension)")
    parser.add_argument("--replace", metavar="PATTERN", dest="replace", required=False, default="S\\1E\\2.\\3", help="the pattern for assembling the new file name")
    parser.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
    parser.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
    parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")
    parsed = parser.parse_args(args=args)
    # configure logging
    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed.verbose:
        logging.basicConfig(level=logging.INFO)
    logger.debug(parsed)
    rename(dir=parsed.dir, find=parsed.find, replace=parsed.replace, recursive=parsed.recursive, dry_run=parsed.dry_run)


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
