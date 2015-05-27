#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Provides the base DataSource class for pypsych data sources.
"""

import pandas as pd


class DataSource(object):
    """
    DataSource base class.
    """

    def __init__(self, config, schedule):
        self.config = self._validate_config(config)
        self.schedule = self._validate_schedule(schedule)
        self.output = pd.Panel()
        self.data = {}

    def load(self, file_paths):
        """By default, loads all files as TSV."""
        for file_type, file_path in file_paths.iteritems():
            self.data[file_type] = pd.read_csv(file_path,
                                               comment="#",
                                               delimiter="\t",
                                               skipinitialspace=True)

    def process(self):
        """Placeholder method for processing the loaded files."""
        pass

    @staticmethod
    def _validate_config(raw):
        """Placeholder method for validating configuration dicts."""
        return raw

    @staticmethod
    def _validate_schedule(raw):
        """Placeholder method for validating schedule configuration dicts."""
        return raw
