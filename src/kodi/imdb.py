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

# imdb.py
# Copyright (C) 2020-2021 Fracpete (fracpete at gmail dot com)

from bs4 import BeautifulSoup
import fnmatch
import json
import logging
import os
import requests
from xml.dom import minidom
from kodi.io_utils import determine_dirs
from kodi.xml_utils import add_node
from kodi.imdb_series import has_episodes, create_episodes_url, extract_seasons, extract_episodes, episode_to_xml, \
    extract_season_episode

# logging setup
logger = logging.getLogger("kodi.imdb")


def generate_imdb(id, language="en", fanart="none", fanart_file="folder.jpg", xml_path=None, episodes=False, path=None,
                  overwrite=False, dry_run=False):
    """
    Generates the XML for the specified IMDB ID.

    :param id: the IMDB ID to use
    :type id: str
    :param language: the preferred language for the titles
    :type language: str
    :param fanart: how to deal with fanart
    :type fanart: str
    :param fanart_file: the fanart filename to use (when downloading or re-using existing)
    :type fanart_file: str
    :param xml_path: the current nfo full file path
    :type xml_path: str
    :param episodes: whether to generate episode information as well
    :type episodes: bool
    :param path: the current directory (used for determining episode files)
    :type path: str
    :param overwrite: whether to overwrite existing .nfo files (ie recreating them)
    :type overwrite: bool
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
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
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))

    # parse html
    soup = BeautifulSoup(r.content, "html.parser")

    doc = minidom.Document()

    widget = soup.find("div", id="star-rating-widget")
    if widget is None:
        preflang_title = None
    else:
        preflang_title = widget["data-title"]

    for script in soup.findAll("script", type="application/ld+json"):
        j = json.loads(script.text)
        logger.debug(j)

        root = add_node(doc, doc, "movie")
        add_node(doc, root, "title", j['name'] if preflang_title is None else preflang_title)
        add_node(doc, root, "originaltitle", j["name"])
        uniqueid = add_node(doc, root, "uniqueid", j["url"].replace("/title/", "").replace("/", ""))
        uniqueid.setAttribute("type", "imdb")
        uniqueid.setAttribute("default", "true")
        if "description" in j:
            add_node(doc, root, "plot", j["description"])
            add_node(doc, root, "outline", j["description"])
        if "datePublished" in j:
            add_node(doc, root, "premiered", j["datePublished"])
        if "director" in j and "name" in j["director"]:
            add_node(doc, root, "director", j["director"]["name"])
        if "genre" in j:
            if isinstance(j["genre"], list):
                for genre in j["genre"]:
                    add_node(doc, root, "genre", genre)
            else:
                add_node(doc, root, "genre", j["genre"])
        if "actor" in j:
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
            add_node(doc, xrating, "value", str(j["aggregateRating"]["ratingValue"]))

        if fanart == "download":
            if "image" in j:
                logger.info("Downloading fanart: %s" % j["image"])
                r = requests.get(j["image"], stream=True)
                if r.status_code == 200:
                    fanart_path = os.path.join(os.path.dirname(xml_path), fanart_file)
                    with open(fanart_path, 'wb') as f:
                        for chunk in r:
                            f.write(chunk)
                    xthumb = add_node(doc, root, "thumb", fanart_file)
                    xthumb.setAttribute("aspect", "poster")
                else:
                    logger.critical("Failed to download fanart, status code: " % r.status_code)
            else:
                logger.warning("No image associated, cannot download!")
        elif fanart == "use-existing":
            xthumb = add_node(doc, root, "thumb", fanart_file)
            xthumb.setAttribute("aspect", "poster")
        elif fanart == "none":
            pass
        else:
            logger.critical("Ignoring unhandled fanart type: %s" % fanart)

        if episodes:
            if has_episodes(soup):
                logger.info("Has episode data")

                # determine seasons
                url = create_episodes_url(id)
                logger.info("Default episodes URL: %s" % url)
                r = requests.get(url, headers={"Accept-Language": language})
                if r.status_code != 200:
                    logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
                    continue
                soup_ep = BeautifulSoup(r.content, "html.parser")
                seasons = extract_seasons(soup_ep)
                logger.info("Seasons: %s" % ", ".join(seasons))

                # extract episodes
                season_data = {}
                for season in seasons:
                    season_data[season] = {}
                    url = create_episodes_url(id, season=season)
                    logger.info("Season %s URL: %s" % (season, url))
                    r = requests.get(url, headers={"Accept-Language": language})
                    if r.status_code != 200:
                        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
                        continue
                    soup_ep = BeautifulSoup(r.content, "html.parser")
                    episodes_data = extract_episodes(soup_ep, season)
                    for k in episodes_data:
                        xml = episode_to_xml(episodes_data[k])
                        season_data[season][k] = xml

                # locate files and output XML
                dirs = []
                determine_dirs(path, True, dirs)
                for d in dirs:
                    files = fnmatch.filter(os.listdir(d), "*S??E??*.*")
                    for f in files:
                        if f.endswith(".nfo"):
                            continue
                        parts = extract_season_episode(f)
                        if parts is None:
                            continue
                        s, e = parts
                        if (s in season_data) and (e in season_data[s]):
                            xml_path = os.path.join(d, os.path.splitext(f)[0] + ".nfo")
                            xml_str = season_data[s][e].toprettyxml(indent="  ")
                            if dry_run:
                                print(xml_str)
                            elif os.path.exists(xml_path) and not overwrite:
                                continue
                            with open(xml_path, "w") as xml_path:
                                xml_path.write(xml_str)

            else:
                logger.info("Has no episode data")

    return doc
