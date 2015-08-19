#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Includes the EPrime data source class."""

# TODO(janmtl): Provide an interface that deuglifies the _0 and channels in this
# interface
import pandas as pd
import io
from data_source import DataSource
from schema import Schema


class EPrime(DataSource):
    def __init__(self, config, schedule):
        """."""
        # Call the parent class init
        super(EPrime, self).__init__(config, schedule)

    def load(self, file_paths):
        """Load Keyvalue-format edat file."""
        with io.open(file_paths['samples'], 'r', encoding="utf-16") as kv_file:
            raw = kv_file.read()
            raw = raw.replace('\t', '')
            raw = raw.replace('*** LogFrame End ***', '')
            raw = raw.replace('Level: 2', '')
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
        self.data['samples'] = self._clean_samples(self.data['samples'])
        sel = ['ID', 'Condition'] + self.config['channels']
        self.data['samples'] = self.data['samples'][sel]

    def bin_data(self):
        """Makes a dict of dicts of pd.DataFrames at self.output."""
        self.output = {channel: self.data['samples'][['ID', 'Condition',
                                                      channel]]
                       for channel in self.config['channels']}

    @staticmethod
    def _clean_samples(samples):
        """."""
        return samples.rename(columns={'Img': 'ID'})

    @staticmethod
    def _validate_config(raw):
        """
        Validate the label configuration dict passed to the Data Source.

        Args:
          raw (dict): must match the following schema
            {channels: [column_names]}
        """
        schema = Schema({'channels': [str]})
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
