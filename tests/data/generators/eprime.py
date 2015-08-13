#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for generating mock EPrime test data
"""

import pandas as pd
import numpy as np
import random
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pypsych.config import Config
from pypsych.schedule import Schedule
from pypsych.data_sources.eprime import EPrime


def generate_mock_eprime_data(config_path, task_name, begaze_data, sched_path):
    pass


def save_mock_eprime_data(output_path, data, subject_id, task_order, task_name):
    pass
