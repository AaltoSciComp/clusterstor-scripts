# -*- coding: utf-8 -*-
"""
This file contains functions that create directories.
"""

import sys
import os

try:
    from sh import lfs, chmod, chown, chgrp
except ModuleNotFoundError:
    print("python3 sh-module is missing. Please install it with:\n\n"
          "yum install python36-sh")
    sys.exit(1)


from clusterstor_tools.common import (
    confirm, get_dir_gid, get_dir_uid, get_dir_permissions,
    ask_for_continue, check_dir_exists, print_warning, get_logger
    )
from clusterstor_tools.stripe_ops import get_dirstripe_count
from clusterstor_tools.quota_ops import generate_project_id

def create_dir(dirname: str, dryrun: bool = True, skip_confirm: bool = False) -> bool:
    """ This function creates a simple directory such as a project directory
    or user's work directory.
    """

    logger = get_logger()

    directory_created = False
    if check_dir_exists(dirname, dryrun=dryrun):
        logger.debug('Directory %s already exists. Skipping creation.', dirname)
    elif skip_confirm or confirm("Create directory '{0}'?".format(dirname), default=True):
        logger.info("Creating directory '%s'", dirname)
        if dryrun:
            logger.debug("Dry run enabled, will not create the "
                         "directory '%s', but will continue.", dirname)
        else:
            os.mkdir(dirname)
        directory_created = True

    return directory_created

def create_dirstriped_dir(dirname: str,
                          dirstripes: int,
                          dryrun: bool = True,
                          skip_confirm: bool = False) -> bool:
    """ This function creates a more complicated dirstriped directory
    such as a department directory. This function will warn the user
    if the number of dirstripes does not match the expected number.

    By setting the number of dirstripes to 2 to a directory "dirname" will
    cause all directories created under this directory to be placed on either
    one of the MDTs. This is called Distributed NamespacE (DNE) and it
    improves:

    a) performance of the system as two MDSs can serve the querie
    b) balancing on Data on Metadata (DoM) as data is stored on all MDTs

    Will return True, if directory has been created.
    """

    logger = get_logger()

    directory_created = False

    if check_dir_exists(dirname, dryrun=dryrun):

        logger.debug("Directory %s already exists. Skipping creation.",
                     dirname)
        current_dirstripes = get_dirstripe_count(dirname, dryrun=dryrun)

        if dirstripes != current_dirstripes:

            print_warning("Dirstripe mismatch!")

            logger.warning(
                ("Dirstripe count for directory '%s' of %s does "
                 "not match the expected value of %s.\n"
                 "This will result in performance problems.\n"
                 "Please re-create the folder.\n"),
                dirname, current_dirstripes, dirstripes)

            ask_for_continue()

    elif skip_confirm or confirm(("Creating dirstriped directory with the following command:\n\n"
                  "lfs setdirstripe -c {0} -i -1 {1}\n\n"
                  "Is this ok?").format(dirstripes, dirname), default=True):

        if dryrun:
            logger.debug(
                ("Dry run enabled, will not create dirstriped "
                 "directory '%s', but will continue."),
                dirname)
        else:
            logger.info("Creating dirstriped directory: '%s'", dirname)
            lfs('setdirstripe', '-c', dirstripes, '-i', '-1', dirname)

        directory_created = True
    return directory_created

def set_dir_owner(dirname: str,
                  user_name: str,
                  dryrun: bool = True,
                  skip_confirm: bool = False) -> bool:

    logger = get_logger()

    ownership_set = False

    try:
        assert check_dir_exists(dirname, dryrun=dryrun), \
            "Cannot set ownership for directory {0}, it does not exist!".format(dirname)
    except AssertionError as error:
        if dryrun:
            logger.debug(("Got an error '%s' with directory '%s', but will "
                          "continue due to dry-run."), error, dirname)
        else:
            raise error

    user_id = generate_project_id(user_name, dryrun=dryrun)

    current_uid = get_dir_uid(dirname)

    if current_uid == user_id:
        logger.debug(
            "Directory '%s' has correct group ownership.",
            dirname)
    elif skip_confirm or confirm(("Setting user ownership with the following command:\n\n"
                  "chown -h {0} {1}\n\n"
                  "Is this ok?").format(user_name, dirname), default=True):
        if dryrun:
            logger.debug(
                ("Dry run enabled, will not set ownership for "
                 "directory '%s', but will continue."),
                dirname)
        else:
            logger.info("Setting ownership for directory: '%s'", dirname)
            chown('-h', user_name, dirname)

        ownership_set = True

    return ownership_set

def set_dir_group(dirname: str,
                  group_name: str,
                  dryrun: bool = True,
                  skip_confirm: bool = False) -> bool:

    logger = get_logger()

    ownership_set = False

    try:
        assert check_dir_exists(dirname, dryrun=dryrun), \
            "Cannot set ownership for directory {0}, it does not exist!".format(dirname)
    except AssertionError as error:
        if dryrun:
            logger.debug(("Got an error '%s' with directory '%s', but will "
                          "continue due to dry-run."), error, dirname)
        else:
            raise error

    group_id = generate_project_id(group_name, dryrun=dryrun)

    current_gid = get_dir_gid(dirname)

    if current_gid == group_id:
        logger.debug(
            "Directory '%s' has correct group ownership.",
            dirname)
    elif skip_confirm or confirm(("Setting group ownership with the following command:\n\n"
                  "chgrp -h {0} {1}\n\n"
                  "Is this ok?").format(group_name, dirname), default=True):
        if dryrun:
            logger.debug(
                ("Dry run enabled, will not set ownership for "
                 "directory '%s', but will continue."),
                dirname)
        else:
            logger.info("Setting ownership for directory: '%s'", dirname)
            chgrp(group_name, dirname)

        ownership_set = True

    return ownership_set

def set_dir_permissions(dirname: str,
                        permissions: str,
                        dryrun: bool = True,
                        skip_confirm: bool = False) -> bool:

    logger = get_logger()

    permissions_set = False

    try:
        assert check_dir_exists(dirname, dryrun=dryrun), \
            "Cannot set ownership for directory {0}, it does not exist!".format(dirname)
    except AssertionError as error:
        if dryrun:
            logger.debug(("Got an error '%s' with directory '%s', but will "
                          "continue due to dry-run."), error, dirname)
    

    current_permissions = get_dir_permissions(dirname)
    
    if current_permissions == permissions:
        logger.debug(
            "Directory '%s' has correct permissions.",
            dirname)
    elif skip_confirm or confirm(("Setting permissions with the following command:\n\n"
                  "chmod {0} {1}\n\n"
                  "Is this ok?").format(permissions, dirname), default=True):
        if dryrun:
            logger.debug(
                ("Dry run enabled, will not set permissions for "
                 "directory '%s', but will continue."),
                dirname)
        else:
            logger.info("Setting permissions for directory: '%s'", dirname)
            chmod(permissions, dirname)

        permissions_set = True

    return permissions_set
