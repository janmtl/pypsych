#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the Experiment class.
"""
import pandas as pd
import numpy as np
import yaml
import pickle
from pkg_resources import resource_filename
from config import Config
from schedule import Schedule
from data_sources.begaze import BeGaze
from data_sources.biopac import Biopac
from data_sources.eprime import EPrime
from data_sources.hrvstitcher import HRVStitcher

pd.set_option('display.max_colwidth', 1000)

DATA_SOURCES = {'BeGaze': BeGaze,
                'Biopac': Biopac,
                'EPrime': EPrime,
                'HRVStitcher': HRVStitcher}


class Experiment(object):
    """
    Main task runner for pypsych.
    """
    def __init__(self, config_path):
        self.config_path = config_path
        raw = yaml.load_all(open(config_path, 'r'))
        global_config, raw_sched, raw_config = [i for i in raw]

        self.data_paths = global_config['data_paths']
        self.pickle_path = global_config['pickle_path']
        self.excluded_subjects = global_config['excluded_subjects']

        self.config = Config(raw_config)
        self.schedule = Schedule(raw_sched)

        self.output = {}

        self.invalid_subjects = []
        self.valid_subjects = []
        self.validation = pd.DataFrame()

        # Data sources will be preserved in memory across trials. This is to
        # ensure that the future Masker data source does not read hundreds of
        # bitmaps repeatedly.
        self.data_sources = {}

    def save(self, path=None):
        if path is None:
            path = self.pickle_path
        pickle.dump(self, open(path, 'wb'))

    def compile(self, validate=False):
        """
        Compile the schedule on the data_paths and spin-up the data sources
        for each task_name.
        """
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

        self.remove_subject(self.excluded_subjects)

        if validate:
            self.validation, self.valid_subjects, self.invalid_subjects = \
                self.validate_files()
        else:
            self.validation = pd.DataFrame()
            self.valid_subjects = self.schedule.subjects
            self.invalid_subjects = []

    def process(self):
        """
        Iterate over the (subject, task) pairs and process each data source.
        """
        if hasattr(self, 'validation'):
            self.schedule.sched_df = self.schedule.sched_df[
                self.schedule.sched_df['Subject'].isin(self.valid_subjects)]

        grouped = self.schedule.sched_df.groupby(['Subject',
                                                  'Task_Name',
                                                  'Data_Source_Name'])

        self.output = {task_name: {} for task_name in self.config.task_names}

        # Iterate over subjects, tasks, and data sources
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
                            columns=['Data_Source_Name',
                                     'Task_Name',
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

        sel = (vf == 'Found').all(axis=1)
        nsel = (vf != 'Found').any(axis=1)
        valid_subjects = list(vf.index[sel])
        invalid_subjects = list(vf.index[nsel])

        return vf, valid_subjects, invalid_subjects

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

    def report_to_html(self, path):
        """Create an HTML report of the experiment at `path`."""



        # Experiment parameters stated in the "Overview" section
        if type(self.data_paths) is list:
            data_paths = '<br/>'.join(self.data_paths)
        else:
            data_paths = self.data_paths

        html = {'CONFIG_PATH': self.config_path,
                'PICKLE_PATH': self.pickle_path,
                'DATA_PATHS': data_paths,
                'VALID_SUBJECTS': str(self.valid_subjects),
                'INVALID_SUBJECTS': str(self.invalid_subjects),
                'EXCLUDED_SUBJECTS': str(self.excluded_subjects)}

        # The configuration and schedul yaml contents
        html['CONFIG'] = yaml.dump(self.config.raw)
        html['SCHEDULE'] = yaml.dump(self.schedule.raw)

        # The validation table
        validation = self.validation.copy(deep=True)
        validation = validation.loc[self.invalid_subjects, :]
        validation_html = validation.to_html()
        validation_html = validation_html.replace('<td>Found</td>',
                                                  '<td class="found"></td>')
        validation_html = validation_html.replace('<td>Corrupt</td>',
                                                  '<td class="corrupt"></td>')
        validation_html = validation_html.replace('<td>Missing</td>',
                                                  '<td class="missing"></td>')
        validation_html = validation_html.replace(
            '<table border="1" class="dataframe">',
            '<table class="table table-bordered">')

        html['VALIDATION'] = validation_html

        # The schedule dataframe
        sched_df = self.schedule.sched_df.copy(deep=True)
        sched_df = sched_df.sort(['Subject', 'Data_Source_Name', 'Task_Name',
                                  'File'])
        sched_df = sched_df.set_index(['Subject', 'Data_Source_Name',
                                      'Task_Name', 'File'])
        sched_df = sched_df.to_html()
        sched_df = sched_df.replace('<table border="1" class="dataframe">',
                                    '<table class="table table-bordered">')
        html['SCHED_DF'] = sched_df

        # Pull in the bootstrap CSS for this document
        with open(resource_filename('report', 'bootstrap.min.css'), 'r') as f:
            html['BOOTSTRAP_CSS'] = f.read()
        with open(resource_filename('report',
                                    'bootstrap-theme.min.css'), 'r') as f:
            html['BOOTSTRAP_THEME_CSS'] = f.read()

        # Read in the template
        with open(resource_filename('report', 'report.tpl'), 'r') as f:
            tpl = f.read()

        for key, injection in html.iteritems():
            tpl = tpl.replace('[[' + key + ']]', injection)

        with open(path, 'w') as report:
            report.write(tpl)

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

    def isolate_subjects(self, subject_ids):
        # TODO(janmtl): check for isinstance(list) on subject_ids
        """Removes all subjects except given subject id."""
        self.schedule.isolate_subjects(subject_ids)

    def isolate_tasks(self, task_names):
        """Removes all tasks except given task name."""
        self.schedule.isolate_tasks(task_names)
        self.config.isolate_tasks(task_names)

    def isolate_data_sources(self, data_source_names):
        """Removes all data sources except given data source name."""
        self.schedule.isolate_data_sources(data_source_names)
