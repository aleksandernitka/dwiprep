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
    def __init__(self, filename):
        from datetime import datetime as dt
        from datetime import timedelta as td
        from os.path import exists, join
        from os import mkdir
        if not exists('logs'):
            mkdir('logs')
        # Make datetime available to all methods
        self.dt = dt
        self.filename = join('logs', filename)
        self.file = open(self.filename, 'w')
        self.file.write(f'{self.dt.now()}\tALL\tNA\tStatusLog initialised.')

    def ok(self, id, message):
        # Logs successful completion of a task
        self.file.write(f'\n{self.dt.now()}\t{id}\tOK\t{message}')
    
    def error(self, id, message):
        # Logs errors or exceptions
        self.file.write(f'\n{self.dt.now()}\t{id}\tOK\t{message}')

    def warning(self, id, message):
        # Logs warnings
        self.file.write(f'\n{self.dt.now()}\t{id}\tWARNING\t{message}')

    def info(self, id, message):
        # Logs information
        self.file.write(f'\n{self.dt.now()}\t{id}\tINFO\t{message}')
    
    def deltaTstart(self):
        # Logs the start of a deltaT processing
        self.start = self.dt.now()

    def deltaTend(self, id, task):        
        # Logs the end of a deltaT processing
        self.end = self.dt.now()
        self.file.write(f'\n{self.end}\t{id}\tTASKEND\t{task}: {self.end - self.start}')

    def subjectStart(self, id, task):
        # Logs the start of a subject processing
        self.subStart = self.dt.now()
        self.file.write(f'\n{self.subStart}\t{id}\tSUBSTART\t{task}: Subject started')
        
    def subjectEnd(self, id, task):
        # Logs the end of a subject processing
        self.subEnd = self.dt.now()
        self.file.write(f'\n{self.dt.now()}\t{id}\tSUBEND\t{task}: Subject ended, duration: {self.subEnd - self.subStart}')
        
    def close(self):
        self.file.write(f'\n{self.dt.now()}\tALL\tNA\tStatusLog closed.')
        # Closes the log file
        self.file.close()


if __name__ == '__main__':
    statuslog = StatusLog('status.log')
