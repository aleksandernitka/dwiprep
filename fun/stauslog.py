class StatusLog:
    """
    Simple logging class for status messages. Puts a log into the logs folder.
    Each update is structured as follows:
    DATETIME \t ID \t STATUS \t MESSAGE

    TODO:
    Add method to load log file and return a pandas dataframe
    Add method to send log file via telegram
    Add method to filter log file by ID, or by status

    """
    def __init__(self, task):
        from datetime import datetime as dt
        from datetime import timedelta as td
        from os.path import exists, join
        from os import mkdir
        if not exists('logs'):
            mkdir('logs')
        # Make datetime available to all methods
        self.dt = dt
        self.timestamps = self.dt.now().strftime('%Y%m%d%H%M%S')
        self.filename = join('logs', f'{self.timestamp}_{task.replace(" ","").lower()[:10]}.log')
        self.file = open(self.filename, 'w')
        self.file.write(f'{self.dt.now()}\tALL\tNA\tStatusLog initialised.')
        self.file.close()

    def ok(self, id, message):
        # Logs successful completion of a task
        self.file = open(self.filename, 'a')
        self.file.write(f'\n{self.dt.now()}\t{id}\tOK\t{message}')
        self.file.close()
    
    def error(self, id, message):
        # Logs errors or exceptions
        self.file = open(self.filename, 'a')
        self.file.write(f'\n{self.dt.now()}\t{id}\tOK\t{message}')
        self.file.close()

    def warning(self, id, message):
        # Logs warnings
        self.file = open(self.filename, 'a')
        self.file.write(f'\n{self.dt.now()}\t{id}\tWARNING\t{message}')
        self.file.close()

    def info(self, id, message):
        # Logs information
        self.file = open(self.filename, 'a')
        self.file.write(f'\n{self.dt.now()}\t{id}\tINFO\t{message}')
        self.file.close()
    
    def deltaTstart(self):
        # Logs the start of a deltaT processing
        self.file = open(self.filename, 'a')
        self.start = self.dt.now()
        self.file.close()

    def deltaTend(self, id, task):        
        # Logs the end of a deltaT processing
        self.file = open(self.filename, 'a')
        self.end = self.dt.now()
        self.file.write(f'\n{self.end}\t{id}\tTASKEND\t{task}: {self.end - self.start}')
        self.file.close()

    def subjectStart(self, id, task):
        # Logs the start of a subject processing
        self.file = open(self.filename, 'a')
        self.subStart = self.dt.now()
        self.file.write(f'\n{self.subStart}\t{id}\tSUBSTART\t{task}: Subject started')
        self.file.close()
        
    def subjectEnd(self, id, task):
        # Logs the end of a subject processing
        self.file = open(self.filename, 'a')
        self.subEnd = self.dt.now()
        self.file.write(f'\n{self.dt.now()}\t{id}\tSUBEND\t{task}: Subject ended, duration: {self.subEnd - self.subStart}')
        self.file.close()
        
    def close(self):
        self.file = open(self.filename, 'a')
        self.file.write(f'\n{self.dt.now()}\tALL\tNA\tStatusLog closed.')
        # Closes the log file
        self.file.close()

    def subdump(self, subjects):
        # Dumps the list of subjects to the file
        self.subdumpfile = open(join('logs', f'{self.timestamp}_{self.task.replace(" ","").lower()[:10]}_subjects.log'), 'w')
        self.subdumpfile.write(subjects)
        self.subdumpfile.close()