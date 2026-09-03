import numpy as np
import matplotlib.pyplot as plt

data = np.load("sc2_income.npz")

print(data.files)

time = data['time']
min_rate = data['minerals_rate']

T = 60*9

unit_ressources = []

for i in range(len(time)):
    t_value = time[i]
    if t_value > T:
        break
    min_rate_value = min_rate[i]

    ressources_collected = min_rate_value * (T-t_value)
    unit_ressources.append(ressources_collected)

plt.plot(time[:len(unit_ressources)], unit_ressources)
plt.xlabel("Time (s)")
plt.ylabel("Units ressources")
plt.grid()
plt.savefig("minerals_collected_over_time.png")

