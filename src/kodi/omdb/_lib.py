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

# Copyright (C) 2025 Fracpete (fracpete at gmail dot com)

import argparse
import fnmatch
import json
import logging
import os
import requests
import time
import traceback

from typing import Optional
from datetime import datetime
from xml.dom import minidom
from kodi.env import setup_env, interactive
from kodi.io_utils import determine_dirs, read_id, skip, proceed, json_loads, prompt, get_nfo_file, strip_id, \
    TAG_MOVIE, FILENAME_TVSHOW
from kodi.xml_utils import add_node, output_xml


# logging setup
logger = logging.getLogger("kodi.omdb")


def iterate_omdb(ns: argparse.Namespace):
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
                file_generated = generate_omdb(id, ns.key, path=d, fanart=ns.fanart, fanart_file=ns.fanart_file,
                                               overwrite=ns.overwrite, dry_run=ns.dry_run,)
            except Exception:
                logger.info(traceback.format_exc())

            if interactive and not proceed():
                break
            if file_generated and (delay > 0):
                time.sleep(delay)


def _parse_date(s: str) -> Optional[str]:
    """
    Parses dates like '17 May 2019' and returns them as '2019-05-17'.

    :param s: the date string to parse
    :type s: str
    :return: the generated date (YYYY-MM-DD), None if failed
    :type: str or None
    """
    try:
        d = datetime.strptime(s, "%d %b %Y")
    except:
        d = None
    if d is None:
        try:
            d = datetime.strptime(s, "%d %B %Y")
        except:
            d = None
    if d is None:
        return None
    else:
        return d.strftime("%Y-%m-%d")


def generate_omdb(tid, key, fanart="none", fanart_file="folder.jpg", path=None, overwrite=False, dry_run=False):
    """
    Generates the XML for the specified IMDB ID.

    :param tid: the IMDB ID to use
    :type tid: str
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

    # can we skip?
    if not overwrite:
        f = get_nfo_file(path)
        if f is not None:
            logger.info(".nfo file already exists, skipping: %s" % f)
            return False

    # generate URL
    params = {
        'apikey': key,
        'i': tid,
        'plot': 'full',
    }
    url = "http://www.omdbapi.com/"
    logger.info("OMDb query: %s / %s" % (url, str(params)))

    # retrieve json
    r = requests.get(url, params=params)
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
        return False

    output_generated = False

    j = json_loads(r.content)
    logger.debug(json.dumps(j))

    # default movie .nfo

    if j["Type"] == "series":
        xml_path = os.path.join(path, FILENAME_TVSHOW)
    else:
        xml_path = os.path.join(path, os.path.basename(path) + ".nfo")

    doc = minidom.Document()
    root = add_node(doc, doc, TAG_MOVIE)
    add_node(doc, root, "title", j['Title'])
    uniqueid = add_node(doc, root, "uniqueid", j["imdbID"])
    uniqueid.setAttribute("type", "imdb")
    uniqueid.setAttribute("default", "true")
    if "Plot" in j:
        add_node(doc, root, "plot", j["Plot"])
    if "Released" in j:
        d = _parse_date(j["Released"])
        if d is not None:
            add_node(doc, root, "premiered", d)
    add_node(doc, root, "director", j["Director"])
    if "Genre" in j:
        for genre in j["Genre"].split(","):
            add_node(doc, root, "genre", genre.strip())
    if "Actors" in j:
        for actor in j["Actors"].split(","):
            xactor = add_node(doc, root, "actor")
            add_node(doc, xactor, "name", actor.strip())
    if "imdbRating" in j:
        xratings = add_node(doc, root, "ratings")
        xrating = add_node(doc, xratings, "rating")
        xrating.setAttribute("name", "imdb")
        xrating.setAttribute("max", "10")
        add_node(doc, xrating, "value", str(j["imdbRating"]))

    # fanart
    fanart_path = os.path.join(path, fanart_file)
    fanart_act = fanart
    if fanart_act == "download-missing":
        if os.path.exists(fanart_path):
            fanart_act = "use-existing"
        else:
            fanart_act = "download"
    if fanart_act == "download":
        if "Poster" in j:
            logger.info("Downloading fanart: %s" % j["Poster"])
            r = requests.get(j["Poster"], stream=True)
            if r.status_code == 200:
                with open(fanart_path, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
                xthumb = add_node(doc, root, "thumb", fanart_file)
                xthumb.setAttribute("aspect", "poster")
            else:
                logger.critical("Failed to download fanart, status code: " % r.status_code)
        else:
            logger.warning("No image associated, cannot download!")
    elif fanart_act == "use-existing":
        xthumb = add_node(doc, root, "thumb", fanart_file)
        xthumb.setAttribute("aspect", "poster")
    elif fanart_act == "none":
        pass
    else:
        logger.critical("Ignoring unhandled fanart type: %s" % fanart_act)

    if output_xml(doc, xml_path, dry_run=dry_run, overwrite=overwrite, logger=logger):
        output_generated = True

    return output_generated


def iterate_guess_omdb(ns: argparse.Namespace):
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
            meta_path = os.path.join(d, dname + ".imdb")
            guess_omdb(dname, ns.key, meta_path, dry_run=ns.dry_run)
        except Exception:
            logger.info(traceback.format_exc())


def guess_omdb(title, key, meta_path, dry_run=False):
    """
    Generates .imdb files using the user's selection of OMDb search results for the title.

    :param key: the api key to use
    :type key: str
    :param title: the title to look for
    :type title: str
    :param meta_path: the file to store the IMDB title ID in
    :type meta_path: str
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    :return: whether to continue
    :rtype: bool
    """
    url = "http://www.omdbapi.com/"
    params = {'apikey': key, 's': title}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))

    # in case we are overwriting files
    tid = None
    if os.path.exists(meta_path):
        tid = read_id(meta_path)

    j = json_loads(r.content)
    logger.debug(j)
    choices = []
    if len(j["Search"]) == 0:
        print("0. No results, continue...")
    else:
        for i, result in enumerate(j["Search"], start=1):
            # marker for current title?
            if (tid is not None) and (tid == result["imdbID"]):
                current = " <-- current"
            else:
                current = ""
            print("%d. %s: %s%s" % (i, result["imdbID"], result["Title"], current))
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
        tid = j["Search"][int(choice) - 1]["imdbID"]
        if dry_run:
            print(tid)
        else:
            logger.info("Writing ID %s to: %s" % (tid, meta_path))
            with open(meta_path, "w") as f:
                f.write(tid)
        return True
