# -*- coding: utf-8 -*-
import pandas as pd
import numpy  as np
from clint.textui import progress
import logging

class Biopac:
  def __init__(self, config):
    self.config = config
    pass

  def load(self, trial):
    self.input = None
    pass

  def validate_task(self, trial):
    pass

  def process(self):
    pass