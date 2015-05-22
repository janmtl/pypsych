#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Config class, validation functions, and shortcut functions to
frequently accessed elements of the configuration dictionary.

Validation functions:
    validate_global_config: Checks paths and tasks.

Config class shortcut functions:
    tasks:
    tasks_ids:
    ids_tasks:
    interfaces:
    interface_tasks:
    get_:
"""
from pkg_resources import resource_filename
import yaml


class Config(object):
    """
    A pypsych configuration object with special shortcuts.

    Args:
        config_path (str): path to current YAML config file.

    Attributes:
        default_path (str): path to default configuration file included with
            pypsych.
        global (dict): global settings
        tasks (dict): interface configs grouped by task
        interfaces (dict): task configs grouped by interface
    """

    def __init__(self, **kwargs):
        default_path = resource_filename('pypsych.defaults', 'config.yaml')
        self.path = kwargs.get('path', default_path)
        self.raw = yaml.load(open(self.path, 'r'))

    def tasks(self):
        """Returns list of all tasks in config."""

    def interfaces(self):
        """Returns list of all interface names in config."""

    def tasks_ids(self):
        """Returns dict of {task name: [interface names]}."""

    def get_interface_config(self, interface_name):
        """Fetches the configuration for a given."""
