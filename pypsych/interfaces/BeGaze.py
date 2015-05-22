# -*- coding: utf-8 -*-
import os, re
import pandas as pd
import numpy  as np
from scipy import ndimage, misc, stats
from itertools import product
import logging

def encodeMask(lst):
  return ''.join(['1' if x else '0' for x in lst])

def nans(x):
  return np.isnan(x).sum()

def sem(x):
  return x.sem(axis=0)

class BeGaze:
  def __init__(self, config):
    self.config  = config
    self.samples = []
    self.labels  = []
    self.output  = []
    self.label_configs = [{'event_type': name, 
                           'event_duration': params[0],
                           'n_bins': params[1],
                           'pattern': params[2]} for name, params in self.config['labels'].iteritems()]

    # Compute self.output_columns from the label configurations
    self.output_columns = ['Subject_ID', 'Event_ID']
    for label in self.label_configs:
      self.output_columns.extend([
        label['event_type'] + '_' + str(x[0]) + '_' + x[1] for x in product(range(label['n_bins']), ['MEAN', 'SEM', 'COUNT', 'NANS'])
      ])

    self.masks = pd.DataFrame(columns = ['Event_ID', 'Coder', 'Area', 'Mask', 'Path'])
    # check if ROI is available
    if 'ROI' in self.config.keys():
      self.output_columns.append('roi')
      for coder_idx, coder_config in enumerate(self.config['ROI']):
        cache_path = os.path.join(coder_config['path'], str(coder_idx)+'_cache.txt')
        if os.path.isfile(cache_path):
          self.masks = pd.concat([self.masks, self.loadMasks(cache_path)])
        else:
          self.masks = pd.concat([self.masks, self.createMasks(coder_idx, coder_config, cache_path)])
      self.masks.index = pd.MultiIndex.from_tuples(zip(self.masks['Event_ID'], self.masks['Coder']))

  def load(self, files):
    self.samples = pd.read_csv(files['BeGaze_samples'], comment="#", delimiter="\t", skipinitialspace=True)
    self.labels  = pd.read_csv(files['BeGaze_labels'],  comment="#", delimiter="\t", skipinitialspace=True)

  def process(self, Subject_ID):
    print 'Processing BeGaze for subject: '+str(Subject_ID)
    raw     = self.samples
    labels  = self.labels

    # Extract and rename relevant columns
    labels  = labels[['Time Trial [ms]', 'Event']]
    labels.columns = ['Start_Time', 'Event']
    temp_labels = pd.DataFrame(index = labels.index,
                               columns = ['Event_ID', 'Event_Group', 'Event_Type', 'Event_Duration', 'N_Bins'])
    labels = pd.concat([labels,temp_labels], axis = 1)

    for label_config in self.label_configs:
      temp_labels = labels['Event'].str.extract(label_config['pattern'])
      if isinstance(temp_labels, pd.core.series.Series): temp_labels = pd.DataFrame(temp_labels)
      temp_pos = pd.notnull(temp_labels).any(1)
      temp_labels.loc[temp_pos, 'Event_Type']     = label_config['event_type']
      temp_labels.loc[temp_pos, 'Event_Duration'] = label_config['event_duration']
      temp_labels.loc[temp_pos, 'N_Bins']         = label_config['n_bins']
      labels.update(temp_labels)
    labels.dropna(axis = 0, how = 'any', inplace = True)
    labels[['Start_Time', 'Event_Duration']] = labels[['Start_Time', 'Event_Duration']].astype(float)

    duplicate_labels = labels[labels.duplicated(subset=['Event_ID', 'Event_Type'])]
    grouped = duplicate_labels.groupby(['Event_ID', 'Event_Type'])
    for idx, label in grouped:
      labels.loc[label.index, 'Event_ID'] = label['Event_ID'] + np.arange(1,label.shape[0]+1,1).astype(str)

    labels['End_Time'] = labels['Start_Time'] + labels['Event_Duration']
    labels = labels.drop(['Event', 'Event_Duration'], 1)

    raw[['Time']] = raw[['Time']] - raw.loc[0, 'Time']
    raw[['Time']] = raw[['Time']]/1000

    stats = pd.DataFrame(columns = self.output_columns)
    
    grouped = labels.groupby('Event_ID')
    for event_id, group in grouped:
      event_stats = pd.DataFrame(columns = [])
      for idx, label in group.iterrows():
        selector = (raw['Time'] >= label['Start_Time']) & (raw['Time'] <= label['End_Time'])
        samples  = self.clean_samples(raw[selector])
        subgrouped = samples.groupby(pd.cut(x = samples.index,
                                            bins = np.linspace( start = samples.index[0], 
                                                                stop  = samples.index[-1],
                                                                num   = label['N_Bins']+1)
                                            ))
        sub_diam_stats  = subgrouped['Diameter'].agg({'MEAN': np.mean, 'SEM': sem, 'COUNT': np.size, 'NANS': nans})
        if 'ROI' in self.config.keys():
          sub_roi_stats = subgrouped[['posx', 'posy']].apply(lambda x: self.apply_masks(x, event_id))
          sub_stats = pd.merge(sub_diam_stats, sub_roi_stats, left_index=True, right_index=True)
        else:
          sub_stats = sub_diam_stats
        sub_stats.reset_index(inplace=True, drop=True)
        sub_stats['Bin'] = sub_stats.index
        sub_stats['Event_Type'] = label['Event_Type']
        sub_stats['Subject_ID'] = Subject_ID
        event_stats = event_stats.append(sub_stats)

      event_stats['BinnedType'] = event_stats['Event_Type'] + '_' + event_stats['Bin'].astype(str)
      event_stats.drop(['Event_Type', 'Bin'], axis=1, inplace=True)
      event_stats = event_stats.pivot(index = 'Subject_ID', columns = 'BinnedType')
      event_stats.columns = event_stats.columns.swaplevel(0,1)
      event_stats.columns = ['_'.join(col) for col in event_stats.columns.values]
      event_stats['Event_ID']    = event_id
      event_stats['Event_Group'] = group['Event_Group'].iloc[0]
      event_stats.reset_index(inplace=True)
      stats = stats.append(event_stats)
    stats.reset_index(inplace=True)
    self.output = stats
        
  def save_output(path):
    self.output.to_csv(path, delimiter = "\t")
    pass

  def apply_masks(self, pos, event_id):
    coords = np.floor(pos['posy'])*768+np.floor(pos['posx'])
    coords = np.minimum(coords, 1024*768-1)
    nan_count = np.count_nonzero(np.isnan(pos['posx']) & np.isnan(pos['posy']))
    coords = np.nan_to_num(coords).astype(int)
    coders = self.masks.index.levels[1]
    hit_stats = 0
    for coder_idx in coders:
      hits = coords.apply(lambda coord: self.masks.loc[np.float_(event_id), coder_idx]['Mask'][coord]).astype(int)
      hit_count = np.sum(hits)/self.masks.loc[np.float_(event_id), coder_idx]['Area']
      hit_stats = hit_stats + hit_count/len(coders)
    return pd.Series({'roi': hit_stats})

  @staticmethod
  def clean_samples(raw):
    samples = raw[['Time', 'L Pupil Diameter [mm]', 'L POR X [px]', 'L POR Y [px]', 'L Event Info']]
    samples.columns = ['Time', 'Diameter', 'posx', 'posy', 'info']
    samples.set_index('Time', drop = True, inplace = True)
    no_fixations = (samples['info'] != 'Fixation')
    samples.loc[no_fixations,:] = np.nan
    # samples.drop('info', axis = 1, inplace=True)
    return samples

  @staticmethod
  def createMasks(coder_idx, coder_config, save_path):
    masks = []
    ff = os.listdir(coder_config['path'])
    for f_idx, f in enumerate(ff):
      m = re.match(coder_config['files'], f)
      if m:
        d = m.groupdict()
        d['Path'] = os.path.join(coder_config['path'], f)
        d['Coder'] = coder_idx
        img = ndimage.imread(d['Path'])
        img_vec = np.reshape(img, (img.shape[0]*img.shape[1], img.shape[2]))
        mask_vec = np.all((img_vec == coder_config['color']), axis=1)
        d['Mask'] = encodeMask(mask_vec)
        d['Area'] = mask_vec.sum()
        masks.append(d)

    masks = pd.DataFrame(masks)
    masks.sort(['Event_ID', 'Coder'], inplace = True)
    masks[['Event_ID', 'Coder']] = masks[['Event_ID', 'Coder']].astype(float)
    masks.to_csv(save_path, sep="\t")
    return masks    

  @staticmethod
  def loadMasks(cache_path):
    masks = pd.read_csv(cache_path, delimiter="\t")
    return masks

    

