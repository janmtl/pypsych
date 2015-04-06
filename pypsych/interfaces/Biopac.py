# -*- coding: utf-8 -*-
import pandas as pd
import numpy  as np
from clint.textui import progress
import logging

class Biopac:
  def __init__(self, config):
    self.config  = config
    self.samples = []
    self.labels  = []
    self.output  = []
    pass

  def load(self, files):
    self.input = None
    pass

  def process(self):
    pass