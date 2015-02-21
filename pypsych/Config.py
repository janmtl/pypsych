import os
import yaml
from pkg_resources import resource_filename
from schema import Schema, Or, Optional, SchemaError
import logging

class Config:
  def __init__(self, **kwargs):
    schema = Schema({
        'interfaces': {
          str: {
            'file_patterns': {
              're': str,
              Optional('Channel'): str # THIS SHOULD BE CHECKED AGAINST THE REGEX
            },
            Optional('label_patterns'): [{
              'task_ID': Or(str, int),
              'labels': [{
                'pattern': str,
                'duration': int
              }]
            }]
          }
        }
      })
    default = yaml.load(open(resource_filename('pypsych.defaults', 'config.yaml'), 'r'))
    
    try:
      raw = yaml.load(open(kwargs.get('path', 'config.yaml'), 'r'))
      schema.validate(raw)
    except IOError:
      logging.warning("The config file could not be loaded. Using default config.")
      self.raw = default
    except yaml.YAMLError:
      logging.warning("The file " + path + " is not valid YAML. Using default config.")
      self.raw = default
    except SchemaError:
      logging.warning("The file " + path + " is not a valid configuration. Using default config.")
      self.raw = default
    else:
      self.raw = raw
      
  def get(self, param, **kwargs):
    # Fetch all of the file searching parameters
    if param == "file_patterns":
      output = {}
      for name, interface in self.raw['interfaces'].iteritems():
        output[name] = interface['file_patterns']
    # Fetch all of the labels for a task (default task 1)
    elif param == "label_patterns":
      output = []
      task_ID = kwargs.get('task_ID', 1)
      for name, interface in self.raw['interfaces'].iteritems():
        if 'label_patterns' in interface.keys():
          for label_pattern in interface['label_patterns']:
            if label_pattern['task_ID'] == task_ID: output+=label_pattern['labels']

    return output
