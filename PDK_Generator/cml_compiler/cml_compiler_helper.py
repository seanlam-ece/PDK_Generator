import subprocess
import os, sys
import platform
import xml.etree.ElementTree as ET
from shutil import rmtree, copyfile
from distutils.dir_util import copy_tree
from datetime import date

if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))
from generate_template_xml import create_cml_xml
from lumerical_lumapi import lumapi


class CMLCompilerHelper():
    """Helper class for the CML Compiler
    
    Runs CML Compiler and INTERCONNECT to create compact models and create
    .cml files.
    
    Attributes
    ----------
    publisher_key : str
        Publisher key used to determine the access rights for the generated CML
        (i.e. Public or Protected+). Depending on the version of Lumerical
        installed, CML Compiler may or may not need the publisher key.
    cml_compilations_path : str
        Absolute path of the CML Compilations directory. The location where
        all CML Compiler related data is stored.
        
    Examples
    --------
    The following shows how to generate the CML Compilations folder
    
    >>> cml_helper = CMLCompilerHelper()
    
    Continuing from above... the following shows how to generate a CML compilation
    template for a new PDK named 'Cheam'.
    
    >>> cml_helper.generate_cml_template('Cheam')
    
    After populating the 'Cheam' CML compilation folder with compact models and
    compact model data, the following shows how to generate the .cml file.
    
    >>> cml_helper.generate_cml('Cheam')
    
    """
    
    
    
    def __init__(self):
        self.publisher_key = self.get_publisher_key()
        self.create_cml_compilations_folder()
        
    def generate_cml(self, cml_name, cml_version=None):
        """Generate Compact Model Library files
        
        Generates compact models and library files (.ice and .cml) using CML
        Compiler and INTERCONNECT. Generate files will be located in the named 
        CML compilation folder within 'artifacts/interconnect'
        
        Parameters
        ----------
        cml_name : str
            Compact Model Library name (i.e. 'SiEPICfab-Grouse').
        cml_version : str, optional
            Compact model version (i.e. 'v2020_09_01''). The default is None.

        Raises
        ------
        NotADirectoryError
            If CML compilation template for given CML name does not exist.
        Exception
            If CML Compiler exits with an error even though components are
            defined in CML compilation template.

        Returns
        -------
        None.

        """
        # Set CML version to present day if no version specified
        if not cml_version:
            cml_version = 'v'+str(date.today()).replace('-','_')
        
        if not os.path.exists(os.path.join(self.cml_compilations_path, cml_name)):
            raise NotADirectoryError("'{}' is not a CML Compilation directory... Create a CML Compilation by generating a template and reformatting folders + files..."\
                                     .format(os.path.join(self.cml_compilations_path, cml_name)))
            return
        
        try:
            self.cml_compiler("all", os.path.join(self.cml_compilations_path, cml_name))
            cml_file = os.path.join(self.cml_compilations_path, cml_name, "artifacts", "interconnect", cml_name+".cml")
            os.rename(cml_file, os.path.join(os.path.dirname(cml_file), cml_name+"_"+cml_version+".cml"))
        except:
            print("\nCML Compiler does not support generating CMLs from only user generated compact models...")
            print("Running INTERCONNECT to generate CML from user created compact models...")
            # Get number of elements used for CML compiler
            tree = ET.ElementTree(file=os.path.join(self.cml_compilations_path, cml_name, cml_name+".xml"))
            num_elements = len(list(tree.getroot().find('element_list')))
            # CML Compiler Version 3.1.2347 throws exception when no elements are specified in element_list
            # The following covers the case when only user created compact models are available
            if num_elements == 0:
                with lumapi.INTERCONNECT(hide=True) as INTC:
                    # Rename user_created folder to cml_name
                    # This ensures the CML is installed using the cml_name rather than "user_created"
                    os.rename(os.path.join(self.cml_compilations_path, cml_name, "source", "user_created"), os.path.join(self.cml_compilations_path, cml_name, "source", cml_name))
                    
                    # Create .cml from user generated .ice files
                    INTC.loadcustom(os.path.join(self.cml_compilations_path, cml_name, "source"))
                    cml_folder = os.path.join(self.cml_compilations_path, cml_name, "artifacts", "interconnect")
                    try:
                        INTC.cd(cml_folder)
                    except:
                        if not os.path.exists(cml_folder):
                            os.makedirs(cml_folder)
                            INTC.cd(cml_folder)
                    
                    cml_file_name = cml_name+"_"+cml_version+".cml"
                    INTC.packagedesignkit(cml_name, cml_file_name, False, True)
                    print("Generated CML: {}".format(os.path.join(cml_folder, cml_file_name)))
                    # Rename user_created folder back to its original name
                    os.rename(os.path.join(self.cml_compilations_path, cml_name, "source", cml_name), os.path.join(self.cml_compilations_path, cml_name, "source", "user_created"))
                    
                    # Install CML in INTERCONNECT
                    INTC.installdesignkit(cml_file_name, cml_folder, True)
                    print("Installed CML in INTERCONNECT...")
                    
                    
                    # NOTE: The following code does NOT WORK. Lumerical functions don't work as expected...
                    # # Export .lib
                    # if not os.path.isdir(os.path.join(cml_folder, "library_files")):
                    #     os.makedirs(os.path.join(cml_folder, "library_files"))
                    # INTC.loadcustom(os.path.dirname(cml_folder))
                    # INTC.exportlib(cml_file_name, os.path.join(cml_folder, "library_files"), True)
                    # print("Exported LIB: {}".format(os.path.join(cml_folder, "library_files", cml_file_name)))
                    
                    # # Export .html for each compact model
                    # INTC.cd(cml_export_folder)
                    # compact_models = [x.replace("::custom::","") for x in INTC.library().split('\n') if "::custom::user_created::" in x]
                    # for model in compact_models:
                    #     INTC.exporthtml(model)
                    #     print("Export HTML: {}".format(model))
                    # print("Exported HTMLs: {}".format(cml_export_folder))
    
            else:
                raise Exception("CML Compiler returned with an error... See above traceback...")
                
    def generate_cml_template(self, cml_name):
        """Create CML compilation template from lumfoundry template
        
        Copies the lumfoundry template, replacing lumfoundry with given cml name.
        
        Parameters
        ----------
        cml_name : str
            Name of compact model library (i.e. 'SiEPICfab-Grouse').

        Returns
        -------
        None.

        """
        # Generate cml directory
        cml_dir = os.path.join(self.cml_compilations_path, cml_name)
        if not os.path.isdir(cml_dir):
            self.cml_compiler("template", self.cml_compilations_path)
            os.rename(os.path.join(self.cml_compilations_path, "lumfoundry_template"), cml_dir)
        else:
            print("Template for {} has already been generated... Returning...".format(cml_name))
            return

        # Update the generate_template_xml.py script in cml directory
        with open(os.path.join(os.path.dirname(__file__), 'generate_template_xml.py'), 'r') as f1:
            code = f1.read()
            code += "\n"
            code += "cml_name = \""+cml_name+"\"\n"
            code += "directory = os.path.dirname(__file__)\n"
            code += "create_cml_xml(cml_name, directory)\n"
            
        with open(os.path.join(cml_dir, 'generate_template_xml.py'), 'w') as f2:
            f2.write(code)
            
        # Remove default xml file then create cml xml file
        os.remove(os.path.join(cml_dir, 'lumfoundry_template.xml'))
        create_cml_xml(cml_name, cml_dir)
    
    def cml_compiler(self, cmd, directory):
        """Run CML Compiler in given directory with given command
        
        Supported commands are:
            template
            library
            install
            test
            all
            runtests
            support
            
        See https://support.lumerical.com/hc/en-us/articles/360037138374 for 
        details about CML Compiler commands.
        
        Parameters
        ----------
        cmd : str
            CML Compiler command.
        directory : str
            Path where CML Compiler will run.

        Returns
        -------
        None.

        """
        if cmd in ["template", "library", "install", "test", "all", "runtests", "support"]:
            print("\nRunning CML Compiler...")
            print("Directory: {}".format(directory))
            
            # If cmd is "template", delete lumfoundry_template folder if it exists
            # If lumfoundry_template folder is not deleted, exception will be raised (CalledProcessError and EOFError)
            if cmd == "template" and os.path.isdir(os.path.join(directory, "lumfoundry_template")):
                rmtree(os.path.join(directory, "lumfoundry_template"))
                
            if self.publisher_key:
                print("cml-compiler "+cmd+" --publisher-key "+self.publisher_key)
                result = subprocess.run(["cml-compiler", cmd, "--publisher-key", self.publisher_key], cwd=directory, shell=True, check=True, text=True, stdout=subprocess.PIPE)
            else:
                print("cml-compiler "+cmd)
                result = subprocess.run(["cml-compiler", cmd], cwd=directory, shell=True, check=True, text=True, stdout=subprocess.PIPE)
            print(result.stdout)
        else:
            print("Unsupported command... Exiting...")
            return
    
    def create_cml_compilations_folder(self):
        """Create CML Compilations folder with lumfoundry template
        
        Returns
        -------
        None.

        """
        # Find/make cml_compilations folder
        self.get_cml_compilations_path()
        if not os.path.isdir(self.cml_compilations_path):
            os.mkdir(self.cml_compilations_path)

        # Populate cml_compilations with lumfoundry template
        if not os.path.isdir(os.path.join(self.cml_compilations_path, 'lumfoundry_template')):
            self.cml_compiler("template", self.cml_compilations_path)
        print("cml_compilations folder: \n{}\n".format(self.cml_compilations_path))
    
    def get_cml_compilations_path(self):
        """Get CML Compilations directory path
        
        CML Compilations folder is where all CML Compiler related data is stored.
        
        Raises
        ------
        Exception
            If 'PDK-Generator' is not a folder or repo root folder does not exist.

        Returns
        -------
        str
            Absolute path of CML compilations directory.

        """
        repo_root = os.path.dirname(__file__)
        while repo_root.split('\\')[-1].split('/')[-1] != "PDK-Generator":
            repo_root = os.path.dirname(repo_root)
            if ((repo_root == "C:\\" or repo_root == "C:/") and platform.system() == "Windows")\
            or (repo_root == "/" and platform.system() == "Darwin"):
                print("Cannot get cml_compilations folder... Cannot find PDK-Generator root folder... Exiting...")
                raise Exception("Cannot get cml_compilations folder... Cannot find PDK-Generator root folder... Exiting...")
        self.cml_compilations_path = os.path.join(repo_root, "cml_compilations")
        
        return self.cml_compilations_path
    
    def get_publisher_key(self):
        """Get publisher key from INTERCONNECT for CML Compiler
        
        Returns
        -------
        str
            The publisher key.

        """
        
        with lumapi.INTERCONNECT(hide=True) as INTC:
            print("\nGetting publisher key...")
            try:
                pkeys = INTC.getdesignkitkey().split('\n')
            except:
                print("Lumerical INTERCONNECT Version {} does not support 'getdesignkitkey'... No publisher key found...".format(INTC.version()))
                return ""
            prompt = "Check your Lumerical licensing for the appropriate publisher key to use (Public vs. Protected)\n"
            for i in range(0,len(pkeys)):
                prompt += "Choose {} to use publisher key: ".format(i) + pkeys[i] + '\n'
            result = int(input(prompt + "Choice: "))
            return pkeys[result]
    
    def update_cml_with_new_models(self, cml_name, compact_models, cml_version = None):
        '''Update compact model library (CML) with new compact models
        
        Copy compact model files and folders to specified CML and compiles CML.
        NOTE: CML template must already exist for this to work.

        Parameters
        ----------
        cml_name : str
            Name of compact model library that already exists.
        compact_models : dict or list
            If dict, Keys = absolute path to compact model file, Values = photonic model.
            If list, list of absolute paths to compact model files (.ice)
            

        Returns
        -------
        None.

        '''
        # If empty
        if not compact_models:
            print("No compact models defined... Not updating {} CML...".format(cml_name))
            return
        
        if not cml_version:
            cml_version = 'v'+str(date.today()).replace('-','_')
        
        cml_path = os.path.join(self.cml_compilations_path, cml_name)
        if not os.path.isdir(cml_path):
            self.generate_cml_template(cml_name)
        
        if type(compact_models) == dict:
            print("Updating CML with photonic model mapping...")
            element_list = []
            for compact_model_folder, photonic_model in compact_models.items():
                # Make dir for compact model if it does not exist
                model_name = compact_model_folder.split(os.sep)[-1]
                cml_model_path = os.path.join(cml_path, "source", model_name)
                if not os.path.isdir(cml_model_path):
                    os.mkdir(cml_model_path)
                
                # Copy compact model files and folder to CML and create element list
                copy_tree(compact_model_folder, cml_model_path)
                element_list.append([model_name, photonic_model, ".lsf"])
                print("Added to {} CML: {}".format(cml_name, model_name))
            
            # Update XML file
            create_cml_xml(cml_name, cml_path, element_list)
            print("Updated {} CML".format(cml_name))
        elif type(compact_models) == list:
            print("Updating CML with custom compact model file...")
            for compact_model_path in compact_models:
                copyfile(compact_model_path, os.path.join(cml_path, "source", "user_created"))
                
        # Run CML Compiler to compile models
        self.cml_compiler('all', cml_path)
        self.cml_compiler('template', self.cml_compilations_path)
        # self.generate_cml(cml_name)
        
        # Rename the .cml file to add the version number
        cml_file = os.path.join(cml_path, "artifacts", "interconnect", cml_name+".cml")
        cml_versioned = os.path.join(cml_path, "artifacts", "interconnect", cml_name+"_"+cml_version+".cml")
        copyfile(cml_file, cml_versioned)
        