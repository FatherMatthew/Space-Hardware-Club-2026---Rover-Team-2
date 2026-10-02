# Arm code so far. Only prints for now, no hardware connected.


class RoverArm:
    def __init__(self):
        # Still need the pin assignments.
        self.pins = {
            "Base": None,
            "Shoulder": None,
            "Elbow": None,
            "Wrist": None,
            "Gripper": None,
        }

        # Test values, not the actual arm position.
        self.angles = {
            "Base": 90,
            "Shoulder": 90,
            "Elbow": 90,
            "Wrist": 90,
        }
        self.step = 5

    def setup_servos(self):
        # Add PWM setup once we have the hardware details.
        pass

    def move_servo(self, joint, amount):
        if joint not in self.angles:
            print("Unknown joint:", joint)
            return

        # Temporary range for testing. Need to check each joint's limits.
        target = max(0, min(180, self.angles[joint] + amount))
        self.angles[joint] = target
        print(f"Test: {joint} -> {target}")
        # Send to the servo here later.

    def control_gripper(self, action):
        # Still need to work out the gripper control.
        pass

    def stop_all(self):
        # Stop logic still needs to be added.
        pass

    def handle_command(self, command):
        if command == "STOP_ALL":
            self.stop_all()
        elif command in ("GRIPPER_OPEN", "GRIPPER_CLOSE"):
            self.control_gripper(command.split("_")[1])
        else:
            parts = command.rsplit("_", 1)
            if len(parts) != 2 or parts[1] not in ("PLUS", "MINUS"):
                print("Unsupported arm command:", command)
                return

            joint = parts[0].title()
            amount = self.step if parts[1] == "PLUS" else -self.step
            self.move_servo(joint, amount)


if __name__ == "__main__":
    arm = RoverArm()
    arm.setup_servos()
    arm.handle_command("BASE_PLUS")
    arm.handle_command("SHOULDER_MINUS")
    arm.handle_command("GRIPPER_OPEN")
    arm.handle_command("STOP_ALL")

    # Need to connect this to incoming commands from the Orange Pi.
