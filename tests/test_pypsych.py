#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pypsych
----------------------------------

Tests for `pypsych` module.
"""

import unittest
from pypsych import pypsych
import numpy as np
import pandas as pd
import logging
logging.basicConfig(level=logging.INFO)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

class TestPypsych(unittest.TestCase):

  def setUp(self):
    pass

  def test_config(self):
    experiment = pypsych.Experiment()
    experiment.compile_interfaces()
    experiment.compile_schedule()
    experiment.consume_schedule()

  def tearDown(self):
    pass

if __name__ == '__main__':
  unittest.main()
