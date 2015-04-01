# -*- coding: utf-8 -*-
import pandas as pd
import numpy  as np
from clint.textui import progress
import logging

class BeGaze:
  def __init__(self, config):
    self.config = config
    pass
    # masks = []
    # for idx, path in enumerate(dirs):
    #   ff = os.listdir(path)
    #   with progress.Bar(label="Coder "+str(idx), expected_size=len(ff)) as bar:
    #     for f_idx, f in enumerate(ff):
    #       m = re.match(file_pattern, f)
    #       if m:
    #         d = m.groupdict()
    #         d['Path'] = os.path.join(path, f)
    #         d['Coder'] = idx
    #         img = ndimage.imread(d['Path'])
    #         img_vec = np.reshape(img, (img.shape[0]*img.shape[1], img.shape[2]))
    #         mask_vec = np.all((img_vec == colors[idx]), axis=1)
    #         d['Mask'] = mask_vec
    #         d['Area'] = mask_vec.sum()
    #         masks.append(d)
    #       bar.show(f_idx)

    # self.masks = pd.DataFrame(masks)
    # self.masks.sort(['Event_ID', 'Coder'], inplace = True)
    # self.masks[['Event_ID', 'Coder']] = self.masks[['Event_ID', 'Coder']].astype(float)
    # self.masks.set_index(['Event_ID', 'Coder'], inplace = True)
    # self.coders = self.masks.index.levels[1]

  def load(self, trial):
    self.samples = None
    self.labels = None
    pass

  def process(self):
  #def process(task_ID, subject_ID, samples_path, labels_path, label_patterns):
    # Load all data
    raw     = pd.read_csv(samples_path, comment="#", delimiter="\t", skipinitialspace=True)
    labels  = pd.read_csv(labels_path,  comment="#", delimiter="\t", skipinitialspace=True)

    # Extract and rename relevant columns
    labels  = labels[['Time Trial [ms]', 'Event']]
    labels.columns = ['Start Time', 'Event']

    # Patterns for event and fix Event labels
    patterns = {
      'event'     : r'(?P<Event_ID>^[0-9]+)(?P<Pattern>_[A-z0-9]+)',
      'event_type': r'_(?P<Event_Group>[A-z0-9]+)_(?P<Event_Type>[A-z0-9]+)',
      'fix'       : r'(?P<Pattern>BlackFix|GreyFix|WhiteFix)(?P<Event_ID>[0-9]+)',
      'fix_type'  : r'(?P<Event_Type>Black|Grey|White)(?P<Event_Group>Fix)'
    }

    events = labels['Event'].str.extract(patterns['event'])
    events[['Event_Group', 'Event_Type']] = events['Pattern'].str.extract(patterns['event_type'])
    fixes  = labels['Event'].str.extract(patterns['fix'])
    fixes[['Event_Type', 'Event_Group']] = fixes['Pattern'].str.extract(patterns['fix_type'])

    # Form the label_patterns into a DataFrame
    lp = pd.DataFrame(label_patterns)
    lp.columns = ["Event_Duration", "Pattern"]

    labels[['Event_Group', 'Event_Type', 'Event_ID', 'Pattern']] = events.combine_first(fixes)
    labels = labels.merge(lp, on='Pattern')
    labels['End Time'] = labels['Start Time'] + labels['Event_Duration']
    labels = labels.drop(['Pattern', 'Event', 'Event_Duration'], 1)

    raw[['Time']] = raw[['Time']] - raw.loc[0, 'Time']
    raw[['Time']] = raw[['Time']]/1000


    samples = pd.DataFrame(columns = raw.columns)
    n = np.empty(labels.shape[0])
    with progress.Bar(label="-".join([str(task_ID), str(subject_ID)]), expected_size=labels.shape[0]) as bar:
      for idx, label in labels.iterrows():
        selector = (raw['Time'] >= label['Start Time']) & (raw['Time'] <= label['End Time'])
        samples = samples.append(raw[selector], ignore_index=True)
        n[idx] = np.sum(selector)
        bar.show(idx)

    lls = pd.DataFrame(np.repeat(labels[['Event_Group', 'Event_ID', 'Event_Type']].values, n.astype(int), axis=0), columns = ['Event_Group', 'Event_Type', 'Event_ID'])
    samples = pd.concat([samples, lls], axis=1)
    
    self.output = samples