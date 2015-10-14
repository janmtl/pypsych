#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Config class, validation functions, and shortcut functions to
frequently accessed elements of the configuration dictionary.

Schema (YAML):
  {task_name (str):
    {data_source_name (str): data_source_configuration (dict)}
  }
"""
from schema import Schema
import functools


def memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    return memoizer


class Config(object):
    """
    A pypsych configuration object with special shortcuts.

    Args:
      path (str): path to current YAML config file.

    Attributes:
      task_names (list): list of tasks in config.
      data_source_names (list): list of data sources in config.

    Methods:
      load: loads the yaml from file.
      get_subconfig: fetch the configuration dict for the given task and data
        source.
      validate_schema: Check yaml against schema.
      validate_data_source_names Check yaml against valid data source names.
    """

    def __init__(self, raw):
        self.raw = self.validate_schema(raw)
        self.task_names = [task_name for task_name in self.raw.keys()]
        self.data_source_names = []
        for _, task, in self.raw.iteritems():
            for data_source_name in task.keys():
                if data_source_name not in self.data_source_names:
                    self.data_source_names.append(data_source_name)

    def isolate_tasks(self, task_names):
        """."""
        # TODO(janmtl): fix this docstring.
        self.task_names = task_names

    @memoize
    def get_subconfig(self, task_name, data_source_name):
        """Fetches the configuration for a given task and data source."""
        return self.raw[task_name][data_source_name]

    @staticmethod
    def validate_schema(raw):
        """Validate the config dictionary against the schema described above."""
        schema = Schema({str: {str: dict}})
        return schema.validate(raw)

    @staticmethod
    def validate_data_source_names(raw, valid_data_source_names):
        """
        Validate that all data source names are contained in the
        valid data source names list.

        Args:
            raw (yaml):
            valid_data_source_names (list(str)): list of valid data sources
              names implemented in pypsych.
        """
        # TODO(janmtl): this function is never actually called.

        for _, task in raw.iteritems():
            for data_source_name in task.keys():
                if data_source_name not in valid_data_source_names:
                    raise Exception(
                        'Config could not validate data source ',
                        data_source_name
                        )
