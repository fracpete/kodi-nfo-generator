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

# exports.py
# Copyright (C) 2020 Fracpete (fracpete at gmail dot com)

import argparse
import fnmatch
import logging
import os
import traceback
from kodi.io_utils import determine_dirs, read_id, read_id_from_nfo, skip, proceed

# logging setup
logger = logging.getLogger("kodi.export")


def write_to_csv(csv_file, dir, name, id):
    """
    Writes a row to the CSV file.

    :param csv_file: the file handle to write to.
    :type csv_file: file
    :param dir: the directory to write out
    :type dir: str`
    :param name: the file name (without path or extension)
    :type name: str
    :param id: the ID to write out
    :type id: str
    """

    csv_file.write("\"")
    csv_file.write(dir)
    csv_file.write("\"")
    csv_file.write(",")
    csv_file.write("\"")
    csv_file.write(name.replace("\"", ""))
    csv_file.write("\"")
    csv_file.write(",")
    csv_file.write(id)
    csv_file.write("\n")


def export_ids(dir, idtype="imdb", recursive=True, pattern="*.imdb", output="./kodi.csv", interactive=False):
    """
    Exports the IDs from ID or .nfo files.

    :param dir: the directory to look for ID/.nfo files
    :type dir: str
    :param idtype: what type of IDs to extract from .nfo files (choices: 'imdb')
    :type idtype: str
    :param recursive: whether to locate files recursively
    :type recursive: bool
    :param pattern: the pattern for the ID files (glob)
    :type pattern: str
    :param output: the output CSV file to generate
    :type output: str
    :param interactive: whether to use interactive mode
    :type interactive: bool
    """

    dirs = []
    determine_dirs(dir, recursive, dirs)
    dirs.sort()
    logger.info("Dirs: %s" % ",".join(dirs))

    with open(output, "w") as csv_file:
        csv_file.write("Directory,File,ID\n")
        for d in dirs:
            logger.info("Current dir: %s" % d)
            if interactive and skip():
                if proceed():
                    continue
                else:
                    break
            processed = set()

            # ID file
            id_filenames = fnmatch.filter(os.listdir(d), pattern)
            for id_filename in id_filenames:
                id_path = os.path.join(d, id_filename)
                id = read_id(id_path)
                logger.info("ID: %s" % id)
                name = os.path.splitext(id_filename)[0]
                processed.add(name)
                write_to_csv(csv_file, d, name, id)

            # .nfo file (if not already processed)
            nfo_filenames = fnmatch.filter(os.listdir(d), "*.nfo")
            for nfo_filename in nfo_filenames:
                name = os.path.splitext(nfo_filename)[0]
                if name not in processed:
                    nfo_path = os.path.join(d, nfo_filename)
                    id = read_id_from_nfo(nfo_path, idtype)
                    logger.info("ID: %s" % id)
                    write_to_csv(csv_file, d, name, id)

            if interactive and not proceed():
                break


def main(args=None):
    """
    Performs the export.
    Use -h to see all options.

    :param args: the command-line arguments to use, uses sys.argv if None
    :type args: list
    """

    parser = argparse.ArgumentParser(
        description='Exports Kodi ID/.nfo files to CSV, associating directories with IDs.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="kodi-nfo-export")
    parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
    parser.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
    parser.add_argument("--type", dest="type", choices=["imdb"], default="imdb", required=False, help="what type of ID the movie ID files represent, ie the website they are from")
    parser.add_argument("--pattern", metavar="GLOB", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie IDs")
    parser.add_argument("--output", metavar="CSV", dest="output", required=True, help="the CSV output file to store the collected information in")
    parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")
    parser.add_argument("--interactive", action="store_true", dest="interactive", required=False, help="for enabling interactive mode")
    parsed = parser.parse_args(args=args)
    # interactive mode turns on verbose mode
    if parsed.interactive and not (parsed.verbose or parsed.debug):
        parsed.verbose = True
    # configure loggin
    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed.verbose:
        logging.basicConfig(level=logging.INFO)
    logger.debug(parsed)
    if parsed.interactive:
        logger.info("Entering interactive mode")
    export_ids(dir=parsed.dir, recursive=parsed.recursive, pattern=parsed.pattern, output=parsed.output,
               interactive=parsed.interactive)


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
