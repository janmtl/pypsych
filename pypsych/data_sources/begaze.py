#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the BeGaze data source class
"""
import pandas as pd
import numpy  as np
from itertools import product
from data_source import DataSource
from schema import Schema, Or


class BeGaze(DataSource):
    def __init__(self, config, schedule):
        
        # Call the parent class init
        super(BeGaze, self).__init__(config, schedule)

        # Diameter channel statistics
        self.panels = {'Diameter': {'VAL': np.mean,
                                    'SEM': lambda x: x.sem(axis=0),
                                    'COUNT': np.size,
                                    'NANS': lambda x: np.isnan(x).sum()}}

    def process(self):
        """."""
        self.merge_data()
        self.bin_data()

    def merge_data(self):
        """
        Clean and merge the samples and labels data.
        """
        # TODO(janmtl): return an error if the files have not been loaded yet.

        # Clean the samples data frame and the labels data frame
        self.data['samples'] = self._clean_samples(self.data['samples'])
        self.data['labels'] = self._clean_labels(self.data['labels'])

        # Combine the labels data with the labels configuration
        self.data['labels'] = self._merge_labels_and_config(
            labels=self.data['labels'],
            config=self.config)

        self.data['labels'] = self._clean_duplicate_labels(self.data['labels'])

    @staticmethod
    def _clean_labels(labels):
        """
        Extract relevant columns from BeGaze labels file and add new columns
        that will hold the label configuration information.

        Args:
          labels (pandas Data Frame): result of the 
        """
        # TODO(janmtl): finish this docstring
        # Extract and rename relevant columns
        labels = labels[['Time Trial [ms]', 'Event']]
        labels.columns = ['Start_Time', 'Event']
        # Create new columns to hold the additional label info
        temp_labels = pd.DataFrame(index=labels.index,
                                   columns=['Event_Type',
                                            'Event_Group',
                                            'Event_ID',
                                            'Event_Order',
                                            'Duration',
                                            'N_Bins'])
        labels = pd.concat([labels, temp_labels], axis=1)      
        return labels

    @staticmethod
    def _clean_samples(samples):
        """
        Turn any non-Fixation data points into NaN values and extract and
        relabel the columns.

        Args:
          samples (pandas Data Frame): data frame resulting from loading the
            BeGaze samples file.
        """
        # Extract and rename columns of interest. We are using the left pupil
        # by convention.
        samples = samples.loc[:, ['Time', \
                                   'L Pupil Diameter [mm]', \
                                   'L Event Info']]
        samples.columns = ['Time', 'Diameter', 'info']

        # Adjust the sample time to the epoch at the top of the file and convert
        # to milliseconds.
        samples[['Time']] = samples[['Time']] - samples.loc[0, 'Time']
        samples[['Time']] = samples[['Time']]/1000

        # Change the data frame index to the Time column for faster indexing
        # later.
        samples.set_index('Time', drop=True, inplace=True)

        # Replace any non-fixation data points with NaN values and drop the
        # 'info' axis which identifies such points.
        no_fixations = (samples['info'] != 'Fixation')
        samples.loc[no_fixations,:] = np.nan
        samples.drop('info', axis=1, inplace=True)

        return samples

    @staticmethod
    def _merge_labels_and_config(labels, config):
        """
        Merge together the contents of the labels file with the label
        configuration dictionary.

        Args:
          labels (pandas Data Frame): result of _clean_labels on the BeGaze
            labels file.
          config (dict): the label configuration dictionary used to initialize
            this data source.

        Output:
          labels (pandas Data Frame): the resulting merged data frame with the
            following columns ['Start_Time', Event_Type', 'Duration', 'N_Bins']
        """
        # Iterate over label configurations
        for event_type, label_config in config.iteritems():
            
            # Match given regex pattern on the entire labels data frame
            temp_labels = labels['Event'].str.extract(label_config['pattern'])
            
            # If the regex only contains one field, the DataFrame.extract
            # operation above will only return a Series. Thus, change this
            # Series to a Data Frame
            if isinstance(temp_labels, pd.core.series.Series):
                temp_labels = pd.DataFrame(temp_labels)

            # The temp_pos is the address of all labels that matched the current
            # regex.
            temp_pos = pd.notnull(temp_labels).any(1)

            # Write in the various properites of this label into the temp_labels
            # data frame at the positions indicated by temp_pos.
            temp_labels.loc[temp_pos, 'Event_Type'] = event_type
            temp_labels.loc[temp_pos, 'Duration'] = label_config['duration']
            temp_labels.loc[temp_pos, 'N_Bins'] = label_config['bins']
            labels.update(temp_labels)

        # Fill out the Event_Order column
        labels['Event_Order'] = np.arange(0, len(labels['Event_Order']))

        # Any labels that went unrecognized by any regex pattern should be
        # dropped.
        labels.dropna(axis=0,
                      how='any',
                      subset = ['Event_Type', 'Event_Group', 'Event_ID',
                                'Duration', 'N_Bins'],
                      inplace=True)

        # Drop the now superfluous 'Event' column
        labels.drop('Event', axis=1, inplace=True)

        # Make sure that the times and durations are handled as floats not
        # strings.
        labels[['Start_Time', 'Duration']] = \
            labels[['Start_Time', 'Duration']].astype(np.float64)
        # Make sure that N_Bins is an integer
        labels[['N_Bins']] = labels[['N_Bins']].astype(np.int64)

        return labels

    @staticmethod
    def _clean_duplicate_labels(labels):
        """
        In the case of labels that appear more than once (such as in certain
        cases of calibration tasks), add a running ID suffix to those labels.

        Args:
            labels (pandas Data Frame)

        Outputs:
            labels (pandas Data Frame)
        """

        # Group the labels by their duplicates
        duplicate_labels = labels[labels.duplicated(subset=['Event_ID',
                                                            'Event_Type'])]
        grouped = duplicate_labels.groupby(['Event_ID', 'Event_Type'])

        # In each group of duplicates, add a suffix to the Event_ID
        for _, label in grouped:
            labels.loc[label.index, 'Event_ID'] = \
                label['Event_ID'] + np.arange(1,label.shape[0]+1,1).astype(str)

        return labels

    @staticmethod
    def _create_label_bins(labels):
        """Replace the N_Bins column with Bin_Index and the Duration column
        with End_Time. This procedure grows the number of rows in the labels
        data frame."""

        total_bins = labels['N_Bins'].sum()
        label_bins = pd.DataFrame(columns=['Event_ID','Event_Type',
                                           'Event_Group', 'Event_Order',
                                           'Start_Time', 'End_Time',
                                           'Bin_Index'],
                                  index=np.arange(0,total_bins))
        idx = 0
        for event_order, label in labels.iterrows():
            n_bins = label['N_Bins']
            cuts = np.linspace(start=label['Start_Time'],
                               stop=(label['Start_Time'] + label['Duration']),
                               num=n_bins+1)
            label_info = np.tile(label.as_matrix(columns = ['Event_ID',
                                                            'Event_Type',
                                                            'Event_Group']),
                                 (n_bins, 1))

            label_bins.iloc[idx:idx+n_bins, 0:3] = label_info
            label_bins.iloc[idx:idx+n_bins, 3] = idx+np.arange(0,n_bins,1)
            label_bins.iloc[idx:idx+n_bins, 4] = cuts[0:n_bins]
            label_bins.iloc[idx:idx+n_bins, 5] = cuts[1:n_bins+1]
            label_bins.iloc[idx:idx+n_bins, 6] = np.arange(0,n_bins,1)
            idx = idx + n_bins

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
                pattern: (str)
              }
            }
        """
        schema = Schema({str: {'duration': Or(float, int),
                               'bins': int,
                               'pattern': str}})

        # TODO(janmtl): This should also validate that pattern regex returns an
        # Event_ID and an Event_Group
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


