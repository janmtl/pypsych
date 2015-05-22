#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_config
----------------------------------

Tests for `config` module of pypsych.
"""

import unittest
import yaml
import logging
from pkg_resources import resource_filename
from pypsych.config import Config
logging.basicConfig(level=logging.INFO)


class BeGazeOnlyTestCase(unittest.TestCase):

    def setUp(self):
        self.config_path = resource_filename('tests.mock',
                                             'begaze.yaml')
        self.mock_config = yaml.load(open(self.config_path, 'r'))

    def testLoadNoFile(self):
        pass

    def testLoadBadFiletype(self):
        pass

    def testLoadBadYAMLfile(self):
        pass

    def testLoadBadYAMLSchema(self):
        pass

    def testLoadGoodSchema(self):
        """
        Test importing the raw config.yaml
        """
        self.c = Config(path=self.config_path)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
