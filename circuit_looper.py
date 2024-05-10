from circuit_reader import *
from circuit_calcs import *

# SETTINGS

# runner mode plots various variables in one circuit
# looper mode plots change of results of one circuit due to change of params
mode = "looper"  # "runner"  # 
template = "kent"
param_file = "kent_params_240507.txt"
variation = "biased_jj"  # None  # 
results_to_watch = ["v(101)", "v(102)"]  # phase, leff, etc.

# looper settings
if mode == "looper":
    param_to_change = "idc_mag"  # "idc_mag"
    param_list = np.linspace(0, 2e-6, 201)  # 0e-6, 5e-6, 101)
    results_list = {}
    for result in results_to_watch:
        results_list[result] = []

# Settings end, begin simulating results

# make CircuitData object
cd = CircuitData()

if mode == "runner":
    # simulate circuit
    cd.simulation_cycle(template, param_file, variation)
    time_array = cd.data["time"]
    for result in results_to_watch:
        plt.plot(time_array, cd.data[result], label=f"{result}")
    plt.tight_layout()
    plt.grid()
    plt.legend()
    plt.show()
    
elif mode == "looper":
    t1 = time.time()
    for param in param_list:
        print(param)
        cd.change_param(param_to_change, param)
        cd.simulation_cycle(template, param_file, variation)
        time_array = cd.data["time"]
        for result in results_to_watch:
            result_value = cd.data[result].to_numpy()[-1]  # final value only for now
            results_list[result].append(result_value)
    t2 = time.time()
    print(f"Simulation loop took {(t2 - t1)/60} minutes.")
    
    for result in results_to_watch:
        plt.plot(param_list, results_list[result], label=f"{result}")
    plt.xlabel(f"{param_to_change}")
    plt.tight_layout()
    plt.grid()
    plt.legend()
    plt.show()
