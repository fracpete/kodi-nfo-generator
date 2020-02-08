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
import csv
import logging
import os
import traceback
from kodi.io_utils import guess_file_name, skip, proceed

# logging setup
logger = logging.getLogger("kodi.import")


def import_ids(input, dir, idtype="imdb", cols=dict(), dry_run=False, overwrite=False, interactive=False):
    """
    Imports the IDs from the CSV file.

    :param input: the input CSV file to read from
    :type input: str
    :param dir: the top-level movie directory, in case relative paths are stored in the CSV file
    :type dir: str
    :param idtype: what type of ID files to generate (choices: 'imdb')
    :type idtype: str
    :param cols: the dictionary with the columns (name or 1-based index)
    :type cols: dict
    :param dry_run: whether to perform a 'dry-run', ie only outputting the content of the ID files but not writing them to disk
    :type dry_run: bool
    :param overwrite: whether to overwrite existing ID files or skip them
    :type overwrite: bool
    :param interactive: whether to use interactive mode
    :type interactive: bool
    """

    indices = {}
    indices["id"] = -1
    indices["dir"] = -1
    indices["file"] = -1
    first = True
    with open(input, newline='') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if first:
                first = False
                # determine column indices
                for i, name in enumerate(row):
                    for k in cols:
                        if cols[k] == name:
                            indices[k] = i
                        else:
                            try:
                                if int(cols[k]) - 1 == i:
                                    indices[k] = i
                            except:
                                pass
                logger.info("Indices (0-based): %s" % str(indices))
                if indices["id"] == -1:
                    raise Exception("ID column not found ('%s')!" % cols["id"])
                if indices["dir"] == -1:
                    raise Exception("Dir column not found ('%s')!" % cols["dir"])
            else:
                # read values
                r_id = row[indices["id"]]
                if r_id is None or len(r_id) == 0:
                    logger.warning("No ID, skipping row: %s" % str(row))
                    continue
                r_dir = row[indices["dir"]]
                if r_dir is None or len(r_dir) == 0:
                    logger.warning("No directory, skipping row: %s" % str(row))
                    continue
                r_file = None
                if indices["file"] != -1:
                    r_file = row[indices["file"]]
                if not os.path.isabs(r_dir):
                    r_dir = os.path.join(dir, r_dir)
                logger.info("id|dir|file: %s|%s|%s" % (r_id, r_dir, r_file))

                if interactive and skip():
                    if proceed():
                        continue
                    else:
                        break

                # output ID file
                if dry_run:
                    if r_file is not None:
                        print("%s -> %s" % (os.path.join(r_dir, r_file), r_id))
                    else:
                        print("%s -> %s" % (r_dir, r_id))
                else:
                    if r_file is not None and len(r_file) > 0:
                        id_path = os.path.join(r_dir, r_file + "." + idtype)
                    else:
                        id_path = os.path.join(r_dir, guess_file_name(r_dir) + "." + idtype)
                    logger.info("ID file: %s" % id_path)
                    if not overwrite and os.path.exists(id_path):
                        logger.info("Already exists, skipping")
                    else:
                        with open(id_path, "w") as id_file:
                            id_file.write(r_id)

                if interactive and not proceed():
                    break


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
        prog="kodi-nfo-import")
    parser.add_argument("--input", metavar="CSV", dest="input", required=True, help="the CSV output file to store the collected information in")
    parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the top-level directory of the movies if relative directories are used in the CSV file")
    parser.add_argument("--type", dest="type", choices=["imdb"], default="imdb", required=False, help="what type of ID to create, ie what website the IDs are from")
    parser.add_argument("--col_id", metavar="COL", dest="col_id", required=True, help="the column that contains the ID (name or 1-based index)")
    parser.add_argument("--col_dir", metavar="COL", dest="col_dir", required=True, help="the column that contains the directory (name or 1-based index)")
    parser.add_argument("--col_file", metavar="COL", dest="col_file", required=False, default=None, help="the column that contains the file name (name or 1-based index)")
    parser.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the ID file content to stdout but not saving them to files")
    parser.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite any existing ID files or leave them be")
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
    cols = {}
    cols["id"] = parsed.col_id
    cols["dir"] = parsed.col_dir
    cols["file"] = parsed.col_file
    import_ids(input=parsed.input, dir=parsed.dir, idtype=parsed.type, dry_run=parsed.dry_run,
               overwrite=parsed.overwrite, cols=cols, interactive=parsed.interactive)


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
