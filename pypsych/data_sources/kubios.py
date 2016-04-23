#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Kubios data source class
"""
import pandas as pd
import numpy as np
from io import StringIO
from scipy.io import loadmat
from data_source import DataSource
from schema import Schema, Or, Optional


def _val(x, pos, label_bin):
    return np.mean(x)


def _std(x, pos, label_bin):
    return x.std(axis=0)


def _sem(x, pos, label_bin):
    return x.sem(axis=0)


def _var(x, pos, label_bin):
    return np.var(x)


def _start_time(x, pos, label_bin):
    return x.index.values[0]


def _end_time(x, pos, label_bin):
    return x.index.values[-1]


class Kubios(DataSource):
    def __init__(self, config, schedule):

        # Call the parent class init
        super(Kubios, self).__init__(config, schedule)

        # cols = ['Time (s)', 'Mean RR (ms)', 'STD RR (ms)', 'Mean HR (1/min)',
        #         'STD HR (1/min)', 'RMSSD (ms)', 'NN50 (count)', 'pNN50 (%)',
        #         'VLF peak (Hz)', 'LF peak (Hz)', 'HF peak (Hz)',
        #         'VLF power (ms^2)', 'LF power (ms^2)', 'HF power (ms^2)',
        #         'VLF power.1 (%)', 'LF power.1 (%)', 'HF power.1 (%)',
        #         'LF power.2 (n.u.)', 'HF power.2 (n.u.)', 'LF/HF ratio ',
        #         'ApEn ', 'SampEn ']
        # self.panels = {col: {'VAL': _val, 'SEM': _sem} for col in cols}
        self.panels = {"Time (s)": {'Start Time': _start_time,
                                    'End Time': _end_time}}

    def load(self, file_paths):
        """Override for load method to include .mat compatibility."""

        fbuffer = ""
        with open(file_paths['samples'], 'r') as f:
            reader = False
            for line in f:
                if "TIME-VARYING RESULTS" in line:
                    reader = True
                elif reader & ("RR INTERVAL DATA" in line):
                    reader = False
                if reader:
                    fbuffer = fbuffer + line

        df = pd.read_csv(StringIO(unicode(fbuffer)),
                         delimiter=";",
                         skipinitialspace=True,
                         index_col=False,
                         skiprows=3)
        newcolumns = ["{} {}".format(*col)
                      for col in zip(df.columns[1:-2],
                                     df.iloc[0, 1:-2].fillna(""))]
        df = df.iloc[1:, 1:-2]
        df.columns = newcolumns
        df = df.astype(np.float)
        self.data['samples'] = df

        raw_mat = loadmat(file_paths['labels'])
        events = raw_mat['events'][:, 0]
        self.data['labels'] = pd.DataFrame({'flag': events},
                                           index=np.arange(events.size))

    def merge_data(self):
        """
        Clean and merge the samples and labels data.
        """
        # TODO(janmtl): return an error if the files have not been loaded yet.

        # Clean the samples data frame and the labels data frame
        self.data['samples'] = self._clean_samples(self.data['samples'])
        self.data['labels'] = self._clean_labels(self.data['labels'])

        self.label_config = self._label_config_to_df(self.config)

        # Combine the labels data with the labels configuration
        self.data['labels'] = self._merge_labels_and_config(
            labels=self.data['labels'],
            config=self.label_config)

    @staticmethod
    def _label_config_to_df(config):
        """Convert the label configuration dictionary to a data frame."""
        labels_list = []
        for event_type, label_config in config.iteritems():
            pattern = label_config['pattern']
            if isinstance(pattern, dict):
                for event_group, flag in label_config['pattern'].iteritems():
                    labels_list.append({
                        'Label': event_type,
                        'Condition': event_group,
                        'Duration': label_config['duration'],
                        'N_Bins': label_config['bins'],
                        'Left_Trim': label_config.get('left_trim', 0),
                        'Right_Trim': label_config.get('right_trim', 0),
                        'flag': flag})
            elif isinstance(pattern, int):
                labels_list.append({
                    'Label': event_type,
                    'Condition': np.nan,
                    'Duration': label_config['duration'],
                    'N_Bins': label_config['bins'],
                    'Left_Trim': label_config.get('left_trim', 0),
                    'Right_Trim': label_config.get('right_trim', 0),
                    'flag': pattern})
            else:
                raise Exception('Bad Biopac config flag {}'.format(pattern))

        return pd.DataFrame(labels_list)

    @staticmethod
    def _clean_labels(labels):
        """
        Turn the Biopac flag channel into a data frame of label flags and start
        times.
        """
        # TODO(janmtl): finish this docstring
        flags = labels['flag'].values
        low_offset = np.append(-255, flags)
        high_offset = np.append(flags, flags[-1])
        sel = ((low_offset-high_offset) != 0)[:-1]
        event_flags = flags[sel]
        start_times = np.where((low_offset-high_offset) != 0)[0]

        labels = pd.DataFrame({'flag': event_flags,
                               'Start_Time': start_times})

        labels = labels[(labels['flag'] != 255)]
        return labels

    @staticmethod
    def _clean_samples(samples):
        """
        .
        """
        samples['pos'] = True
        samples['Time'] = samples['Time (s)'].copy(deep=True)
        samples.set_index('Time', drop=True, inplace=True)
        return samples

    @staticmethod
    def _merge_labels_and_config(labels, config):
        """
        Merge together the contents of the labels file with the label
        configuration dictionary.
        """
        labels = pd.merge(labels, config, on='flag')
        labels = labels.sort_values(by='Start_Time', axis=0)
        return labels

    def create_label_bins(self, labels):
        """Replace the N_Bins column with Bin_Index and the Duration column
        with End_Time. This procedure grows the number of rows in the labels
        data frame."""
        total_bins = labels['N_Bins'].sum()
        label_bins = pd.DataFrame(columns=['Order', 'ID', 'Label',
                                           'Condition', 'Bin_Order',
                                           'Start_Time', 'End_Time',
                                           'Bin_Index'],
                                  index=np.arange(0, total_bins))
        idx = 0
        for _, label in labels.iterrows():
            n_bins = label['N_Bins']
            cuts = np.linspace(start=label['Start_Time'] + label['Left_Trim'],
                               stop=(label['Start_Time']
                                     + label['Duration']
                                     - label['Right_Trim']),
                               num=n_bins+1)
            label_info = np.tile(label.as_matrix(columns=['Label',
                                                          'Condition']),
                                 (n_bins, 1))

            # Order and ID
            label_bins.iloc[idx:idx+n_bins, 0:2] = np.nan
            # Label, Condition
            label_bins.iloc[idx:idx+n_bins, 2:4] = label_info
            # Bin_Order
            label_bins.iloc[idx:idx+n_bins, 4] = idx+np.arange(0, n_bins, 1)
            # Start_Time
            label_bins.iloc[idx:idx+n_bins, 5] = cuts[0:n_bins]
            # End_Time
            label_bins.iloc[idx:idx+n_bins, 6] = cuts[1:n_bins+1]
            # Bin_Index
            label_bins.iloc[idx:idx+n_bins, 7] = np.arange(0, n_bins, 1)

            idx = idx + n_bins

        # Add the Order by iterating over Labels and Bin indices
        for lc, group in label_bins.groupby(['Label', 'Bin_Index']):
            selector = (label_bins['Label'] == lc[0]) & \
                       (label_bins['Bin_Index'] == lc[1])
            label_bins.loc[selector, 'Order'] = \
                np.arange(0, np.sum(selector), 1)

        label_bins[['Start_Time', 'End_Time']] = \
            label_bins[['Start_Time', 'End_Time']] / 1000.0

        return label_bins

    @staticmethod
    def _validate_config(raw):
        """
        Validates the label configuration dict passed to the Data Source.

        Args:
          raw (dict): must match the following schema
            {event_type (str):
              {
                duration: (float or int),
                bins: (int),
                pattern: dictionary of flags keyed by group
              }
            }
        """
        # TODO(janmtl): improve this docstring
        schema = Schema({str: {'duration': Or(float, int),
                               'bins': int,
                               'pattern': Or(int, {str: int}),
                               Optional('left_trim'): Or(float, int),
                               Optional('right_trim'): Or(float, int)}})

        return schema.validate(raw)

    @staticmethod
    def _validate_schedule(raw):

        """
        Validates the schedule configuration dict passed to the Data Source.

        Args:
          raw (dict): must match the following schema
            {file_type (str): pattern (str)}
        """
        schema = Schema({str: str})

        return schema.validate(raw)
