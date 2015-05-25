# -*- coding: utf-8 -*-
"""
Includes the Experiment and Schedule_Item classes
"""


import os, re
import yaml
import pandas as pd
import numpy  as np
from pkg_resources import resource_filename
from schema import Schema, And, Or, Optional, SchemaError
from collections import namedtuple
import logging

from interfaces.BeGaze import BeGaze
from interfaces.Biopac import Biopac

class Experiment:
  def __init__(self, **kwargs):
    # Load in the configuration
    self.config        = self.compile_config(kwargs.get('config_path', resource_filename('pypsych.defaults', 'config.yaml')))
    self.tasks         = {}
    self.schedule      = pd.DataFrame(columns = [u"Subject_ID", u"Task_ID", u"Task_Name", u"Task_Order", u"Include?", u"Warning"])
    self.schedule_path = os.path.join(self.config['data_path'],'pypsych_schedule.txt')

  def compile_interfaces(self):
    # Get a list of interfaces from the config file
    tasks = self.config['tasks']
    
    for task_name, task in tasks.iteritems():
      for interface_name in self.config['interfaces']:
        if interface_name == 'BeGaze': task['BeGaze'] = BeGaze(task['interfaces'][interface_name])
        if interface_name == 'Biopac': task['Biopac'] = Biopac(task['interfaces'][interface_name])

    self.tasks = tasks

  def compile_schedule(self):
    if os.path.isfile(self.schedule_path):
      self.schedule = pd.read_csv(self.schedule_path, delimiter="\t")
      self.schedule.sort(['Task_Name', 'Subject_ID'], inplace = True)
      miix = pd.MultiIndex.from_arrays([self.schedule['Task_Name'], self.schedule['Subject_ID']])
      self.schedule.set_index(miix, inplace = True)
      self.schedule.drop(['Task_Name', 'Subject_ID'], axis = 1, inplace = True)
    else:
      for interface_name in self.config['interfaces']:

        for task_name, task in self.config['tasks'].iteritems():
          patterns = task['interfaces'][interface_name]['files']
          if type(patterns) == str: patterns = {'main': patterns}    
          for pattern_name, pattern in patterns.iteritems():

            for root, dirs, files in os.walk(self.config['data_path']):
              for f in files: 
                m = re.match(pattern, f)
                if m:
                  d = m.groupdict()
                  pos = (self.schedule['Subject_ID'] == d['Subject_ID']) & (self.schedule['Task_Order'] == d['Task_Order'])
                  if pos.any():
                    self.schedule.loc[pos, interface_name+"_"+pattern_name] = os.path.join(root, f)
                  else:
                    d['Task_Name'] = task_name
                    d['Task_ID']   = task['ID']
                    d[interface_name+"_"+pattern_name] = os.path.join(root, f)
                    self.schedule = self.schedule.append(pd.DataFrame(d, index = [0]), ignore_index = True)

      sch_nans = pd.isnull(self.schedule.drop(['Warning', 'Include?'], axis=1)).any(1)
      self.schedule.loc[sch_nans, 'Include?'] = False
      self.schedule['Include?'].fillna(True, inplace=True)
      self.schedule.loc[sch_nans, 'Warning'] = self.schedule.loc[sch_nans].drop('Warning', axis=1).apply(
        lambda x: "Missing "+", ".join(self.schedule.columns[pd.isnull(x)])
        , axis=1)

      self.schedule.sort(['Task_Name', 'Subject_ID'], inplace = True)
      miix = pd.MultiIndex.from_arrays([self.schedule['Task_Name'], self.schedule['Subject_ID']])
      self.schedule.set_index(miix, inplace = True)
      self.schedule.drop(['Task_Name', 'Subject_ID', 'Task_ID'], axis = 1, inplace = True)
      self.schedule.to_csv(self.schedule_path, sep = "\t")
    pass

  def consume_schedule(self):
    for task_name, task in self.tasks.iteritems():
      print 'Processing '+task_name
      trials = self.schedule.loc[task_name]
      trials = trials[trials['Include?']]
      trials.reset_index(inplace=True)

      task_output = trials[['Subject_ID', 'Task_Order']]
      interface_outputs = {}

      for idx, trial in trials.iterrows():
        for interface_name, interface in task.iteritems():
          if interface_name not in ('interfaces', 'ID', 'index', 'columns'):
            files = trial.filter(regex= r'^'+interface_name).to_dict()
            interface.load(files)
            interface.process(trial['Subject_ID'])
            if interface_name == 'BeGaze':
              if interface_name in interface_outputs.keys():
                interface_outputs[interface_name] = interface_outputs[interface_name].append(interface.output)
              else:
                interface_outputs[interface_name] = interface.output
      # interface_outputs['BeGaze'].to_csv(os.path.join(self.config['output_path'], task_name+".txt"), sep="\t", float_format='%11.2f')
    pass

  @staticmethod
  def compile_config(path):
    default = yaml.load(open(resource_filename('pypsych.defaults', 'config.yaml'), 'r'))
    return default












