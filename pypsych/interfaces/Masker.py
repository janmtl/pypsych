# -*- coding: utf-8 -*-
import pandas as pd
import numpy  as np
from scipy import ndimage, misc
import os, re
from clint.textui import progress
import logging

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