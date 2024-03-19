# -*- coding: utf-8 -*-
"""
This file contains functions that read the site configuration file.
"""
import os
import sys
from typing import Iterator
"""
try:
    from yaml import load, dump
    from yaml import CLoader as Loader, Dumper
except ModuleNotFoundError:
    print(("PyYAML is missing. "
           "Please install it with:\n\nyum install python36-PyYAML"))
    sys.exit(1)
"""
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
except ModuleNotFoundError:
    print(("ruamel is missing. "
           "Please install it with:\n\npython3 -m pip install --user -U ruamel.yaml"))
    sys.exit(1)


from clusterstor_tools.common import (
  confirm, get_logger, get_group_users, get_group_id )
from clusterstor_tools.dir_ops import check_dir_exists
from clusterstor_tools.quota_ops import check_quotadict, initialize_quotadict

def read_config(conf_filename: str) -> dict:
    """ This function loads a configuration from an yaml file."""
    with open(conf_filename, 'r') as conf_file:
        yaml_loader = YAML()
        conf = yaml_loader.load(conf_file)
    assert conf is not None, \
        "Problem loading configuration: Configuration file '{0}' was empty!".format(conf_filename)
    return conf


def write_config(conf_filename: str, config: YAML, dryrun: bool = True, skip_confirm: bool = False) -> bool:
    """ This function writes configuration to an yaml file."""
    
    logger = get_logger()
    
    assert isinstance(config, CommentedMap), \
           "Config should be a ruamel.yaml.comments.CommentedMap instance to preserve comments"
    
    write_file = True
    if not skip_confirm and os.path.isfile(conf_filename):
        write_file = confirm(
            "Overwrite configuration file '{0}?".format(conf_filename),
            default=True)
    if write_file:
        if dryrun:
            logger.debug("Dry run enabled, will not overwrite the "
                         "configuration '%s', but will continue.", conf_filename)
        else:
            yaml_writer = YAML()
            with open(conf_filename, 'w') as conf_file:
                yaml_writer.dump(config, conf_file)
    return write_file


def get_defaults(site_config: dict) -> dict:
    """ This function will provide the 'defaults' of the site configuration."""

    assert 'defaults' in site_config, "'defaults' was not found in site config."
    
    return site_config['defaults']


def get_mountpoint(site_config: dict) -> str:
    """ This function will provide the 'mountpoint'-key from 'defaults'."""

    defaults = get_defaults(site_config)
    assert 'mountpoint' in defaults, \
            "Value for 'mountpoint' was not found in site-config's 'defaults'."
    
    mountpoint = defaults['mountpoint']
    assert isinstance(mountpoint, str), \
            "Value of 'mountpoint' was not a string."
    assert check_dir_exists(mountpoint), \
            "Path for mountpoint {0} does not exist.".format(mountpoint)
    
    return mountpoint

def get_users_group(site_config: dict) -> str:
    """ This function will provide the 'users_group'-key from 'defaults'."""

    defaults = get_defaults(site_config)
    assert 'users_group' in defaults, \
            "Value for 'users_group' was not found in site-config's 'defaults'."
    
    users_group = defaults['users_group']
    assert isinstance(users_group, str), \
            "Value of 'users_group' was not a string."
    
    return users_group
    

def get_work_dir_name(site_config: dict) -> str:
    """ This function will provide the 'work_dir_name'-key from 'defaults'."""

    defaults = get_defaults(site_config)
    assert 'work_dir_name' in defaults, \
            "Value for 'work_dir_name' was not found in site-config's 'defaults'."

    work_dir_name = defaults['work_dir_name']
    assert isinstance(work_dir_name, str), \
            "Value of 'work_dir_name' was not a string."
    
    return work_dir_name


def get_dirstripe_count(site_config: dict) -> int:
    """ This function will provide the 'dirstripe_count'-key
    from 'defaults'."""

    defaults = get_defaults(site_config)
    assert 'dirstripe_count' in defaults, \
            "Key 'dirstripe_count' is missing from 'defaults'."

    dirstripe_count = defaults['dirstripe_count']
    assert isinstance(dirstripe_count, int), \
            "Value of 'dirstripe_count' is not an integer."

    return dirstripe_count


def get_stripe_parameter_reference(site_config: dict) -> str:
    """ This function will provide the loaded 'stripe_parameter_reference'. """

    defaults = get_defaults(site_config)
    
    assert 'stripe_parameter_reference' in defaults, \
            "Key 'stripe_parameter_reference' is missing from 'defaults'."

    stripe_parameter_reference = defaults['stripe_parameter_reference']
    assert isinstance(stripe_parameter_reference, str), \
            "Value of 'stripe_parameter_reference' is not a string."

    assert os.path.isfile(stripe_parameter_reference), \
            "Stripe parameter reference '{0}' does not exist".format(
                stripe_parameter_reference)
    
    with open(stripe_parameter_reference, 'r') as reference_file:
        reference = reference_file.read()

    return reference


def get_stripe_parameters(site_config: dict) -> str:
    """ This function will provide the 'stripe_parameters'-key
    from 'defaults'."""

    defaults = get_defaults(site_config)
    assert 'stripe_parameters' in defaults, \
            "Key 'stripe_parameters' is missing from 'defaults'."

    stripe_parameters = defaults['stripe_parameters']
    assert isinstance(stripe_parameters, str), \
            "Value of 'stripe_parameters' is not a string."

    return stripe_parameters


def get_default_quotas(site_config: dict) -> dict:
    """ This function will provide the default quotas from
    'defaults'."""

    defaults = get_defaults(site_config)

    assert 'default_quotas' in defaults, \
            "Key 'default_quotas' is missing from 'defaults'."

    default_quotas = defaults['default_quotas']

    assert isinstance(default_quotas, dict), \
            "Value of 'default_quotas' is not a dictionary."

    return default_quotas


def get_default_project_quotas(site_config: dict) -> dict:
    """ This function will provide the default project quotas from
    'default_quotas'."""

    default_quotas = get_default_quotas(site_config)

    assert 'projects' in default_quotas, \
            "Key 'projects' is missing from 'default_quotas'."

    default_project_quotas = default_quotas['projects']

    assert isinstance(default_project_quotas, dict), \
            "Value of 'projects' is not a dictionary."

    assert check_quotadict(default_project_quotas), \
        ("'projects' is not a proper quota "
         "dictionary: {0}").format(default_project_quotas)

    return default_project_quotas


def get_default_workdir_quotas(site_config: dict) -> dict:
    """ This function will provide the default workdir quotas from
    'default_quotas'."""

    default_quotas = get_default_quotas(site_config)

    assert 'workdir' in default_quotas, \
            "Key 'workdir' is missing from 'default_quotas'."

    default_workdir_quotas = default_quotas['workdir']

    assert isinstance(default_workdir_quotas, dict), \
            "Value of 'workdir' is not a dictionary."

    assert check_quotadict(default_workdir_quotas), \
        ("'workdir' is not a proper quota "
         "dictionary: {0}").format(default_workdir_quotas)

    return default_workdir_quotas



def get_project_dirs(site_config: dict) -> Iterator[dict]:
    """ This function constructs an information dictionary for each project directory."""

    mountpoint = get_mountpoint(site_config)

    stripe_parameters = get_stripe_parameters(site_config)
    stripe_parameter_reference = get_stripe_parameter_reference(site_config)

    default_project_quotas = get_default_project_quotas(site_config)

    for department_name, projects in site_config.get('project_dirs', {}).items():
        assert isinstance(projects, dict), \
                "Department '{0}' is not a dictionary.".format(department_name)
        for project_name, project_quota_dict in projects.items():

            quotadict = initialize_quotadict(
                project_quota_dict,
                default_project_quotas
            )

            assert check_quotadict(quotadict), \
                ("Quota for project '{0}' is not a proper quota "
                 "dictionary: {1}").format(project_name, quotadict)

            project_dir_info = {
                'mountpoint': mountpoint,
                'name': project_name,
                'path': os.path.join(mountpoint, department_name, project_name),
                'stripe_parameters': stripe_parameters,
                'stripe_parameter_reference': stripe_parameter_reference,
                'permissions': '2770',
                'quota': quotadict,
            }
            yield project_dir_info

def get_new_work_dir(site_config: dict, user: str) -> Iterator[dict]:
    """ This function constructs an information dictionary for each work directory."""
    
    logger = get_logger()

    try:
        user_id = get_group_id(user)
    except ValueError as e:
        logger.error('Could not find user "%s"', user)
        raise e

    assert isinstance(user_id, int), \
      'User id "%s" for user "%s" is invalid!' % (user_id, user)

    mountpoint = get_mountpoint(site_config)

    main_work_dir = get_main_work_dir(site_config)['path']
    
    stripe_parameters = get_stripe_parameters(site_config)
    stripe_parameter_reference = get_stripe_parameter_reference(site_config)
    
    workdir_quotas = site_config.get('work_dirs', {})
    
    default_workdir_quota = get_default_workdir_quotas(site_config)
    user_quota = workdir_quotas.get(user, {})

    quotadict = initialize_quotadict(
        user_quota,
        default_workdir_quota
    )
    
    work_dir_info = {
        'mountpoint': mountpoint,
        'name': user,
        'path': os.path.join(main_work_dir, user),
        'stripe_parameters': stripe_parameters,
        'stripe_parameter_reference': stripe_parameter_reference,
        'permissions': '2700',
        'quota': quotadict,
    }
    return work_dir_info

def get_work_dirs(site_config: dict) -> Iterator[dict]:
    """ This function constructs an information dictionary for each work directory."""

    mountpoint = get_mountpoint(site_config)

    main_work_dir = get_main_work_dir(site_config)['path']

    stripe_parameters = get_stripe_parameters(site_config)
    stripe_parameter_reference = get_stripe_parameter_reference(site_config)

    default_workdir_quota = get_default_workdir_quotas(site_config)

    workdir_quotas = site_config.get('work_dirs', {})

    users_group = get_users_group(site_config)

    for user in get_group_users(users_group):

        user_quota = workdir_quotas.get(user, {})

        quotadict = initialize_quotadict(
            user_quota,
            default_workdir_quota
        )

        assert check_quotadict(quotadict), \
            ("Quota for user '{0}' is not a proper quota "
             "dictionary: {1}").format(user, quotadict)

        work_dir_info = {
            'mountpoint': mountpoint,
            'name': user,
            'path': os.path.join(main_work_dir, user),
            'stripe_parameters': stripe_parameters,
            'stripe_parameter_reference': stripe_parameter_reference,
            'permissions': '2700',
            'quota': quotadict,
        }
        yield work_dir_info


def get_main_work_dir(site_config: dict) -> dict:
    """ This function constructs an information dictionary for the main work directory."""
    
    dirstripe_count = get_dirstripe_count(site_config)
    stripe_parameters = get_stripe_parameters(site_config)
    stripe_parameter_reference = get_stripe_parameter_reference(site_config)

    mountpoint = get_mountpoint(site_config)
    work_dir_name = get_work_dir_name(site_config)

    work_dir_path = os.path.join(mountpoint, work_dir_name)
    main_work = {
        'name': work_dir_name,
        'path': work_dir_path,
        'dirstripe_count': dirstripe_count,
        'stripe_parameters': stripe_parameters,
        'stripe_parameter_reference': stripe_parameter_reference,
    }

    return main_work

def get_department_dirs(site_config: dict) -> Iterator[dict]:
    """ This function constructs an information dictionary for each
    department directory."""

    dirstripe_count = get_dirstripe_count(site_config)
    stripe_parameters = get_stripe_parameters(site_config)
    stripe_parameter_reference = get_stripe_parameter_reference(site_config)

    mountpoint = get_mountpoint(site_config)
    for department_name, projects in site_config.get('project_dirs', {}).items():
        assert isinstance(projects, dict), \
                "Department '{0}' is not a dictionary.".format(department_name)
        department_dir = os.path.join(mountpoint, department_name)
        department_info = {
            'name': department_name,
            'path': department_dir,
            'dirstripe_count': dirstripe_count,
            'stripe_parameters': stripe_parameters,
            'stripe_parameter_reference': stripe_parameter_reference,
        }
        yield department_info
