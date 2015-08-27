#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_schedule
----------------------------------

Tests for `Schedule` class provided in pypsych.schedule module.
"""


import unittest
import yaml
import schema
import pandas as pd
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pkg_resources import resource_filename
from pypsych.schedule import Schedule


def assert_filesdfs_equality(df1, df2):
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
    if 'Path' in df1.columns:
        df1.sort('Path', axis=0, inplace=True)
    if 'Path' in df2.columns:
        df2.sort('Path', axis=0, inplace=True)
    try:
        pd.util.testing.assert_frame_equal(df1, df2, check_names=True)
        return True
    except (AssertionError, ValueError, TypeError):
        return False


class ScheduleLoadingTestCases(unittest.TestCase):
    """
    Asserts that bad schedule.yaml files cannot be loaded.
    """

    def setUp(self):
        self.schedule_path = resource_filename('tests.schedule',
                                               'schedule.yaml')
        self.mock_schedule = yaml.load(open(self.schedule_path, 'r'))

    def test_load_no_file(self):
        """Should throw an error when yaml file does not exist."""
        with self.assertRaisesRegexp(IOError, '[Errno 2]'):
            schedule = Schedule(path=resource_filename('tests.schedule',
                                                       'notexist.xyz'))
            schedule.load()

    def test_load_bad_yaml_file(self):
        """Should throw an error when file is not valid yaml."""
        with self.assertRaises(yaml.parser.ParserError):
            schedule = Schedule(path=resource_filename('tests.schedule',
                                                       'bad_yaml.yaml'))
            schedule.load()

    def test_load_bad_yaml_schema(self):
        """Should throw an error when yaml file does match schema."""
        with self.assertRaises(schema.SchemaError):
            schedule = Schedule(path=resource_filename(
                'tests.schedule',
                'bad_schema.yaml'
                ))
            schedule.load()

    def test_load_good_schedule(self):
        """Should not throw errors when correct file is loaded"""
        schedule = Schedule(path=self.schedule_path)
        schedule.load()


class ScheduleCompilationTestCases(unittest.TestCase):
    """
    Tests to ensure that Schedule correctly finds all files in the data path
    and resolves any ambiguity due to missing Task_Order fields.
    """

    def setUp(self):
        # Load in the mock schedule configuration
        self.schedule_path = resource_filename('tests.schedule',
                                               'schedule.yaml')
        self.mock_schedule = yaml.load(open(self.schedule_path, 'r'))
        self.data_path = "tests/data"

        # Load in the mock results of searching the data path
        self.files_df = pd.read_csv(resource_filename('tests.schedule',
                                                      'files_df.txt'))

        # Load in the mock results of resolving Task_Order ambiguity
        self.sched_df = pd.read_csv(resource_filename('tests.schedule',
                                                      'sched_df.txt'))

        # Construct the test Schedule object and load in the configuration
        self.schedule = Schedule(path=self.schedule_path)
        self.schedule.load()

    def test_searching_for_files(self):
        """Returns all file pattern matches in a given directory."""
        files_df = self.schedule.search(self.mock_schedule, 'tests/data')
        self.assertTrue(assert_filesdfs_equality(files_df, self.files_df))

    def test_compile_schedule(self):
        """Returns a task_order resolved file table after search."""
        self.schedule.compile(self.data_path)
        self.assertTrue(assert_filesdfs_equality(
            self.schedule.sched_df,
            self.sched_df))

    def test_get_file_paths(self):
        """Check that the file paths dictionary is correctly extracted from
        the sched_df."""
        valid_file_paths = {'labels': 'tests/data/1011_begaze_labels.txt',
                            'samples': 'tests/data/1011_begaze_samples.txt'}
        self.schedule.compile(self.data_path)
        file_paths = self.schedule.get_file_paths(101, 'Mock1', 'BeGaze')
        self.assertEqual(valid_file_paths, file_paths)

    def test_get_subschedule(self):
        """Test the task, data source schedule getter."""
        test_dict = self.schedule.get_subschedule('Mock1', 'BeGaze')
        valid_dict = {
            'samples':
            '(?P<Subject>[0-9]{3})(?P<Task_Order>[0-9])_begaze_samples.txt',
            'labels':
            '(?P<Subject>[0-9]{3})(?P<Task_Order>[0-9])_begaze_labels.txt'}
        self.assertEqual(test_dict, valid_dict)


class ScheduleValidationTestCases(unittest.TestCase):
    """
    Tests to ensure that Schedule validates its configuration correctly against
    pypsych requirements
    """

    def setUp(self):
        # Load in the mock schedule configuration
        self.good_schedule_path = resource_filename('tests.schedule',
                                                    'schedule.yaml')
        self.good_schedule = yaml.load(open(self.good_schedule_path, 'r'))
        self.baddatasourcenames = yaml.load(open(resource_filename(
            'tests.schedule',
            'bad_data_source_names.yaml'
            ), 'r'))
        self.badpatterns = yaml.load(open(resource_filename(
            'tests.schedule',
            'bad_file_patterns.yaml'
            ), 'r'))

        # Set the valid data source names
        self.valid_names = ['Biopac', 'BeGaze', 'EPrime']

        # Construct the test Schedule object and load in the configuration
        self.schedule = Schedule(path=self.good_schedule_path)

    def test_bad_data_source_names(self):
        """Invalid data source names are not accepted."""
        with self.assertRaises(Exception):
            self.schedule.validate_data_source_names(
                self.baddatasourcenames,
                self.valid_names
                )

    def test_good_data_source_names(self):
        """Valid data source names are accepted."""
        self.schedule.validate_data_source_names(
            self.good_schedule,
            self.valid_names
            )

    def test_bad_file_patterns(self):
        """File patterns that do not provide Subject_ID and Task_Order are
        not accepted."""
        with self.assertRaises(Exception):
            self.schedule.validate_patterns(self.baddatasourcenames)

    def test_good_file_patterns(self):
        """File patterns that provide Subject_ID and Task_Order are accepted."""
        self.schedule.validate_patterns(self.good_schedule)

if __name__ == '__main__':
    unittest.main()
