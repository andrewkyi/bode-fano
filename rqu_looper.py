from circuit_reader import *
from circuit_calcs import *

# SETTINGS

# runner mode plots various variables in one circuit
# looper mode plots change of results of one circuit due to change of params
mode = "looper"  # "looper", "runner"
template = "rqu"  # "parallel"
param_file = "rqu_params_240507.txt"  # "parallel_params_240506.txt"
results_to_watch = ["v(101)", "v(102)", "v(103)"]  # phase, leff, etc.

# looper settings
if mode == "looper":
    param_to_change = "ib1_mag"  # "ibias_mag"
    param_to_link = "ib2_mag"
    param_list = np.linspace(0e-5, 4e-4, 401)  # (1.68e-4, 1.72e-4, 401)  # 
    results_to_watch = ["v(101)", "v(102)", "v(103)"]  # phase, leff, etc.
    results_list = {}
    for result in results_to_watch:
        results_list[result] = []

# make CircuitData object
cd = CircuitData()
# simulate circuit
cd.simulation_cycle(template, param_file)
time_array = cd.data["time"]  # this is always in common

if mode == "runner":
    cd.change_param("tran_stop", 2e-10)
    cd.change_param("tran_step", 1e-14)
    cd.simulation_cycle(template, param_file)
    cd.data["v(101)"] = -cd.data["v(101)"]
    time_array = cd.data["time"]
    for result in results_to_watch:
        plt.plot(time_array, cd.data[result], label=f"{result}")
        # plt.xlabel(result)
    plt.tight_layout()
    plt.grid()
    plt.legend()
    plt.show()
    
    y_j1, y_j2, y_j3 = 10e-6 * np.cos(cd.data["v(101)"]), 10e-6 * np.cos(cd.data["v(102)"]), 17e-6 * np.cos(cd.data["v(103)"])
    ic_j1, ic_j2, ic_j3 = 10e-6 * np.sin(cd.data["v(101)"]), 10e-6 * np.sin(cd.data["v(102)"]), 17e-6 * np.sin(cd.data["v(103)"])
    phases = np.linspace(0, 2*np.pi, 721)
    plt.rcParams["figure.figsize"] = [8,8]
    plt.rcParams.update({'font.size': 16})

    for time_idx in range(len(time_array)):
        c_frac = 1
        c1, c2, c3 = ((196-126*c_frac)/255,(216-79*c_frac)/255,(233-44*c_frac)/255), ((250-8*c_frac)/255,(213-61*c_frac)/255,(176-118*c_frac)/255), ((206-117*c_frac)/255,(229-60*c_frac)/255,(203-129*c_frac)/255)
        # c_frac = time_idx / (len(time_array) - 1)
        # c1, c2, c3 = ((196-126*c_frac)/255,(216-79*c_frac)/255,(233-44*c_frac)/255), ((250-8*c_frac)/255,(213-61*c_frac)/255,(176-118*c_frac)/255), ((206-117*c_frac)/255,(229-60*c_frac)/255,(203-129*c_frac)/255)
        idx_div=80
        if time_idx%idx_div==1:
            print(time_idx//idx_div)
            plt.plot(10e-6 * np.cos(phases), 10e-6 * np.sin(phases), color=c1, zorder=0, label="JJ1")
            plt.plot(10e-6 * np.cos(phases), 10e-6 * np.sin(phases), color=c2, zorder=0, label="JJ2")
            plt.plot(17e-6 * np.cos(phases), 17e-6 * np.sin(phases), color=c3, zorder=0, label="JJ3")
            plt.plot(y_j1[time_idx], ic_j1[time_idx], ".", markersize=20, color=c1)
            plt.plot(y_j2[time_idx], ic_j2[time_idx], ".", markersize=20, color=c2)
            plt.plot(y_j3[time_idx], ic_j3[time_idx], ".", markersize=20, color=c3)
            # plt.plot(y_j1[time_idx]+y_j2[time_idx]+y_j3[time_idx], ic_j1[time_idx]+ic_j2[time_idx]+ic_j3[time_idx], ".", markersize=20, color=(0.5,0.5,0.5))
            # 70, 137, 189 -> 196, 216, 233 / 242, 152, 58 -> 250, 213, 176 / 89, 169, 74 -> 206, 229, 203
            plt.xlabel("Josephson Junction admittance (normalized)")
            plt.ylabel("Current through junction (A)")
            plt.tight_layout()
            plt.grid()
            plt.legend()
            # plt.show()
            plt.savefig(f"rqu_frames/phase_plot_{time_idx//idx_div}.png")
            plt.clf()

    from matplotlib.animation import FuncAnimation
    nframes = len(time_array)//idx_div
    plt.subplots_adjust(top=1, bottom=0, left=0, right=1)
    def animate(i):
        print(i)
        im = plt.imread(f"rqu_frames/phase_plot_{i}.png")
        plt.imshow(im)
    anim = FuncAnimation(plt.gcf(), animate, frames=nframes, interval=(20000.0/nframes))
    anim.save("rqu_circle_plot.gif")
    
elif mode == "looper":
    t1 = time.time()
    for param in param_list:
        print(param)
        cd.change_param(param_to_change, param)
        if param_to_link is not None:
            cd.change_param(param_to_link, param)
        cd.simulation_cycle(template, param_file)  # drop the param_file, which is already loaded
        for result in results_to_watch:
            if result == "v(101)": result_value = -cd.data[result].to_numpy()[-1]  # final value only for now
            else: result_value = cd.data[result].to_numpy()[-1]  # final value only for now
            results_list[result].append(result_value)
    t2 = time.time()
    print(f"Simulation loop took {(t2 - t1)/60} minutes.")
    
    for result in results_to_watch:
        plt.plot(param_list, results_list[result], "x", label=f"{result}")
        # plt.xlabel(result)
    plt.xlabel("Bias Current (A)")
    plt.ylabel("Phase (rad)")
    plt.tight_layout()
    plt.grid()
    plt.legend()
    plt.savefig("rqu_ibias_phase.png")
    plt.show()
    
    l_j1, l_j2, l_j3 = calc_lj(10e-6, results_list["v(101)"]), calc_lj(10e-6, results_list["v(102)"]), calc_lj(17e-6, results_list["v(103)"])
    plt.plot(param_list, 1/l_j1 + 1/l_j2 + 1/l_j3, label="JJ admittance")
    plt.xlabel("Bias Current (A)")
    plt.ylabel("Total Josephson Junction Admittance (1/H)")
    plt.tight_layout()
    plt.grid()
    plt.legend()
    plt.savefig("rqu_ibias_totaly.png")
    plt.show()
