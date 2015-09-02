<html>

<head>
  <title>PyPsych: Experiment Report</title>
</head>

<body>
  <h1>PyPsych: Experiment Report</title>

  <h2>Overview</h2>
  <ul>
    <li>Config file path: [[CONFIG_PATH]]</li>
    <li>Schedule file path: [[SCHEDULE_PATH]]</li>
    <li>Data paths: [[DATA_PATHS]]</li>
    <li>Valid subjects: [[VALID_SUBJECTS]]</li>
    <li>Invalid subjects: [[INVALID_SUBJECTS]] <emph>(See the <a href="#validation">validation table</a> for more info.)</emph></li>
    <li>Excluded subjects: [[EXCLUDED_SUBJECTS]]</li>
  </ul>

  <h2>Configuration</h2>
  <pre>[[CONFIG]]</pre>

  <h2>Schedule configuration</h2>
  <pre>[[SCHEDULE]]</pre>

  <h2><a name="validation">Data Quality</a></h2>

  <h3>Legend</h3>
  <table border="1">
  <thead><tr><th>Status</th><th>Color code</th></tr></thead>
  <tbody>
  <tr><td>File found</td><td bgcolor="green"></td></tr>
  <tr><td>Corrupt or empty file</td><td bgcolor="yellow"></td></tr>
  <tr><td>Missing or mislabeled file</td><td bgcolor="red"></td></tr>
  <tbody>
  </table>

  [[VALIDATION]]

  <h2>Compiled schedule of files</h2>

  [[SCHED_DF]]
</body>
</html>
