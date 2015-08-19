#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_eprime
----------------------------------

Tests for `EPrime` Data Source provided in pypsych.data_sources.eprime module.
"""


import unittest
import pandas as pd
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pkg_resources import resource_filename
from pypsych.config import Config
from pypsych.schedule import Schedule
from pypsych.data_sources.eprime import EPrime


class EprimeLoading(unittest.TestCase):
    """
    Asserts that bad config and schedule yaml files cannot be loaded.
    """

    def setUp(self):
        # Load a config and a schedule
        config = Config(path=resource_filename('tests.config', 'config.yaml'))
        config.load()
        schedule = Schedule(path=resource_filename('tests.schedule',
                                                   'schedule.yaml'))
        schedule.load()
        schedule.compile('tests/data')

        # Extract the configuration and schedule for just one task
        self.subconfig = config.get_subconfig('Mock1', 'EPrime')
        self.subschedule = schedule.get_subschedule('Mock1', 'EPrime')
        self.file_paths = schedule.get_file_paths(101, 'Mock1', 'EPrime')

    def test_create_eprime(self):
        """Should not throw errors when correct configuration is loaded."""
        eprime = EPrime(config=self.subconfig, schedule=self.subschedule)
        # Check that eprime instance matches
        self.assertIsInstance(eprime, EPrime)

    def test_load_eprime(self):
        """Should not throw errors when correct file is loaded."""
        eprime = EPrime(config=self.subconfig, schedule=self.subschedule)
        eprime.load(self.file_paths)


class EPrimeBinData(unittest.TestCase):
    """
    Tests that EPrime correctly bins data to take statistics.
    """

    def setUp(self):
        # Load a config and a schedule
        config = Config(path=resource_filename('tests.config', 'config.yaml'))
        config.load()
        schedule = Schedule(path=resource_filename('tests.schedule',
                                                   'schedule.yaml'))
        schedule.load()
        schedule.compile('tests/data')

        # Extract the configuration and schedule for just one task
        subconfig = config.get_subconfig('Mock1', 'EPrime')
        subschedule = schedule.get_subschedule('Mock1', 'EPrime')
        file_paths = schedule.get_file_paths(101, 'Mock1', 'EPrime')

        # Create an instance of the eprime data source
        self.eprime = EPrime(config=subconfig, schedule=subschedule)
        self.eprime.load(file_paths)
        self.eprime.merge_data()

    def test_bin_data(self):
        """Test if stats are being calculated correctly."""
        self.eprime.bin_data()
        print self.eprime.output

if __name__ == '__main__':
    unittest.main()
