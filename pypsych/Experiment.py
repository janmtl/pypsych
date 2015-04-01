# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import os, re
import yaml
import pandas as pd
from pkg_resources import resource_filename
from schema import Schema, And, Or, Optional, SchemaError
from collections import namedtuple
import logging

from interfaces.BeGaze import BeGaze
from interfaces.Biopac import Biopac

class Experiment:
  def __init__(self, **kwargs):
    # Load in the configuration
    self.config          = self.compile_config(kwargs.get('config_path', resource_filename('pypsych.defaults', 'config.yaml')))
    self.interfaces      = {}
    self.interface_names = []
    self.task_names      = []
    self.schedule        = pd.DataFrame(columns = [u"Subject_ID", u"Task_ID", u"Task_Name", u"Task_Order"])
    self.output          = []

  def compile_interfaces(self):
    # Get a list of interfaces from the config file
    interface_configs = {}
    task_names = []
    for task_name, task_config in self.config['tasks'].iteritems():
      if task_name not in task_names: task_names.append(task_name)
      for interface_name, interface_config in task_config['interfaces'].iteritems():
        interface_configs[interface_name, task_name] = interface_config
    for idx, config in interface_configs.iteritems():
      if idx[0] == 'BeGaze': self.interfaces[idx] = BeGaze(config)
      if idx[0] == 'Biopac': self.interfaces[idx] = Biopac(config)
    self.interfaces = interface_configs
    self.task_names = task_names

  def compile_schedule(self):

    sch = self.schedule

    for interface_name in self.config['interfaces']:

      for task_name, task in self.config['tasks'].iteritems():
        patterns = task['interfaces'][interface_name]['files']
        if type(patterns) == str: patterns = {'main': patterns}    
        for pattern_name, pattern in patterns.iteritems():
          self.schedule[interface_name+"_"+pattern_name] = ""

          for root, dirs, files in os.walk(self.config['data_path']):
            for f in files: 
              m = re.match(pattern, f)
              if m:
                d = m.groupdict()
                pos = (sch['Subject_ID'] == d['Subject_ID']) & (sch['Task_Order'] == d['Task_Order'])
                if pos.any():
                  sch.loc[pos, interface_name+"_"+pattern_name] = os.path.join(root, f)
                else:
                  d['Task_Name'] = task_name
                  d['Task_ID']   = task['ID']
                  d[interface_name+"_"+pattern_name] = os.path.join(root, f)
                  sch = sch.append(pd.DataFrame(d, index = [0]), ignore_index = True)

    sch.sort(['Subject_ID', 'Task_Name'], inplace = True)
    print sch

    pass

  def consume_schedule(self):
    pass

  @staticmethod
  def compile_config(path):
    schema = Schema({
        'data_path': str,
        'output_path': str,
        'interfaces': [str],
        'tasks': {
          str: {
            'ID': int,
            'interfaces': {
              str: {
                'files': Or({str:str}, str),
                Optional('labels'): {
                  str: Or(str, [int, int], [int, int, str])
                },
                Optional('ROI'): [{
                  'coder': {
                    'path': str, 'files': str, 'color': And([int], lambda x: len(x)==3)
                  }
                }]
              }
            }
          }
        }
      })
    default = yaml.load(open(resource_filename('pypsych.defaults', 'config.yaml'), 'r'))


    # STILL HAVE TO APPLY GLOBAL CONFIGS TO TASK-SPECIFIC CONFIGS
    


    return schema.validate(default)












