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

# registry.py
# Copyright (C) 2026 Fracpete (fracpete at gmail dot com)

import argparse
import logging
import os
import traceback

from typing import Dict, List, Optional

from seppl import ClassListerRegistry, Plugin, get_class_name

# environment variable with comma-separated list of class listers to use
ENV_KODI_CLASS_LISTERS = "KODI_CLASS_LISTERS"

# environment variable with comma-separated list of class listers to exclude
ENV_KODI_CLASS_LISTERS_EXCL = "KODI_CLASS_LISTERS_EXCL"

# the default class listers to inspect (for development)
# can be overridden with KODI_CLASS_LISTERS environment variable
DEFAULT_KODI_CLASS_LISTERS = [
    "kodi.class_lister",
]

# environment variable with comma-separated list of class listers to provided ignored classes
ENV_KODI_CLASS_LISTERS_IGNORED = "KODI_CLASS_LISTERS_IGNORED"

# environment variable for managing the class cache: on|off|reset
ENV_KODI_CLASS_CACHE = "KODI_CLASS_CACHE"

# the default class listers that provide ignored classes
# can be overridden with KODI_CLASS_LISTERS_IGNORED environment variable
DEFAULT_KODI_CLASS_LISTERS_IGNORED = [
    "kodi.class_lister_ignored",
]

REGISTRY = ClassListerRegistry(default_class_listers=DEFAULT_KODI_CLASS_LISTERS,
                               env_class_listers=ENV_KODI_CLASS_LISTERS,
                               env_excluded_class_listers=ENV_KODI_CLASS_LISTERS_EXCL,
                               ignored_class_listers=DEFAULT_KODI_CLASS_LISTERS_IGNORED,
                               env_ignored_class_listers=ENV_KODI_CLASS_LISTERS_IGNORED,
                               app_name="image-dataset-converter",
                               class_cache_env=ENV_KODI_CLASS_CACHE)

IMG_REGISTRY = "kodi.registry"

_logger = None


LIST_APIS = "apis"
LIST_CUSTOM_CLASS_LISTERS = "custom-class-listers"
LIST_ENV_CLASS_LISTERS = "env-class-listers"
LIST_TYPES = [
    LIST_APIS,
    LIST_CUSTOM_CLASS_LISTERS,
    LIST_ENV_CLASS_LISTERS,
]


def logger() -> logging.Logger:
    """
    Returns the logger instance to use, initializes it if necessary.

    :return: the logger instance
    :rtype: logging.Logger
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(IMG_REGISTRY)
    return _logger


def available_apis() -> Dict[str, Plugin]:
    """
    Returns all available API plugins.

    :return: the dict of plugin objects
    :rtype: dict
    """
    return REGISTRY.plugins("kodi.api.MediaAPI", fail_if_empty=False)


def register_plugins(custom_class_listers: List[str] = None, excluded_class_listers: List[str] = None):
    """
    Registers all plugins.

    :param custom_class_listers: the list of custom class listers to use instead of env variable or default class listers
    :type custom_class_listers: list
    :param excluded_class_listers: the list of class listers to exclude
    :type excluded_class_listers: list
    """
    REGISTRY.custom_class_listers = custom_class_listers
    REGISTRY.excluded_class_listers = excluded_class_listers
    available_apis()


def _list(list_type: str, custom_class_listers: Optional[List[str]] = None, excluded_class_listers: Optional[List[str]] = None):
    """
    Lists various things on stdout.

    :param custom_class_listers: the list of custom class listers to use instead of env variable or default class listers
    :type custom_class_listers: list
    :param excluded_class_listers: the list of class listers to exclude
    :type excluded_class_listers: list
    :param list_type: the type of list to generate
    :type list_type: str
    """
    register_plugins(custom_class_listers=custom_class_listers, excluded_class_listers=excluded_class_listers)

    if list_type in [LIST_APIS]:
        if list_type == LIST_APIS:
            plugins = available_apis()
        else:
            raise Exception("Unhandled type: %s" % list_type)
        print("name: class")
        for name in plugins:
            print("%s: %s" % (name, get_class_name(plugins[name])))
    elif list_type == LIST_CUSTOM_CLASS_LISTERS:
        class_listers = REGISTRY.custom_class_listers
        print("custom class listers:")
        if class_listers is None:
            print("-none")
        else:
            for m in class_listers:
                print(m)
    elif list_type == LIST_ENV_CLASS_LISTERS:
        print("env class listers:")
        if REGISTRY.env_class_listers is None:
            print("-none-")
        else:
            class_listers = os.getenv(REGISTRY.env_class_listers)
            if class_listers is None:
                print("-none listed in env var %s-" % REGISTRY.env_class_listers)
            else:
                class_listers = class_listers.split(",")
                for m in class_listers:
                    print(m)


def main(args=None):
    """
    The main method for parsing command-line arguments.

    :param args: the commandline arguments, uses sys.argv if not supplied
    :type args: list
    """
    parser = argparse.ArgumentParser(
        description="For inspecting/querying the registry.",
        prog="kodi-nfo-registry",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--custom_class_listers", type=str, default=None, help="The comma-separated list of custom class listers to use.", required=False)
    parser.add_argument("-e", "--excluded_class_listers", type=str, default=None, help="The comma-separated list of class listers to exclude.", required=False)
    parser.add_argument("-l", "--list", choices=LIST_TYPES, default=None, help="For outputting various lists on stdout.", required=False)
    parsed = parser.parse_args(args=args)

    custom_class_listers = None
    if parsed.custom_class_listers is not None:
        custom_class_listers = parsed.custom_class_listers.split(",")

    if parsed.list is not None:
        _list(parsed.list, custom_class_listers=custom_class_listers)


def sys_main() -> int:
    """
    Runs the main function using the system cli arguments, and
    returns a system error code.

    :return: 0 for success, 1 for failure.
    """
    try:
        main()
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    main()
