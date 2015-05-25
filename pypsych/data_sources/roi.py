# -*- coding: utf-8 -*-
import pandas as pd
import numpy  as np
from scipy import ndimage, misc
import os, re
from clint.textui import progress
import logging


        # self.masks = pd.DataFrame(columns = ['Event_ID', 'Coder', 'Area', 'Mask', 'Path'])
        # # check if ROI is available
        # if 'ROI' in self.config.keys():
        #     self.output_columns.append('roi')
        #     for coder_idx, coder_config in enumerate(self.config['ROI']):
        #         cache_path = os.path.join(coder_config['path'], str(coder_idx)+'_cache.txt')
        #         if os.path.isfile(cache_path):
        #             self.masks = pd.concat([self.masks, self.loadMasks(cache_path)])
        #         else:
        #             self.masks = pd.concat([self.masks, self.createMasks(coder_idx, coder_config, cache_path)])
        #     self.masks.index = pd.MultiIndex.from_tuples(zip(self.masks['Event_ID'], self.masks['Coder']))


def encodeMask(lst):
    return ''.join(['1' if x else '0' for x in lst])

class Masker:
  def __init__(self, dirs, colors, file_pattern):
    masks = []
    for idx, path in enumerate(dirs):
      ff = os.listdir(path)
      with progress.Bar(label="Coder "+str(idx), expected_size=len(ff)) as bar:
        for f_idx, f in enumerate(ff):
          m = re.match(file_pattern, f)
          if m:
            d = m.groupdict()
            d['Path'] = os.path.join(path, f)
            d['Coder'] = idx
            img = ndimage.imread(d['Path'])
            img_vec = np.reshape(img, (img.shape[0]*img.shape[1], img.shape[2]))
            mask_vec = np.all((img_vec == colors[idx]), axis=1)
            d['Mask'] = mask_vec
            d['Area'] = mask_vec.sum()
            masks.append(d)
          bar.show(f_idx)

    self.masks = pd.DataFrame(masks)
    self.masks.sort(['Event_ID', 'Coder'], inplace = True)
    self.masks[['Event_ID', 'Coder']] = self.masks[['Event_ID', 'Coder']].astype(float)
    self.masks.set_index(['Event_ID', 'Coder'], inplace = True)
    self.coders = self.masks.index.levels[1]

  # WRITE A BROADCASTABLE FUNCTION FOR THIS
  def get_roi(self, samples):
    # roi = samples[['Time', 'L POR X [px]', 'L POR Y [px]', 'R POR X [px]', 'R POR Y [px]', 'Event_ID']]
    # roi.loc[:,'Coder 0'] = np.nan
    # roi[self.coders] = np.nan
    for event_id, coder_id in self.masks.index.values:
      this_mask = self.masks.xs((event_id, coder_id), level=['Event_ID', 'Coder'])['Mask'].values[0]
      coords_x = samples[samples['Event_ID']==event_id]['L POR X [px]'].values
      coords_y = samples[samples['Event_ID']==event_id]['L POR Y [px]'].values
      coords = np.floor(coords_y)*768+np.floor(coords_x)
      coords = np.minimum(coords, 1024*768-1).astype(int)
      roi[roi['Event_ID']==event_id, 'Coder '+str(coder_id)] = this_mask[coords]
    roi.drop(['L POR X [px]', 'L POR Y [px]', 'R POR X [px]', 'R POR Y [px]', 'Event_ID'], axis=1, inplace=True)
    return roi


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