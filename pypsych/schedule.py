#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Schedule class, validation functions, and compilation functions
for compiling a schedule of files to process.

Methods:
    compile: shortcut for validating the loaded configuration, then
      performing the search, and _resolve functions

    load: load the schedule.yaml file into a dictionary

    get_file_paths: return a dictionary of files for a given subject, task, and
      data source.

    search: search the data_path for all files matching the patterns.

    validate_schema: validate yaml contents against the schedule configuration
      schema.

    validate_data_source_names: validates that the data source names contained
    in the configuration match a given list of possible data source names

    validate_patterns: validates that the regex patterns return named fields
      matching a list of required named fields

Configuration schema (YAML):
  {task_name (str):
    {data_source_name (str):
      {filetype (str): pattern (str)}
    }
  }
"""
from schema import Schema
import os
import re
import pandas as pd
import numpy as np
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


# TODO(janmtl): Schedule should extend pd.DataFrame

class Schedule(object):
    """
    An object for scheduling files to be processed by data sources.

    Args:
      path (str): path to YAML schedule configuration file.

    Attributes:
      path (str): path to YAML schedule configuration file.
      raw (dict): the dictionary resulting from the YAML configuration.
      sched_df (pands.DataFrame): a Pandas DataFrame listing all files found
    """

    def __init__(self, raw):
        self.raw = self.validate_schema(raw)
        self.sched_df = None
        self.subjects = []
        self.valid_subjects = []
        self.invalid_subjects = []

    @memoize
    def get_subschedule(self, task_name, data_source_name):
        """Fetches the schedule for a given task and data source."""
        return self.raw[task_name][data_source_name]

    def compile(self, data_paths):
        """Search the data path for the files to add to the schedule."""
        # TODO(janmtl): this should accept globs
        # TODO(janmtl): should be able to pass a list of excluded subjects

        if not isinstance(data_paths, list):
            data_paths = list(data_paths)

        files_df = self.search(self.raw, data_paths)
        self.sched_df = self._resolve(files_df)
        self.sched_df[['Subject', 'Task_Order']] = \
            self.sched_df[['Subject', 'Task_Order']].astype(np.int64)
        self.subjects = list(np.unique(self.sched_df['Subject']))

    # TODO(janmtl): The function that checks the integrity of a subject's data
    # should also return which subjects are broken and why

    def validate_files(self):
        """Iterate over subjects and make sure that they all have all the files
        they need."""
        cf = (self.sched_df.pivot_table(index='Subject',
                                        columns=['Data_Source_Name',
                                                 'Task_Name',
                                                 'File'],
                                        values='Path',
                                        aggfunc=lambda x: len(x)) == 1)
        return cf

    def remove_subject(self, subject_id):
        self.sched_df = self.sched_df[self.sched_df['Subject'] != subject_id]
        if subject_id in self.subjects:
            self.subjects.remove(subject_id)

    def isolate_subjects(self, subject_ids):
        self.sched_df = self.sched_df[self.sched_df['Subject']
                                      .isin(subject_ids)]
        self.subjects = subject_ids

    def isolate_tasks(self, task_names):
        self.sched_df = self.sched_df[self.sched_df['Task_Name']
                                      .isin(task_names)]

    def isolate_data_sources(self, data_source_names):
        self.sched_df = self.sched_df[self.sched_df['Data_Source_Name']
                                      .isin(data_source_names)]

    def get_file_paths(self, subject_id, task_name, data_source_name):
        """Return all a dictionary of all files for a given subject, task,
        and data source."""
        if self.sched_df.empty:
            raise Exception('Schedule is empty, try Schedule.compile(path).')
        sub_df = self.sched_df[
            (self.sched_df['Subject'] == subject_id)
            & (self.sched_df['Task_Name'] == task_name)
            & (self.sched_df['Data_Source_Name'] == data_source_name)
            ]
        if sub_df.empty:
            raise Exception(
                '({}, {}, {}) not found in schedule.'.format(subject_id,
                                                             task_name,
                                                             data_source_name)
                )
        list_of_files = sub_df[['File', 'Path']].to_dict('records')
        files_dict = {ds['File']: ds['Path'] for ds in list_of_files}
        return files_dict

    @staticmethod
    def search(raw, data_paths):
        """Search the data paths for matching file patterns and return a pandas
        DataFrame of the results."""
        files_dict = []
        for task_name, task in raw.iteritems():
            for data_source_name, patterns in task.iteritems():
                for pattern_name, pattern in patterns.iteritems():
                    for data_path in data_paths:
                        for root, _, files in os.walk(data_path):
                            for filepath in files:
                                file_match = re.match(pattern, filepath)
                                if file_match:
                                    fd = file_match.groupdict()
                                    fd['Task_Name'] = task_name
                                    fd['Data_Source_Name'] = data_source_name
                                    fd['File'] = pattern_name
                                    fd['Path'] = os.path.join(root, filepath)
                                    files_dict.append(fd)
        files_df = pd.DataFrame(files_dict)
        files_df[['Subject', 'Task_Order']] = \
            files_df[['Subject', 'Task_Order']].astype(np.int64)
        return files_df

    @staticmethod
    def _resolve(files_df):
        """
        Resolve any files that matched multiple Task_Order values and
        return a subset of the Data Frame.

        Args:
          files_df (pandas.DataFrame): a DataFrame resulting from
          Schedule.search().
        """
        counter = files_df.groupby(['Subject',
                                    'Data_Source_Name',
                                    'File',
                                    'Task_Name'])['Task_Order'].count()
        maps = counter[counter == 1]
        maps = maps.reset_index()
        maps.drop('Task_Order', axis=1, inplace=True)
        orders = pd.merge(maps, files_df)[['Subject',
                                           'Task_Name',
                                           'Task_Order']]
        orders.drop_duplicates(inplace=True)
        sched_df = pd.merge(orders, files_df)[['Subject',
                                               'Task_Name',
                                               'Task_Order',
                                               'File',
                                               'Data_Source_Name',
                                               'Path']]
        return sched_df

    @staticmethod
    def validate_schema(raw):
        """Validate the schedule dictionary against the schema described
        above."""
        schema = Schema({str: {str: {str: str}}})
        return schema.validate(raw)

    @staticmethod
    def validate_data_source_names(raw, data_source_names):
        """
        Validate that all data source names are contained in the
        data_source_names list.

        Args:
          data_source_names (list(str)): list of valid data source names
          implemented in pypsych.
        """
        for _, task in raw.iteritems():
            for data_source_name in task.keys():
                if data_source_name not in data_source_names:
                    raise Exception(
                        'Schedule could not validate data source ',
                        data_source_name
                        )

    @staticmethod
    def validate_patterns(raw):
        """Validate that all file pattern regex expressions yield Task_Order
        and Subject fields."""
        for _, task in raw.iteritems():
            for _, data_source in task.iteritems():
                for _, pattern in data_source.iteritems():
                    compiled_pattern = re.compile(pattern)
                    for group_name in compiled_pattern.groupindex.keys():
                        if group_name not in ['Task_Order', 'Subject']:
                            raise Exception(
                                'Schedule could not validate pattern ',
                                pattern
                                )
