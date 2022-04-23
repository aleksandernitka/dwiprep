#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def mk_run_lists_pretopup(rawdir, list_len):
    """
    Because fsl's topup is not paralelised, to speed things up, it would be beneficial
    if things are run concurently using multiple proccessing lists. This fn creates
    N-number of lists of all but last one are of specified len. 

    Parameters
    ----------
    rawdir : PATH or STR
        Location of rawdata to source sub-ids.
        
    list_len : INT
        How long shall each list be.

    Returns
    -------
    Saves X runList_x.csv files in the root dir.
    
    Created on Fri Apr 22 10:37:14 2022
    @author: aleksander nitka

    """

    import os
    from itertools import islice
    
    subs = [f for f in os.listdir(rawdir) if f.startswith('sub-')]

    
    # list to hold required lens for each list
    lens = []
    # keep the tally up
    totaln = len(subs)
    
    # add list len untill len is less than the list len
    while totaln > list_len:
        lens.append(list_len)
        totaln = totaln - list_len
    lens.append(totaln)
    totaln = totaln - totaln # Should 0
    
    # this should generate list of lists
    it = iter(subs)
    outputs = [list(islice(it, elem)) for elem in lens]
    
    # for each sub-list write a file
    for i, l in enumerate(outputs):
        with open(f'tmp/runList_{i}.csv', 'w') as f:
            # each subjects needs to be written to a file
            for j in outputs[i]:
                f.write(f'{j}\n')
            f.close()