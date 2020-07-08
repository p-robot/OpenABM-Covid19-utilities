"""
Script to count number infected over a time window, stratified by a particular variable
from the transmission_file output from the OpenABM-Covid19 model.  

Arguments
---------

python transmissions_over_time_by_age.py \
    --df_trans : path to csv file of transmissions file (as output from OpenABM-Covid19)
    --limits : lower and upper limits of the time window of interest
    --window : window over which to bin transmission events
    --step : step of the lower limit of the window
    --output_csv : path to output csv of where to save results
    --grouping_var : name of the column of df_trans within which to group outputs
        (`status_source` for stratifying by infectiousness of source, `age_group_recipient`
        for stratifying by age of recipient, etc).  
"""

import os, argparse, numpy as np, pandas as pd
from os.path import join


def overlapping_bins(start, stop, window, step):
    """Generate overlapping bins"""
    
    bins = []
    for i in np.arange(start, stop - window + 1, step = step):
        bins.append((i, i + window))
    return(bins)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    #################
    # Required args #
    #################
    
    parser.add_argument('--df_trans', type = str,
        help = 'Path to transmission file, as output from OpenABM-Covid19', required = True)
    
    parser.add_argument('--grouping_var', type = str,
        help = 'Name of the column within which to group individuals', required = True)
    
    parser.add_argument('--output_csv', type = str, 
        help = 'Path to output CSV file to be written', required = True)
    
    #################
    # Optional args #
    #################
    
    parser.add_argument('--limits', type = int, nargs = '+',
        help = 'Range of time over which to calculate', default = [0, 100])
    
    parser.add_argument('--window', type = int, 
        help = 'Window over which to count transmission events', default = 5)
    
    parser.add_argument('--step', type = int, 
        help = 'Steps within limits over which to count transmission events', default = 5)
    
    parser.add_argument('--write_pivot', action = 'store_true', 
        help = 'Write a pivot (wide format) table to csv?', default = False)
    
    parser.add_argument('--write_long', action = 'store_true', 
        help = 'Write a long-format table to csv?', default = True)
    
    args = parser.parse_args()
    
    df_trans = pd.read_csv(args.df_trans)
    
    start, stop = args.limits
    bins = overlapping_bins(start = start, stop = stop + args.window, 
        window = args.window, step = args.step)
    
    df_trans["time_infected_bin"] = np.nan
    df_trans["time_infected_bin_idx"] = np.nan
    df_trans["lower_bin_edge"] = np.nan
    df_trans["upper_bin_edge"] = np.nan
    
    for i, b in enumerate(bins):
        lower, upper = b
        
        binned_events = (df_trans.time_infected >= lower) & (df_trans.time_infected < upper)
        df_trans.loc[binned_events, ["time_infected_bin_idx"]] = i
        df_trans.loc[binned_events, ["time_infected_bin"]] = pd.Interval(*b, closed = "right")
        
        df_trans.loc[binned_events, ["lower_bin_edge"]] = b[0]
        df_trans.loc[binned_events, ["upper_bin_edge"]] = b[1]
    
    if args.write_pivot:
        df_pivot = pd.pivot_table(df_trans, 
            index = ["time_infected_bin", "time_infected_bin_idx", 
                "lower_bin_edge", "upper_bin_edge"],
            columns = args.grouping_var, 
            aggfunc = 'size', fill_value = 0)
        
        df_pivot.to_csv("pivot_" + args.output_csv)
    
    if args.write_long:
        # Create long dataset from pivot table (since it nicely fills with zeros)
        idvars = ["time_infected_bin", args.grouping_var]
        df_agg = df_trans.groupby(idvars).size().reset_index(name = 'incident_infections')
        df_agg.to_csv(args.output_csv, index = False)
