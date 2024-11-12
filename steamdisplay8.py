import pygame
import math
import threading
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from openant.devices.power_meter import PowerMeter, PowerData

# Initialize global variables to hold the latest power and heart rate values
power = 0
heart_rate = 0

# Set up Pygame display
pygame.init()
screen_width, screen_height = 1317, 737
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Heart Rate and Power Indicator")

# Load images
background_image = pygame.image.load("background.png")
hr_indicator_image = pygame.image.load("bigarrow.png")
power_indicator_image = pygame.image.load("smallarrow.png")

# Set up rotation center points
center_x, center_y = 658, 368	

# Variables to set the initial rotation angles for heart rate and power indicators
hr_start_angle = -140  # Adjust this for the heart rate indicator starting angle
power_start_angle = 90  # Adjust this for the power indicator starting angle

# Multipliers and offsets for scaling rotation
power_multiplier = 300 / 1000  # 1000W equals 300 degrees rotation
hr_multiplier = 3  # 1 BPM equals 3 degrees of rotation
hr_offset = 110  # Ignore heart rate values below 110 BPM

# Font setup for number display
font = pygame.font.Font(None, 36)  # Use default font, size 36

# Function to rotate and draw an image around a center
def blit_rotate_center(surf, image, pos, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=pos).center)
    surf.blit(rotated_image, new_rect.topleft)

# Variables for smooth animation
prev_hr_value, prev_power_value = 0, 0
hr_angle, power_angle = hr_start_angle, power_start_angle  # Initialize angles with start angles
hr_velocity, power_velocity = 0, 0
max_acceleration = 0.05  # Adjust for desired smoothness

# Update function for smooth rotation based on data
def update_rotation(target_value, current_angle, velocity, multiplier, start_angle, offset=0, max_power_threshold=None):
    # Calculate adjusted target angle
    adjusted_value = max(0, target_value - offset)  # Ignore values below offset
    target_angle = start_angle + adjusted_value * multiplier

    # Limit target angle if there's a maximum threshold
    if max_power_threshold and target_value > max_power_threshold:
        target_angle = start_angle + max_power_threshold * multiplier

    # Calculate angle difference
    diff = target_angle - current_angle

    # Calculate acceleration based on angle difference
    acceleration = max_acceleration * abs(diff)

    # Update velocity based on direction
    if diff > 0:
        velocity += acceleration
    elif diff < 0:
        velocity -= acceleration

    # Apply dynamic damping: increase damping as angle difference decreases
    base_damping = 0.05  # Base damping factor
    damping_factor = base_damping + (1 - abs(diff) / 360) * 0.1  # Adjust this scaling factor as needed
    velocity *= (1 - damping_factor)

    # Update current angle based on velocity
    current_angle += velocity

    # Keep angle within 0-360 degrees
    current_angle %= 360

    return current_angle, velocity

# Pygame loop for displaying the indicators
def display_loop():
    global prev_hr_value, prev_power_value, hr_angle, power_angle, hr_velocity, power_velocity
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update indicator angles with respective multipliers and offsets
        hr_angle, hr_velocity = update_rotation(heart_rate, hr_angle, hr_velocity, hr_multiplier, hr_start_angle, hr_offset)
        power_angle, power_velocity = update_rotation(power, power_angle, power_velocity, power_multiplier, power_start_angle)

        # Draw everything
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(background_image, (0, 0))  # Draw dial background

        # Rotate and draw indicators with the starting offset
        blit_rotate_center(screen, hr_indicator_image, (center_x, center_y), hr_angle)
        blit_rotate_center(screen, power_indicator_image, (center_x, center_y), power_angle)

        # Display the current heart rate and power values
        hr_text = font.render(f"Heart Rate: {heart_rate} BPM", True, (255, 255, 255))
        power_text = font.render(f"Power: {power} W", True, (255, 255, 255))

        # Position text in the right half of the window
        screen.blit(hr_text, (screen_width - 300, screen_height // 2 - 50))
        screen.blit(power_text, (screen_width - 300, screen_height // 2 + 10))

        # Update display and tick clock
        pygame.display.flip()
        clock.tick(30)  # 30 FPS for smooth animation

    pygame.quit()

# Main ANT+ data acquisition function
def main():
    node = Node()
    node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
    
    # Define devices
    devices = [PowerMeter(node), HeartRate(node)]
    
    # Define device callbacks
    def on_found(device):
        print(f"Device {device} found and receiving")
        
    def on_device_data(page: int, page_name: str, data):
        global power, heart_rate
        if isinstance(data, HeartRateData):
            heart_rate = data.heart_rate  # Update global heart_rate variable
        elif isinstance(data, PowerData):
            power = data.instantaneous_power  # Update global power variable
    
    # Assign callbacks to devices
    for d in devices:
        d.on_found = lambda d=d: on_found(d)
        d.on_device_data = on_device_data

    # Start the ANT+ node in a separate thread
    ant_thread = threading.Thread(target=node.start)
    ant_thread.start()

    # Start the Pygame display loop
    display_loop()

if __name__ == "__main__":
    main()
