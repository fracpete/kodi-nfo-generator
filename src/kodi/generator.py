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
# Copyright (C) 2020 Fracpete (fracpete at gmail dot com)

import argparse
from bs4 import BeautifulSoup
import fnmatch
import json
import logging
import os
import requests
import time
import traceback
from xml.dom import minidom

# logging setup
logger = logging.getLogger("kodi.generator")


def add_node(doc, parent, name, value=None):
    """
    Adds a node to the DOM document.

    :param doc: the DOM document
    :type doc: minidom.Document
    :param parent: the parent node to add the new node to
    :type parent: minidom.Element
    :param name: the name of the node
    :type name: str
    :param value: the text value, ignored if None
    :type value: str
    :return: the generated node
    :rtype: minidom.Element
    """

    node = doc.createElement(name)
    parent.appendChild(node)
    if value is not None:
        text = doc.createTextNode(value)
        node.appendChild(text)

    return node


def generate_imdb(id, language="en"):
    """
    Generates the XML for the specified IMDB ID.

    :param id: the IMDB ID to use
    :type id: str
    :param language: the preferred language for the titles
    :type language: str
    :return: the generated XML DOM
    :rtype: minidom.Document
    """

    id = id.strip()

    # generate URL
    if id.startswith("http"):
        url = id
    else:
        url = "https://www.imdb.com/title/%s/" % id
    logger.info("IMDB URL: " + url)


    # retrieve html
    r = requests.get(url, headers={"Accept-Language": language})

    # parse html
    soup = BeautifulSoup(r.content, "html.parser")

    doc = minidom.Document()

    widget = soup.find("div", id="star-rating-widget")
    eng_title = widget["data-title"]

    for script in soup.findAll("script", type="application/ld+json"):
        j = json.loads(script.text)
        logger.debug(j)

        root = add_node(doc, doc, "movie")
        add_node(doc, root, "title", eng_title)
        add_node(doc, root, "originaltitle", j["name"])
        uniqueid = add_node(doc, root, "uniqueid", j["url"].replace("/title/", "").replace("/", ""))
        uniqueid.setAttribute("type", "imdb")
        uniqueid.setAttribute("default", "true")
        add_node(doc, root, "plot", j["description"])
        add_node(doc, root, "outline", j["description"])
        add_node(doc, root, "premiered", j["datePublished"])
        if "director" in j and "name" in j["director"]:
            add_node(doc, root, "director", j["director"]["name"])
        if isinstance(j["genre"], list):
            for genre in j["genre"]:
                add_node(doc, root, "genre", genre)
        else:
            add_node(doc, root, "genre", j["genre"])
        for actor in j["actor"]:
            xactor = add_node(doc, root, "actor")
            add_node(doc, xactor, "name", actor["name"])
        if "trailer" in j and "embedUrl" in j["trailer"]:
            add_node(doc, root, "trailer", "https://www.imdb.com" + j["trailer"]["embedUrl"])
        if "aggregateRating" in j and "ratingValue" in j["aggregateRating"]:
            xratings = add_node(doc, root, "ratings")
            xrating = add_node(doc, xratings, "rating")
            xrating.setAttribute("name", "imdb")
            xrating.setAttribute("max", "10")
            add_node(doc, xrating, "value", j["aggregateRating"]["ratingValue"])

    return doc


def determine_dirs(dir, recursive, result):
    """
    Determines all the directories to inspect.

    :param dir: the top-level directory
    :type dir: str
    :param recursive: whether to look for directories recursively
    :type recursive: bool
    :param result: for storing the located dirs
    :type param: list
    """

    result.append(dir)
    if recursive:
        files = os.listdir(dir)
        for f in files:
            full = os.path.join(dir, f)
            if os.path.isdir(full):
                determine_dirs(full, True, result)


def generate(dir, idtype="imdb", recursive=True, pattern="*.imdb", delay=1, dry_run=False, overwrite=False,
             language="en"):
    """
    Traverses the directory Generates the .nfo files.

    :param dir: the directory to traverse
    :type dir: str
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
    """

    dirs = []
    determine_dirs(dir, recursive, dirs)
    dirs.sort()
    logger.info("Dirs: %s" % ",".join(dirs))

    for d in dirs:
        logger.info("Current dir: %s" % d)
        id_filenames = fnmatch.filter(os.listdir(d), pattern)

        for id_filename in id_filenames:
            id_path = os.path.join(d, id_filename)
            xml_path = os.path.join(d, os.path.splitext(id_filename)[0] + ".nfo")
            logger.info("ID file: %s" % id_path)

            if not overwrite and os.path.exists(xml_path):
                logger.info(".nfo file already exists, skipping")
                continue

            with open(id_path, "r") as id_file:
                id = id_file.readline()
                logger.info("ID: %s" % id)

                try:
                    if idtype == "imdb":
                        doc = generate_imdb(id, language=language)
                    else:
                        logger.critical("Unhandled ID type: %s" % idtype)
                        return
                    xml_str = doc.toprettyxml(indent="  ")
                    if dry_run:
                        print(xml_str)
                    else:
                        logger.info("Writing .nfo file: %s" % xml_path)
                        with open(xml_path, "w") as xml_file:
                            xml_file.write(xml_str)
                except Exception:
                    logger.info(traceback.format_exc())

            if delay > 0:
                time.sleep(delay)


def main(args=None):
    """
    Runs a classifier from the command-line. Calls JVM start/stop automatically.
    Use -h to see all options.

    :param args: the command-line arguments to use, uses sys.argv if None
    :type args: list
    """

    parser = argparse.ArgumentParser(
        description='Generates.')
    parser.add_argument("--dir", metavar="dir", dest="dir", required=True, help="the directory to traverse")
    parser.add_argument("--type", metavar="type", dest="type", choices=["imdb"], default="imdb", required=False, help="what type of ID the movie ID files represent, ie the website they are from")
    parser.add_argument("--recursive", action="store_true", dest="recursive", required=False, help="whether to traverse the directory recursively")
    parser.add_argument("--pattern", metavar="glob", dest="pattern", required=False, default="*.imdb", help="the pattern for the files that contain the movie IDs")
    parser.add_argument("--delay", metavar="delay", dest="delay", type=int, required=False, default=1, help="the delay in seconds between web queries (to avoid blacklisting)")
    parser.add_argument("--preferred_language", metavar="lang", dest="language", required=False, default="en", help="the preferred language for the titles (ISO 639-1, see https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)")
    parser.add_argument("--dry_run", action="store_true", dest="dry_run", required=False, help="whether to perform a 'dry-run', ie only outputting the .nfo content to stdout but not saving it to files")
    parser.add_argument("--overwrite", action="store_true", dest="overwrite", required=False, help="whether to overwrite existing .nfo files, ie recreating them with freshly retrieved data")
    parser.add_argument("--verbose", action="store_true", dest="verbose", required=False, help="whether to output logging information")
    parser.add_argument("--debug", action="store_true", dest="debug", required=False, help="whether to output debugging information")
    parsed = parser.parse_args(args=args)
    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed.verbose:
        logging.basicConfig(level=logging.INFO)
    generate(dir=parsed.dir, idtype=parsed.type, recursive=parsed.recursive, pattern=parsed.pattern,
             dry_run=parsed.dry_run, overwrite=parsed.overwrite, language=parsed.language)


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
