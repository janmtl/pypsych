# -*- coding: utf-8 -*-
from Config   import Config
from Schedule import Schedule
import interfaces.BeGaze

if __name__ == '__main__':
  CONFIG = Config()
  schedule = Schedule( data_path     = '/users/yan/dev-local/eye',
                       file_patterns = CONFIG.get('file_patterns'))
  print schedule.data[1:2,105]