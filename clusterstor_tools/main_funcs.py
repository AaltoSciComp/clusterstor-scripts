#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from clusterstor_tools.common import (
    catch_interrupt, print_smallheader)
from clusterstor_tools.dir_ops import (
    create_dir, set_dir_owner, set_dir_group, set_dir_permissions)
from clusterstor_tools.stripe_ops import set_striping, compare_striping
from clusterstor_tools.quota_ops import (
    set_project_id, verify_set_project_id,
    set_project_quota, verify_project_quota)

@catch_interrupt
def create_project_dir(project_info: dict = None,
                       redo_striping: bool = None,
                       redo_project_ids: bool = None,
                       redo_quotas: bool = None,
                       redo_ownerships: bool = None,
                       strict_project_checking: bool = None,
                       dryrun: bool = True) -> None:
    """ Create project directory. """
    print_smallheader(
        "Working with project: '{0}'".format(project_info['name']))
    directory_created = create_dir(
        project_info['path'],
        dryrun=dryrun)
    if (directory_created or
        (redo_striping and
         not compare_striping(
                project_info['path'],
                project_info['stripe_parameter_reference']))):
            set_striping(
                project_info['path'],
                project_info['stripe_parameters'],
                dryrun=dryrun)
    if (directory_created or
        (redo_project_ids and
         not verify_set_project_id(
                project_info['path'],
                strict=strict_project_checking,
                dryrun=dryrun))):
        set_project_id(
            project_info['path'],
            project_info['name'],
            dryrun=dryrun)
    if (directory_created or redo_ownerships):
        set_dir_group(
            project_info['path'],
            project_info['name'],
            dryrun=dryrun)
        set_dir_permissions(
            project_info['path'],
            project_info['permissions'],
            dryrun=dryrun)
    if (directory_created or
        (redo_quotas and
         not verify_project_quota(
            project_info['path'],
            project_info['name'],
            project_info['quota'],
            dryrun=dryrun))):
        set_project_quota(
            project_info['path'],
            project_info['name'],
            project_info['quota'],
            dryrun=dryrun)

@catch_interrupt
def create_work_dir(workdir_info: dict = None,
                    redo_striping: bool = None,
                    redo_project_ids: bool = None,
                    redo_quotas: bool = None,
                    redo_ownerships: bool = None,
                    strict_project_checking: bool = None,
                    dryrun: bool = True,
                    skip_confirm: bool = False) -> None:
    """ Creates a work directory for user. """
    print_smallheader(
        "Working with user: '{0}'".format(workdir_info['name']))
    directory_created = create_dir(
        workdir_info['path'],
        dryrun=dryrun,
        skip_confirm=skip_confirm)
    if (directory_created or
        (redo_striping and
         not compare_striping(
                workdir_info['path'],
                workdir_info['stripe_parameter_reference']))):
            set_striping(
                workdir_info['path'],
                workdir_info['stripe_parameters'],
                dryrun=dryrun,
                skip_confirm=skip_confirm)
    if (directory_created or
        (redo_project_ids and
         not verify_set_project_id(
                workdir_info['path'],
                strict=strict_project_checking,
                dryrun=dryrun))):
        set_project_id(
            workdir_info['path'],
            workdir_info['name'],
            dryrun=dryrun,
            skip_confirm=skip_confirm)
    if (directory_created or redo_ownerships):
        set_dir_owner(
            workdir_info['path'],
            workdir_info['name'],
            dryrun=dryrun,
            skip_confirm=skip_confirm)
        set_dir_group(
            workdir_info['path'],
            workdir_info['name'],
            dryrun=dryrun,
            skip_confirm=skip_confirm)
        set_dir_permissions(
            workdir_info['path'],
            workdir_info['permissions'],
            dryrun=dryrun,
            skip_confirm=skip_confirm)
    if (directory_created or
        (redo_quotas and
         not verify_project_quota(
            workdir_info['path'],
            workdir_info['name'],
            workdir_info['quota'],
            dryrun=dryrun))):
        set_project_quota(
            workdir_info['path'],
            workdir_info['name'],
            workdir_info['quota'],
            dryrun=dryrun,
            skip_confirm=skip_confirm)
