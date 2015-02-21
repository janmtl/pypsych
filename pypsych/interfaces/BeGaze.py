import pandas as pd
import numpy  as np
import yaml
from clint.textui import progress

class BeGaze:
  def __init__(self):
    pass

def assemble(samples_path, labels_path, label_patterns):
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
  fixes[['Event_Group', 'Event_Type']] = fixes['Pattern'].str.extract(patterns['fix_type'])

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
  with progress.Bar(label="nonlinear", expected_size=labels.shape[0]) as bar:
    for idx, label in labels.iterrows():
      selector = (raw['Time'] >= label['Start Time']) & (raw['Time'] <= label['End Time'])
      samples = samples.append(raw[selector], ignore_index=True)
      n[idx] = np.sum(selector)
      bar.show(idx)

  lls = pd.DataFrame(np.repeat(labels[['Event_Group', 'Event_Type', 'Event_ID']].values, n.astype(int), axis=0), columns = ['Event_Group', 'Event_Type', 'Event_ID'])
  samples = pd.concat([samples, lls], axis=1)
  return samples