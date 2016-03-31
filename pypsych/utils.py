"""A collection of helpul utility functions for analysis of pypsych outputs."""

import pandas as pd
import numpy as np


def collapse_bins(df, prefixes):
    """Collapse (mean) any columns that start with each prefix."""
    for prefix in prefixes:
        sel = [colname.startswith(prefix) for colname in df.columns]
        df[prefix] = df.loc[:, sel].mean(axis=1)
        df.drop(df.columns[sel], axis=1, inplace=True)
    pass


def find_prefix_cols(df, prefix):
    """List all df columns with the given prefix."""
    sel = [colname.startswith(prefix) for colname in df.columns]
    return df.columns[sel]


def findreplace_prefix_cols(df, old_prefix, new_prefix):
    """List columns names with old prefix replaced by new prefix."""
    sel = [colname.startswith(old_prefix) for colname in df.columns]
    old_cols = df.columns[sel]
    new_cols = [old_col.replace(old_prefix, new_prefix, 1)
                for old_col in old_cols]
    return new_cols


def get_renaming_dict(df, old_prefix, new_prefix):
    """Generate re_dict for use in pandas.DataFrame.rename(columns=re_dict)."""
    newcols = findreplace_prefix_cols(df, old_prefix, new_prefix)
    oldcols = find_prefix_cols(df, old_prefix)
    re_dict = dict(zip(oldcols, newcols))
    return re_dict


def merge_and_rename_columns(df, new_name, old_names):
    """
    Create new_name column by filling in non-nan values from old_names in order.
    """
    res = df.copy(deep=True)

    if type(old_names) is not list:
        if new_name != old_names:
            res[new_name] = np.nan
        sel = ~pd.notnull(res[new_name])
        res.loc[sel, new_name] = res.loc[sel, old_names]
    else:
        if new_name not in old_names:
            res[new_name] = np.nan
        for old_name in old_names:
            sel = ~pd.notnull(res[new_name])
            res.loc[sel, new_name] = res.loc[sel, old_name]

    return res
