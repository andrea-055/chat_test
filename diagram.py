import matplotlib.pyplot as plt
import numpy as np

# Data from the 3 runs
runs = ['Run 1', 'Run 2', 'Run 3']
user_loads = ['10 users', '30 users', '50 users']

# Successful and failed messages for each run and user load
successful_messages = [
    [50, 150, 250],  # Run 1
    [50, 150, 250],  # Run 2
    [50, 145, 243]   # Run 3
]
failed_messages = [
    [0, 0, 0],  # Run 1
    [0, 0, 0],  # Run 2
    [0, 5, 7]   # Run 3
]
failure_rates = [
    [0, 0, 0],  # Run 1
    [0, 0, 0],  # Run 2
    [0, 3.33, 2.8]  # Run 3
]

# Diagram
fig, ax1 = plt.subplots(figsize=(12, 6))
bar_width = 0.25
x = np.arange(len(user_loads))

# Bars for each run
for i, run in enumerate(runs):
    ax1.bar(x + i * bar_width, successful_messages[i], bar_width, label=f'{run} - Successful', color=['green', 'limegreen', 'forestgreen'][i])
    ax1.bar(x + i * bar_width, failed_messages[i], bar_width, bottom=successful_messages[i], label=f'{run} - Failed', color=['red', 'darkred', 'firebrick'][i])

# Left axis (number of messages)
ax1.set_xlabel('Number of Users')
ax1.set_ylabel('Number of Messages', color='black')
ax1.set_xticks(x + bar_width)
ax1.set_xticklabels(user_loads)
ax1.legend(loc='upper left')

# Values on top of bars
for i, run in enumerate(runs):
    for j, user_load in enumerate(user_loads):
        total = successful_messages[i][j] + failed_messages[i][j]
        ax1.text(x[j] + i * bar_width, total + 1, str(successful_messages[i][j]), ha='center', va='bottom')

# Right axis (failure rate)
ax2 = ax1.twinx()
for i, run in enumerate(runs):
    ax2.plot(x + i * bar_width, failure_rates[i], marker='o', label=f'{run} - Failure Rate', color=['blue', 'cyan', 'navy'][i])
ax2.set_ylabel('Failure Rate (%)', color='blue')
ax2.tick_params(axis='y', labelcolor='blue')
ax2.legend(loc='upper right')

# Text annotations for failure rates
for i, run in enumerate(runs):
    for j, rate in enumerate(failure_rates[i]):
        ax1.text(x[j] + i * bar_width, 50, f'{rate:.1f}%', color=['blue', 'cyan', 'navy'][i], fontsize=8, ha='center')

# Title
plt.title('UI Test Results: Message Delivery Across Test Runs')

# Display
plt.tight_layout()
plt.show()