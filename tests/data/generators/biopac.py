#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for generating mock Biopac test data
"""

import pandas as pd
import numpy as np
import random
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from scipy.io import savemat
from pypsych.config import Config
from pypsych.schedule import Schedule
from pypsych.data_sources.biopac import Biopac

# Labels columns:
# - Other Column 1
# - Time Trial [ms]
# - Event

# Samples columns:
# - Other Column 1
# - Other Column 2
# - Time
# - L Pupil Diameter [mm]
# - L POR X [px]
# - L POR Y [px]
# - L Event Info


def generate_mock_biopac_data(config_path, task_name, begaze_data, sched_path):

    config = Config(path=config_path)
    config.load()
    subconfig = config.get_subconfig(task_name, 'Biopac')
    schedule = Schedule(path=sched_path)
    schedule.load()
    subschedule = schedule.get_subschedule(task_name, 'Biopac')

    biopac = Biopac(config=subconfig, schedule=subschedule)
    bp_labels = biopac._label_config_to_df(subconfig)
    bg_labels = begaze_data['merged_labels']
    bbg_labels = bg_labels.drop(['N_Bins', 'Duration'], axis=1)
    labels = pd.merge(bbg_labels, bp_labels, on=['Label', 'Condition'])
    labels['End_Time'] = labels['Start_Time'] + labels['Duration']
    total_time = np.max(labels['End_Time'].values)

    # Generate data
    event_bpms = []
    event_rrs = []
    event_twaves = []

    events = np.repeat(255, total_time)
    bpm = np.repeat(0.0, total_time/10)
    rr = np.repeat(0.0, total_time/10)
    twave = np.repeat(0.0, total_time/10)

    for _, label in labels.iterrows():
        events[label['Start_Time']:label['End_Time']] = label['flag']

        event_bpm = random.uniform(60, 120)
        event_rr = random.uniform(600, 1200)
        event_twave = random.uniform(-0.5, 0.5)

        bpm[label['Start_Time']/10:label['End_Time']/10] = event_bpm
        rr[label['Start_Time']/10:label['End_Time']/10] = event_rr
        twave[label['Start_Time']/10:label['End_Time']/10] = event_twave

        event_bpms.append(event_bpm)
        event_rrs.append(event_rr)
        event_twaves.append(event_twave)

    unbinned = labels
    unbinned['bpm'] = event_bpms
    unbinned['rr'] = event_rrs
    unbinned['twave'] = event_twaves

    samples = pd.DataFrame({'bpm': bpm, 'rr': rr, 'twave': twave})
    labels = pd.DataFrame({'events': events})
    return {'samples': samples, 'labels': labels, 'unbinned': unbinned}


def save_mock_biopac_data(output_path, data, subject_id, task_order, task_name):
    """
    Save the mock biopac files to output_path.
    """

    base_path = ''.join([output_path,
                         task_name,
                         '_',
                         str(subject_id),
                         str(task_order)])
    samples_path = ''.join([base_path, '_biopac_samples.txt'])
    labels_path = ''.join([base_path, '_biopac_labels.mat'])
    unbinned_path = ''.join([base_path, '_biopac_unbinned.txt'])

    data['samples'].to_csv(samples_path, sep="\t", header=False, index=False)
    savemat(labels_path, data['labels'].to_dict(orient='list'))
    data['unbinned'].to_csv(unbinned_path, sep="\t")
    pass
