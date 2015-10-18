#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Includes the BeGazeROI data source class
"""
import pandas as pd
import numpy as np
from begaze import BeGaze
from scipy import ndimage
import os
import re


class BeGazeROI(BeGaze):
    def __init__(self, config, schedule):

        # Call the parent class init
        super(BeGazeROI, self).__init__(config['Labels'], schedule)

        # Position channel statistics
        self.panels = {'XY': {'CODEDRATE': self._coded_rate,
                              'ONMASKRATE': self._onmask_rate}}

        self.screen_size = config['ScreenSize']
        self.mask_size = config['MaskSize']
        self.mask_position = config['MaskPosition']
        self.masks = self._create_masks(config['Coders'])

    def _coded_rate(self, xy, pos, label_bin):
        # Fetch the masks for this ID
        sel = (self.masks['ID'] == label_bin['ID'])
        coded_rates = []
        for _, mask in self.masks.loc[sel, :].iterrows():
            x = np.remainder(xy, self.screen_size[0]) \
                - self.mask_position[0]
            y = np.floor(np.divide(xy, self.screen_size[0])) \
                - self.mask_position[1]
            sel_onmask = (x > 0) & (x < self.mask_size[0]) & \
                         (y > 0) & (y < self.mask_size[1])
            mxy = (x + self.mask_size[0] * y)[sel_onmask]
            hits = 0.0
            for p in mxy:
                if mask['Mask'][p]:
                    hits = hits + 1.0
            coded_rate = hits / float(mask['Area'] * (np.sum(pos)+1))
            coded_rates.append(coded_rate)

        # Use the mean rate from the two coders
        rate = np.mean(coded_rates)
        return rate

    def _onmask_rate(self, xy, pos, label_bin):
        sel = (self.masks['ID'] == label_bin['ID'])
        onmask_rates = []
        for _, mask in self.masks.loc[sel, :].iterrows():
            x = np.remainder(xy, self.screen_size[0]) \
                - self.mask_position[0]
            y = np.floor(np.divide(xy, self.screen_size[0])) \
                - self.mask_position[1]
            sel_onmask = (x > 0) & (x < self.mask_size[0]) & \
                         (y > 0) & (y < self.mask_size[1])
            onmask_rates.append(np.mean(sel_onmask))

        # Use the mean rate from the two coders
        rate = np.mean(onmask_rates)
        return rate

    def _create_masks(self, config):
        mw = self.mask_size[0]
        mh = self.mask_size[1]
        ml = mw * mh
        masks = []
        for coder_name, coder_config in config.iteritems():
            filenames = os.listdir(coder_config['path'])
            for filename in filenames:
                m = re.match(coder_config['pattern'], filename)
                if m:
                    d = m.groupdict()
                    path = os.path.join(coder_config['path'], filename)
                    d['Coder'] = coder_name
                    img = ndimage.imread(path)
                    img = np.transpose(img, (1, 0, 2))
                    img_vec = np.reshape(img, (ml, 3))
                    mask_vec = np.all((img_vec == coder_config['color']),
                                      axis=1)
                    d['Mask'] = mask_vec
                    d['Area'] = mask_vec.sum()
                    masks.append(d)

        Masks = pd.DataFrame(masks)
        return Masks

    def _clean_samples(self, samples):
        """
        Turn any non-Fixation data points into NaN values and extract and
        relabel the columns.

        Args:
          samples (pandas Data Frame): data frame resulting from loading the
            BeGaze samples file.
        """
        # Extract and rename columns of interest. We are using the left pupil
        # by convention.
        samples = samples.loc[:, ['Time',
                                  'L POR X [px]',
                                  'L POR Y [px]',
                                  'L Event Info']]
        samples.columns = ['Time', 'X', 'Y', 'info']

        # Adjust the sample time to the epoch at the top of the file and convert
        # to milliseconds.
        samples[['Time']] = samples[['Time']] - samples.loc[0, 'Time']
        samples[['Time']] = samples[['Time']]/1000

        # Change the data frame index to the Time column for faster indexing
        # later.
        samples.set_index('Time', drop=True, inplace=True)

        # Replace any non-fixation data points with NaN values and drop the
        # 'info' axis which identifies such points.
        no_fixations = (samples['info'] != 'Fixation')
        samples.drop('info', axis=1, inplace=True)
        samples['pos'] = np.invert(no_fixations)
        samples.loc[no_fixations, 'X'] = np.nan
        samples.loc[no_fixations, 'Y'] = np.nan
        # samples.loc[:, 'X'] = samples.loc[:, 'X'].interpolate(method='spline',
        #                                                       order=3)
        # samples.loc[:, 'Y'] = samples.loc[:, 'Y'].interpolate(method='spline',
        #                                                       order=3)

        sw = self.screen_size[0]
        samples.loc[:, 'XY'] = samples.loc[:, 'X'] + sw * samples.loc[:, 'Y']
        samples.drop(['X', 'Y'], axis=1, inplace=True)

        return samples
