# -*- coding: utf-8 -*-
"""
This file contains functions that set the striping on directories.
"""

import sys

try:
    from sh import lfs
    from sh import ErrorReturnCode
except ModuleNotFoundError:
    print("python3 sh-module is missing. Please install it with:\n\n"
          "yum install python36-sh")
    sys.exit(1)

from clusterstor_tools.common import (
    confirm, check_dir_exists, get_logger, print_warning,
    pause_until_input)


def get_dirstripe_count(dirname: str, dryrun: bool = True) -> int:
    """ This function will produce the number of dirstripes that are
    set for a directory. """

    logger = get_logger()

    num_dirstripes = -1
    logger.debug("Checking dirstriping with: lfs getdirstripe -c %s", dirname)
    try:
        num_dirstripes = int(lfs("getdirstripe", "-c", dirname).strip())
    except ErrorReturnCode as error:
        if dryrun:
            logger.debug(error)
            logger.info(("Got an error '%s' with directory '%s', but will "
                         "continue due to dry-run."), error, dirname)
        else:
            raise error
    return num_dirstripes

def get_striping(dirname: str, dryrun: bool = True) -> str:
    """ This function will produce the striping information
    for a directory. """

    logger = get_logger()

    striping = 'No striping could be obtained!'
    logger.debug("Checking striping with: lfs getstripe -d --yaml %s", dirname)

    try:
        assert check_dir_exists(dirname)
        striping = str(lfs("getstripe", "-d", "--yaml", dirname).strip())
    except (ErrorReturnCode, AssertionError) as error:
        if dryrun:
            logger.debug(error)
            logger.info(("Got an error while checking striping for directory "
                         "%s', but will continue due to dry-run.\n"), dirname)
            return ''
        else:
            raise error
    return striping

def compare_striping(dirname: str,
                     stripe_reference: str,
                     dryrun: bool = True) -> bool:
    """ This function will compare the striping of a directory to a
    reference state."""


    logger = get_logger()

    current_striping = get_striping(dirname, dryrun).strip()
    reference_striping = stripe_reference.strip()

    stripe_match = current_striping == reference_striping

    if stripe_match:
        logger.debug(("Striping on directory '%s' matches to the "
                      "reference striping"), dirname)
    else:
        print_warning("Striping mismatch")
        logger.warning(("Striping on directory '%s' does not match to the "
                        "reference striping"), dirname)
        pause_until_input()

    return stripe_match

def set_striping(dirname: str,
                 striping_parameters: str,
                 dryrun: bool = True,
                 skip_confirm: bool = False) -> None:
    """ This function will set the striping on a folder. """

    logger = get_logger()

    striping_cmd = "setstripe {0} {1}".format(striping_parameters, dirname)

    if skip_confirm or confirm(("Setting striping for directory '{0}' with the following command:\n\n"
                "lfs setstripe {1}\n\n"
                "Is this ok?").format(dirname, striping_cmd), default=True):
        if dryrun:
            logger.debug(("Dry run enabled, will not set striping for "
                          "directory '%s', but will continue."), dirname)
        else:
            logger.info("Setting striping for directory: '%s'", dirname)
            lfs(*striping_cmd.split())
    else:
        print_warning("Striping might not be set correctly")
        if skip_confirm or confirm(("Do you want to view the striping information for "
                    "folder '{0}'").format(dirname), default=True):
            logger.info(
                "Striping for folder %s\n\n%s\n",
                dirname,
                get_striping(dirname, dryrun=dryrun))
            pause_until_input()
