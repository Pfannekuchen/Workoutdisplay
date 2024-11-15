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
