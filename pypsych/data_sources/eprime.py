#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Includes the EPrime data source class."""

# TODO(janmtl): Provide an interface that deuglifies the _0 and channels in this
# interface
import pandas as pd
import io
from data_source import DataSource
from schema import Schema, Or
from utils import merge_and_rename_columns


def _idem(x, pos, label_bin):
    return x.values[0]


class EPrime(DataSource):
    def __init__(self, config, schedule):
        """."""
        # Call the parent class init
        super(EPrime, self).__init__(config, schedule)

        channels = self.config.keys()
        channels.remove('ID')
        channels.remove('Condition')
        self.panels = {channel: {'VAL': _idem}
                       for channel in channels}

    def load(self, file_paths):
        """Load Keyvalue-format edat file."""
        with io.open(file_paths['samples'], 'r', encoding="utf-16") as kv_file:
            raw = kv_file.read()
            raw = raw.replace('\t', '')
            raw = raw.replace('*** LogFrame End ***', '')
            arr = raw.split('*** LogFrame Start ***')
            frames = []
            for frame in arr:
                lines = frame.split('\n')
                lines = [line.split(':', 1) for line in lines]
                d = {line[0].strip(' '): line[1].strip(' ')
                     for line in lines
                     if len(line) == 2}
                frames.append(d)
            self.data['samples'] = pd.DataFrame.from_dict(frames)

    def merge_data(self):
        """Clean the EPrime file data."""
        # Assemble samples
        self.data['samples'] = self._clean_samples(self.data['samples'])
        self.data['samples'].loc[:, 'pos'] = True
        # Assemble labels
        self.data['labels'] = self.data['samples'].loc[:, ['ID', 'Condition']]
        self.data['labels'].loc[:, 'Label'] = None

    def create_label_bins(self, labels):
        """Construct the dummy label_bins dataframe."""
        label_bins = labels
        label_bins.loc[:, 'Order'] = labels.index.values - 1
        label_bins.loc[:, 'Bin_Order'] = labels.index.values
        label_bins.loc[:, 'Start_Time'] = labels.index.values
        label_bins.loc[:, 'End_Time'] = labels.index.values + 1
        label_bins.loc[:, 'Bin_Index'] = 0
        return label_bins

    def _clean_samples(self, samples):
        """
        Create the columns from the keys and names that were passed into the
        configuration.
        """
        for key, names in self.config.iteritems():
            samples = merge_and_rename_columns(samples, key, names)

        # Pick out only the columns of interest
        samples = samples.loc[:, self.config.keys()]

        # Pick out only the rows that are not all nan
        samples.dropna(how='all', axis=0, inplace=True)

        return samples

    @staticmethod
    def _validate_config(raw):
        """
        Validate the label configuration dict passed to the Data Source.

        Args:
          raw (dict): must match the following schema
            {'ID': key name or list of keys,
             'Condition': key name or list of keys,
             'Channels': list of keys}}
        """
        schema = Schema({'ID': Or([str], str),
                         'Condition': Or([str], str),
                         str: Or([str], str)})
        return schema.validate(raw)

    @staticmethod
    def _validate_schedule(raw):
        """
        Validate the schedule configuration dict passed to the Data Source.

        Args:
          raw (dict): must match the following schema
            {file_type (str): pattern (str)}
        """
        schema = Schema({str: str})

        return schema.validate(raw)
