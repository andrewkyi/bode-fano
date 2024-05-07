from circuit_reader import *

# SETTINGS

# runner mode plots various variables in one circuit
# looper mode plots change of results of one circuit due to change of params
mode = "looper"  # "looper"
template = "parallel"
param_file = "parallel_params_240506.txt"

# looper settings
if mode == "looper":
    param_to_change = "ibias_mag"
    param_list = np.linspace(0e-6, 4e-5, 41)
    results_to_watch = ["v(101)"]  # phase, leff, etc.
    results_list = {}
    for result in results_to_watch:
        results_list[result] = []

# make CircuitData object
cd = CircuitData()

if mode == "runner":
    # simulate circuit
    cd.simulation_cycle(template, param_file)
    
elif mode == "looper":
    t1 = time.time()
    for param in param_list:
        print(param)
        cd.change_param(param_to_change, param)
        print(cd.params)
        cd.simulation_cycle(template, param_file)  # drop the param_file, which is already loaded
        for result in results_to_watch:
            result_value = cd.data[result].to_numpy()[-1]  # final value only for now
            results_list[result].append(result_value)
    t2 = time.time()
    print(f"Simulation loop took {(t2 - t1)/60} minutes.")
    
for result in results_to_watch:
    plt.plot(param_list, results_list[result])
    plt.show()
