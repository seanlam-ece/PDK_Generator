""" Copyright chriskeraly
    Copyright (c) 2019 Lumerical Inc. """

import os
import lumapi

class Simulation(object):
    """
        Object to manage the FDTD CAD. 

        Parameters
        ----------
        :param workingDir:    working directory for the CAD session.
        :param hide_fdtd_cad: if true, runs the FDTD CAD in the background.
    """

    def __init__(self, workingDir, use_var_fdtd, hide_fdtd_cad):
        """ Launches FDTD CAD and stores a handle. """
        self.fdtd = lumapi.MODE(hide = hide_fdtd_cad) if use_var_fdtd else lumapi.FDTD(hide = hide_fdtd_cad)
        self.workingDir = os.path.abspath(workingDir)
        self.fdtd.cd(self.workingDir)

    def save(self, name):
        """ Saves simulation file. """
        self.fdtd.cd(self.workingDir)
        full_name = os.path.join(self.workingDir, name)
        self.fdtd.save(full_name)
        return full_name

    def load(self, name):
        full_name = os.path.join(self.workingDir, name)
        self.fdtd.load(full_name)

    def save_index_to_vtk(self, filename):
        """ Checks if an index monitor with the name "global_index" exists. If so, it will store the 'index' attribute in a .vtr file.
            Parameters
            ----------
            :param filename:    filename of the VTK file to store the index data
        """
        if self.fdtd.getnamednumber("global_index") > 0:
            script=('idx = getresult("global_index", "index");'
                    'vtksave("{}.vtr", idx);'
                    'clear(idx);').format(filename)
            self.fdtd.eval(script)

    def remove_data_and_save(self):
        self.fdtd.switchtolayout()
        self.fdtd.save()
        
    def __del__(self):
        self.fdtd.close()
