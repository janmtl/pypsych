#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Provides the base DataSource class for pypsych data sources.
"""

import pandas as pd
import numpy as np


class DataSource(object):
    """
    DataSource base class.
    """

    def __init__(self, config, schedule):
        self.config = self._validate_config(config)
        self.schedule = self._validate_schedule(schedule)
        self.output = pd.Panel()
        self.data = {}

    def load(self, file_paths):
        """By default, loads all files as TSV."""
        for file_type, file_path in file_paths.iteritems():
            self.data[file_type] = pd.read_csv(file_path,
                                               comment="#",
                                               delimiter="\t",
                                               skipinitialspace=True)

    def process(self):
        """."""
        self.merge_data()
        self.bin_data()

    def bin_data(self):
        """Makes a dict of dicts of pd.DataFrames at self.output."""
        label_bins = self.create_label_bins(self.data['labels'])
        major_axis = label_bins.index.values
        minor_axis = label_bins.drop(['Start_Time', 'End_Time'], axis=1).columns
        minor_axis = minor_axis.append(pd.Index(['stat']))

        raw = self.data['samples']

        output = {channel: pd.Panel(items=statistics.keys(),
                                    major_axis=major_axis,
                                    minor_axis=minor_axis)
                  for channel, statistics in self.panels.iteritems()}

        for channel, statistics in self.panels.iteritems():
            for stat_name, stat_fun in statistics.iteritems():
                stats = []
                new_panel = label_bins.copy(deep=True)
                new_panel.drop(['Start_Time', 'End_Time'], axis=1, inplace=True)
                for _, label_bin in label_bins.iterrows():
                    selector = (raw.index.values >= label_bin['Start_Time']) \
                               & (raw.index.values < label_bin['End_Time'])
                    samples = raw[selector][channel]
                    pos = raw.loc[selector, 'pos']
                    stats.append(stat_fun(samples, pos))

                new_panel['stat'] = stats
                output[channel][stat_name] = new_panel.sort('Bin_Order')

        self.output = output

    @staticmethod
    def _validate_config(raw):
        """Placeholder method for validating configuration dicts."""
        return raw

    @staticmethod
    def _validate_schedule(raw):
        """Placeholder method for validating schedule configuration dicts."""
        return raw
