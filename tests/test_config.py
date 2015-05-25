#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_config
----------------------------------

Tests for `Config` class provided in pypsych.config module.
"""


import unittest
import yaml
import schema
import pandas as pd
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pkg_resources import resource_filename
from pypsych.config import Config

class ConfigLoadingTestCases(unittest.TestCase):
    """
    Asserts that bad config.yaml files cannot be loaded.
    """

    def setUp(self):
        self.config_path = resource_filename('tests.config',
                                             'data_sources.yaml')
        self.mock_config = yaml.load(open(self.config_path, 'r'))

    def test_load_no_file(self):
        """Should throw an error when yaml file does not exist."""
        with self.assertRaisesRegexp(IOError, '[Errno 2]'):
            config = Config(path=resource_filename('tests.config',
                                                   'notexist.xyz'))
            config.load()

    def test_load_bad_yaml_file(self):
        """Should throw an error when file is not valid yaml."""
        with self.assertRaises(yaml.parser.ParserError):
            config = Config(path=resource_filename('tests.config',
                                                   'bad_yaml.yaml'))
            config.load()

    def test_load_bad_yaml_schema(self):
        """Should throw an error when yaml file does match schema."""
        with self.assertRaises(schema.SchemaError):
            config = Config(path=resource_filename('tests.config',
                                                   'bad_schema.yaml'))
            config.load()

    def test_load_good_config(self):
        """Should not throw errors when correct file is loaded"""
        config = Config(path=self.config_path)
        config.load()


class ConfigValidationTestCases(unittest.TestCase):
    """
    Tests to ensure that Config validates its configuration correctly against
    pypsych requirements
    """

    def setUp(self):
        # Load in the mock configuration
        self.config_path = resource_filename('tests.config',
                                             'data_sources.yaml')
        self.good_config = yaml.load(open(self.config_path, 'r'))
        self.baddatasourcenames = yaml.load(open(resource_filename(
            'tests.config',
            'bad_data_source_names.yaml'
            ), 'r'))

        # Set the valid data source names
        self.valid_names = ['Biopac', 'BeGaze']

        # Construct the test Config object and load in the configuration
        self.config = Config(path=self.config_path)

    def test_bad_data_source_names(self):
        """Invalid data source names are not accepted."""
        with self.assertRaises(Exception):
            self.config.validate_data_source_names(
                self.baddatasourcenames,
                self.valid_names
                )

    def test_good_data_source_names(self):
        """Valid data source names are accepted."""
        self.config.validate_data_source_names(
            self.good_config,
            self.valid_names
            )

class ConfigShortcutsTestCases(unittest.TestCase):
    """
    Tests for the shortcut functions provided by the Config class.
    """

    def setUp(self):
        # Load in the mock configuration
        self.config_path = resource_filename('tests.config',
                                             'data_sources.yaml')

        # Construct the test Config object and load in the configuration
        self.config = Config(path=self.config_path)
        self.config.load()

    def test_task_names_shortcut(self):
        """Test the Config.task_names attribute."""
        test_list = self.config.task_names
        valid_list = ['Mock1', 'Mock2']
        self.assertEqual(sorted(test_list), valid_list)

    def test_data_source_names_attribute(self):
        """Test the Config.data_source_names attribute."""
        test_list = self.config.data_source_names
        valid_list = ['BeGaze', 'Biopac']
        self.assertEqual(sorted(test_list), valid_list)

    def test_get_subconfig(self):
        """Test the task, data source configuration getter."""
        test_dict = self.config.get_subconfig('Mock1', 'BeGaze')
        valid_dict = {'Key': 'Mock1 BeGaze'}
        self.assertEqual(test_dict, valid_dict)


if __name__ == '__main__':
    unittest.main()
