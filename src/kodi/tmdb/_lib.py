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

import argparse
import fnmatch
import json
import logging
import os
import time
from typing import Optional, Dict
from xml.dom import minidom

import requests

from kodi.api import MediaAPI
from kodi.env import setup_env, interactive
from kodi.io_utils import determine_dirs, read_id, skip, proceed, json_loads, prompt, get_nfo_file, strip_id, \
    TAG_MOVIE, TAG_TVSHOW, FILENAME_TVSHOW
from kodi.xml_utils import add_node, output_xml

# logging setup
logger = logging.getLogger("kodi.tmdb")


POSTER_URL = "https://image.tmdb.org/t/p/original"
""" see here: https://www.themoviedb.org/talk/5ee4ba52a217c0001fd0cb83#5ee4c7bc5b4fed001e6460bf """


TYPE_MOVIE = "movie"
TYPE_TVSHOW = "tv-show"
TYPES = [
    TYPE_MOVIE,
    TYPE_TVSHOW,
]


class TMDB(MediaAPI):

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "tmdb"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Uses the TMDB API as backend: https://www.themoviedb.org/"

    def iterate(self, sub_parsers):
        """
        Adds the argument sub-parser for the API that iterates
        over directories looking for media to update.

        Tool: kodi-nfo-gen

        :param sub_parsers: the sub-parsers to append
        """
        parser = sub_parsers.add_parser(self.name(), help=self.description())
        parser.set_defaults(func=iterate_tmdb)
        parser.add_argument("--type", dest="type", choices=TYPES, default=TYPE_MOVIE, required=False, help="what type of media to process")
        parser.add_argument("--key", metavar="KEY", dest="key", required=True, help="the access token to use")
        parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
        parser.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
        parser.add_argument("--pattern", metavar="GLOB", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie IDs")
        parser.add_argument("--delay", metavar="SECONDS", dest="delay", type=int, required=False, default=1, help="the delay in seconds between web queries (to avoid blacklisting)")
        parser.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
        parser.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite existing .nfo files, ie recreating them with freshly retrieved data")
        parser.add_argument("--max_actors", metavar="NUM", dest="max_actors", type=int, required=False, default=3, help="the maximum number of actors to store")
        parser.add_argument("--fanart", dest="fanart", choices=["none", "download", "download-missing", "use-existing"], default="none", required=False, help="how to deal with fan-art")
        parser.add_argument("--fanart_file", metavar="FILE", dest="fanart_file", default="folder.jpg", required=False, help="when downloading or using existing fanart, use this filename")
        parser.add_argument("--interactive", action="store_true", dest="interactive", required=False, help="for enabling interactive mode")
        parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
        parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")

    def guess(self, sub_parsers):
        """
        Adds the argument sub-parser for the API that iterates
        over directories looking for media to update.

        Tool: kodi-nfo-guess

        :param sub_parsers: the sub-parsers to append
        """
        parser = sub_parsers.add_parser(self.name(), help=self.description())
        parser.set_defaults(func=iterate_guess_tmdb)
        parser.add_argument("--type", dest="type", choices=TYPES, default=TYPE_MOVIE, required=False, help="what type of media to process")
        parser.add_argument("--key", metavar="KEY", dest="key", required=True, help="the access token to use")
        parser.add_argument("--dir", metavar="DIR", dest="dir", required=True, help="the directory to traverse")
        parser.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
        parser.add_argument("--pattern", metavar="GLOB", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie IDs")
        parser.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
        parser.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite existing .nfo files, ie recreating them with freshly retrieved data")
        parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
        parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")


def iterate_tmdb(ns: argparse.Namespace):
    """
    Traverses the directory and generates the .nfo files.

    :param ns: the parsed options
    :type ns: argparse.Namespace
    """
    """
    Traverses the directory and generates the .nfo files.

    :param ns: the parsed options
    :type ns: argparse.Namespace
    """
    # setup environment
    setup_env(ns, logger)

    dirs = []
    determine_dirs(ns.dir, ns.recursive, dirs)
    dirs.sort()
    logger.info("# dirs: %d" % len(dirs))
    delay = ns.delay
    if interactive:
        delay = 0

    for d in dirs:
        logger.info("Current dir: %s" % d)
        id_filenames = fnmatch.filter(os.listdir(d), ns.pattern)

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
                if ns.type == TYPE_MOVIE:
                    file_generated = generate_tmdb_movie(id, ns.key, ns.max_actors, path=d, fanart=ns.fanart, fanart_file=ns.fanart_file,
                                                         overwrite=ns.overwrite, dry_run=ns.dry_run,)
                elif ns.type == TYPE_TVSHOW:
                    file_generated = generate_tmdb_tvshow(id, ns.key, ns.max_actors, path=d, fanart=ns.fanart,
                                                          fanart_file=ns.fanart_file,
                                                          overwrite=ns.overwrite, dry_run=ns.dry_run, )
                else:
                    logger.error("Unhandled type: %s" % ns.type)
            except Exception:
                logger.exception("Failed to process ID: %s" % id)

            if interactive and not proceed():
                break
            if file_generated and (delay > 0):
                time.sleep(delay)


def create_header(key: str) -> Dict[str, str]:
    """
    Creates the header for requests.

    :param key: the TMDB API key
    :type key: str
    :return: the headers
    :rtype: dict
    """
    return {
        "Authorization": "Bearer %s" % key,
        "accept": "application/json",
    }


def imdb_to_tmdb(tid: str, key: str, type_: str) -> Optional[str]:
    """
    Determines the TMDB ID from the IMDB one.

    :param tid: the IMDB title ID
    :type tid: str
    :param key: the API key to use
    :type key: str
    :param type_: movie or tv-show
    :type type_: str
    :return: the TMDB ID or None if failed to determine
    :rtype: str or None
    """
    logger.info("Determining TMDB ID for IMDB ID: %s" % tid)

    # generate URL
    url = "https://api.themoviedb.org/3/find/%s?external_source=imdb_id" % tid
    logger.info("tmdb query: %s" % url)

    # retrieve json
    r = requests.get(url, headers=create_header(key))
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
        return None

    j = r.json()
    logger.debug(json.dumps(j))

    # default movie .nfo
    if (type_ == TYPE_MOVIE) and ("movie_results" in j):
        if len(j["movie_results"]) > 0:
            j = j["movie_results"][0]
            result = str(j["id"])
            logger.info("Determined TMDB ID (movie): %s" % result)
            return result
    elif (type_ == TYPE_TVSHOW) and ("tv_results" in j):
        if len(j["tv_results"]) > 0:
            j = j["tv_results"][0]
            result = str(j["id"])
            logger.info("Determined TMDB ID (TV show): %s" % result)
            return result
    else:
        logger.error("Unhandled type: %s" % type_)

    return None


def download_fanart_tmdb(doc=None, root=None, poster_path: str = None, path: str = None, fanart: str = "none", fanart_file: str = "folder.jpg"):
    """
    Downloads the fanart and attaches the information to the XML document.

    :param doc: the XML document
    :param root: the root node
    :param poster_path: the URL part for the poster
    :type poster_path: str
    :param path: the path to save it under
    :type path: str
    :param fanart: the fanart
    :type fanart: str
    :param fanart_file: the file to use
    :type fanart_file: str
    """
    fanart_path = os.path.join(path, fanart_file)
    fanart_act = fanart
    if fanart_act == "download-missing":
        if os.path.exists(fanart_path):
            fanart_act = "use-existing"
        else:
            fanart_act = "download"
    if fanart_act == "download":
        logger.info("Downloading fanart: %s" % poster_path)
        r = requests.get(POSTER_URL + poster_path, stream=True)
        if r.status_code == 200:
            with open(fanart_path, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            xthumb = add_node(doc, root, "thumb", fanart_file)
            xthumb.setAttribute("aspect", "poster")
        else:
            logger.critical("Failed to download fanart, status code: " % r.status_code)
    elif fanart_act == "use-existing":
        xthumb = add_node(doc, root, "thumb", fanart_file)
        xthumb.setAttribute("aspect", "poster")
    elif fanart_act == "none":
        pass
    else:
        logger.critical("Ignoring unhandled fanart type: %s" % fanart_act)


def generate_tmdb_movie(tid: str, key: str, max_actors: int = 5, fanart: str = "none", fanart_file: str = "folder.jpg",
                        path: str = None, overwrite: bool = False, dry_run: bool = False):
    """
    Generates the XML for the specified TMDB/IMDB movie ID.

    :param tid: the imdb or tmdb ID to use
    :type tid: str
    :param key: the TMDB API key
    :type key: str
    :param max_actors: the maximum number of actors to store
    :type max_actors: int
    :param fanart: how to deal with fanart
    :type fanart: str
    :param fanart_file: the fanart filename to use (when downloading or re-using existing)
    :type fanart_file: str
    :param path: the current directory (used for determining episode files)
    :type path: str
    :param overwrite: whether to overwrite existing .nfo files (ie recreating them)
    :type overwrite: bool
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    :return: whether a file was generated
    :rtype: bool
    """
    tid = strip_id(tid)
    is_imdb = tid.startswith("tt")

    # can we skip?
    if not overwrite:
        f = get_nfo_file(path)
        if f is not None:
            logger.info(".nfo file already exists, skipping: %s" % f)
            return False

    # generate URL
    if is_imdb:
        tid = imdb_to_tmdb(tid, key, TYPE_MOVIE)
        if tid is None:
            return False

    url = "https://api.themoviedb.org/3/movie/%s" % tid
    logger.info("tmdb query: %s" % url)

    # retrieve json
    r = requests.get(url, headers=create_header(key))
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
        return False

    output_generated = False

    j = r.json()
    logger.debug(json.dumps(j))

    xml_path = os.path.join(path, os.path.basename(path) + ".nfo")

    doc = minidom.Document()
    root = add_node(doc, doc, TAG_MOVIE)
    add_node(doc, root, "title", j['title'])
    uniqueid = add_node(doc, root, "uniqueid", str(j["id"]))
    uniqueid.setAttribute("type", "tmdb")
    uniqueid.setAttribute("default", "true")
    if "overview" in j:
        add_node(doc, root, "plot", j["overview"])
    if "release_date" in j:
        add_node(doc, root, "premiered", j["release_date"])
    if "genres" in j:
        for genre in j["genres"]:
            add_node(doc, root, "genre", genre["name"].strip())
    # actors
    url = "https://api.themoviedb.org/3/movie/%s/credits" % str(j["id"])
    r = requests.get(url, headers=create_header(key))
    if r.status_code != 200:
        logger.info("Failed to obtain cast information, status code: %d" % r.status_code)
    else:
        cast = r.json()
        num_actors = 0
        for actor in cast["cast"]:
            if actor["known_for_department"] == "Acting":
                num_actors += 1
                xactor = add_node(doc, root, "actor")
                add_node(doc, xactor, "name", actor["name"])
                if num_actors >= max_actors:
                    break
    if "vote_average" in j:
        xratings = add_node(doc, root, "ratings")
        xrating = add_node(doc, xratings, "rating")
        xrating.setAttribute("name", "imdb")
        xrating.setAttribute("max", "10")
        add_node(doc, xrating, "value", str(j["vote_average"]))

    # fanart
    poster_path = None
    if "poster_path" in j:
        poster_path = j["poster_path"]
    download_fanart_tmdb(doc=doc, root=root, path=path, fanart=fanart, fanart_file=fanart_file, poster_path=poster_path)

    if output_xml(doc, xml_path, dry_run=dry_run, overwrite=overwrite, logger=logger):
        output_generated = True

    return output_generated


def generate_tmdb_tvshow(tid: str, key: str, max_actors: int = 5, fanart: str = "none", fanart_file: str = "folder.jpg",
                         path: str = None, overwrite: bool = False, dry_run: bool = False):
    """
    Generates the XML for the specified TMDB/IMDB tv show ID.

    :param tid: the imdb or tmdb ID to use
    :type tid: str
    :param key: the TMDB API key
    :type key: str
    :param max_actors: the maximum number of actors to store
    :type max_actors: int
    :param fanart: how to deal with fanart
    :type fanart: str
    :param fanart_file: the fanart filename to use (when downloading or re-using existing)
    :type fanart_file: str
    :param path: the current directory (used for determining episode files)
    :type path: str
    :param overwrite: whether to overwrite existing .nfo files (ie recreating them)
    :type overwrite: bool
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    :return: whether a file was generated
    :rtype: bool
    """
    tid = strip_id(tid)
    is_imdb = tid.startswith("tt")

    # can we skip?
    if not overwrite:
        f = get_nfo_file(path)
        if f is not None:
            logger.info(".nfo file already exists, skipping: %s" % f)
            return False

    # generate URL
    if is_imdb:
        tid = imdb_to_tmdb(tid, key, TYPE_TVSHOW)
        if tid is None:
            return False

    url = "https://api.themoviedb.org/3/tv/%s" % tid
    logger.info("tmdb query: %s" % url)

    # retrieve json
    r = requests.get(url, headers=create_header(key))
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
        return False

    output_generated = False

    j = r.json()
    logger.debug(json.dumps(j))

    xml_path = os.path.join(path, FILENAME_TVSHOW)
    doc = minidom.Document()
    root = add_node(doc, doc, TAG_TVSHOW)

    add_node(doc, root, "title", j['name'])
    add_node(doc, root, "originaltitle", j["original_name"])
    uniqueid = add_node(doc, root, "uniqueid", str(j["id"]))
    uniqueid.setAttribute("type", "tmdb")
    uniqueid.setAttribute("default", "true")
    if "overview" in j:
        add_node(doc, root, "plot", j["overview"])
        add_node(doc, root, "outline", j["overview"])
    if "vote_average" in j:
        add_node(doc, root, "mpaa", str(j["vote_average"]))
    if "first_air_date" in j:
        add_node(doc, root, "premiered", j["first_air_date"])
    if "genres" in j:
        for genre in j["genres"]:
            add_node(doc, root, "genre", genre["name"])
    # actors
    url = "https://api.themoviedb.org/3/tv/%s/credits" % str(j["id"])
    r = requests.get(url, headers=create_header(key))
    if r.status_code != 200:
        logger.info("Failed to obtain cast information, status code: %d" % r.status_code)
    else:
        cast = r.json()
        num_actors = 0
        for actor in cast["cast"]:
            if actor["known_for_department"] == "Acting":
                num_actors += 1
                xactor = add_node(doc, root, "actor")
                add_node(doc, xactor, "name", actor["name"])
                if num_actors >= max_actors:
                    break
    # TODO episodes

    # fanart
    poster_path = None
    if "poster_path" in j:
        poster_path = j["poster_path"]
    download_fanart_tmdb(doc=doc, root=root, path=path, fanart=fanart, fanart_file=fanart_file, poster_path=poster_path)

    if output_xml(doc, xml_path, dry_run=dry_run, overwrite=overwrite, logger=logger):
        output_generated = True

    return output_generated


def iterate_guess_tmdb(ns: argparse.Namespace):
    """
    Traverses the directory and generates the .nfo files.

    :param ns: the parsed options to use
    :type ns: argparse.Namespace
    """
    # setup environment
    setup_env(ns, logger)

    dirs = []
    determine_dirs(ns.dir, ns.recursive, dirs)
    dirs.sort()
    logger.info("# dirs: %d" % len(dirs))

    for d in dirs:
        logger.info("Current dir: %s" % d)
        if (not ns.overwrite) and (len(fnmatch.filter(os.listdir(d), ns.pattern)) > 0):
            continue

        dname = os.path.basename(d)
        print("\n%s\n%s" % (dname, "=" * len(dname)))

        try:
            meta_path = os.path.join(d, dname + ".tmdb")
            guess_tmdb(dname, ns.key, meta_path, dry_run=ns.dry_run)
        except Exception:
            logger.exception("Failed to process directory: %s" % d)


def guess_tmdb(title, key, type_, meta_path, dry_run=False):
    """
    Generates .tmdb files using the user's selection of tmdb search results for the title.

    :param key: the api key to use
    :type key: str
    :param title: the title to look for
    :type title: str
    :param type_: movie or tv-show
    :type type_: str
    :param meta_path: the file to store the tmdb title ID in
    :type meta_path: str
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    :return: whether to continue
    :rtype: bool
    """
    if type_ == TYPE_MOVIE:
        url = "https://api.themoviedb.org/3/search/movie"
    elif type == TYPE_TVSHOW:
        url = "https://api.themoviedb.org/3/search/tv"
    else:
        logger.error("Unhandled type: %s" % type_)
        return False

    params = {"query": title}
    r = requests.get(url, params=params, headers=create_header(key))
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
        return False

    # in case we are overwriting files
    tid = None
    if os.path.exists(meta_path):
        tid = read_id(meta_path)

    j = json_loads(r.content)
    logger.debug(j)
    choices = []
    if len(j["results"]) == 0:
        print("0. No results, continue...")
    else:
        for i, result in enumerate(j["results"], start=1):
            # marker for current title?
            if (tid is not None) and (tid == result["id"]):
                current = " <-- current"
            else:
                current = ""
            if "title" in result:
                title = result["title"]
            elif "original_name" in result:
                title = result["original_name"]
            else:
                continue

            print("%d. %s: %s%s" % (i, result["id"], title, current))
            choices.append(str(i))
        print("0. None of the above, continue...")
    print("X. Exit")
    choices.append("0")
    choices.append("X")
    choice = prompt("Your selection (%s): ", choices=choices)
    if choice == "X":
        print("User requested exit.")
        return False
    elif choice == "0":
        return True
    else:
        tid = j["results"][int(choice) - 1]["id"]
        if dry_run:
            print(tid)
        else:
            logger.info("Writing ID %s to: %s" % (tid, meta_path))
            with open(meta_path, "w") as f:
                f.write(tid)
        return True
