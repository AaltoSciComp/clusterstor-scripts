# -*- coding: utf-8 -*-
"""
This file contains miscellaneous helper functions.
"""

import os
import re
import sys
import logging
from distutils.util import strtobool
from functools import lru_cache
from typing import Any, Callable, TypeVar, Tuple, cast, List

try:
    from sh import getent, ErrorReturnCode
except ModuleNotFoundError:
    print("python3 sh-module is missing. Please install it with:\n\n"
          "yum install python36-sh")
    sys.exit(1)


def create_logger(verbose: bool) -> None:
    """ This function sets the default logger. """

    logger = logging.getLogger('clusterstor')

    handler = logging.StreamHandler(sys.stdout)

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_logger():
    """ This function gives the default logger. """

    return logging.getLogger('clusterstor')

def confirm(verification_str: str, default: bool = False) -> bool:
    """ This function asks for a verification to a query. """

    response = default
    response_str = "[Y/n]" if default else "[y/N]"
    try:
        verification = input("{0} {1}\n".format(verification_str, response_str))
        response = bool(strtobool(verification))
    except ValueError:
        response = response

    return response

def pause_until_input() -> None:
    """ This function asks for confirmation until execution resumes. """
    input("Press RETURN to continue.")

def ask_for_continue() -> None:
    """ This function asks whether execution should continue. """
    if not confirm("Continue with execution?"):
        sys.exit(1)

def print_header(header: str) -> None:
    """ This helper function prints a very visible header. """

    logger = get_logger()

    separator = 60*'-'

    logger.info('\n%s\n%s\n%s', separator, header.upper(), separator)

def print_smallheader(header: str) -> None:
    """ This helper function prints a smaller header. """

    logger = get_logger()

    separator = len(header)*'-'

    logger.debug('\n%s\n%s\n', header, separator)

def print_warning(warning: str) -> None:
    """ This helper function prints a very visible warning. """

    logger = get_logger()
    warning = "WARNING: {0}".format(warning)
    separator = len(warning)*'#'
    logger.warning('\n%s\n%s\n%s\n', separator, warning, separator)


@lru_cache(maxsize=65536)
def stat_dir(dirname: str):
    """ This helper function stats a directory. """

    logger = get_logger()

    stat_response = None

    try:

        stat_response = os.stat(dirname)

    except FileNotFoundError as error:
        logger.warning("Could not stat directory '%s': %s", dirname, error)

    return stat_response


def get_dir_permissions(dirname: str) -> str:
    """ This helper function checks the permissions of a directory. """
    
    stat_response = stat_dir(dirname)

    if stat_response is not None:
        return oct(stat_response.st_mode)[-4:]
    
    return None


def get_dir_gid(dirname: str) -> int: 
    """ This helper function checks for a GID of a directory. """
    
    stat_response = stat_dir(dirname)

    if stat_response is not None:
        return stat_response.st_gid
    
    return None


def get_dir_uid(dirname: str) -> int: 
    """ This helper function checks for a UID of a directory. """
    
    stat_response = stat_dir(dirname)

    if stat_response is not None:
        return stat_response.st_uid
    
    return None


def check_dir_name(dirname: str) -> bool:
    """ This helper function checks that dirname has only allowed
    characters (a-zA-Z0-9_-). """

    match = re.match(r"^(/[\w-]+)+$", dirname)

    return match is not None


def check_dir_exists(dirname: str, dryrun: bool = True) -> bool:
    """ This helper function checks whether a directory already exists. """

    logger = get_logger()

    try:
        assert check_dir_name(dirname), \
               "Directory name '{0} has invalid characters!".format(dirname)

        assert os.path.isdir(os.path.dirname(dirname)), \
               'Base directory for folder {0} does not exist!'.format(dirname)

        assert os.path.isdir(dirname) or not os.path.exists(dirname), \
                "Path '{0}' exists, but it is not a directory!".format(dirname)
    except AssertionError as error:
        if dryrun:
            logger.debug(("Got an error '%s' with directory '%s', but will "
                          "continue due to dry-run."), error, dirname)
        else:
            raise error

    return os.path.isdir(dirname)


@lru_cache(maxsize=65536)
def get_group_id(group_name: str) -> int:
    """ This helper function returns group id for a group. Outputs are cached. """

    logger = get_logger()

    try:
        getent_output = getent('group', group_name)
    except ErrorReturnCode as error:
        logger.debug(f'Command "getent group {group_name}" failed. Trying "getent passwd {group_name}" instead.')
        try:
            getent_output = getent('passwd', group_name)
        except ErrorReturnCode as error:
            raise ValueError(f'Command "getent group {group_name}" and "getent passwd {group_name}" returned errors! Error:\n {error}')
    group_id = int(getent_output.split(':')[2])
    return group_id

@lru_cache(maxsize=65536)
def get_group_users(group_name: str) -> List[str]:
    """ This helper function returns users that belong to a group. Outputs are cached. """
    getent_output = getent('group', group_name) 
    group_users = getent_output.split(':')[3].strip().split(',')
    return group_users

# Type for decorated functions
F = TypeVar('F', bound=Callable[..., Any])

def catch_interrupt(func: F) -> F:
    """ This helper function catches keyboard interrupts for interactive functions. """
    
    def wrapper(*args, **kwargs):
        
        logger = get_logger()
    
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt as interrupt:
            logger.error('Interrupt obtained. Quitting.')
            sys.exit(1)

    return cast(F, wrapper)
