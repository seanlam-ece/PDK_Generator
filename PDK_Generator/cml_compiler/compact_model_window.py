"""
Compact Model Window
Purpose: To ease the upfront learning of CML Compiler and automate parts of CML Compiler

TODO: Add parsing for model params
TODO: Add parsing for QA params
TODO: Add parsing for statistical params
TODO: Add functionality to copy and replace params for the .lsf scripts in each template

"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QDialog, QScrollArea, QSpinBox, QLineEdit, QComboBox, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QGridLayout, QWidget, QDesktopWidget
from PyQt5.QtGui import QFont
import sys, os
import math
import yaml

class CompactModelWindow(QDialog):
    
    def __init__(self, techname, compact_model_name):
        super(CompactModelWindow, self).__init__()
        self.init_ui(techname, compact_model_name)
        
    def init_ui(self, techname, compact_model_name):
        # Set window properties
        self.setGeometry(50, 50, 1850, 800)
        self.setWindowTitle("Compact Model Generation")
        
        # Set group box wrapper
        self.groupBox = QGroupBox("Compact Model Generation")
        self.groupBox.setAlignment(QtCore.Qt.AlignHCenter)
        gboxfont = QFont()
        gboxfont.setBold(True)
        gboxfont.setPointSize(10)
        self.groupBox.setFont(gboxfont)
        
        # Create subsections in groupbox
        self.gridlayout = QGridLayout(self) 
        subsect_titles = ["1. Compact Model Details", "Notes",
                          "2. Configure Compact Model Ports", "3. Configure Compact Model Params",
                          "4. Configure Statistical Modelling (Optional)", "5. Configure QA Settings (Optional)"]
        self.subsect_layouts = [QGridLayout() for x in range(0, len(subsect_titles))]
        for x in self.subsect_layouts: x.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        subsect_gboxes = []
        subsect_scrollareas = []
        subsect_font = QFont()
        subsect_font.setBold(False)
        subsect_font.setPointSize(9)
        for i in range(0,len(subsect_titles)):
            subsect_gboxes.append(QGroupBox(subsect_titles[i]))
            subsect_gboxes[i].setFont(subsect_font)
            subsect_scrollareas.append(QScrollArea())
            subsect_scrollareas[i].setWidget(subsect_gboxes[i])
            subsect_scrollareas[i].setWidgetResizable(True)
            if i == 0 or i == 1:
                subsect_scrollareas[i].setMaximumHeight(230)
            else:
                subsect_scrollareas[i].setMaximumHeight(400)
            self.gridlayout.addWidget(subsect_scrollareas[i], math.floor(i/2), i%2)
        
        
        ##### Create description subsection #####
        description_label_widgets = [QLabel("Technology:"), QLabel("Compact Model Name:"),
                                     QLabel("Description:"), QLabel("Template:"),
                                     QLabel("Number of Notes:"), QLabel("Number of Ports:")]
        for i in range(0, len(description_label_widgets)):
            description_label_widgets[i].setFixedSize(200,25)
            self.subsect_layouts[0].addWidget(description_label_widgets[i], i, 0)
        
        # Create techname and compact model name labels
        techname_label = QLabel(techname)
        compact_model_name_label = QLabel(compact_model_name)
        techname_label.setFixedSize(100,25)
        compact_model_name_label.setFixedSize(100,25)
        self.subsect_layouts[0].addWidget(techname_label, 0, 1) 
        self.subsect_layouts[0].addWidget(compact_model_name_label, 1, 1) 
        
        # Create description text box
        self.compact_model_description = QLineEdit()
        self.compact_model_description.setFixedSize(400,25)
        self.subsect_layouts[0].addWidget(self.compact_model_description, 2, 1)
        
        # Create photonic models drop down menu
        with open(os.path.join(os.path.dirname(__file__), "photonic_model_links.yml")) as f:
            self.model_linkage = yaml.load(f, Loader=yaml.FullLoader)
        
        lum_template = list(self.model_linkage.keys())
        self.template_combobox = QComboBox()
        self.template_combobox.setFixedSize(400,25)
        for template in lum_template:
            if template != "Photonic Models":
                self.template_combobox.addItem(template)
        self.template_combobox.activated.connect(self.get_template_params)
        self.subsect_layouts[0].addWidget(self.template_combobox, 3, 1)
        
        self.num_notes_input = QSpinBox()
        self.num_notes_input.setRange(0, 20)
        self.num_notes_input.valueChanged.connect(self.set_note_count)
        self.num_notes_input.setFixedSize(40,25)
        self.subsect_layouts[0].addWidget(self.num_notes_input, 4, 1)
        
        self.num_ports_input = QSpinBox()
        self.num_ports_input.setRange(0, 20)
        self.num_ports_input.valueChanged.connect(self.set_port_count)
        self.num_ports_input.setFixedSize(40,25)
        self.subsect_layouts[0].addWidget(self.num_ports_input, 5, 1)
        
        subsect_gboxes[0].setLayout(self.subsect_layouts[0])
        
        
        ##### Create notes #####
        self.notes_property_fields = []
        self.notes_value_fields = []
        self.notes_row_labels = []
        self.note_count = 0
        
        # Create note line(s)
        for i in range(0, 20):
            self.notes_row_labels.append(QLabel(str(i+1)+":"))
            self.notes_row_labels[-1].setFixedSize(15, 25)
            self.notes_property_fields.append(QLineEdit())
            self.notes_property_fields[-1].setFixedSize(200,25)
            self.notes_value_fields.append(QLineEdit())
            self.notes_value_fields[-1].setFixedSize(500,25)
            
            self.subsect_layouts[1].addWidget(self.notes_row_labels[-1], i+1, 0)
            self.subsect_layouts[1].addWidget(self.notes_property_fields[-1], i+1, 1)
            self.subsect_layouts[1].addWidget(self.notes_value_fields[-1], i+1, 2)
        
        # Hide note line(s)
        for i in range(0, 20):
            for j in range(0, 3):
                self.subsect_layouts[1].itemAtPosition(i+1, j).widget().hide()
        
        self.subsect_layouts[1].addWidget(QLabel("Property"), 0, 1)
        self.subsect_layouts[1].addWidget(QLabel("Description"), 0, 2)
        
        subsect_gboxes[1].setLayout(self.subsect_layouts[1])
        
        ##### Create compact model ports section #####
        port_category_labels = ["Name", "Direction", "Type", "Position", "Location\n(0 to 1)", "Mapping"]
        for i in range(0, len(port_category_labels)):
            self.subsect_layouts[2].addWidget(QLabel(port_category_labels[i]), 0, i+1)
        
        self.port_names = []
        self.port_directions = []
        self.port_types = []
        self.port_positions = []
        self.port_locations = []
        self.port_row_labels = []
        self.port_mappings = []
        self.port_count = 0
        
        # Instantiate port line(s)
        for i in range(0, 20):
            self.port_row_labels.append(QLabel(str(i+1)+":"))
            self.port_row_labels[-1].setFixedSize(15, 25)
            
            self.port_names.append(QLineEdit())
            self.port_names[-1].setFixedSize(150,25)
            
            self.port_directions.append(QComboBox())
            self.port_directions[-1].addItems(["Input", "Output", "Bidirectional"])
            self.port_directions[-1].setFixedSize(150,25)
            
            self.port_types.append(QComboBox())
            self.port_types[-1].addItems(["Optical Signal", "Electrical Signal"])
            self.port_types[-1].setFixedSize(150,25)
            
            self.port_positions.append(QComboBox())
            self.port_positions[-1].addItems(["Left", "Right", "Top", "Bottom"])
            self.port_positions[-1].setFixedSize(100,25)
            
            self.port_locations.append(QLineEdit())
            self.port_locations[-1].setFixedSize(70,25)
            
            self.port_mappings.append(QComboBox())
            self.port_mappings[-1].setFixedSize(150,25)
            
            self.subsect_layouts[2].addWidget(self.port_row_labels[-1], i+1, 0)
            self.subsect_layouts[2].addWidget(self.port_names[-1], i+1, 1)
            self.subsect_layouts[2].addWidget(self.port_directions[-1], i+1, 2)
            self.subsect_layouts[2].addWidget(self.port_types[-1], i+1, 3)
            self.subsect_layouts[2].addWidget(self.port_positions[-1], i+1, 4)
            self.subsect_layouts[2].addWidget(self.port_locations[-1], i+1, 5)
            self.subsect_layouts[2].addWidget(self.port_mappings[-1], i+1, 6)
        
        # Hide port line(s)
        for i in range(0, 20):
            for j in range(0, 7):
                self.subsect_layouts[2].itemAtPosition(i+1, j).widget().hide()
        
        subsect_gboxes[2].setLayout(self.subsect_layouts[2])
        
        ##### Create Model Params Section #####
        
        self.groupBox.setLayout(self.gridlayout)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.groupBox)
        
        self.setLayout(vbox)
        
        self.center()
        self.show()
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def set_note_count(self, new_count):

        # Show existing note line(s)
        for i in range(self.note_count, new_count):
            for j in range(0, 3):
                self.subsect_layouts[1].itemAtPosition(i+1, j).widget().show()
        # Hide existing note line(s)
        for i in range(new_count, self.note_count):
            for j in range(0, 3):
                self.subsect_layouts[1].itemAtPosition(i+1, j).widget().hide()
        self.note_count = new_count
        
    def set_port_count(self, new_count):
        
        # Show existing port line(s)
        for i in range(self.port_count, new_count):
            for j in range(0, 7):
                self.subsect_layouts[2].itemAtPosition(i+1, j).widget().show()
        # Hide existing port line(s)
        for i in range(new_count, self.port_count):
            for j in range(0, 7):
                self.subsect_layouts[2].itemAtPosition(i+1, j).widget().hide()
        self.port_count = new_count

    def get_template_params(self):
        name = str(self.template_combobox.currentText())
        template_name = self.model_linkage[name]['template']
        
        # Get PDK-Generator root folder
        root = os.path.dirname(__file__)
        while root.split(os.sep)[-1] != "PDK-Generator": 
            root = os.path.dirname(root)
            
        template_file_path = os.path.join(root, "cml_compilations", "lumfoundry_template", "source", template_name, template_name+".lsf")
        if os.path.exists(template_file_path):
            with open(template_file_path) as f:
                code = f.read()
                
            code_lines = code.split('\n')
            max_port_num = 0
            max_note_num = 0
            number_of_ports = 0
            number_of_notes = 0
            relays = []
            for line in code_lines:
                orig_line = line
                stripped_line = line.strip().replace(' ', '')
                if not stripped_line.startswith("#"):
                    if "_RELAY" in stripped_line:
                        relays.append(stripped_line.split("=")[0])
                    if "ports=cell(" in stripped_line:
                        # Set number of ports
                        number_of_ports = int(stripped_line.split("(")[-1].split(")")[0])
                    if "ports{" in stripped_line:
                        # Fill port fields
                        try:
                            port_num = int(stripped_line.split("ports{")[-1].split("}")[0])
                            self.port_names[port_num-1].setText(stripped_line.split("p.name=\"")[-1].split("\"")[0])
                            self.port_directions[port_num-1].setCurrentIndex(self.port_directions[port_num-1].findText(stripped_line.split("p.dir=\"")[-1].split("\"")[0]))
                            ind = self.port_types[port_num-1].findText(orig_line.split("p.type")[-1].split("\"")[1])
                            if ind >= 0:
                                self.port_types[port_num-1].setCurrentIndex(ind)
                            ind = self.port_positions[port_num-1].findText(orig_line.split("p.pos")[-1].split("\"")[1])
                            if ind >= 0:
                                self.port_positions[port_num-1].setCurrentIndex(ind)
                            self.port_locations[port_num-1].setText(stripped_line.split("p.loc=")[-1].split(";")[0])
                        except:
                            # If can't set ports fields, leave field alone
                            pass
                    if "notes=cell(" in stripped_line:
                        # Set number of notes
                        number_of_notes = int(stripped_line.split("(")[-1].split(")")[0])
                    if "notes{" in stripped_line:
                        # Set notes fields
                        try:
                            note_num = int(stripped_line.split("notes{")[-1].split("}")[0])
                            if ".property" in stripped_line:
                                self.notes_property_fields[note_num-1].setText(orig_line.split("\"")[1])
                            if ".value" in stripped_line:
                                self.notes_value_fields[note_num-1].setText(orig_line.split("\"")[1])
                            if note_num > max_note_num:
                                max_note_num = note_num
                        except:
                            # If can't set notes fields, leave field alone
                            pass
                    elif "note_" in stripped_line:
                        try:
                            note_num = int(stripped_line.split("note_")[-1][0])
                            if ".property" in stripped_line:
                                self.notes_property_fields[note_num-1].setText(orig_line.split("\"")[1])
                            if ".value" in stripped_line:
                                self.notes_value_fields[note_num-1].setText(orig_line.split("\"")[1])
                            if note_num > max_note_num:
                                max_note_num = note_num
                        except:
                            # If can't set notes fields, leave field alone
                            pass
            
            self.num_ports_input.setValue(max(number_of_ports, max_port_num))
            self.num_notes_input.setValue(max(number_of_notes, max_note_num))
            for i in range(0, max(number_of_ports, max_port_num)):
                self.port_mappings[i].clear()
                self.port_mappings[i].addItems(relays)
                
        else:
            raise FileNotFoundError("Cannot find template file: {}".format(template_file_path))
        
        

def window():
    app = QApplication(sys.argv)
    win = CompactModelWindow("Grouse", "y_branch")
    sys.exit(app.exec_())
    
window()