#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_data_source
----------------------------------

Tests for Data Source object provided in pypsych.data_source module.
"""


import unittest
import pandas as pd
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pkg_resources import resource_filename
from pypsych.config import Config
from pypsych.schedule import Schedule
from pypsych.data_source import DataSource

class BeGazeLoadingTestCases(unittest.TestCase):
    """
    Asserts that bad config and schedule yaml files cannot be loaded.
    """

    def setUp(self):
        # Load a config and a schedule
        config = Config(path=resource_filename('tests.begaze', 'begaze.yaml'))
        config.load()
        schedule = Schedule(path=resource_filename('tests.begaze', 
                                                   'schedule.yaml'))
        schedule.load()

        # Extract the configuration and schedule for just one task
        self.subconfig = config.get_subconfig('Mock1', 'BeGaze')
        self.subschedule = schedule.get_subschedule('Mock1', 'BeGaze')

    def test_load_bad_config(self):
        """Should throw an error when we pass bad label configurations."""
        pass

    def test_load_bad_schedule(self):
        """Should throw an error when we pass a bad schedule configuration."""
        pass

    def test_load_begaze(self):
        """Should not throw errors when correct file is loaded"""
        data_source = DataSource(self.subconfig, self.subschedule)
        # Check that begaze instance matches
        self.assertIsInstance(data_source, DataSource)
        # TODO(jammtl): check that files and schedule loaded correctly

if __name__ == '__main__':
    unittest.main()
