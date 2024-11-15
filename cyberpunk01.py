import pygame
import math
import sys
from collections import deque
from threading import Thread, Event, Lock
import queue  # For thread-safe communication
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from openant.devices.power_meter import PowerMeter, PowerData

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((1368, 768), pygame.FULLSCREEN)
pygame.display.set_caption("Heart Rate and Power Display")
clock = pygame.time.Clock()

# Load overlay image
overlay_image = pygame.image.load("cyberpunk768.png")

# Colors
RED = (163, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (10,196,169)

# Arc width modifier
ARC_WIDTH = 400  # Change this value to adjust the thickness of the arcs

# Text settings
font = pygame.font.SysFont("Arial", 36)

# Helper functions
def smooth_value(queue, new_value, smoothing_time, fps):
    max_length = int(smoothing_time * fps)
    queue.append(new_value)
    if len(queue) > max_length:
        queue.popleft()
    return sum(queue) / len(queue) if queue else 0

def calculate_heart_arc(value):
    return math.pi * value / 100

def calculate_power_arc(value):
    result = math.pi * value / 300
    return min(result, 2 * math.pi)  # Limit to 2π

# Data queues for smoothing
heart_rate_queue = deque()
power_queue = deque()

# Shared variables for ANT+ data
heart_rate = 100
power = 300

# Lock for thread-safe variable access
data_lock = Lock()

# Placeholder for ANT+ device and node initialization
node = Node()
devices = [PowerMeter(node), HeartRate(node)]

# Shared event to stop threads
stop_event = Event()

def ant_plus_data_logger():
    """ANT+ data logging loop."""
    global heart_rate, power  # Declare the global variables
    try:
        node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)

        # Define device callbacks
        def on_found(device):
            print(f"Device {device} found and receiving")

        def on_device_data(page: int, page_name: str, data):
            global heart_rate, power  # Access global variables
            with data_lock:  # Ensure safe access to shared data
                if isinstance(data, HeartRateData):
                    heart_rate = data.heart_rate  # Update heart rate
                elif isinstance(data, PowerData):
                    power = data.instantaneous_power  # Update power

        # Assign callbacks to devices
        for d in devices:
            d.on_found = lambda d=d: on_found(d)
            d.on_device_data = on_device_data

        print(f"Starting ANT+ node, press Ctrl-C to finish")
        node.start()

    except KeyboardInterrupt:
        print("Closing ANT+ device...")

    finally:
        # Ensure resources are closed
        for d in devices:
            d.close_channel()
        node.stop()

# Start the ANT+ logging thread
ant_plus_thread = Thread(target=ant_plus_data_logger)
ant_plus_thread.start()

# Main loop variables
running = True
fps = 30

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            running = False

    # Smooth data
    smoothed_heart_rate = smooth_value(heart_rate_queue, heart_rate, 4, fps)
    smoothed_power = smooth_value(power_queue, power, 7, fps)

    # Calculate arcs
    heart_arc_angle = calculate_heart_arc(smoothed_heart_rate)
    power_arc_angle = calculate_power_arc(smoothed_power)

    # Draw black background
    screen.fill(BLACK)

    # Draw heart rate arc
    if smoothed_heart_rate > 0:
        pygame.draw.arc(screen, RED, (227, -49, 900, 900), math.pi / 2, math.pi / 2 + heart_arc_angle, 400)

    # Draw power arc
    if smoothed_power > 0:
        pygame.draw.arc(screen, CYAN, (456, 159, 455, 455), math.pi / 2, math.pi / 2 + power_arc_angle, 220)

    # Draw text boxes
    if smoothed_heart_rate > 0:
        heart_text = font.render(f"HR: {int(smoothed_heart_rate)}", True, WHITE)
    else:
        heart_text = font.render("No Heart Rate", True, WHITE)

    if smoothed_power > 0:
        power_text = font.render(f"PWR: {int(smoothed_power)}", True, WHITE)
    else:
        power_text = font.render("No Power", True, WHITE)

    screen.blit(heart_text, (screen.get_width() // 2 - heart_text.get_width() // 2, screen.get_height() // 2 - 50))
    screen.blit(power_text, (screen.get_width() // 2 - power_text.get_width() // 2, screen.get_height() // 2 + 10))

    # Overlay image
    screen.blit(overlay_image, (0, 0))

    # Update display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(fps)

# Stop the ANT+ thread gracefully
stop_event.set()
ant_plus_thread.join()

pygame.quit()
sys.exit()
