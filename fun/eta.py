class Eta():
    
    # Helps with tracking time of experiments, calculating ETA
    # from time of one subject x N subjects
    # Init class before starting data analysis, then update on each subject start

    def __init__(self, mode, N, print_eta=True, return_eta_str=True):
        
        import time as t
        from datetime import timedelta as td
        from datetime import datetime as dt
        from statistics import mean, median, stdev
        
        self.mode = mode
        self.N = N
        self.print_eta = print_eta
        self.return_eta_str = return_eta_str
        self.times = []
        self.t = t
        self.td = td
        self.dt = dt
        self.mean = mean
        self.median = median
        self.stdev = stdev

        self.t0 = None # Start time
        self.tic = None # Start time of current subject
        self.toc = None # End time of current subject
        self.stat_mean = None # Stores Statistics
        self.stat_median = None # Stores Statistics
        self.stat_stdev = None # Stores Statistics
        self.eta = None # Stores ETA

        if self.mode not in ['mean', 'median']:
            raise ValueError('mode must be mean or median')

    
    def update(self):
        
        # If no time 0 has been recorded, record current time
        # Also this means that we are on the very first subject, and 
        # hence we don't have any time data to calculate ETA

        if self.t0 == None:
            self.t0 = self.dt.now() # set time 0
            self.tic = self.t.perf_counter() # start time
            if self.print_eta:
                print('Starting time: {}'.format(self.t0.strftime('%H:%M:%S')))
            if self.return_eta_str:
                return 'Starting time: {}'.format(self.t0.strftime('%H:%M:%S'))
        else:
            self.toc = self.t.perf_counter() # end time
            self.times.append(self.toc - self.tic) # append time
            self.tic = self.t.perf_counter() # start time again

            # Calculate statistics
            self.stat_mean = self.mean(self.times)
            self.stat_median = self.median(self.times)
            if len(self.times) > 2:
                # because we need at least 2 data points to calculate stdev
                self.stat_stdev = self.stdev(self.times)
            else:
                self.stat_stdev = 0

            # Calculate ETA
            if self.mode == 'mean':
                self.eta = self.t0 + self.td(seconds=(self.stat_mean * self.N))
            elif self.mode == 'median':
                self.eta = self.t0 + self.td(seconds=(self.stat_median * self.N))
            
            # Print ETA
            # prepare message, then print and/or return
            msg = f'ETA: {self.eta.strftime("%H:%M:%S on %d.%m.%Y")} | TIMINGS (min): last N = {self.times[-1]/60:0.2f},  M = {self.stat_mean/60:0.2f}, SD = {self.stat_stdev/60:0.2f}, MED = {self.stat_median/60:0.2f}'

            if self.print_eta:
                print(msg)
            if self.return_eta_str:
                return msg

