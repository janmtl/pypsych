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
from clint.textui import progress

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
        self.output = {}

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
        tots = len(grouped)
        prog = 0
        self.output = {task_name: {} for task_name in self.config.task_names}

        # Iterate over subjects, tasks, and data sources
        with progress.Bar(label="Processing ", expected_size=tots) as pbar:
            for idx, _ in grouped:
                # Fetch the file paths from the schedule for this trial
                file_paths = self.schedule.get_file_paths(*idx)
                subject_id, task_name, data_source_name = idx
                ds_id = tuple([task_name, data_source_name])

                # Load and process the data source in question
                self.data_sources[ds_id].load(file_paths)
                self.data_sources[ds_id].process()

                # Iterate over the outputs and append them to existing output
                # data frames if possible
                for p_id, panel in self.data_sources[ds_id].output.iteritems():
                    # Insert a column for the subject id since the data sources
                    # are ignorant of this
                    panel['Subject_ID'] = subject_id

                    # If the panel already exists, append to it, otherwise save
                    # it

                    if p_id in self.output[task_name].keys():
                        self.output[task_name][p_id] = pd.concat(
                            [self.output[task_name][p_id], panel],
                            ignore_index=True)
                    else:
                        self.output[task_name][p_id] = panel

                prog = prog +1
                pbar.show(prog)

        self._fill_index_columns()

    def save_outputs(self, output_path):
        """Save all of the items in the self.output dict object to seperate
        files named using the the index [task_name][(channel, statistic)]."""

        for task_name in self.config.task_names:
            for idx, item in self.output[task_name].iteritems():
                item_path = output_path+'/'+task_name+'_'+'_'.join(idx)+'.txt'
                item.to_csv(item_path, sep="\t")

    def _fill_index_columns(self):
        """Fill out Event_ID, Event_Type, Event_Group, Event_Order,
        Bin_Index, and Subject_ID for all output data frames."""

        idx_cols = [
            'Event_ID', 'Event_Type', 'Event_Group', 'Event_Order',
            'Bin_Index', 'Subject_ID']

        for task_name in self.config.task_names:
            all_idx = pd.DataFrame(columns=idx_cols)

            for idx, item in self.output[task_name].iteritems():
                all_idx = pd.merge(
                    item.dropna(how='all', axis=1).drop('_'.join(idx), axis=1),
                    all_idx,
                    how='outer'
                    )

            for idx in self.output[task_name].keys():
                self.output[task_name][idx][idx_cols] = all_idx[idx_cols]

    def save_pivoted_outputs(self, output_path):
        """Pivot."""
        # TODO(janmtl): improve this docstring

        for task_name in self.config.task_names:
            for idx, item in self.output[task_name].iteritems():
                item['Event'] = item['Event_Type'] \
                                + item['Bin_Index'].astype(str)

                # Only allow for indices which are filled and discard the rest
                all_cols = ['Subject_ID', 'Event_Group', 'Event_Order',
                            'Event_ID']
                full_cols = item.dropna(how='all', axis=1).columns
                piv_cols = [val for val in all_cols if val in full_cols]

                item_piv = pd.pivot_table(
                    item,
                    values='_'.join(idx),
                    index=piv_cols,
                    columns='Event',
                    aggfunc=lambda x: x)
                item_path = output_path+'/'+task_name+'_'+'_'.join(idx)+'.txt'
                item_piv.to_csv(item_path, sep="\t") 

    #Shortcuts
    def remove_subject(self, subject_ids):
        """Removes the given subject or subjects."""
        if isinstance(subject_ids, list):
            for subject_id in subject_ids:
                self.schedule.remove_subject(subject_id)
        else:
            self.schedule.remove_subject(subject_ids)

    def isolate_subject(self, subject_id):
        """Removes all subjects except given subject id."""
        self.schedule.isolate_subject(subject_id)

    def isolate_task(self, task_name):
        """Removes all tasks except given task name."""
        self.schedule.isolate_task(task_name)
        self.config.isolate_task(task_name)