#! /usr/bin/python3

import matplotlib.pyplot as mpl

in_file = "time_profile.txt"
site_bringdown_time = {}
site_bringup_time = {}
site_cycle_time = {}
idx = 0
with open(in_file, "r") as tf:
    words = tf.readlines()
    for word in words:
        if idx % 2 == 0:
            site = word.split()[0]
            fn = word.split()[1]
        else:
            if fn == "bringdown":
                site_bringdown_time[site] = word.strip("\n").split()
            elif fn == "bringup":
                site_bringup_time[site] = word.strip("\n").split()
            elif fn == "cycle":
                site_cycle_time[site] = word.strip("\n").split()
                # site_cycle_time[site] += ["400.0"]
        idx += 1
    tf.close()

# print(f" site_bringdown_time: {site_bringdown_time}")
# print(f" site_bringup_time: {site_bringup_time}")
# print(f" site_cycle_time: {site_cycle_time}")

fig, ax = mpl.subplots()
sites = site_bringdown_time.keys()
print(sites)

site_avg_cycle_time = {}
for site in sites:
    site_avg_cycle_time[site] = 0.0
    if len(site_bringup_time[site]) > 1:
        for i in range(1, len(site_bringup_time[site])):
            site_avg_cycle_time[site] += float(site_bringdown_time[site][i]) + float(
                site_bringup_time[site][i]
            )
            # print(f" site_avg_cycle_time[{site}] numerator = {site_avg_cycle_time[site]}")
        site_avg_cycle_time[site] /= len(site_cycle_time[site]) - 1
        print(f"{site} Avg cycle time: {site_avg_cycle_time[site]}")

for site in sites:
    fig, ax = mpl.subplots()
    print(f"Plotting graph for site {site}")
    if len(site_bringup_time[site]) > 0:
        for i in range(0, len(site_bringup_time[site])):
            bottom = 0.0
            # Set precision to 2 decimal points
            new_bottom = float("{:.2f}".format(float(site_bringdown_time[site][i])))
            # print(new_bottom)
            # Set color of bottom half to blue
            ax.bar(
                i + 1,
                float("{:.2f}".format(float(site_bringdown_time[site][i]))),
                0.5,
                label="below",
                bottom=bottom,
                color="b",
            )
            bottom += new_bottom
            # Set color of upper half to red
            ax.bar(
                i + 1,
                float("{:.2f}".format(float(site_bringup_time[site][i]))),
                0.5,
                label="above",
                bottom=bottom,
                color="r",
            )
        avg_list = []
        x_list = []
        for i in range(1, len(site_cycle_time[site])):
            avg_list += [site_avg_cycle_time[site]]
            x_list += [i]
        # print(avg_list)
        ax.plot(x_list, avg_list, color="g")
    ax.set_title(f"Bringdown and bringup for each cycle on {site}")
    mpl.savefig(f"time_profile_graphs/time_profile_{site}.png")

"""
for site in site_cycle_time:
    ax.bar(site.key(), site.value(), 0.5, label=boolean, bottom=0)
"""
