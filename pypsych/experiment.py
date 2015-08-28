#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Experiment class.
"""
import pandas as pd
import numpy as np
from config import Config
from schedule import Schedule
from data_sources.begaze import BeGaze
from data_sources.biopac import Biopac
from data_sources.eprime import EPrime
from clint.textui import progress

DATA_SOURCES = {'BeGaze': BeGaze, 'Biopac': Biopac, 'EPrime': EPrime}


class Experiment(object):
    """
    Main task runner for pypsych.
    """
    def __init__(self, config_path, schedule_path, data_paths):
        self.config_path = config_path
        self.schedule_path = schedule_path
        self.data_paths = data_paths
        self.config = Config(self.config_path)
        self.schedule = Schedule(self.schedule_path)
        self.output = {}

        # Data sources will be preserved in memory across trials. This is to
        # ensure that the future Masker data source does not read hundreds of
        # bitmaps repeatedly.
        self.data_sources = {}

    def compile(self):
        """
        Compile the schedule on the data_paths and spin-up the data sources
        for each task_name.
        """
        self._load()
        self.schedule.compile(self.data_paths)

        task_datas = self.schedule\
                         .sched_df[['Task_Name', 'Data_Source_Name']]\
                         .drop_duplicates()

        for _, task_data in task_datas.iterrows():
            subconfig = self.config.get_subconfig(*tuple(task_data))
            subschedule = self.schedule.get_subschedule(*tuple(task_data))
            self.data_sources[tuple(task_data)] = \
                DATA_SOURCES[task_data['Data_Source_Name']](subconfig,
                                                            subschedule)

        self.validate_files()

    def process(self):
        """
        Iterate over the (subject, task) pairs and process each data source.
        """

        self.schedule.drop_incomplete_subjects()

        grouped = self.schedule.sched_df.groupby(['Subject',
                                                  'Task_Name',
                                                  'Data_Source_Name'])
        tots = len(grouped)
        prog = 0
        self.output = {task_name: {} for task_name in self.config.task_names}

        # Iterate over subjects, tasks, and data sources
        with progress.Bar(label="Processing ", expected_size=tots) as pbar:
            pbar.show(prog)
            for idx, _ in grouped:
                print idx
                # Fetch the file paths from the schedule for this trial
                file_paths = self.schedule.get_file_paths(*idx)
                subject_id, task_name, data_source_name = idx
                ds_id = tuple([task_name, data_source_name])

                # Load and process the data source in question
                self.data_sources[ds_id].load(file_paths)
                self.data_sources[ds_id].process()

                # Iterate over the outputs and append them to existing output
                # data frames if possible
                ds_out = self.data_sources[ds_id].output
                panels = self.data_sources[ds_id].panels

                for channel, statistics in panels.iteritems():
                    # Insert a column for the subject id since the data
                    # sources are ignorant of this
                    ds_out[channel].loc[:, :, 'Subject'] = subject_id

                    # If the channel already exists, append to it, otherwise
                    # save it
                    if channel in self.output[task_name].keys():
                        self.output[task_name][channel] = pd.concat(
                            [self.output[task_name][channel], ds_out[channel]],
                            ignore_index=True,
                            axis=1)
                    else:
                        self.output[task_name][channel] = ds_out[channel]

                prog = prog + 1
                pbar.show(prog)

    def validate_files(self):
        """
        Iterate over the (subject, task) pairs and validate each data source.
        """

        # First, run the normal validation on the Schedule
        vf = self.schedule.validate_files()

        grouped = self.schedule.sched_df.groupby(['Subject',
                                                  'Task_Name',
                                                  'Data_Source_Name'])

        validation = {}

        # Iterate over subjects, tasks, and data sources
        for idx, _ in grouped:
            # Fetch the file paths from the schedule for this trial
            file_paths = self.schedule.get_file_paths(*idx)
            subject_id, task_name, data_source_name = idx
            ds_id = tuple([task_name, data_source_name])

            # Load and process the data source in question
            try:
                self.data_sources[ds_id].load(file_paths)
            except KeyError as e:
                validation[idx] = {str(e)[1:-1]: False}
            else:
                validation[idx] = self.data_sources[ds_id].validate_data()

            # TODO(janmtl): The above will not report a samples file that is
            # empty when a labels file is missing

        # Now we take the newly found validation informaiton (that pertains to
        # corrupt, rather than missing files) and transform the schedule
        # validation matrix
        ef = [{'Subject': subject,
               'Task_Name': task,
               'File': file_type,
               'Data_Source_Name': ds_name,
               'Status': status}
              for (subject, task, ds_name), sub in validation.iteritems()
              for file_type, status in sub.iteritems()]
        ef = pd.DataFrame.from_dict(ef)
        ef = ef.pivot_table(index='Subject',
                            columns=['Task_Name',
                                     'Data_Source_Name',
                                     'File'],
                            values='Status',
                            aggfunc=lambda x: x).replace(np.nan, True)
        ef = ef.as_matrix()
        zf = vf.as_matrix()
        yf = np.copy(zf).astype(np.object)
        yf[zf] = 'Found'
        yf[~ef] = 'Corrupt'
        yf[~zf] = 'Missing'
        vf.loc[:, :] = yf
        self.validation = vf

    def drop_incomplete_subjects(self):
        """."""
        sel = (self.validation == 'Found').all(axis=1)
        valid_subjects = list(self.validation.index[sel])
        self.schedule.sched_df = self.schedule.sched_df[
            self.schedule.sched_df['Subject'].isin(valid_subjects)]

    def pivot_outputs(self):
        """Pivot."""
        # TODO(janmtl): improve this docstring

        pivot_out = {}

        for task_name in self.config.task_names:
            pivot_out[task_name] = {}
            for channel, stats in self.output[task_name].iteritems():
                pivot_out[task_name][channel] = {}
                stats.loc[:, :, 'Event'] = stats.loc[:, :, 'Label'] \
                    + stats.loc[:, :, 'Bin_Index'].astype(str)
                for stat_name, stat in stats.iteritems():
                    # Only allow for indices which are filled and discard the
                    # rest
                    full_cols = stat[['Subject', 'Condition',
                                      'ID', 'Order']].dropna(how='all', axis=1)\
                                                     .columns

                    if ('ID' in full_cols) & ('Order' in full_cols):
                        full_cols.drop('Order')

                    stat_piv = pd.pivot_table(
                        stat,
                        values='stat',
                        index=list(full_cols),
                        columns='Event',
                        aggfunc=lambda x: x)

                    pivot_out[task_name][channel][stat_name] = stat_piv

        return pivot_out

    def _load(self):
        """Create and load the configuration and schedule."""
        self.config.load()
        self.schedule.load()

    # Useful function for recursing down a dictionary of DataFrames
    def save_output(self, output, output_path):
        self._recurse_dict_and_save_df(output, output_path)

    def _recurse_dict_and_save_df(self, node, path):
        if isinstance(node, dict):
            for key, next_node in node.iteritems():
                next_path = path + key + '_'
                self._recurse_dict_and_save_df(next_node, next_path)
        elif isinstance(node, pd.DataFrame):
            node.to_csv(path+'.txt', sep="\t")
        else:
            pass

    # Shortcuts
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

    def isolate_data_source(self, data_source_name):
        """Removes all data sources except given data source name."""
        self.schedule.isolate_data_source(data_source_name)
