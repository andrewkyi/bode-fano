from circuit_reader import *
from circuit_calcs import *

# probably merge this with CalculatedValue and focus on plotting here

class Measurables:
    # this is a class that can classifies measurables (by their labels) so it is easier to plot them
    def __init__(self, cd=None):
        if cd is not None: self.classify_cd_measurables(cd)
        self.phases = []
        self.currents = []
        self.voltages = []
        self.inductances = []
        self.resistances = []
        self.capacitances = []
        self.others = []

    def classify_cd_measurables(self, cd):
        # function using cool regex tools
        # find any measurables that are from josephson junctions.
        r = re.compile("^b")
        jj_list = list(filter(r.match, cd.circuit_text.keys()))
        jj_nodes = [cd.circuit_text[jj].split()[2] for jj in jj_list] # [2] is jj node
        measurables = cd_data.params["measurables"]
        meas_list = meas.split()
        # start classification
        # get currents
        r = re.compile("^i")
        self.currents = list(filter(r.match, meas_list))
        # get phases that are of form @b1[phase]
        r = re.compile("phase")
        self.phases = list(filter(r.search, meas_list))
        # get phases that are of form v(jj_node)
        jj_node_string = ''.join([f"v\({node}\)|" for node in jj_nodes])[:-1]
        r = re.compile(jj_node_string)
        phase_list = list(filter(r.search, meas_list))
        self.phases.extend(phase_list)
        # get voltages of form v(not_jj_node).
        r = re.compile(f"^(?!{jj_node_string})^v\(")
        self.voltages = list(filter(r.search, meas_list))
        
    def classify_external_measurables(self, calc_val):
        # get a measurable list from the CalculatedValues class in circuit_calcs
        if calc_val.measurable_type == "phase":
            list_to_add = self.phases
        elif calc_val.measurable_type == "current":
            list_to_add = self.currents
        elif calc_val.measurable_type == "voltage":
            list_to_add = self.voltages
        elif calc_val.measurable_type == "inductance":
            list_to_add = self.inductances
        elif calc_val.measurable_type == "capacitance":
            list_to_add = self.capacitances
        else:
            list_to_add = self.others
        # extend the specified type list in this object
        list_to_add.extend(calc_val.label)
        
    def plot_measurables(self, calc_val_list):
        # find calc_val_list 
        pass
