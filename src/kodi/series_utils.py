import fnmatch
import os
import re

from kodi.io_utils import determine_dirs


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
