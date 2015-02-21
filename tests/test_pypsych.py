#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pypsych
----------------------------------

Tests for `pypsych` module.
"""

import unittest
from pypsych import pypsych

class TestPypsych(unittest.TestCase):

  def setUp(self):
    pass

  def test_BeGaze(self):
    CONFIG = pypsych.Config()
    schedule = pypsych.Schedule( data_path     = '/users/yan/dev-local/eye',
                                 file_patterns = CONFIG.get('file_patterns'))
    print schedule.data.loc[1,105]
    # print schedule.data[1][105]
    label_patterns = CONFIG.get('label_patterns')
    # samples = pypsych.interfaces.BeGaze.assemble( samples_path   = samples_path,
    #                                               labels_path    = labels_path,
    #                                               label_patterns = label_patterns)
    # print samples

  def tearDown(self):
    pass

if __name__ == '__main__':
  unittest.main()
