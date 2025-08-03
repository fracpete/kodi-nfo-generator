import argparse
import logging

interactive = False


def setup_env(parsed: argparse.Namespace, logger: logging.Logger):
    """
    Sets up the processing environment.

    :param parsed: the parsed options
    :type parsed: argparse.Namespace
    :param logger: the logger to configure
    :type logger: logging.Logger
    """
    global interactive

    # interactive mode turns on verbose mode
    if hasattr(parsed, "interactive"):
        if parsed.interactive and not (parsed.verbose or parsed.debug):
            parsed.verbose = True
        interactive = parsed.interactive

    # configure logging
    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed.verbose:
        logging.basicConfig(level=logging.INFO)
    logger.debug(parsed)

    # environment

    if interactive:
        logger.info("Entering interactive mode")
