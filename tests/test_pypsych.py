#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pypsych
----------------------------------

Tests for `pypsych` module.
"""

import unittest
from pypsych import pypsych
# import numpy as np
# import pandas as pd
# import logging
# logging.basicConfig(level=logging.INFO)
# pd.set_option('display.max_rows', 50)
# pd.set_option('display.max_columns', 500)
# pd.set_option('display.width', 1000)

class TestPypsych(unittest.TestCase):

  def setUp(self):
    pass

  def test_Biopac(self):
    # experiment = pypsych.Experiment()
    # experiment.compile_interfaces()
    # experiment.compile_schedule()
    # experiment.schedule = experiment.schedule.xs(206, level=1, drop_level = False)
    # experiment.consume_schedule()

  # def test_main(self):
  #   experiment = pypsych.Experiment()
  #   experiment.compile_interfaces()
  #   experiment.compile_schedule()
  #   # print experiment.schedule[['Include?', 'Warning']]
  #   experiment.consume_schedule()
    pass

  def tearDown(self):
    pass

if __name__ == '__main__':
  unittest.main()
