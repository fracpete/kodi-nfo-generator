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

# generator.py
# Copyright (C) 2020-2023 Fracpete (fracpete at gmail dot com)

import argparse
import fnmatch
import logging
import os
import time
import traceback
from kodi.imdb import generate_imdb
from kodi.io_utils import determine_dirs, read_id, skip, proceed

# logging setup
logger = logging.getLogger("kodi.generator")


def generate(path, idtype="imdb", recursive=True, pattern="*.imdb", delay=1, dry_run=False, overwrite=False,
             language="en", fanart="none", fanart_file="folder.jpg", interactive=False, episodes=False,
             episode_pattern="*S??E??*.*", season_group=".*S([0-9]?[0-9])E.*", episode_group=".*E([0-9]?[0-9]).*",
             ua="Mozilla"):
    """
    Traverses the directory and generates the .nfo files.

    :param path: the directory to traverse
    :type path: str
    :param idtype: how to interpret the ID files (choices: 'imdb')
    :type idtype: str
    :param recursive: whether to search recursively
    :type recursive: bool
    :param pattern: the file pattern (glob) to use for identifying the files with the IDs
    :type pattern: str
    :param delay: the delay in seconds between web queries
    :type delay: int
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    :param overwrite: whether to overwrite existing .nfo files (ie recreating them)
    :type overwrite: bool
    :param language: the preferred language for the titles
    :type language: str
    :param fanart: how to deal with fanart
    :type fanart: str
    :param fanart_file: the fanart filename to use (when downloading or re-using existing)
    :type fanart_file: str
    :param interactive: whether to use interactive mode
    :type interactive: bool
    :param episodes: whether to generate episode information as well
    :type episodes: bool
    :param episode_pattern: the pattern to use for locating episode files
    :type episode_pattern: str
    :param season_group: the regular expression to extract the season (first group)
    :type season_group: str
    :param episode_group: the regular expression to extract the episode (first group)
    :type episode_group: str
    :param ua: User agent for requests
    :type ua: str
    """

    dirs = []
    determine_dirs(path, recursive, dirs)
    dirs.sort()
    logger.info("# dirs: %d" % len(dirs))
    if interactive:
        delay = 0

    for d in dirs:
        logger.info("Current dir: %s" % d)
        id_filenames = fnmatch.filter(os.listdir(d), pattern)

        for id_filename in id_filenames:
            id_path = os.path.join(d, id_filename)
            logger.info("ID file: %s" % id_path)

            id = read_id(id_path)
            logger.info("ID: %s" % id)

            if interactive and skip():
                if proceed():
                    continue
                else:
                    break

            file_generated = False
            try:
                if idtype == "imdb":
                    file_generated = generate_imdb(id, language=language, fanart=fanart, fanart_file=fanart_file,
                                                   path=d, overwrite=overwrite, dry_run=dry_run,
                                                   episodes=episodes, episode_pattern=episode_pattern,
                                                   season_group=season_group, episode_group=episode_group,
                                                   ua=ua)
                else:
                    logger.critical("Unhandled ID type: %s" % idtype)
                    return
            except Exception:
                logger.info(traceback.format_exc())

            if interactive and not proceed():
                break
            if file_generated and (delay > 0):
                time.sleep(delay)


def main(args=None):
    """
    Runs the .nfo generation.
    Use -h/--help to see all options.

    :param args: the command-line arguments to use, uses sys.argv if None
    :type args: list
    """

    parser = argparse.ArgumentParser(
        description='Generates Kodi .nfo files with information retrieved from IMDB using local files containing the unique IMDB movie ID.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="kodi-nfo-gen")
    parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
    parser.add_argument("--type", dest="type", choices=["imdb"], default="imdb", required=False, help="what type of ID the movie ID files represent, ie the website they are from")
    parser.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
    parser.add_argument("--pattern", metavar="GLOB", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie IDs")
    parser.add_argument("--delay", metavar="SECONDS", dest="delay", type=int, required=False, default=1, help="the delay in seconds between web queries (to avoid blacklisting)")
    parser.add_argument("--preferred_language", metavar="LANG", dest="language", required=False, default="en", help="the preferred language for the titles (ISO 639-1, see https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)")
    parser.add_argument("--fanart", dest="fanart", choices=["none", "download", "download-missing", "use-existing"], default="none", required=False, help="how to deal with fan-art")
    parser.add_argument("--fanart_file", metavar="FILE", dest="fanart_file", default="folder.jpg", required=False, help="when downloading or using existing fanart, use this filename")
    parser.add_argument("--episodes", action="store_true", dest="episodes", required=False, help="whether to generate .nfo files for episodes as well")
    parser.add_argument("--episode_pattern", dest="episode_pattern", required=False, default="*S??E??*.*", help="the shell pattern to use for locating episode files")
    parser.add_argument("--season_group", dest="season_group", required=False, default=".*S([0-9]?[0-9])E.*", help="the regular expression to extract the season (first group)")
    parser.add_argument("--episode_group", dest="episode_group", required=False, default=".*E([0-9]?[0-9]).*", help="the regular expression to extract the episode (first group)")
    parser.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
    parser.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite existing .nfo files, ie recreating them with freshly retrieved data")
    parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")
    parser.add_argument("--interactive", action="store_true", dest="interactive", required=False, help="for enabling interactive mode")
    parser.add_argument("--user-agent", "--ua", type=str, required=False, default="Mozilla", help="User agent for HTTP requests")
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
    generate(path=parsed.dir, idtype=parsed.type, recursive=parsed.recursive, pattern=parsed.pattern,
             dry_run=parsed.dry_run, overwrite=parsed.overwrite, language=parsed.language,
             fanart=parsed.fanart, fanart_file=parsed.fanart_file, interactive=parsed.interactive,
             episodes=parsed.episodes, episode_pattern=parsed.episode_pattern,
             season_group=parsed.season_group, episode_group=parsed.episode_group,
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
