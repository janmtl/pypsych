#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for generating mock test data
"""

import pandas as pd
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pkg_resources import resource_filename
from generators.begaze import generate_mock_begaze_data, save_mock_begaze_data
from generators.biopac import generate_mock_biopac_data, save_mock_biopac_data
from generators.eprime import generate_mock_eprime_data, save_mock_eprime_data


OUTPUT_PATH = 'tests/data/'
N_EVENTS = 12
CONFIG_PATH = resource_filename('tests.config', 'config.yaml')
SCHED_PATH = resource_filename('tests.schedule', 'schedule.yaml')


if __name__ == '__main__':
    for subject_id, task_order, task_name in [(101, 1, 'Mock1'),
                                              (101, 2, 'Mock2'),
                                              (102, 1, 'Mock1'),
                                              (102, 2, 'Mock2')]:
        # Generate mock datas (beware of order)
        BG_DATA = generate_mock_begaze_data(CONFIG_PATH, task_name, N_EVENTS,
                                            SCHED_PATH)
        BP_DATA = generate_mock_biopac_data(CONFIG_PATH, task_name, BG_DATA,
                                            SCHED_PATH)
        EP_DATA = generate_mock_eprime_data(CONFIG_PATH, task_name, BG_DATA,
                                            SCHED_PATH)

        # Save mock datas
        save_mock_begaze_data(OUTPUT_PATH, BG_DATA, subject_id, task_order,
                              task_name)
        save_mock_biopac_data(OUTPUT_PATH, BP_DATA, subject_id, task_order,
                              task_name)
        save_mock_eprime_data(OUTPUT_PATH, EP_DATA, subject_id, task_order,
                              task_name)
