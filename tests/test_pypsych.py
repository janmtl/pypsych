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

class TestPypsych(unittest.TestCase):

  def setUp(self):
    logging.info('Loading config file...')
    self.config   = pypsych.Config()
    logging.info('Building schedule of files...')
    self.schedule = pypsych.Schedule( data_path     = '/users/yan/dev-local/eye',
                                      file_patterns = self.config.get('file_patterns'))
    mask_dirs   = ['/users/yan/dev-local/eye/roi/henry', '/users/yan/dev-local/eye/roi/ko']
    mask_colors = [[30, 255, 0], [30, 255, 0]]
    logging.info('Loading ROI masks...')
    self.masker = pypsych.Masker(dirs         = mask_dirs,
                                 colors       = mask_colors,
                                 file_pattern = self.config.get('mask_file_pattern'))
    pass

  def test_BeGaze(self):
    begaze_sched = self.schedule.data[self.schedule.data['Interface'] == 'BeGaze']
    tiny_sched = begaze_sched.loc[1, 101]
    samples = pd.read_csv('/users/yan/dev-local/out/1_101_LabeledSamples.tsv', sep="\t")
    roi = self.masker.get_roi(samples)
    print roi
    # pypsych.consume_schedule( schedule = tiny_sched,
    #                           config = self.config,
    #                           output_dir = '/users/yan/dev-local/out/',
    #                           masker = self.masker)

  def tearDown(self):
    pass

if __name__ == '__main__':
  unittest.main()
