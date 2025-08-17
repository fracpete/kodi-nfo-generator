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

# Copyright (C) 2021-2025 Fracpete (fracpete at gmail dot com)

import fnmatch
import logging
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
from xml.dom import minidom
from kodi.xml_utils import add_node
from kodi.io_utils import determine_dirs


AIRDATE_FORMAT = "%d %b. %Y"


# logging setup
logger = logging.getLogger("kodi.imdb")


def has_episodes(j):
    """
    Checks whether episodes are available for this parsed IMDB page.

    :param j: the json data
    :type j: dict
    :return: whether episodes are available
    :rtype: bool
    """
    return ("@type" in j) and (j["@type"] == "TVSeries")


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

    # dropdown for seasons
    seasons = soup.find("select", id="bySeason")
    if seasons is not None:
        logger.info("Season using dropdown")
        for option in seasons.find_all("option"):
            result.append(option["value"])
        return result

    # buttons for seasons
    seasons = soup.find_all("li", attrs={"data-testid": "tab-season-entry"})
    if seasons is not None:
        logger.info("Season using buttons")
        for li in seasons:
            result.append(li.text)
        return result

    logger.warning("Failed to get seasons from HTML!")
    return result


def extract_episodes_html(soup, season):
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

    # episodes div-based
    tags = soup.find_all("div", itemprop="episodes")
    if (tags is not None) and (len(tags) > 0):
        logger.info("extract_episodes: episodes-div based")
        for ep_data_tag in tags:
            if ep_data_tag is None:
                continue

            # episode
            ep_tag = ep_data_tag.find("meta", itemprop="episodeNumber")
            if ep_tag is None:
                logger.debug("No episode number tag found")
                continue
            episode = ep_tag["content"].strip()

            # title
            title_tag = ep_data_tag.find("a", itemprop="name")
            if title_tag is None:
                logger.debug("No title tag found")
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
        logger.info("episodes: %s" % ", ".join(sorted(result.keys(), key=int)))
        return result

    # episode-item-wrapper-based
    tags = soup.find_all("article", attrs={"class": "episode-item-wrapper"})
    if tags is not None:
        logger.info("extract_episodes: episode-item-wrapper based")
        regexp_ep = ".*ttep_ep([0-9]+)"
        pattern_ep = re.compile(regexp_ep)
        regexp_ep2 = ".*ttep_ep_([0-9]+)"
        pattern_ep2 = re.compile(regexp_ep2)
        for article in tags:
            # title
            title_tag = article.find("a", attrs={"class": "ipc-lockup-overlay"})
            if title_tag is None:
                continue
            title = title_tag["aria-label"]

            # episode
            href = title_tag["href"]
            if "ttep_ep_" in href:
                logger.debug("Applying pattern: %s" % regexp_ep2)
                match_ep = pattern_ep2.match(href)
                if match_ep is None:
                    logger.debug("No match")
                    continue
                result_ep = match_ep.groups()
                episode = result_ep[0]
                logger.debug("Episode: %s" % episode)
            elif "ttep_ep" in href:
                logger.debug("Applying pattern: %s" % regexp_ep)
                match_ep = pattern_ep.match(href)
                if match_ep is None:
                    logger.debug("No match")
                    continue
                result_ep = match_ep.groups()
                episode = result_ep[0]
                logger.debug("Episode: %s" % episode)
            else:
                continue
            # episode = None

            # episode link
            uniqueid = title_tag["href"].replace("/title/", "")
            uniqueid = uniqueid[0:uniqueid.index("/")]

            # plot
            plot_tag = article.find("div", attrs={"class": "ipc-html-content-inner-div"})
            if plot_tag is None:
                plot = ""
            else:
                plot = plot_tag.text

            # air date
            airdate = None
            span_tags = article.find_all("span")
            if span_tags is not None:
                for span_tag in span_tags:
                    try:
                        airdate = datetime.strptime(span_tag.text.strip(), "%B %d, %Y")
                        break
                    except:
                        pass

            # rating
            rating = None
            rating_tag = article.find("span", attrs={"class": "ipc-rating-star"})
            if (rating_tag is not None) and ("aria-label" in rating_tag):
                s = rating_tag["aria-label"]
                s = s[s.index(":") + 1:]
                rating = float(s)

            # votes
            # not available anymore?

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
                }
            }
        logger.info("episodes: %s" % ", ".join(sorted(result.keys(), key=int)))
        return result

    if len(result) == 0:
        logger.warning("No episode data extracted!")

    return result


def _find_episodes_json(j, key):
    """
    Locates the seasons data recursively in the JSON data.

    :param j: the json data to process
    :type j: dict
    :param key: the seasons key to look for
    :type key: str
    :return: the seasons data or None if not found
    :rtype: dict
    """
    for k in j.keys():
        if k == key:
            return j[k]
        if isinstance(j[k], dict):
            res = _find_episodes_json(j[k], key)
            if res is not None:
                return res
    return None


def extract_episodes_json(j):
    """
    Extracts the data for each episode as dictionary.
    The unique ID is stored under "_uniqueid", the rating data under "_rating",
    all other keys are the relevant XML tags.

    :param j: the json data to use
    :type j: dict
    :return: the dictionary with episodes (episode -> data dict)
    :rtype: dict
    """
    result = {}
    data = _find_episodes_json(j, "episodes")
    if "items" in data:
        for item in data["items"]:
            season = item["season"]
            episode = item["episode"]
            result[episode] = {
                "_uniqueid": item["id"],
                "season": season,
                "episode": episode,
                "title": item["titleText"],
            }
            if "plot" in item:
                result[episode]["plot"] = item["plot"]
            if "aired" in item:
                result[episode]["aired"] = datetime(item["releaseDate"]["year"], month=item["releaseDate"]["month"], day=item["releaseDate"]["day"])
            if ("aggregateRating" in item) and ("voteCount" in item):
                result[episode]["_rating"] = {
                    "value": item["aggregateRating"],
                    "votes": item["voteCount"],
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
        if "votes" in episode_data["_rating"]:
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


def determine_episodes(path, episode_pattern="*S??E??*.*",
                       season_group=".*S([0-9]?[0-9])E.*", episode_group=".*E([0-9]?[0-9]).*"):
    """
    Locates all episodes on disk and associates them with their season.

    :param path: the directory to scan
    :type path: str
    :param episode_pattern: the pattern(s) to use for locating episode files
    :type episode_pattern: str or list
    :param season_group: the regular expression to extract the season (first group)
    :type season_group: str
    :param episode_group: the regular expression to extract the episode (first group)
    :type episode_group: str
    :return: the dictionary of episodes (key is the season)
    :rtype: dict
    """
    result = dict()
    dirs = list()
    if isinstance(episode_pattern, str):
        episode_pattern = [episode_pattern]
    determine_dirs(path, True, dirs)
    for d in dirs:
        for epattern in episode_pattern:
            files = fnmatch.filter(os.listdir(d), epattern)
            for f in files:
                parts = extract_season_episode(f, season_group=season_group, episode_group=episode_group)
                if parts is None:
                    continue
                s, e = parts
                if s not in result:
                    result[s] = list()
                if e not in result[s]:
                    result[s].append(e)
    return result
