# -*- coding: utf-8 -*-
import pandas as pd
import numpy  as np
from clint.textui import progress
import logging
from scipy.io import loadmat

def nans(x):
  return np.isnan(x).sum()

def sem(x):
  return x.sem(axis=0)

class Biopac:
  def __init__(self, config):
    self.config  = config
    self.samples = []
    self.output  = []
    self.labels  = self.compile_labels(self.config)
    pass

  def load(self, files):
    mat = loadmat(files['Biopac_main'])
    self.input = pd.DataFrame(data = mat['data'], columns = mat['labels'])
    pass

  def process(self, Subject_ID):
    print 'Processing Biopac for subject: '+str(Subject_ID)

    samples = self.input[['RSP, X, RSPEC-R', 'ECG, Y, RSPEC-R', 'MARKERS']]
    samples.columns = ['resp', 'ecg', 'flag']
    samples = pd.merge(samples, self.labels, on='flag', how='inner')
    samples['order'] = (samples['flag'].shift(1) != samples['flag']).astype(int).cumsum()

    stats = pd.DataFrame(columns = [])

    grouped = samples.groupby('order', sort=False, as_index=False)
    for order, group in grouped:
      bins = group.loc[group.index[0],'bins']
      subgrouped = samples.groupby(pd.cut(x = samples.index,
                                          bins = np.linspace( start = samples.index[0], 
                                                              stop  = samples.index[-1],
                                                              num   = bins+1)
                                          ))
      resp = subgrouped['resp'].agg({'resp_MEAN': np.mean, 'resp_SEM': sem, 'resp_COUNT': np.size, 'resp_NANS': nans})
      ecg  =  subgrouped['ecg'].agg({ 'ecg_MEAN': np.mean,  'ecg_SEM': sem,  'ecg_COUNT': np.size,  'ecg_NANS': nans})
      flag = subgrouped['flag'].agg({'flag': np.max})
      substats = pd.merge(resp, ecg, left_index=True, right_index=True)
      substats = pd.merge(substats, flag, left_index=True, right_index=True)
      substats.reset_index(inplace=True, drop=True)
      substats['bin'] = substats.index
      stats = stats.append(substats)

    print stats

    # stats.sort_index(by='order', axis=0, inplace=True)
    # stats.index = range(1,len(stats) + 1)
    # stats.drop('order', axis=1, inplace=True)
    # self.output = stats
    # print self.output
    pass

  def compile_labels(self, config):
    labels = [{'flag' : flag,
               'Event_Type': event_type,
               'Event_Group': flag_name,
               'bins' : label['bins']}
               for event_type, label in self.config['labels'].iteritems()
               for flag_name, flag in label['flags'].iteritems()]
    return pd.DataFrame(data = labels)