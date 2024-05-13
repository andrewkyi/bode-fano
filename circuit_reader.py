import numpy as np
import pandas as pd
import math
import cmath
import time
import re
import os
from scipy.fft import fft, fftfreq
from scipy import constants as cnst
from matplotlib import pyplot as plt
from lmfit import Model
# custom imports
from circuit_calcs import *

class CircuitData:
    def __init__(self):  # reads WRSpice output data
        self.reset()
        
    def reset(self):
        # from .cir input wrspice file
        self.params = {}  # dictionary with all params
        self.circuit_type = None
        self.circuit_variation = None
        self.circuit_text = {}  # dictionary used to create .cir file (& maybe create variations or new templates later)
        # measurables: labeled results, can be phase/circuit/voltage (for now)
        self.measurables = {"phases": [], "currents": [], "voltages": [], "single_phases": [], "others": []}
        self.filename = None  # actual filename
        self.integer_params = ["level", "maxdata"]  # parameters that use integer values in wrspice
        self.notes = ""
        self.jj_info = {}  # contains node and critical current for JJs
        # from .txt results file
        self.tags = {}  # random stuff at the beginning of results file
        self.data = None
        self.vars = []
        # self.read_file(self.filename)
        
    def __str__(self):
        return self.notes  # prints template notes
        
    def simulation_cycle(self, template_name, param_file_name=None, variation=None):  # can we get this inherited or sth?
        if self.circuit_type != template_name:  # only if using a different circuit mid-script
            self.reset()
        self.read_template(template_name, param_file_name, variation)  # or smth else later
        self.create_cirfile()
        self.simulate_circuit()
        self.read_results()
        
    def change_param(self, param, value):
        self.params[param] = value 
        
    def read_param(self, param_line):
        # read param from a text line, either from template default or separate file
        param = param_line.split(",")  # gets REQUIRED parameter name & default value
        try:
            param_value = self.params[param[0]]  # param already in CircuitData
        except KeyError:
            param_value = param[1].strip()  # param is from input
            try: # change param value to wanted type. not required to make a .cir file, but is when using params for math
                if param[0] in self.integer_params: param_value = int(param_value)  # param needs to be int
                else: param_value = float(param_value.strip())  # param needs to be float
            except ValueError: pass  # param is string (leave alone)
        finally:
            self.params[param[0]] = param_value
         
    def read_template(self, template_name, param_file_name=None, variation=None):
        self.circuit_type = template_name
        self.circuit_variation = variation
        # if param_file exists, values there are prioritized
        # if there is no param_file, default values in template are used
        if param_file_name is not None:
            param_file = open(f"{param_file_name}", "r")  # must include extension
            param_counter = 0
            for param_line in param_file:
                if param_line.strip() in ["#PARAMS", "#MEASURABLES"]:
                    param_counter += 1
                    continue
                elif param_line.strip() == "": continue
                elif param_counter == 1: self.read_param(param_line)
                elif param_counter == 2: self.params["measurables"] = param_line.strip()
            param_file.close()
        template_file = open(f"templates/{template_name}_template", "r")
        template_line = None
        template_counter = 0
        template_variation = False
        template_vardict = {}  # temporary dictionary to add to circuit text
        for template_line in template_file:
            # print(template_line)
            # template_line = template_line.strip()  # 
            if template_line.strip() in ["#TEMPLATE", "#PARAMS", "#MEASURABLES", "#CIRCUIT", "#VARIATIONS", "#NOTES"]:
                template_counter += 1
                continue
            elif template_line.strip() == "":
                continue
            # add data to CircuitData
            elif template_counter == 1:  # template name
                pass
                # self.circuit_type = template_line.strip()
            elif template_counter == 2:  # params input
                self.read_param(template_line)
            elif template_counter == 3:  # get measurables
                self.params["measurables"] = template_line.strip()  # list of stuff to measure
            elif template_counter == 4:  # get the lines that are needed to write .cir file
                cirfile_line = template_line.split(" ", maxsplit=1)  # preserve whitespace, first word is unique key
                if len(cirfile_line) > 1: self.circuit_text[cirfile_line[0]] = cirfile_line[1]
                else: self.circuit_text[cirfile_line[0].strip()] = "\n"  # not the best practice, i think
            elif template_counter == 5:  # change the lines using variations
                # look for variation title in template file. if match, then fix the circuit_text according to variation
                var_list = template_line.split("=")
                if var_list[0] == "var" and var_list[1].strip() == self.circuit_variation:
                    template_variation = True
                    print(f"Using variation {var_list[1].strip()}.")
                if template_variation:
                    if var_list[0] == "add":  # add to circuit_text
                        cirfile_line = var_list[1].split(" ", maxsplit=1)
                        if len(cirfile_line) > 1: template_vardict[cirfile_line[0]] = cirfile_line[1]
                        else: template_vardict[cirfile_line[0].strip()] = "\n"  # not the best practice, i think
                    elif var_list[0] == "addm":  # add to measurables in params
                        self.params["measurables"] += f" {var_list[1].strip()}"
                    elif var_list[0] == "remove":
                        self.circuit_text.pop(var_list[1], None)  # remove directly from circuit text
                    elif var_list[0] == "removem":
                        self.params["measurables"].replace(var_list[1], "")  # remove directly from measurables
                        self.params["measurables"].replace("  ", " ")  # remove the double space, if it exists
                    elif var_list[0] == "change":
                        cirfile_line = var_list[1].split(" ", maxsplit=1)
                        self.circuit_text[cirfile_line[0]] = cirfile_line[1]  # change circuit text directly
                    elif var_list[0] == "end\n":
                        # finalize changes to circuit_text
                        pos = list(self.circuit_text.keys()).index(".tran")  # currently hard-coded!!
                        items = list(self.circuit_text.items())
                        for key,value in template_vardict.items():
                            items.insert(pos, (key, value))
                        self.circuit_text = dict(items)
                        template_variation = False
                # things like add remove change --> change measurables almost required
            elif template_counter == 6:  # get template lines
                self.notes += template_line  # add notes line by line
            else: continue  # this shouldn't be needed?
        template_file.close()
        self.filename = self.params["filename"]
        self.classify_measurables()  # classify results after loading template
            
    def create_cirfile(self):  # reads data from params and circuit_text to create cirfile
        cirfile = open(f"{self.filename}.cir", "w")
        cirfile_text = ''.join([f"{key} {value}" for key,value in self.circuit_text.items()])
        cirfile.write(cirfile_text.format(**self.params))  # unpack params dictionary and add all in circfile
        cirfile.close()
        
    def simulate_circuit(self, print_time=True):
        t1 = time.time()
        os.system(f"wrspice -b {self.filename}.cir") # -b to end wrspice after run
        t2 = time.time()
        if print_time: print(f"WRSPICE simulation took {(t2 - t1)/60} minutes.")
    
    def read_results(self):
        filename = f"{self.filename}.txt"
        infile = open(filename, "r")
        reached_var = False
        reached_val = False
        curline = 0
        nvars = 0
        data = {}
        for line in infile:
            line_strip = line.strip()
            if line_strip == "Variables:":
                reached_var = True
                continue
            if line_strip == "Values:":
                reached_val = True
                nvars = len(self.vars)
                for var_list in self.vars:
                    data[var_list[0]] = []
                continue
            if not reached_var:
                line_list = line_strip.split(": ")
                self.tags[line_list[0]] = line_list[1]
            elif not reached_val:
                line_list = line_strip.split(" ")
                self.vars.append(line_list[1:])
            else:
                line_strip = line_strip.split("\t")[-1]
                if "," in line_strip:  # when the result is a complex number
                    line_strip = line_strip.split(",")
                    line_strip_real, line_strip_imag = line_strip[0], line_strip[1]
                    data[self.vars[curline][0]].append(float(line_strip_real))
                    # self.data[self.vars[curline][0]].append(float(line_strip_imag))
                else:
                    data[self.vars[curline][0]].append(float(line_strip))
                curline = (curline + 1) % len(self.vars)
        # make into pandas dataframe
        self.data = pd.DataFrame.from_dict(data)
        
    def classify_measurables(self):
        # function using cool regex tools
        # find any measurables that are from josephson junctions.
        r = re.compile("^b")
        jj_list = list(filter(r.match, self.circuit_text.keys()))
        # save jj nodes and their critical currents separately
        r = re.compile("ics")
        for jj in jj_list:
            jj_text = self.circuit_text[jj].split()
            # Phase node is third value in circuit_text
            jj_node = jj_text[2]
            # for each jj, find the circuit_text portion that contains the critical current
            ics_text = list(filter(r.search, jj_text))[0].split("=")[1]
            # split that part off, and use self.params to fill in that value. Then convert to float
            ics = float(ics_text.format(**self.params))
            # some form of using self.params[ics_text.strip("{}")]) could be faster, unsure
            self.jj_info[jj_node] = ics
        jj_nodes = self.jj_info.keys()  # [self.circuit_text[jj].split()[2] for jj in jj_list] # [2] is jj node
        meas_list = self.params["measurables"].split()
        # start classification
        # get currents
        r = re.compile("^i")
        self.measurables["currents"].extend(list(filter(r.match, meas_list)))
        # get phases that are of form @b1[phase]
        r = re.compile("phase")  # use search instead of match
        self.measurables["single_phases"].extend(list(filter(r.search, meas_list)))
        # get phases that are of form v(jj_node)
        jj_node_string = ''.join([f"v\({node}\)|" for node in jj_nodes])[:-1]
        r = re.compile(jj_node_string)
        self.measurables["phases"].extend(list(filter(r.match, meas_list)))
        # self.phases.extend(phase_list)
        # get voltages of form v(not_jj_node).
        r = re.compile(f"^(?!{jj_node_string})^v\(")
        self.measurables["voltages"].extend(list(filter(r.match, meas_list)))
        
    def get_jj_inductances(self, as_measurable=False):
        # find any nodes that were used to measure phase and get their inductances, as a Measurable object if wanted
        # hopefully none of the phases are exactly zero?
        jj_inductances = {}
        for node in self.jj_info.keys():
            try:  # "try" in case for some reason, a node was not used to measure phase
                phase = self.data[f"v({node})"].to_numpy()
                ic = self.jj_info[node]
                lj = calc_lj(ic, phase)
                if as_measurable: jj_inductances[node] = Measurable("JJ Inductance", lj, "")
                else: jj_inductances[node] = lj
            except IndexError: pass
        return jj_inductances
    
class Measurable:
    def __init__(self, label, values, measurable_type, axis_label=None):
        self.label = label  # label for values e.g., leff
        self.values = values  # a list of values
        self.measurable_type = measurable_type  # specify type of measurement for plotter
        if axis_label is None: self.axis_label = self.label  # customizable?
        else: self.axis_label = axis_label
        
    # def __call__(self):
    #     return self.values.to_numpy()
