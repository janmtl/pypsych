"""A collection of helpul utility functions for analysis of pypsych outputs."""


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
