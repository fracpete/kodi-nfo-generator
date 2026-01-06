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

# Copyright (C) 2020-2026 Fracpete (fracpete at gmail dot com)

import argparse
import json

from bs4 import BeautifulSoup
import fnmatch
import logging
import os
import requests
import time
import traceback
from xml.dom import minidom
from kodi.env import setup_env, interactive
from kodi.io_utils import determine_dirs, prompt, read_id, TAG_MOVIE, TAG_TVSHOW, FILENAME_TVSHOW, get_nfo_file, \
    json_loads, output_str, skip, proceed
from kodi.utils import find_sub_dict, get_nested_value
from kodi.xml_utils import add_node, output_xml
from ._series import has_episodes, create_episodes_url, extract_seasons, extract_episodes_html, episode_to_xml, \
    extract_season_episode, determine_episodes, extract_episodes_json

# logging setup
logger = logging.getLogger("kodi.imdb")


def iterate_imdb(ns: argparse.Namespace):
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

    episode_pattern = ns.episode_pattern
    if isinstance(episode_pattern, str):
        episode_pattern = [episode_pattern]

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
                file_generated = generate_imdb(id, language=ns.language, fanart=ns.fanart, fanart_file=ns.fanart_file,
                                               path=d, overwrite=ns.overwrite, dry_run=ns.dry_run,
                                               episodes=ns.episodes, episode_pattern=episode_pattern,
                                               season_group=ns.season_group, episode_group=ns.episode_group,
                                               multi_episodes=ns.multi_episodes, ua=ns.user_agent)
            except Exception:
                logger.info(traceback.format_exc())

            if interactive and not proceed():
                break
            if file_generated and (delay > 0):
                time.sleep(delay)


def generate_imdb(tid, language="en", fanart="none", fanart_file="folder.jpg", path=None, overwrite=False, dry_run=False,
                  episodes=False, episode_pattern="*S??E??*.*",
                  season_group=".*S([0-9]?[0-9])E.*", episode_group=".*E([0-9]?[0-9]).*",
                  multi_episodes=False, ua="Mozilla"):
    """
    Generates the XML for the specified IMDB ID.

    :param tid: the IMDB ID to use
    :type tid: str
    :param language: the preferred language for the titles
    :type language: str
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
    :param episodes: whether to generate episode information as well
    :type episodes: bool
    :param episode_pattern: the pattern(s) to use for locating episode files
    :type episode_pattern: str or list
    :param season_group: the regular expression to extract the season (first group)
    :type season_group: str
    :param episode_group: the regular expression to extract the episode (first group)
    :type episode_group: str
    :param multi_episodes: whether to output multi-episode.nfo files instead of single-episode files
    :type multi_episodes: bool
    :param ua: the user agent to use, ignore if empty string or None
    :type ua: str
    :return: whether a file was generated
    :rtype: bool
    """
    tid = tid.strip()

    if isinstance(episode_pattern, str):
        episode_pattern = [episode_pattern]

    # can we skip?
    if not overwrite:
        f = get_nfo_file(path)
        if f is not None:
            logger.info(".nfo file already exists, skipping: %s" % f)
            return False

    # default movie .nfo
    xml_path = os.path.join(path, os.path.basename(path) + ".nfo")
    xml_path_multi = os.path.join(path, "multi-episode.nfo")

    # generate URL
    if tid.startswith("http"):
        url = tid
    else:
        url = "https://www.imdb.com/title/%s/" % tid
    logger.info("IMDB URL: " + url)

    # retrieve html
    headers = {"Accept-Language": language}
    if (ua is not None) and (ua != ""):
        headers['user-agent'] = ua
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
        return False

    # parse html
    soup = BeautifulSoup(r.content, "html.parser")

    doc = minidom.Document()
    doc_multi = []
    root = None

    widget = soup.find("div", id="star-rating-widget")
    if widget is None:
        preflang_title = None
    else:
        preflang_title = widget["data-title"]

    has_actors = False

    output_generated = False
    for script in soup.findAll("script", type="application/ld+json"):
        j = json_loads(script.text)
        logger.debug(json.dumps(j))

        root = add_node(doc, doc, TAG_MOVIE)
        add_node(doc, root, "title", j['name'] if preflang_title is None else preflang_title)
        add_node(doc, root, "originaltitle", j["name"])
        uniqueid = add_node(doc, root, "uniqueid", j["url"].replace("/title/", "").replace("/", ""))
        uniqueid.setAttribute("type", "imdb")
        uniqueid.setAttribute("default", "true")
        if "description" in j:
            add_node(doc, root, "plot", j["description"])
            add_node(doc, root, "outline", j["description"])
        if "contentRating" in j:
            add_node(doc, root, "mpaa", j["contentRating"])
        if "datePublished" in j:
            add_node(doc, root, "premiered", j["datePublished"])
        for director in j.get("director", ()):
            if "name" in director:
                add_node(doc, root, "director", director["name"])
        if "genre" in j:
            if isinstance(j["genre"], list):
                for genre in j["genre"]:
                    add_node(doc, root, "genre", genre)
            else:
                add_node(doc, root, "genre", j["genre"])
        for actor in j.get("actor", ()):
            xactor = add_node(doc, root, "actor")
            add_node(doc, xactor, "name", actor["name"])
            has_actors = True
        if "trailer" in j and "embedUrl" in j["trailer"]:
            add_node(doc, root, "trailer", j["trailer"]["embedUrl"])
        if "aggregateRating" in j and "ratingValue" in j["aggregateRating"]:
            xratings = add_node(doc, root, "ratings")
            xrating = add_node(doc, xratings, "rating")
            xrating.setAttribute("name", "imdb")
            xrating.setAttribute("max", "10")
            add_node(doc, xrating, "value", str(j["aggregateRating"]["ratingValue"]))

        # fanart
        fanart_path = os.path.join(path, fanart_file)
        fanart_act = fanart
        if fanart_act == "download-missing":
            if os.path.exists(fanart_path):
                fanart_act = "use-existing"
            else:
                fanart_act = "download"
        if fanart_act == "download":
            if "image" in j:
                logger.info("Downloading fanart: %s" % j["image"])
                if (ua is not None) and (ua != ""):
                    r = requests.get(j["image"], headers={'user-agent': ua}, stream=True)
                else:
                    r = requests.get(j["image"], stream=True)
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

        if has_episodes(j):
            logger.info("Has episode data")

            # use special name rather than name-based one
            xml_path = os.path.join(path, FILENAME_TVSHOW)

            # update root tag
            root.tagName = TAG_TVSHOW

            if episodes:
                # determine seasons
                url = create_episodes_url(tid)
                logger.info("Default episodes URL: %s" % url)
                r = requests.get(url, headers={"Accept-Language": language, 'user-agent': ua})
                if r.status_code != 200:
                    logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
                    continue
                soup_ep = BeautifulSoup(r.content, "html.parser")
                seasons = extract_seasons(soup_ep)
                logger.info("Available seasons: %s" % ", ".join(seasons))

                # determine seasons
                seasons_episodes = determine_episodes(path, episode_pattern=episode_pattern,
                                                      season_group=season_group, episode_group=episode_group)
                try:
                    seasons_sorted = sorted(seasons_episodes.keys(), key=int)
                except:
                    seasons_sorted = sorted(seasons_episodes.keys())
                logger.info("Located seasons: %s" % ", ".join(seasons_sorted))

                # extract episodes for seasons on disk
                season_data = {}
                for season in seasons_sorted:
                    season_data[season] = {}
                    url = create_episodes_url(tid, season=season)
                    logger.info("Season %s URL: %s" % (season, url))
                    r = requests.get(url, headers={"Accept-Language": language, 'user-agent': ua})
                    if r.status_code != 200:
                        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))
                        continue
                    soup_ep = BeautifulSoup(r.content, "html.parser")

                    # 1. episode data in json available?
                    use_fallback = False
                    for ep_script in soup_ep.findAll("script", type="application/json"):
                        ep_j = json_loads(ep_script.text)
                        episodes_data = extract_episodes_json(ep_j)
                        if len(episodes_data) == 0:
                            use_fallback = True
                        else:
                            for k in episodes_data:
                                xml = episode_to_xml(episodes_data[k])
                                season_data[season][k] = xml

                    # 2. HTML fallback
                    if use_fallback:
                        episodes_data = extract_episodes_html(soup_ep, season)
                        for k in episodes_data:
                            xml = episode_to_xml(episodes_data[k])
                            season_data[season][k] = xml

                # locate files and output XML
                dirs = []
                determine_dirs(path, True, dirs)
                for d in dirs:
                    for epattern in episode_pattern:
                        files = fnmatch.filter(os.listdir(d), epattern)
                        for f in files:
                            if f.endswith(".nfo"):
                                continue
                            parts = extract_season_episode(f, season_group=season_group, episode_group=episode_group)
                            if parts is None:
                                continue
                            s, e = parts
                            if (s in season_data) and (e in season_data[s]):
                                if multi_episodes:
                                    xml_lines = season_data[s][e].toprettyxml(indent="  ").strip().split("\n")
                                    if (len(doc_multi) > 0) and ("<?xml" in xml_lines[0]):
                                        xml_lines = xml_lines[1:]
                                    doc_multi.extend(xml_lines)
                                else:
                                    xml_path_ep = os.path.join(d, os.path.splitext(f)[0] + ".nfo")
                                    if output_xml(season_data[s][e], xml_path_ep, dry_run=dry_run, overwrite=overwrite, logger=logger):
                                        output_generated = True

    # fallback available?
    if root is not None:
        if not has_actors:
            for script in soup.findAll("script", type="application/json"):
                j = json_loads(script.text)
                cast = find_sub_dict(j, "castPageTitle")
                if cast is None:
                    logger.debug("castPageTitle dict not found")
                    logger.debug(json.dumps(j))
                    continue
                logger.debug(json.dumps(cast))
                if "edges" in cast:
                    for a in cast["edges"]:
                        name = get_nested_value(a, ["node", "name", "nameText", "text"])
                        xactor = add_node(doc, root, "actor")
                        add_node(doc, xactor, "name", name)

    # output .nfo
    if multi_episodes:
        doc_multi = "\n".join(doc_multi)
        if output_str(doc_multi, xml_path_multi, dry_run=dry_run, overwrite=overwrite, logger=logger):
            output_generated = True
    if output_xml(doc, xml_path, dry_run=dry_run, overwrite=overwrite, logger=logger):
        output_generated = True

    return output_generated


def iterate_guess_imdb(ns: argparse.Namespace):
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
            guess_imdb(dname, meta_path, language=ns.language, dry_run=ns.dry_run, ua=ns.user_agent)
        except Exception:
            logger.info(traceback.format_exc())


def guess_imdb(title, meta_path, language="en", dry_run=False, ua="Mozilla"):
    """
    Generates .imdb files using the user's selection of IMDB search results for the title.

    :param title: the title to look for
    :type title: str
    :param meta_path: the file to store the IMDB title ID in
    :type meta_path: str
    :param language: the preferred language for the titles
    :type language: str
    :param dry_run: whether to perform a 'dry-run', ie generating .nfo content but not saving them (only outputting them to stdout)
    :type dry_run: bool
    :param ua: the user agent to use, ignore if empty string or None
    :type ua: str
    :return: whether to continue
    :rtype: bool
    """
    url = "https://www.imdb.com/find/"
    params = {'q': title}
    headers = {"Accept-Language": language}
    if (ua is not None) and (ua != ""):
        headers['user-agent'] = ua
    r = requests.get(url, params=params, headers=headers)
    if r.status_code != 200:
        logging.critical("Failed to retrieve URL (status code %d): %s" % (r.status_code, url))

    # in case we are overwriting files
    tid = None
    if os.path.exists(meta_path):
        tid = read_id(meta_path)

    # parse html
    soup = BeautifulSoup(r.content, "html.parser")

    for script in soup.findAll("script", id="__NEXT_DATA__", type="application/json"):
        j = json_loads(script.text)
        logger.debug(j)
        if ("props" not in j) or ("pageProps" not in j["props"]) or ("titleResults" not in j["props"]["pageProps"]):
            continue
        title_results = j["props"]["pageProps"]["titleResults"]
        if "results" in title_results:
            choices = []
            if len(title_results["results"]) == 0:
                print("0. No results, continue...")
            else:
                for i, result in enumerate(title_results["results"], start=1):
                    # marker for current title?
                    if (tid is not None) and (tid == result["id"]):
                        current = " <-- current"
                    else:
                        current = ""
                    print("%d. %s: %s%s" % (i, result["id"], result["titleNameText"], current))
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
                tid = title_results["results"][int(choice)-1]["id"]
                if dry_run:
                    print(tid)
                else:
                    logger.info("Writing ID %s to: %s" % (tid, meta_path))
                    with open(meta_path, "w") as f:
                        f.write(tid)
                return True
