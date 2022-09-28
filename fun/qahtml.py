#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class QaHtml:
    
    """
    This crates a html pages that help with visual inspection of the data.py
    A main page is created that links to all subject-level pages that will \
    have plots and some numerical information.
    TODO:
        - add a table of contents to the main page; sub-1xxxx
        - add info on packages used by the pipeline
        - think about switching from hardcoding html in this script to using \
            a template with spaceholders or some packages that create html code such as ninja2
    """

    def __init__(self, QaDataDir, SubsList, SessionName):
        
        import os
        from datetime import datetime as dt
        import shutil
        # Import here as self to access it in methods
        self.os = os
        self.dt = dt
        self.sh = shutil

        # The QA directory where all QAs
        self.QaDataDir = QaDataDir
        # The list of subjects
        self.Subs = SubsList
        # The name of the session; can be DWI but may also use it for other sessions
        self.SessionName = SessionName
        # Set session path for easier access:
        self.SessionDirName = self.SessionName.replace(' ', '').lower()
        self.SessionPath = self.os.path.join(self.QaDataDir, self.SessionDirName)

        # check if the directory exists
        if not self.os.path.exists(self.QaDataDir):
            self.os.mkdir(self.QaDataDir)
            print(f'QA Directory created: {self.QaDataDir}')
        else:
            print(f'QA Directory already exists: {self.QaDataDir}')

        if not self.os.path.exists(self.SessionPath):
            self.os.mkdir(self.SessionPath)
            self.os.mkdir(self.os.path.join(self.SessionPath, 'subs'))
            self.os.mkdir(self.os.path.join(self.SessionPath, 'imgs'))
            print(f'QA Session Directory created: {self.SessionPath}')

    def create_main_page(self):
        
        # creates main html page
        ### HTML header and footers
        # for main html page that will have links to all subject pages
        self.MainHeader = f"""<!DOCTYPE html>\n
                            <html>\n
                            <head>\n
                            \t<title>QA {self.SessionName}</title>\n
                            </head>\n
                            <body>\n"""
        
        # This will close the main page
        self.MainFooter = f"""\nAll Watched Over by Machines of Loving Grace\n<br>\n
            timestamp: {self.dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n</body>\n
            </html>"""

        with open(self.os.path.join(self.SessionPath, 'index.html'),'w') as p:
            p.write(self.MainHeader)
            p.write(f'<center><h1>QA {self.SessionName}</h1></center><br><br>\n')

        subs = self.Subs.sort()
        # creates main html page
        # List of subs is to be divided into sets of IDs of the same leading digits
        # that is sub-1xxxx and sub-2xxxx will be in different sets
        l = subs[0][4] # counter from the first digit of the subject number
        for i, s in enumerate(subs):
            if i == 0:
                # first subject, set title
                p.write(f'\n\n<br><br><center><h3><a id="sub-{l}x">sub-{l}x</a></center></h3><br>\n')
                p.write(f'  <a href="subs/{s}.html">{s}</a>  \n')
            else:
                if not s.startswith(f'sub-{l}'):
                    # new digit, set title
                    l = s[4]
                    p.write(f'\n\n<br><br><center><h3><a id="sub-{l}x">sub-{l}x</a></center></h3><br>\n')
                    p.write(f'  <a href="subs/{s}.html">{s}</a>  \n')
                
                else:
                    # same digit, continue
                    p.write(f'  <a href="subs/{s}.html">{s}</a>  \n')
            
        p.write(self.MainFooter)
        p.close()

    def create_sub_page(self, Sub):
        # TODO - this must be less specific to dwi - make it more general to other potential sessions
        # thats why an external template.html file would be better, they will just need to replace a keyword in text with generated text.

        # for subject html page, created for each subject
        self.SubHeader = f"""<!DOCTYPE html>\n
                            <html>\n
                            <head>\n
                            \t<title>{Sub} - QA - {self.SessionName}</title>\n
                            </head>\n
                            <body>\n"""
        self.SubFooter = f"""\nAll Watched Over by Machines of Loving Grace\n<br>\ntimestamp: {self.dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n</body>\n
                            </html>"""

        # H2 level titles
        self.SubSectionsTitles = ['1. Suppression of Gibbs Oscillations',\
                            '2. Denoising with Patch2Self',\
                            '3. TopUp',\
                            '4. Eddy Correction']
        # Give some info about each section
        self.SubSectionsInfo = ['Gibbs de-ringing was performed with\
            <a href = "https://dipy.org/documentation/1.5.0/interfaces/gibbs_unringing_flow/">dipy_gibbs_ringing</a> command (DIPY 1.5.0,\
            more about the method <a href="https://dipy.org/documentation/1.5.0/examples_built/denoise_gibbs/#example-denoise-gibbs">here</a>.)',\
            'Denoising was performed with <a href = "https://dipy.org/documentation/1.5.0/interfaces/patch2self_flow/">dipy_patch2self</a> command (DIPY 1.5.0,\
            more about the method <a href="https://dipy.org/documentation/1.5.0/examples_built/denoise_patch2self/#example-denoise-patch2self">here</a>.)',\
            'TopUp was performed with <a href = "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup">topup</a> command (FSL 6.0.5,\
            more about the method <a href="https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup/TopupUsersGuide">here</a>.)',\
            'Eddy correction was performed with <a href = "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy">eddy</a> command (FSL 6.0.5,\
            more about the method <a href="https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide">here</a>.)']

        # These are for table of contents generation
        self.SubSectionsTags = ['Gibbs', 'Patch2Self', 'TopUp', 'Eddy']
        # These will be added to the html page, then later replaced with content
        self.SubSectionsSpaceHolders = ['[[TBC_Gibbs]]', '[[TBC_Patch2Self]]', '[[TBC_TopUp]]', '[[TBC_Eddy]]']

        # creates subject html page
        with open(self.os.path.join(self.SessionPath, 'subs', f'{Sub}.html'),'w') as p:
            p.write(self.SubHeader)
            p.write(f'<center><h1>{Sub}</h1></center>\n')
            # make table of contents
            for i in range(len(self.SubSectionsTitles)):
                p.write(f'<a href="#{self.SubSectionsTags[i]}">{self.SubSectionsTitles[i]}</a><br>\n')
            p.write('<br><br><hr><br><br>\n')
            
            # add sections
            for i in range(len(self.SubSectionsTitles)):
                p.write(f'<h2><a id="{self.SubSectionsTags[i]}">{self.SubSectionsTitles[i]}</a></h2> <br><br>\n<center><p>{self.SubSectionsInfo[i]}</p></center>\n\
                    <br><br><center>\n\n{self.SubSectionsSpaceHolders[i]}\n\n</center> <br><br> <hr> <br><br>\n\n')

            p.write(self.SubFooter)
            p.close()   

    def initialise(self, clean):
        # creates initial html file, run just once, after first step of preprocessing
        # creates the directory structure
        if not self.os.path.exists(self.SessionPath):
            # No dirs, create them
            self.os.mkdir(self.SessionPath)
            self.os.mkdir(self.os.path.join(self.SessionPath, 'subs'))
            self.os.mkdir(self.os.path.join(self.SessionPath, 'imgs'))
        elif self.os.path.exists(self.SessionPath) and clean:
            # Remove all files in the directory
            self.shutil.rmtree(self.SessionPath)
            self.os.mkdir(self.SessionPath)
            self.os.mkdir(self.os.path.join(self.SessionPath, 'subs'))
            self.os.mkdir(self.os.path.join(self.SessionPath, 'imgs'))
        else:
            # Directory exists cannot init -> exit
            print(f'QA Directory already exists: {self.QaDataDir}, please delete it first or set clean=True.')
            exit()
        
        # the below should not continue if the directory exists and clean=False
        # create main html page
        self.create_main_page()
        # create subject html pages
        for s in self.Subs:
            self.create_sub_page(s)
    
    def software_versions(self, flag):
        # Get all python packages versions to a file
        # TODO: add FSL version
        
        import subprocess as sp
        sp.run(f'pip list > {self.SessionPath}/pip_freeze_{flag}.tsv', shell=True)
    
    ###############################################################################################################
    # DWI PREPROCESSING METHODS ###################################################################################
    ###############################################################################################################


    def add_dwi_gibbs(self, subject, subjectDataDir):
        
        # Method specific to DWI preprocessing
        # Adds the Gibbs suppression section to the subject html page
        # Run after all Gibbs stuff has been done for the subject (single)
        # subject: subject name

        if 'sub-' not in subject:
            subject = 'sub-' + subject
        
        # Copy all the images to the imgs directory, should be in sub-x/pngs/gibbs, overwrite
        if not self.os.path.exists(self.os.path.join(subjectDataDir, 'imgs',f'{subject}', 'gibbs')):
            self.os.path.mkdir(self.os.path.join(subjectDataDir, 'imgs',f'{subject}', 'gibbs'))
        try:
            self.shutil.copytree(self.os.path.join(subjectDataDir, 'pngs', 'gibbs'), self.os.path.join(self.SessionPath, 'imgs', f'{subject}', 'gibbs'))
        except FileExistsError:
            self.shutil.rmtree(self.os.path.join(self.SessionPath, 'imgs', f'{subject}', 'gibbs'))
            self.shutil.copytree(self.os.path.join(subjectDataDir, 'pngs', 'gibbs'), self.os.path.join(self.SessionPath, 'imgs', f'{subject}', 'gibbs'))
        except:
            print(f'Error copying gibbs images for subject {subject}')
            exit()
        
        # Get the images
        gifs = [g for g in self.os.listdir(self.os.path.join(subjectDataDir, 'pngs', 'gibbs')) if g.endswith('.gif')]
        imgs = [f for f in self.os.listdir(self.os.path.join(subjectDataDir, 'pngs', 'gibbs')) if f.endswith('.png')]
        # Create the html code for the images
        html = ''
        # First add the gifs
        for g in gifs:
            html += f'<center><img src="../imgs/{subject}/gibbs/{g}" width="100%"></center><br>\n'

        # Then add the pngs
        imgs.sort()
        for i in imgs:
            html += f'<center><img src="../imgs/{subject}/gibbs/{i}" width="100%"></center><br>\n'

        # get the subject html page and replace space holder with html code
        try:
            with open(self.os.path.join(self.SessionPath, 'subs', f'{subject}.html'),'a') as p:
                p.replace(self.SubSectionsSpaceHolders[0], html)
            p.close()
        except:
            print(f'Cannot append to subject {subject} html page in {self.SessionPath}.')
            exit()

        # Remove the gifs and pngs from the subject directory
        self.shutil.rmtree(self.os.path.join(subjectDataDir, 'pngs', 'gibbs'))


    def add_dwi_p2s(self, subject):
        # Method specific to DWI preprocessing
        pass
    def add_dwi_topup(self, subject):
        # Method specific to DWI preprocessing
        pass
    def add_dwi_eddy(self, subject):
        # Method specific to DWI preprocessing
        pass

