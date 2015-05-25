#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the BeGaze data source class
"""
import os
import re
import itertools
import pandas as pd
import numpy  as np
from pypsych.data_source import DataSource
from scipy import ndimage, misc

def nans(x):
    return np.isnan(x).sum()

def sem(x):
    return x.sem(axis=0)

class Begaze(DataSource):
    def __init__(self, config, schedule):
        self.config = config
        self.schedule = schedule
        self.output = pd.DataFrame()

    @staticmethod
    def parse_config(config):

    def process(self, Subject_ID):
        print 'Processing BeGaze for subject: '+str(Subject_ID)
        raw     = self.samples
        labels  = self.labels

        # Extract and rename relevant columns
        labels  = labels[['Time Trial [ms]', 'Event']]
        labels.columns = ['Start_Time', 'Event']
        temp_labels = pd.DataFrame(index = labels.index,
                                                             columns = ['Event_ID', 'Event_Group', 'Event_Type', 'Event_Duration', 'N_Bins'])
        labels = pd.concat([labels,temp_labels], axis = 1)

        for label_config in self.label_configs:
            temp_labels = labels['Event'].str.extract(label_config['pattern'])
            if isinstance(temp_labels, pd.core.series.Series): temp_labels = pd.DataFrame(temp_labels)
            temp_pos = pd.notnull(temp_labels).any(1)
            temp_labels.loc[temp_pos, 'Event_Type']     = label_config['event_type']
            temp_labels.loc[temp_pos, 'Event_Duration'] = label_config['event_duration']
            temp_labels.loc[temp_pos, 'N_Bins']         = label_config['n_bins']
            labels.update(temp_labels)
        labels.dropna(axis = 0, how = 'any', inplace = True)
        labels[['Start_Time', 'Event_Duration']] = labels[['Start_Time', 'Event_Duration']].astype(float)

        duplicate_labels = labels[labels.duplicated(subset=['Event_ID', 'Event_Type'])]
        grouped = duplicate_labels.groupby(['Event_ID', 'Event_Type'])
        for idx, label in grouped:
            labels.loc[label.index, 'Event_ID'] = label['Event_ID'] + np.arange(1,label.shape[0]+1,1).astype(str)

        labels['End_Time'] = labels['Start_Time'] + labels['Event_Duration']
        labels = labels.drop(['Event', 'Event_Duration'], 1)

        raw[['Time']] = raw[['Time']] - raw.loc[0, 'Time']
        raw[['Time']] = raw[['Time']]/1000

        stats = pd.DataFrame(columns = self.output_columns)
        
        grouped = labels.groupby('Event_ID')
        for event_id, group in grouped:
            event_stats = pd.DataFrame(columns = [])
            for idx, label in group.iterrows():
                selector = (raw['Time'] >= label['Start_Time']) & (raw['Time'] <= label['End_Time'])
                samples  = self.clean_samples(raw[selector])
                subgrouped = samples.groupby(pd.cut(x = samples.index,
                                                                                        bins = np.linspace( start = samples.index[0], 
                                                                                                                                stop  = samples.index[-1],
                                                                                                                                num   = label['N_Bins']+1)
                                                                                        ))
                sub_diam_stats  = subgrouped['Diameter'].agg({'MEAN': np.mean, 'SEM': sem, 'COUNT': np.size, 'NANS': nans})
                if 'ROI' in self.config.keys():
                    sub_roi_stats = subgrouped[['posx', 'posy']].apply(lambda x: self.apply_masks(x, event_id))
                    sub_stats = pd.merge(sub_diam_stats, sub_roi_stats, left_index=True, right_index=True)
                else:
                    sub_stats = sub_diam_stats
                sub_stats.reset_index(inplace=True, drop=True)
                sub_stats['Bin'] = sub_stats.index
                sub_stats['Event_Type'] = label['Event_Type']
                sub_stats['Subject_ID'] = Subject_ID
                event_stats = event_stats.append(sub_stats)

            event_stats['BinnedType'] = event_stats['Event_Type'] + '_' + event_stats['Bin'].astype(str)
            event_stats.drop(['Event_Type', 'Bin'], axis=1, inplace=True)
            event_stats = event_stats.pivot(index = 'Subject_ID', columns = 'BinnedType')
            event_stats.columns = event_stats.columns.swaplevel(0,1)
            event_stats.columns = ['_'.join(col) for col in event_stats.columns.values]
            event_stats['Event_ID']    = event_id
            event_stats['Event_Group'] = group['Event_Group'].iloc[0]
            event_stats.reset_index(inplace=True)
            stats = stats.append(event_stats)
        stats.reset_index(inplace=True)
        self.output = stats

    @staticmethod
    def clean_samples(raw):
        samples = raw[['Time', 'L Pupil Diameter [mm]', 'L POR X [px]', 'L POR Y [px]', 'L Event Info']]
        samples.columns = ['Time', 'Diameter', 'posx', 'posy', 'info']
        samples.set_index('Time', drop = True, inplace = True)
        no_fixations = (samples['info'] != 'Fixation')
        samples.loc[no_fixations,:] = np.nan
        # samples.drop('info', axis = 1, inplace=True)
        return samples

    @staticmethod
    def parse_config(config):
        self.label_config = 
        pass

    @staticmethod
    def validate_config(raw):
        pass

    @staticmethod
    def validate_schedule(raw):
        pass


