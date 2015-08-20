#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_biopac
----------------------------------

Tests for `Biopac` Data Source provided in pypsych.data_sources.biopac module.
"""


import unittest
import pandas as pd
import numpy as np
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pkg_resources import resource_filename
from pypsych.config import Config
from pypsych.schedule import Schedule
from pypsych.data_sources.biopac import Biopac


def assert_labelsdfs_equality(df1, df2):
    """
    Asserts whether two Pandas dataframes are exactly equal irregardless of
    their column order.

    Args:
        df1 (Pandas.DataFrame): The first dataframe to compare.
        df2 (Pandas.DataFrame): The second dataframe to compare.

    Output:
        Equality (bool): The output of assert_frame_equal function found in
            Pandas.util.testing applied to df1 and df2 with sorted columns.
    """

    df1.sort(axis=1, inplace=True)
    df2.sort(axis=1, inplace=True)
    if 'Unnamed: 0' in df1.columns:
        df1.drop('Unnamed: 0', axis=0, inplace=True)
    if 'Unnamed: 0' in df2.columns:
        df2.sort('Unnamed: 0', axis=0, inplace=True)
    pd.util.testing.assert_frame_equal(df1, df2, check_names=True)


class BiopacLoadingTestCases(unittest.TestCase):
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
        self.subconfig = config.get_subconfig('Mock1', 'Biopac')
        self.subschedule = schedule.get_subschedule('Mock1', 'Biopac')
        self.file_paths = schedule.get_file_paths(101, 'Mock1', 'Biopac')

    def test_create_biopac(self):
        """Should not throw errors when correct configuration is loaded."""
        biopac = Biopac(config=self.subconfig, schedule=self.subschedule)
        # Check that biopac instance matches
        self.assertIsInstance(biopac, Biopac)

    def test_load_biopac(self):
        """Should not throw errors when correct file is loaded."""
        biopac = Biopac(config=self.subconfig, schedule=self.subschedule)
        biopac.load(self.file_paths)

class BeGazeMergeLabelsConfig(unittest.TestCase):
    """
    Tests that Biopac correctly merges labels and label configurations.
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
        subconfig = config.get_subconfig('Mock1', 'Biopac')
        subschedule = schedule.get_subschedule('Mock1', 'Biopac')
        file_paths = schedule.get_file_paths(101, 'Mock1', 'Biopac')

        # Create an instance of the biopac data source
        self.biopac = Biopac(config=subconfig, schedule=subschedule)
        self.biopac.load(file_paths)

    def test_merge_data(self):
        """Test if labels and label config is merging correctly."""
        self.biopac.merge_data()


class BeGazeBinData(unittest.TestCase):
    """
    Tests that Biopac correctly bins data to take statistics.
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
        subconfig = config.get_subconfig('Mock1', 'Biopac')
        subschedule = schedule.get_subschedule('Mock1', 'Biopac')
        file_paths = schedule.get_file_paths(101, 'Mock1', 'Biopac')

        # Create an instance of the biopac data source
        self.biopac = Biopac(config=subconfig, schedule=subschedule)
        self.biopac.load(file_paths)
        self.biopac.merge_data()

    def test_bin_data(self):
        """Test if stats are being calculated correctly."""
        self.biopac.bin_data()

if __name__ == '__main__':
    unittest.main()
