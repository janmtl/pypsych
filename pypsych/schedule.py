#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Schedule class, validation functions, and compilation functions
for compiling a schedule of files to process.

Methods:
    compile: shortcut for validating the loaded configuration, then
        performing the search, and _resolve functions
    
    load: load the schedule.yaml file into a dictionary
    
    search: search the data_path for all files matching the patterns.

    validate_schema: validate yaml contents against the schedule configuration
        schema.
    
    validate_interface_names: validates that the interface names contained in
        the configuration match a given list of possible interface names
    
    validate_patterns: validates that the regex patterns return named fields
        matching a list of required named fields

Configuration schema (YAML):
    [task_name (str):
        [interface_name (str):
            [filetype (str): pattern (str)]
        ]
    ]
"""
from schema import Schema
import yaml
import os
import re
import pandas as pd

class Schedule(object):
    """
    An object for scheduling files to be processed by interfaces.

    Args:
        path (str): path to YAML schedule configuration file.

    Attributes:
        path (str): path to YAML schedule configuration file.
        sched_df (pands.DataFrame): a Pandas DataFrame listing all files found
    """

    def __init__(self, path):
        self.path = path
        self.raw = None
        self.sched_df = None

    def load(self):
        """Load in the raw schedule configuration."""
        self.raw = self.validate_schema(yaml.load(open(self.path, 'r')))

    def compile(self, data_path):
        """Search the data path for the files to add to the schedule."""
        files_df = self.search(self.raw, data_path)
        self.sched_df = self._resolve(files_df)

    @staticmethod
    def search(raw, data_path):
        """Search the data path for matching file patterns and return a pandas
        DataFrame of the results."""
        files_dict = []
        for task_name, task in raw.iteritems():
            for interface_name, patterns in task.iteritems():
                for pattern_name, pattern in patterns.iteritems():
                    for root, _, files in os.walk(data_path):
                        for filepath in files:
                            file_match = re.match(pattern, filepath)
                            if file_match:
                                file_dict = file_match.groupdict()
                                file_dict['Task_Name'] = task_name
                                file_dict['Interface_Name'] = interface_name
                                file_dict['File'] = pattern_name
                                file_dict['Path'] = os.path.join(root, filepath)
                                files_dict.append(file_dict)
        return pd.DataFrame(files_dict)

    @staticmethod
    def _resolve(files_df):
        """
        Resolve any files that matched multiple Task_Order values and
        return a subset of the Data Frame.

        Args:
            files_df (pandas.DataFrame): a DataFrame resulting from
            Schedule.search().
        """
        counter = files_df.groupby(['Subject_ID',
                                    'Interface_Name',
                                    'File',
                                    'Task_Name'])['Task_Order'].count()
        maps = counter[counter == 1]
        maps = maps.reset_index()
        maps.drop('Task_Order', axis=1, inplace=True)
        orders = pd.merge(maps, files_df)[['Subject_ID',
                                           'Task_Name',
                                           'Task_Order']]
        orders.drop_duplicates(inplace=True)
        sched_df = pd.merge(orders, files_df)[['Subject_ID',
                                               'Task_Name',
                                               'Task_Order',
                                               'File',
                                               'Interface_Name',
                                               'Path']]
        return sched_df

    @staticmethod
    def validate_schema(raw):
        """Validate the schedule dictionary against the schema described
        above."""
        schema = Schema({str: {str: {str: str}}})
        return schema.validate(raw)

    @staticmethod
    def validate_interface_names(raw, interface_names):
        """
        Validate that all interface names are contained in the
        interface_names list.

        Args:
            interface_names (list(str)): list of valid interface names
            implemented in pypsych.
        """
        for _, task in raw.iteritems():
            for interface_name in task.keys():
                if not interface_name in interface_names:
                    raise Exception(
                        'Schedule could not validate interface ',
                        interface_name
                        )

    @staticmethod
    def validate_patterns(raw):
        """Validate that all file pattern regex expressions yield Task_Order
        and Subject_ID fields."""
        for _, task  in raw.iteritems():
            for _, interface in task.iteritems():
                for _, pattern in interface.iteritems():
                    compiled_pattern = re.compile(pattern)
                    for group_name in compiled_pattern.groupindex.keys():
                        if not group_name in ['Task_Order', 'Subject_ID']:
                            raise Exception(
                                'Schedule could not validate pattern ',
                                pattern
                                )
