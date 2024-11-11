import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import datetime as dt
import random
import time

class RealTimePlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Power and Heart Rate Plot")
        
        # Set up matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        
        # Set up the Power plot
        self.ax_power = self.figure.add_subplot(211)
        self.ax_power.set_title("Power (Watt)")
        self.ax_power.set_ylabel("Power (W)")
        self.ax_power.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        
        # Set up the Heart Rate plot
        self.ax_hr = self.figure.add_subplot(212)
        self.ax_hr.set_title("Heart Rate (BPM)")
        self.ax_hr.set_ylabel("BPM")
        self.ax_hr.set_xlabel("Time")
        self.ax_hr.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        
        # Embed matplotlib figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Data lists
        self.times = []
        self.power_data = []
        self.hr_data = []
        
        # Start updating
        self.update_plot()

    def update_plot(self):
        current_time = dt.datetime.now()
        
        # Generate random data for simulation
        power = random.randint(100, 300)  # Replace with actual power data
        heart_rate = random.randint(60, 180)  # Replace with actual heart rate data
        
        # Update data lists
        self.times.append(current_time)
        self.power_data.append(power)
        self.hr_data.append(heart_rate)
        
        # Keep data for the last 5 minutes (300 seconds)
        while self.times and (current_time - self.times[0]).total_seconds() > 300:
            self.times.pop(0)
            self.power_data.pop(0)
            self.hr_data.pop(0)
        
        # Clear and update plots
        self.ax_power.clear()
        self.ax_power.plot(self.times, self.power_data, color='blue')
        self.ax_power.set_title("Power (Watt)")
        self.ax_power.set_ylabel("Power (W)")
        self.ax_power.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        
        self.ax_hr.clear()
        self.ax_hr.plot(self.times, self.hr_data, color='red')
        self.ax_hr.set_title("Heart Rate (BPM)")
        self.ax_hr.set_ylabel("BPM")
        self.ax_hr.set_xlabel("Time")
        self.ax_hr.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        
        # Refresh canvas
        self.canvas.draw()
        
        # Schedule next update
        self.root.after(1000, self.update_plot)  # Update every second

# Main
root = tk.Tk()
app = RealTimePlotApp(root)
root.mainloop()
