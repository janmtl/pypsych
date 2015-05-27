#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Experiment class.
"""
import pandas as pd
import numpy  as np
from config import Config
from schedule import Schedule
from data_sources.begaze import BeGaze
from data_sources.biopac import Biopac

DATA_SOURCES = {'BeGaze': BeGaze, 'Biopac': Biopac}

class Experiment(object):
    """
    Main task runner for pypsych.
    """
    def __init__(self, config_path, schedule_path, data_path):
        self.config_path = config_path
        self.schedule_path = schedule_path
        self.data_path = data_path
        self.config = Config(self.config_path)
        self.schedule = Schedule(self.schedule_path)

        # Output will be stored in a massive pandas Panel
        self.output_dict = {}
        self.output = pd.Panel()

        # Data sources will be preserved in memery across trials. This is to
        # ensure that the future Masker data source does not read hundreds of
        # bitmaps repeatedly.
        self.data_sources = {}

    def load(self):
        """Create and load the configuration and schedule."""
        self.config.load()
        self.schedule.load()

    def compile(self):
        """
        Compile the schedule on the data_path and spin-up the data sources
        for each task_name.
        """
        self.schedule.compile(self.data_path)

        task_datas = self.schedule.\
                        sched_df[['Task_Name', 'Data_Source_Name']].\
                        drop_duplicates()

        for _, task_data in task_datas.iterrows():
            subconfig = self.config.get_subconfig(*tuple(task_data))
            subschedule = self.schedule.get_subschedule(*tuple(task_data))
            self.data_sources[tuple(task_data)] = \
                DATA_SOURCES[task_data['Data_Source_Name']](subconfig,
                                                            subschedule)

    def process(self):
        """
        Iterate over the (subject, task) pairs and process each data source.
        """

        grouped = self.schedule.sched_df.groupby(['Subject_ID',
                                                  'Task_Name',
                                                  'Data_Source_Name'])
        # Iterate over subjects, tasks, and data sources
        for idx, _ in grouped:
            # Fetch the file paths from the schedule for this trial
            file_paths = self.schedule.get_file_paths(*idx)
            subject_id, task_name, data_source_name = idx
            ds_id = tuple([task_name, data_source_name])

            # Load and process the data source in question
            self.data_sources[ds_id].load(file_paths)
            self.data_sources[ds_id].process()

            # Iterate over the outputs and append them to existing output data
            # frames if possible
            for p_id, panel in self.data_sources[ds_id].output.iteritems():
                # Insert a column for the subject id since the data sources are
                # ignorant of this
                panel['Subject_ID'] = subject_id

                # Panels are indexed by (task_name, channel, statistic)
                panel_id = (task_name,)+p_id

                # If the panel already exists, append to it, otherwise save it
                if panel_id in self.output_dict.keys():
                    self.output_dict[panel_id] = pd.concat(
                        [self.output_dict[panel_id], panel],
                        ignore_index=True)
                else:
                    self.output_dict[panel_id] = panel

        # Turn the dictionary of outputs into a pandas Panel object
        self.output = pd.Panel(self.output_dict)

    def save_outputs(self, output_path):
        """Save all of the items in the self.output Panel object to seperate
        files named using the the index (task_name, channel, statistic)."""

        for idx, item in self.output.iteritems():
            item_path = output_path+'/'+'_'.join(idx)+'.txt'
            item.to_csv(item_path, sep="\t")










