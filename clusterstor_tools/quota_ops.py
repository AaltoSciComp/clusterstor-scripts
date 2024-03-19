# -*- coding: utf-8 -*-
"""
This file contains functions that check and modify the project quotas.
"""

import os
import re
import sys
from typing import Tuple

try:
    from sh import lfs
    from sh import ErrorReturnCode
except ModuleNotFoundError:
    print("python3 sh-module is missing. Please install it with:\n\n"
          "yum install python36-sh")
    sys.exit(1)


from clusterstor_tools.common import (
    confirm, get_logger, pause_until_input, print_warning, get_group_id)


DEFAULT_QUOTADICT = {'byte_quota': '0', 'inode_quota': '0'}
QUOTA_REGEX = re.compile(r'^(?P<value>(\d|\.)+)(?P<suffix>[kMGTPE]?)(?P<asterisk>[*]?)$')


def check_quotavalue(quotavalue: str) -> bool:
    """ This helper function checks that a string is a proper quota value. """

    quotamatch = QUOTA_REGEX.match(quotavalue)

    return quotamatch is not None


def check_quotadict(quotadict: dict) -> bool:
    """ This helper function checks that a dictionary is
    a proper quota dictionary. """

    logger = get_logger()

    try:
        assert 'byte_quota' in quotadict, \
            "'byte_quota' is missing from the quotadict"

        byte_quota = str(quotadict['byte_quota'])

        assert check_quotavalue(byte_quota), \
            "'byte_quota' is of invalid format: {0}".format(byte_quota)

        assert 'inode_quota' in quotadict, \
            "'inode_quota' is missing from the quotadict"

        inode_quota = str(quotadict['inode_quota'])

        assert check_quotavalue(inode_quota), \
            "'inode_quota' is of invalid format: {0}".format(inode_quota)

        assert len(quotadict) == 2, \
            "Quota dict has extraneous keys: '{0}'".format([quotadict.keys()])

    except AssertionError as error:
        logger.error(
            "Error encountred while checking quota dictionary: %s",
            error)
        return False

    return True


def get_absolute_quotadict(quotadict: dict) -> dict:
    """ This helper function converts quota dictionary the absolute numbers. """

    abs_quotadict = DEFAULT_QUOTADICT.copy()

    suffixmap = {
        '': 1,
        'k': 1024,
        'M': 1024**2,
        'G': 1024**3,
        'T': 1024**4,
        'P': 1024**5,
        'E': 1024**6,
    }

    for key in ('byte_quota', 'inode_quota'):
        quotastr = str(quotadict[key])
        try:
            quotamatch = QUOTA_REGEX.match(quotastr).groupdict()
            abs_quotadict[key] = str(int(float(quotamatch['value']) * suffixmap[quotamatch['suffix']]))
        except AttributeError:
            raise Exception("Problem matching quotastr '%s' from quotadict '%s'" % (quotastr, quotadict))

    return abs_quotadict


def initialize_quotadict(quotadict: dict, defaults: dict) -> dict:
    """ This helper function initializes a quotadict with defaults. """

    updated_quotadict = defaults.copy()
    updated_quotadict.update(quotadict)

    # Make all arguments strings
    for key in updated_quotadict:
        updated_quotadict[key] = str(updated_quotadict[key])

    return updated_quotadict


def generate_project_id(group_name: str, dryrun: bool = True) -> int:
    """ This function will generate a project ID that matches groups GID. """

    logger = get_logger()

    logger.debug("Checking group id for group '%s'.", group_name)

    group_id = 0

    try:
        group_id = get_group_id(group_name)
    except Exception as error:
        if dryrun:
            logger.debug(error)
            logger.info(("Got an error '%s' with group name '%s', but will "
                         "continue due to dry-run."), error, group_name)
        else:
            logger.error("Got an error with group name '%s'.", group_name)
            raise error

    return group_id


def get_project_id(dirname: str, dryrun: bool = True) -> Tuple[int, str]:
    """ This function will get a project id of a folder. """

    logger = get_logger()

    logger.debug("Checking project id for directory '%s'.", dirname)

    project_id = -1
    inheritance = False

    try:
        lfs_output = lfs('project', '-d', dirname).strip().split()
        project_id = int(lfs_output[0])
        inheritance = lfs_output[1] == 'P'
    except Exception as error:
        if dryrun:
            logger.debug(error)
            logger.info(("Got an error '%s' with directory '%s', but will "
                         "continue due to dry-run."), error, dirname)
        else:
            raise error

    return (project_id, inheritance)

def set_project_id(dirname: str,
                   group_name: int,
                   dryrun: bool = True,
                   skip_confirm: bool = False) -> None:
    """ This function will set the project ID on a folder based on group name. """

    logger = get_logger()

    project_id = generate_project_id(group_name, dryrun=dryrun)

    if skip_confirm or confirm(("Setting project ID of directory '{0}' to '{1}' with the "
                "following command:\n\n"
                "lfs project -p {1} -s {0}\n\n"
                "Is this ok?").format(dirname, project_id), default=True) :
        if dryrun:
            logger.debug(("Dry run enabled, will not set project ID for "
                          "directory '%s', but will continue."), dirname)
        else:
            logger.info("Setting project for directory: '%s'", dirname)
            lfs('project', '-p', project_id, '-s', dirname)
    else:
        print_warning("Project ID might not be set correctly")
        if skip_confirm or confirm(("Do you want to view the project id information for "
                    "folder '{0}'").format(dirname), default=True):

            current_project_id, inheritance = get_project_id(dirname, dryrun=dryrun)
            logger.info(
                "Project ID for folder '%s': '%s'\nInheritance enabled: %s",
                dirname,
                current_project_id,
                inheritance
            )
            pause_until_input()

def verify_set_project_id(dirname: str,
                          strict: bool = False,
                          dryrun: bool = True) -> bool:
    """ This function will check that project ID has been set
    with an inheritance flag.

    In strict mode, project ID is compared against actual group ID.
    Otherwise, project ID that is greater than 0 passes.
    """

    logger = get_logger()

    current_project_id, inheritance = get_project_id(dirname, dryrun)

    if strict:
        project_name = os.path.basename(dirname)
        reference_project_id = generate_project_id(project_name, dryrun)
        project_id_set = current_project_id == reference_project_id and inheritance
    else:
        project_id_set = current_project_id > 0 and inheritance


    if project_id_set:
        logger.debug(
            "Directory '%s' has a project ID and inheritance set",
            dirname)
    else:
        print_warning("Project ID mismatch")
        logger.warning(("Project ID on directory '%s' does not seem to be "
                        "set correctly:\n\n"
                        "Project ID: %s\nInheritance: %s\n"),
                       dirname,
                       current_project_id,
                       inheritance)
        pause_until_input()

    return project_id_set


def set_project_quota(dirname: str,
                      group_name: str,
                      quotadict: dict,
                      dryrun: bool = False,
                      skip_confirm: bool = False) -> bool:
    """ This function sets quota for a project. """

    logger = get_logger()

    project_id = generate_project_id(group_name, dryrun)

    quota_set = False

    try:
        assert check_quotadict(quotadict), \
               "Quota dictionary for project '{0}' is invalid!"

        cmd_args = ['setquota', '-p', str(project_id),
                    '--block-softlimit', quotadict['byte_quota'],
                    '--block-hardlimit', quotadict['byte_quota'],
                    '--inode-softlimit', quotadict['inode_quota'],
                    '--inode-hardlimit', quotadict['inode_quota'],
                    dirname]

        if skip_confirm or confirm(("Setting project quota of directory '{0}' with the "
                    "following command:\n\n"
                    "lfs {1}\n\n"
                    "Is this ok?").format(dirname, ' '.join(cmd_args)), default=True):
            if dryrun:
                logger.debug(("Dry run enabled, will not set quota for "
                              "project '%s', but will continue."), dirname)
            else:
                logger.info("Setting project for directory: '%s'", dirname)
                lfs(*cmd_args)
            quota_set = True
    except AssertionError as error:
        logger.error(
            "Error encountred while setting project quota: %s",
            error)
        if dryrun:
            logger.error("Dry run enabled, continuing despite of errors.")
            quota_set = True

    return quota_set


def get_project_quotadict(dirname: str, project_id: int, dryrun: bool = True) -> dict:
    """ This function gets quota for a project and will return the output as
    a quotadict. """

    logger = get_logger()
    
    logger.debug("Checking quota for project id '%d'.", project_id)

    quotadict = DEFAULT_QUOTADICT.copy()

    try:
        quota_cmd_output = lfs('quota', '-q', '-h', '-p', str(project_id), dirname)
        if 'is using default' in quota_cmd_output:
            quotadict['byte_usage'] = 0
            quotadict['byte_quota'] = 0
            quotadict['inode_usage'] = 0
            quotadict['inode_quota'] = 0
            logger.debug('Default quota was still set, interpreting as no quota set!')
        else:
            quota_output = quota_cmd_output.replace(dirname, '')
            quota_output = quota_output.splitlines()[-1].split()
            quotadict['byte_usage'] = quota_output[0]
            quotadict['byte_quota'] = quota_output[1]
            quotadict['inode_usage'] = quota_output[4]
            quotadict['inode_quota'] = quota_output[5]
        logger.debug(('Found the following quota: '
                      ' %s ') % quotadict)
    except Exception as error:
        if dryrun:
            logger.debug(error)
            logger.info(("Got an error '%s' when checking quota for "
                         "project '%d', but will "
                         "continue due to dry-run."), error, project_id)
        else:
            raise error

    return quotadict


def verify_project_quota(dirname: str,
                         group_name: str,
                         quotadict: dict,
                         dryrun: bool = False) -> bool:
    """ This function verifies that the quota for a project has been
    set correctly. """
    
    logger = get_logger()
    
    logger.debug("Verifying quota for project '%s'.", group_name)

    project_id = generate_project_id(group_name, dryrun)

    quota_correct = False

    try:
        assert check_quotadict(quotadict), \
               "Quota dictionary for project '{0}' is invalid!"
        
        set_quotadict = get_project_quotadict(dirname, project_id, dryrun)

        # Normalize quotadicts
        abs_quotadict = get_absolute_quotadict(quotadict)
        abs_set_quotadict = get_absolute_quotadict(set_quotadict)

        quota_correct = (
            abs_quotadict['byte_quota'] == abs_set_quotadict['byte_quota'] and
            abs_quotadict['inode_quota'] == abs_set_quotadict['inode_quota'])

        if not quota_correct:
            logger.info("Quota for directory '%s' does not match the expected "
                        "quota. Set byte quota: '%s' Expected byte quota: '%s' "
                        "Set inode quota: '%s' Expected inode quota: '%s'", dirname,
                        abs_set_quotadict['byte_quota'], abs_quotadict['byte_quota'],
                        abs_set_quotadict['inode_quota'], abs_quotadict['inode_quota'])
        else:
            logger.debug("Quota for directory '%s' is set correctly.", dirname)

    except AssertionError as error:
        logger.error(
            "Error encountred while setting project quota: %s",
            error)
        if dryrun:
            logger.error("Dry run enabled, continuing despite of errors.")
            quota_set = True

    return quota_correct
