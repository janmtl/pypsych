#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for generating mock EPrime test data
"""

import pandas as pd
import numpy as np
import io
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pypsych.config import Config


def generate_mock_eprime_data(config_path, task_name, begaze_data, sched_path):
    """Generate mock eprime data based on mock begaze data."""
    superconfig = Config(path=config_path)
    superconfig.load()
    config = superconfig.get_subconfig(task_name, 'EPrime')

    bg = begaze_data['merged_labels'][['Condition', 'ID']]
    ed = np.random.randint(0, 10, (bg.shape[0], len(config['channels'])))
    ep = pd.DataFrame(data=ed, index=bg.index, columns=config['channels'])
    df = pd.concat([bg, ep], axis=1, join='inner')

    df.rename(columns={'ID': 'Img'}, inplace=True)

    result = []
    for _, row in df.iterrows():
        props = ["\t" + str(idx) + ': ' + str(val)
                 for idx, val in zip(list(row.index), list(row))]
        result.append("\n\n".join(props))
    result = ('\n\n\t*** LogFrame End ***\n\n'
              '\tLevel: 2\n\n'
              '\t*** LogFrame Start ***\n\n').join(result)
    prestring = ('*** Header Start ***\n\n'
                 'GARBAGE\n\n'
                 '*** Header End ***\n\n'
                 '\tLevel: 2\n\n'
                 '\t*** LogFrame Start ***\n\n')
    result = prestring + result + '\n\n\t*** LogFrame End ***'
    return {'df': df, 'raw': result}


def save_mock_eprime_data(output_path, data, subject_id, task_order, task_name):
    """Save the mock eprime files to output_path."""
    base_path = ''.join([output_path,
                         task_name,
                         '_',
                         str(subject_id),
                         str(task_order)])
    raw_path = ''.join([base_path, '_eprime.txt'])
    df_path = ''.join([base_path, '_eprime_df.txt'])

    with io.open(raw_path, 'w', encoding="utf-16") as f:
        f.write(unicode(data['raw']))

    data['df'].to_csv(df_path, sep="\t")

    pass
