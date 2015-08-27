#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for generating mock BeGaze test data
"""

import pandas as pd
import numpy as np
import random
import string
import exrex
import re
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pypsych.config import Config

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


def generate_mock_begaze_data(config_path, task_name, n_events, sched_path):
    """
    Generate Mock BeGaze labels, samples, and binned data files.
    """

    # We will create the labels data frame first, and so we need to load in
    # a valid labels configuration
    config = Config(path=config_path)
    config.load()
    subconfig = config.get_subconfig(task_name, 'BeGaze')

    # We will generate a run of labels randomly chosen from the available ones
    # in the subconfig and the 'garbage_label' which will not be recognized.

    # First, let's start the Timestamp column at a random epoch and the Event
    # column with a random string
    epoch = random.randint(1, 20)*100
    time = []
    event = []
    event_types = []
    event_ids = []
    event_groups = []
    event_orders = []
    event_bins = []
    durations = []

    # Iterate over the number of events desired
    for idx in range(n_events):
        # Choose a random label from the configuration
        event_type = random.choice(subconfig.keys() + ['garbage_label'])

        # If we choose the 'garbage_label', generate some garbage
        if event_type == 'garbage_label':
            duration = random.randint(100, 1000)
            label_name = ''.join(random.choice(string.ascii_uppercase
                                 + string.digits) for _ in range(10))
            bins = 1
            event_id = 0
            event_group = 'garbage'
        else:
            duration = subconfig[event_type]['duration']
            bins = subconfig[event_type]['bins']
            label_name = exrex.getone(subconfig[event_type]['pattern'])
            lm = re.match(subconfig[event_type]['pattern'], label_name)
            md = lm.groupdict()
            event_id = md['ID']
            event_group = md['Condition']

        time.append(epoch)
        event.append(label_name)
        durations.append(duration)
        event_types.append(event_type)
        event_ids.append(event_id)
        event_groups.append(event_group)
        event_orders.append(idx)
        event_bins.append(bins)
        epoch = epoch + duration

    # Generate data for "Other Column 1"
    other_column_1 = np.random.randint(100, size=len(event))

    # Compile the arrays together into the labels data frame
    labels = pd.DataFrame.from_dict({'Other Column 1': other_column_1,
                                     'Time Trial [ms]': time,
                                     'Event': event})

    # Also, give a merged_labels data frame for testing begaze's intermediate
    # steps

    merged_labels = pd.DataFrame.from_dict({
        'Label': event_types,
        'Condition': event_groups,
        'ID': event_ids,
        'Event_Order': event_orders,
        'Duration': durations,
        'N_Bins': event_bins,
        'Start_Time': time,
        'Bin_Order': ''})
    merged_labels = merged_labels[(merged_labels['Label'] !=
                                   'garbage_label')]
    merged_labels['Bin_Order'] = merged_labels.index.values()

    # Now on to the samples and binned files. We will iterate over the
    # event_types array and construct runs of data points that match the
    # duration of each bin in that event.

    # samples file array must be started off with random data of the length of
    # the random displacement of the first event in the labels file.
    samples_times = [0]
    samples_other_column_1 = [0.0]
    samples_other_column_2 = [0.0]
    samples_diameters = [0.0]
    samples_pos_xs = [0.0]
    samples_pos_ys = [0.0]
    samples_event_infos = ['Nothing']

    # binned file arrays
    binned_event_types = []
    binned_event_ids = []
    binned_event_groups = []
    binned_event_orders = []
    binned_bin_numbers = []
    binned_diameters = []
    binned_pos_xs = []
    binned_pos_ys = []
    binned_nans = []

    for idx, event_type in enumerate(event_types):
        # Samples are repeated 'ticks_in_bin' number of times
        bin_times = np.linspace(time[idx],
                                time[idx]+durations[idx],
                                event_bins[idx]+1)
        bin_start_times = bin_times[0:event_bins[idx]]
        bin_end_times = bin_times[1:event_bins[idx]+1]
        bin_number = 0
        for start_time, end_time in zip(bin_start_times, bin_end_times):
            sample_count = random.randint(50, 100)
            # Setup the data for this bin
            diameter = float(random.randint(300, 700))/100
            pos_x = random.randint(0, 1024)
            pos_y = random.randint(0, 768)
            # The nan value will set the number of Saccades
            nan = random.randint(0, int(0.5*sample_count/event_bins[idx]))

            # Repeat this data over the bin duration
            time_samples = np.linspace(start_time, end_time, sample_count)
            other_column_1_samples = np.random.randint(10, size=sample_count)
            other_column_2_samples = np.random.randint(20, size=sample_count)
            diameter_samples = np.repeat(diameter, sample_count)
            pos_x_samples = np.repeat(pos_x, sample_count)
            pos_y_samples = np.repeat(pos_y, sample_count)
            # Make all of the events fixations except for the first 'nan' of
            # them (which are made Saccades)
            event_info_samples = np.repeat('Fixation', sample_count)
            event_info_samples[0:nan] = 'Saccade'

            # Add these values to the arrays used to construct the samples file
            samples_times = np.append(samples_times, time_samples)
            samples_other_column_1 = np.append(samples_other_column_1,
                                               other_column_1_samples)
            samples_other_column_2 = np.append(samples_other_column_2,
                                               other_column_2_samples)
            samples_diameters = np.append(samples_diameters, diameter_samples)
            samples_pos_xs = np.append(samples_pos_xs, pos_x_samples)
            samples_pos_ys = np.append(samples_pos_ys, pos_y_samples)
            samples_event_infos = np.append(samples_event_infos,
                                            event_info_samples)

            # Add these values to the arrays used to construct the binned file
            if event_type != 'garbage_label':
                binned_event_types.append(event_type)
                binned_event_ids.append(event_ids[idx])
                binned_event_groups.append(event_groups[idx])
                binned_event_orders.append(idx)
                binned_bin_numbers.append(bin_number)
                binned_diameters.append(diameter)
                binned_pos_xs.append(pos_x)
                binned_pos_ys.append(pos_y)
                binned_nans.append(nan)

            # Update the bin_number
            bin_number = bin_number+1

    samples = pd.DataFrame.from_dict({
        'Other Column 1': samples_other_column_1,
        'Other Column 2': samples_other_column_2,
        'Time': samples_times * 1000,
        'L Pupil Diameter [mm]': samples_diameters,
        'L POR X [px]': samples_pos_xs,
        'L POR Y [px]': samples_pos_ys,
        'L Event Info': samples_event_infos})

    binned = pd.DataFrame.from_dict({
        'Label': binned_event_types,
        'ID': binned_event_ids,
        'Condition': binned_event_groups,
        'Event_Order': binned_event_orders,
        'Bin_Number': binned_bin_numbers,
        'L Diameter': binned_diameters,
        'Pos X': binned_pos_xs,
        'Pos Y': binned_pos_ys,
        'NANS': binned_nans})

    return {'samples': samples,
            'labels': labels,
            'merged_labels': merged_labels,
            'binned': binned}


def save_mock_begaze_data(output_path, data, subject_id, task_order, task_name):
    """
    Save the mock begaze files to output_path.
    """

    base_path = ''.join([output_path, str(subject_id), str(task_order)])
    samples_path = ''.join([base_path, '_begaze_samples.txt'])
    labels_path = ''.join([base_path, '_begaze_labels.txt'])
    binned_path = ''.join([base_path, '_begaze_binned.txt'])
    merged_labels_path = ''.join([base_path, '_begaze_merged_labels.txt'])

    data['samples'].to_csv(samples_path, sep="\t")
    data['labels'].to_csv(labels_path, sep="\t")
    data['binned'].to_csv(binned_path, sep="\t")
    data['merged_labels'].to_csv(merged_labels_path, sep="\t")
