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
        self.config = config
        self.schedule = schedule
        self.files = {}

    def load(self, file_paths):
        """Loads all files as CSV."""
        for file_type, file_path in file_paths.iteritems():
            self.files[file_type] = pd.read_csv(file_path)

    @staticmethod
    def validate_config(raw):
        """Placeholder method for validating configuration dicts."""
        pass

    @staticmethod
    def validate_schedule(raw):
        """Placeholder method for validating schedule configuration dicts."""
        pass
