# Sensor drivers still need to be added.
class SensorReader:
    def __init__(self):
        # TODO: set up the sensors.
        pass

    def read(self):
        # Return the readings in these units:
        # temperature: Celsius, pressure: kPa, acceleration: m/s^2, altitude: m.
        # Use None for missing readings.
        # Example shape:
        # {"temperature": ..., "pressure": ..., "accel_x": ...,
        #  "accel_y": ..., "accel_z": ..., "altitude": ...}
        return None
