<html>

<head>
  <title>PyPsych: Experiment Report</title>

  <style type="text/css">
  [[BOOTSTRAP_CSS]]
  [[BOOTSTRAP_THEME_CSS]]
  .path{
    font-family: monospace;
    color: #990000;
  }
  .paths{
    font-family: monospace;
    color: #990000;
  }
  .subject_list{
    font-family: monospace;
    color: #990000;
  }
  .found{background-color: green;}
  .corrupt{background-color: yellow;}
  .missing{background-color: red;}
  .small table{font-size: 12px;}

  </style>
</head>

<body>
  <div class="container">
    <h1>PyPsych: Experiment Report</title>

    <h2>Overview</h2>
    <table class="table">
      <tr>
        <td width="25%">
          <h4>
            Config file path
          </h4>
        </td>
        <td class="path">[[CONFIG_PATH]]</td>
      </tr>
      <tr>
        <td width="25%">
          <h4>
            Pickle path<br/>
            <small>(used for saving the state of the experiment)</small>
          </h4>
        </td>
        <td class="path">[[PICKLE_PATH]]</td>
      </tr>
      <tr>
        <td width="25%">
          <h4>
            Data paths
          </h4>
        </td>
        <td class="paths">[[DATA_PATHS]]</td>
      </tr>
      <tr>
        <td width="25%">
          <h4>
            Valid subjects
          </h4>
        </td>
        <td class="subject_list">[[VALID_SUBJECTS]]</td>
      </tr>
      <tr>
        <td width="25%">
            <h4>
              Invalid subjects<br/>
              <small>(See the <a href="#validation">validation table</a> for more info.)</small>
            </h4>
        </td>
        <td class="subject_list">[[INVALID_SUBJECTS]]</td>
      </tr>
      <tr>
        <td width="25%">
          <h4>
            Excluded subjects
          </h4>
        </td>
        <td class="subject_list">[[EXCLUDED_SUBJECTS]]</span></td>
      </tr>
    </table>

    <h2><a name="validation"></a>Data Quality</h2>

    <h3>Legend</h3>
    <table class="table">
    <thead><tr><th>Status</th><th>Color code</th></tr></thead>
    <tbody>
    <tr><td>File found</td><td class="found"></td></tr>
    <tr><td>Corrupt or empty file</td><td class="corrupt"></td></tr>
    <tr><td>Missing or mislabeled file</td><td class="missing"></td></tr>
    <tbody>
    </table>

    <p>The table below only shows the <emph>invalid subjects</emph> for which pypsych found an error:</p>

    <div class="small">[[VALIDATION]]</div>

    <h2>Configuration</h2>
    <pre>[[CONFIG]]</pre>

    <h2>Schedule configuration</h2>
    <pre>[[SCHEDULE]]</pre>


    <h2>Compiled schedule of files</h2>

    [[SCHED_DF]]
  </div>
</body>
</html>
