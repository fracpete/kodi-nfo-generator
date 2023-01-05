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

# imdb_series.py
# Copyright (C) 2021-2023 Fracpete (fracpete at gmail dot com)

import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from xml.dom import minidom
from kodi.xml_utils import add_node


AIRDATE_FORMAT = "%d %b. %Y"


# logging setup
logger = logging.getLogger("kodi.imdb")


def has_episodes(soup):
    """
    Checks whether episodes are available for this parsed IMDB page.

    :param soup: the parsed document
    :type soup: BeautifulSoup
    :return: whether episodes are available
    :rtype: bool
    """
    episodes = soup.find("a", href="episodes/?ref_=tt_ov_epl")
    return episodes is not None


def create_episodes_url(id, season=None):
    """
    Generates the URL for the episodes overview page.

    :param id: the IMDB ID
    :type id: str
    :param season: the optional season to use
    :type season: str
    :return: the generated URL
    :rtype: str
    """
    result = "https://www.imdb.com/title/%s/episodes/" % id
    if season is not None:
        result += "?season=%s" % season
    return result


def extract_seasons(soup):
    """
    Extracts the seasons from this parsed IMDB page.

    :param soup: the parsed document
    :type soup: BeautifulSoup
    :return: the list of seasons (strings)
    :rtype: list
    """
    result = []
    byseason = soup.find("select", id="bySeason")
    for option in byseason.find_all("option"):
        result.append(option["value"])
    return result


def extract_episodes(soup, season):
    """
    Extracts the data for each episode as dictionary.
    The unique ID is stored under "_uniqueid", the rating data under "_rating",
    all other keys are the relevant XML tags.

    :param soup: the parsed season page
    :type soup: BeautifulSoup
    :param season: the season of this page
    :type season: str
    :return: the dictionary with episodes (episode -> data dict)
    :rtype: dict
    """
    result = {}
    for ep_data_tag in soup.find_all("div", itemprop="episodes"):
        if ep_data_tag is None:
            continue

        # episode
        ep_tag = ep_data_tag.find("meta", itemprop="episodeNumber")
        if ep_tag is None:
            continue
        episode = ep_tag["content"].strip()

        # title
        title_tag = ep_data_tag.find("a", itemprop="name")
        if title_tag is None:
            continue
        title = title_tag.string.strip()

        # episode link
        uniqueid = title_tag["href"].replace("/title/", "")
        uniqueid = uniqueid[0:uniqueid.index("/")]

        # plot
        plot_tag = ep_data_tag.find("div", attrs={"itemprop": "description", "class": "item_description"})
        if (plot_tag is None) or (plot_tag.string is None):
            plot = None
        else:
            plot = plot_tag.string.strip()

        # air date
        airdate_tag = ep_data_tag.find("div", attrs={"class", "airdate"})
        if airdate_tag is None:
            airdate = None
        else:
            try:
                airdate = datetime.strptime(airdate_tag.string.strip(), AIRDATE_FORMAT)
            except:
                airdate = None

        # rating
        rating_tag = ep_data_tag.find("span", attrs={"class": "ipl-rating-star__rating"})
        if rating_tag is None:
            rating = None
        else:
            try:
                rating = float(rating_tag.string.strip())
            except:
                rating = None

        # votes
        votes_tag = ep_data_tag.find("span", attrs={"class": "ipl-rating-star__total-votes"})
        if votes_tag is None:
            votes = None
        else:
            try:
                votes = int(votes_tag.string.strip().replace("(", "").replace(")", "").replace(",", ""))
            except:
                votes = None

        # assemble episode data
        result[episode] = {
            "_uniqueid": uniqueid,
            "season": season,
            "episode": episode,
            "title": title,
            "plot": plot,
            "aired": airdate,
            "_rating": {
                "value": rating,
                "votes": votes,
            }
        }
    return result


def episode_to_xml(episode_data):
    """
    Generates an XML string from the episode data.

    :param episode_data: the dictionary with the data about the episode
    :type episode_data: dict
    :return: the generated XML DOM
    :rtype: minidom.Document
    """
    doc = minidom.Document()
    root = add_node(doc, doc, "episodedetails")
    for k in episode_data:
        if k.startswith("_"):
            continue
        if (k == "aired") and (episode_data[k] is not None):
            add_node(doc, root, k, episode_data[k].strftime("%Y-%m-%d"))
        else:
            add_node(doc, root, k, episode_data[k])
    if "_uniqueid" in episode_data:
        uniqueid = add_node(doc, root, "uniqueid", episode_data["_uniqueid"])
        uniqueid.setAttribute("type", "imdb")
        uniqueid.setAttribute("default", "true")
    if "_rating" in episode_data:
        ratings = add_node(doc, root, "ratings")
        rating = add_node(doc, ratings, "ratings")
        rating.setAttribute("name", "imdb")
        rating.setAttribute("max", "10")
        rating.setAttribute("default", "true")
        add_node(doc, rating, "value", str(episode_data["_rating"]["value"]))
        add_node(doc, rating, "votes", str(episode_data["_rating"]["votes"]))

    return doc


def extract_season_episode(path, season_group=".*S([0-9]?[0-9])E.*", episode_group=".*E([0-9]?[0-9]).*"):
    """
    Extracts season and episode from the file path (format: *S??E??*).

    :param path: the path to extract the season/episode from
    :type path: str
    :param season_group: the regular expression to extract the season (first group)
    :type season_group: str
    :param episode_group: the regular expression to extract the episode (first group)
    :type episode_group: str
    :return: the list of season/episode, None if no match
    :rtype: list
    """
    pattern_s = re.compile(season_group)
    pattern_e = re.compile(episode_group)
    match_s = pattern_s.match(path)
    match_e = pattern_e.match(path)
    if (match_s is None) or (match_e is None):
        return None
    result_s = match_s.groups()
    result_e = match_e.groups()
    if (len(result_s) == 1) and (len(result_e) == 1):
        return [str(int(result_s[0])), str(int(result_e[0]))]
    else:
        return None
