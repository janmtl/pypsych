# -*- coding: utf-8 -*-
from Config            import Config
from Schedule          import Schedule
from interfaces.Masker import Masker
import interfaces.BeGaze as BeGaze
import os
import numpy as np
import logging

def consume_schedule(schedule, config, output_dir, **kwargs):
  for task_ID, subject_ID in np.unique(schedule.index.values):
    tiny_sched = schedule.loc[task_ID, subject_ID]
    samples_path = tiny_sched[tiny_sched["File"] == "samples"]["Path"].iloc[0]
    labels_path  = tiny_sched[tiny_sched["File"] == "labels" ]["Path"].iloc[0]
    label_patterns = config.get('label_patterns')
    samples = BeGaze.assemble(task_ID        = task_ID,
                              subject_ID     = subject_ID,
                              samples_path   = samples_path,
                              labels_path    = labels_path,
                              label_patterns = label_patterns)
    if 'masker' in kwargs.keys():
      pass
      #roi = kwargs['masker'].parse_BeGaze(samples)
    output_path = os.path.join(output_dir, "_".join([str(subject_ID), str(task_ID), "LabeledSamples.tsv"]))
    samples.to_csv(output_path, sep="\t")

if __name__ == '__main__':
  config = Config()
  schedule = Schedule( data_path     = '/users/yan/dev-local/eye',
                       file_patterns = config.get('file_patterns'))