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
# Copyright (C) 2020-2025 Fracpete (fracpete at gmail dot com)

import argparse
import logging
import traceback

from kodi.imdb import iterate_imdb
from kodi.omdb import iterate_omdb

# logging setup
logger = logging.getLogger("kodi.generator")


def main(args=None):
    """
    Runs the .nfo generation.
    Use -h/--help to see all options.

    :param args: the command-line arguments to use, uses sys.argv if None
    :type args: list
    """

    parser = argparse.ArgumentParser(
        description='Generates Kodi .nfo files with information retrieved from internet sources using local files containing the unique movie and TV series IDs.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="kodi-nfo-gen")
    subparsers = parser.add_subparsers(help='Backend help', required=True)
    
    # imdb
    parser_imdb = subparsers.add_parser('imdb', help='Use IMDB as backend: https://www.imdb.com/')
    parser_imdb.set_defaults(func=iterate_imdb)
    parser_imdb.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
    parser_imdb.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
    parser_imdb.add_argument("--pattern", metavar="GLOB", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie/TV series IDs")
    parser_imdb.add_argument("--delay", metavar="SECONDS", dest="delay", type=int, required=False, default=1, help="the delay in seconds between web queries (to avoid blacklisting)")
    parser_imdb.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
    parser_imdb.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite existing .nfo files, ie recreating them with freshly retrieved data")
    parser_imdb.add_argument("--multi_episodes", action="store_true", dest="multi_episodes", required=False, help="whether to store the episodes info in a single file")
    parser_imdb.add_argument("--preferred_language", metavar="LANG", dest="language", required=False, default="en", help="the preferred language for the titles (ISO 639-1, see https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)")
    parser_imdb.add_argument("--fanart", dest="fanart", choices=["none", "download", "download-missing", "use-existing"], default="none", required=False, help="how to deal with fan-art")
    parser_imdb.add_argument("--fanart_file", metavar="FILE", dest="fanart_file", default="folder.jpg", required=False, help="when downloading or using existing fanart, use this filename")
    parser_imdb.add_argument("--episodes", action="store_true", dest="episodes", required=False, help="whether to generate .nfo files for episodes as well")
    parser_imdb.add_argument("--episode_pattern", dest="episode_pattern", required=False, default="*S??E??*.*", help="the shell pattern(s) to use for locating episode files", nargs="*")
    parser_imdb.add_argument("--season_group", dest="season_group", required=False, default=".*S([0-9]?[0-9])E.*", help="the regular expression to extract the season (first group)")
    parser_imdb.add_argument("--episode_group", dest="episode_group", required=False, default=".*E([0-9]?[0-9]).*", help="the regular expression to extract the episode (first group)")
    parser_imdb.add_argument("--user-agent", "--ua", type=str, required=False, default="Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version", help="User agent for HTTP requests")
    parser_imdb.add_argument("--interactive", action="store_true", dest="interactive", required=False, help="for enabling interactive mode")
    parser_imdb.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser_imdb.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")

    # omdb
    parser_omdb = subparsers.add_parser('omdb', help='Use OMDb API as backend: https://www.omdbapi.com/')
    parser_omdb.set_defaults(func=iterate_omdb)
    parser_omdb.add_argument("--key", metavar="KEY", dest="key", required=True, help="the API key to use")
    parser_omdb.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
    parser_omdb.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
    parser_omdb.add_argument("--pattern", metavar="GLOB", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie IDs")
    parser_omdb.add_argument("--delay", metavar="SECONDS", dest="delay", type=int, required=False, default=1, help="the delay in seconds between web queries (to avoid blacklisting)")
    parser_omdb.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
    parser_omdb.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite existing .nfo files, ie recreating them with freshly retrieved data")
    parser_omdb.add_argument("--fanart", dest="fanart", choices=["none", "download", "download-missing", "use-existing"], default="none", required=False, help="how to deal with fan-art")
    parser_omdb.add_argument("--fanart_file", metavar="FILE", dest="fanart_file", default="folder.jpg", required=False, help="when downloading or using existing fanart, use this filename")
    parser_omdb.add_argument("--interactive", action="store_true", dest="interactive", required=False, help="for enabling interactive mode")
    parser_omdb.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser_omdb.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")

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
