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

# Function to rotate and draw an image around a center
def blit_rotate_center(surf, image, pos, angle, offset=(0, 0)):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=pos).center)
    adjusted_rect = new_rect.move(offset[0], offset[1])
    surf.blit(rotated_image, adjusted_rect.topleft)

# Variables for smooth animation
prev_hr_value, prev_power_value = 0, 0
hr_angle, power_angle = hr_start_angle, power_start_angle  # Initialize angles with start angles
hr_velocity, power_velocity = 0, 0
max_acceleration = 0.05  # Adjust for desired smoothness

# Update function for smooth rotation based on data
def update_rotation(target_value, prev_value, current_angle, velocity, multiplier, start_angle, offset=0):
    # Calculate adjusted target angle based on multiplier and offset
    adjusted_value = max(0, target_value - offset)  # Ignore values below offset
    if adjusted_value == 0:
        return current_angle, 0
    
    target_angle = start_angle + adjusted_value * multiplier

    # Normalize the target angle to the 0-360 range
    target_angle = target_angle % 360
    
    # Calculate the difference between the current and target angle
    diff = target_angle - current_angle

    # Apply acceleration
    acceleration = max_acceleration * abs(diff)
    if diff > 0:
        velocity += acceleration
    elif diff < 0:
        velocity -= acceleration

    # Limit the velocity to avoid overshooting
    max_velocity = 5  # Maximum velocity (tune this value to control speed)
    if velocity > max_velocity:
        velocity = max_velocity
    elif velocity < -max_velocity:
        velocity = -max_velocity

    # Update angle based on velocity
    current_angle += velocity

    # Normalize the angle to stay within the 0-360 range
    if current_angle >= 360:
        current_angle -= 360
    elif current_angle < 0:
        current_angle += 360
    
    # Print debugging information for target_angle and adjusted_value
    print(f"Target Value: {target_value}, Adjusted Value: {adjusted_value}, Target Angle: {target_angle}, Current Angle: {current_angle}")
    
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

        # Set target values based on updated data (heart_rate and power)
        target_hr_value = heart_rate  # Use the latest heart rate data
        target_power_value = power  # Use the latest power data

        # Update indicator angles with respective multipliers and offsets
        hr_angle, hr_velocity = update_rotation(target_hr_value, prev_hr_value, hr_angle, hr_velocity,
                                                hr_multiplier, hr_start_angle, hr_offset)
        power_angle, power_velocity = update_rotation(target_power_value, prev_power_value, power_angle, power_velocity,
                                                      power_multiplier, power_start_angle)

        # Draw everything
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(background_image, (0, 0))  # Draw dial background

        # Rotate and draw indicators with the starting offset
        blit_rotate_center(screen, hr_indicator_image, (center_x, center_y), hr_angle)
        blit_rotate_center(screen, power_indicator_image, (center_x, center_y), power_angle)

        # Update previous values
        prev_hr_value, prev_power_value = heart_rate, power

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
    def start_ant_node():
        try:
            print(f"Starting {devices}, press Ctrl-C to finish")
            node.start()
        except KeyboardInterrupt:
            print("Closing ANT+ device...")
        finally:
            for d in devices:
                d.close_channel()
            node.stop()

    ant_thread = threading.Thread(target=start_ant_node)
    ant_thread.start()

    # Start the Pygame display loop
    display_loop()

if __name__ == "__main__":
    main()
