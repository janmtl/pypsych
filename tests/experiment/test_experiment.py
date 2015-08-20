#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_experiment
----------------------------------

Tests for `Experiment` class provided in pypsych.experiment module.
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
from pypsych.experiment import Experiment


class ExperimentLoadingTestCases(unittest.TestCase):
    """
    Asserts that bad config and schedule yaml files cannot be loaded.
    """

    def setUp(self):
        # Load a config and a schedule
        self.config_path = resource_filename('tests.config', 'config.yaml')
        self.schedule_path = resource_filename('tests.schedule',
                                               'schedule.yaml')
        self.data_path = 'tests/data'

    def test_create_experiment(self):
        """Should not throw errors when correct configuration is loaded."""
        experiment = Experiment(config_path=self.config_path,
                                schedule_path=self.schedule_path,
                                data_path=self.data_path)

        # Check that biopac instance matches
        self.assertIsInstance(experiment, Experiment)
        experiment.load()

    def test_compile_experiment(self):
        """Test that compilation works."""
        experiment = Experiment(config_path=self.config_path,
                                schedule_path=self.schedule_path,
                                data_path=self.data_path)
        experiment.load()
        experiment.compile()

class ExperimentProcessingTestCases(unittest.TestCase):
    """
    Asserts that experiment can consume a schedule.
    """

    def setUp(self):
        # Load a config and a schedule
        self.config_path = resource_filename('tests.config', 'config.yaml')
        self.schedule_path = resource_filename('tests.schedule',
                                               'schedule.yaml')
        self.data_path = 'tests/data'

        self.experiment = Experiment(config_path=self.config_path,
                                     schedule_path=self.schedule_path,
                                     data_path=self.data_path)
        self.experiment.load()
        self.experiment.compile()

    def test_process_experiment(self):
        """Consume a schedule."""
        self.experiment.process()

class ExperimentSavingTestCases(unittest.TestCase):
    """
    Asserts that experiment can save the results of a consumed schedule.
    """

    def setUp(self):
        # Load a config and a schedule
        self.config_path = resource_filename('tests.config', 'config.yaml')
        self.schedule_path = resource_filename('tests.schedule',
                                               'schedule.yaml')
        self.data_path = 'tests/data'
        self.output_path = 'tests/output'

        self.experiment = Experiment(config_path=self.config_path,
                                     schedule_path=self.schedule_path,
                                     data_path=self.data_path)
        self.experiment.load()
        self.experiment.compile()
        self.experiment.process()

    def test_save_experiment(self):
        """Save the outputs."""
        # TODO(janmtl): should test all paths everywhere to be safe against
        # dropped backslashes (i.e.: move to os.join())
        self.experiment.save_outputs(self.output_path)

if __name__ == '__main__':
    unittest.main()
