import os, re
import pandas as pd

class Schedule:
  def __init__(self, data_path, file_patterns):
    l=[]
    for root, dirs, files in os.walk(data_path):
      for f in files:     
        for idx, pattern in file_patterns.iteritems():
          m = re.match(pattern['re'], f)
          if m:
            d = m.groupdict()
            for k in pattern:
              if not k=='re': d.setdefault(k, pattern[k])
            d['Interface'] = idx
            d['Path'] = os.path.join(root, f)
            l.append(d)

    df = pd.DataFrame(l)
    df[['Subject_ID', 'Task_ID']] = df[['Subject_ID', 'Task_ID']].astype(int)
    df.sort(['Task_ID', 'Subject_ID'], inplace = True)
    df.set_index(['Task_ID', 'Subject_ID'], inplace = True)

    self.data = df