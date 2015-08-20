#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_begaze
----------------------------------

Tests for `BeGaze` Data Source provided in pypsych.data_sources.begaze module.
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
from pypsych.data_sources.begaze import BeGaze


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


class BeGazeLoadingTestCases(unittest.TestCase):
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
        self.subconfig = config.get_subconfig('Mock1', 'BeGaze')
        self.subschedule = schedule.get_subschedule('Mock1', 'BeGaze')
        self.file_paths = schedule.get_file_paths(101, 'Mock1', 'BeGaze')

    def test_create_begaze(self):
        """Should not throw errors when correct configuration is loaded."""
        begaze = BeGaze(config=self.subconfig, schedule=self.subschedule)
        # Check that begaze instance matches
        self.assertIsInstance(begaze, BeGaze)

    def test_load_begaze(self):
        """Should not throw errors when correct file is loaded."""
        begaze = BeGaze(config=self.subconfig, schedule=self.subschedule)
        begaze.load(self.file_paths)

class BeGazeMergeLabelsConfig(unittest.TestCase):
    """
    Tests that BeGaze correctly merges labels and label configurations.
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
        subconfig = config.get_subconfig('Mock1', 'BeGaze')
        subschedule = schedule.get_subschedule('Mock1', 'BeGaze')
        file_paths = schedule.get_file_paths(101, 'Mock1', 'BeGaze')

        # Create an instance of the begaze data source
        self.begaze = BeGaze(config=subconfig, schedule=subschedule)
        self.begaze.load(file_paths)

    def test_merge_data(self):
        """Test if labels and label config is merging correctly."""
        valid_labels_path = resource_filename(
            'tests.data',
            '1011_begaze_merged_labels.txt')

        valid_labels = pd.read_csv(valid_labels_path,
                                   delimiter="\t",
                                   index_col=0,
                                   dtype={'Duration': np.float64,
                                          'Condition': np.object,
                                          'Event_ID': np.object,
                                          'Event_Order': np.int64,
                                          'Event_Type': np.object,
                                          'N_Bins': np.int64,
                                          'Start_Time': np.float64})

        self.begaze.merge_data()
        assert_labelsdfs_equality(self.begaze.data['labels'], valid_labels)


class BeGazeBinData(unittest.TestCase):
    """
    Tests that BeGaze correctly calculates binning statistics.
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
        subconfig = config.get_subconfig('Mock1', 'BeGaze')
        subschedule = schedule.get_subschedule('Mock1', 'BeGaze')
        file_paths = schedule.get_file_paths(101, 'Mock1', 'BeGaze')

        # Create an instance of the begaze data source
        self.begaze = BeGaze(config=subconfig, schedule=subschedule)
        self.begaze.load(file_paths)
        self.begaze.merge_data()

    def test_bin_data(self):
        """Test if statistics are being calculated and binned correctly."""
        # TODO: check the output of this test
        self.begaze.bin_data()

if __name__ == '__main__':
    unittest.main()
