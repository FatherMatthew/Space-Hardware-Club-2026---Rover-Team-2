# Pico arm control. Dry run keeps PWM off.
try:
    from . import arm_config as config
    from .protocol import validate_command
except ImportError:
    import arm_config as config
    from protocol import validate_command

class RoverArm:
    def __init__(self, dry_run=None):
        self.dry_run = config.DRY_RUN if dry_run is None else dry_run
        self.enabled = False
        self.ready = False
        self.outputs = {}
        self.angles = {}
        self.last_note = "Not set up"

    def setup_servos(self):
        if self.dry_run:
            self.angles = {name: 90 for name in config.JOINTS}
            self.ready = True
            self.last_note = "Simulation ready; no hardware output"
            return self.status()

        # Pins and limits need to be filled in first.
        pins = set()
        channels = set()
        slice_frequencies = {}
        for name, settings in config.JOINTS.items():
            if any(settings[key] is None for key in settings):
                raise ValueError("Finish the settings for " + name)
            pin = settings["pin"]
            if not isinstance(pin, int) or pin < 0 or pin > 28 or pin in pins:
                raise ValueError("Invalid or repeated pin for " + name)
            channel = pin % 16
            pwm_slice = channel // 2
            if channel in channels:
                raise ValueError("Two joints use the same Pico PWM channel")
            freq = settings["frequency"]
            if freq <= 0 or (pwm_slice in slice_frequencies and
                            slice_frequencies[pwm_slice] != freq):
                raise ValueError("Check PWM frequencies for " + name)
            if not (settings["min_deg"] < settings["max_deg"] and
                    settings["min_deg"] <= settings["home_deg"] <= settings["max_deg"]):
                raise ValueError("Check angle limits for " + name)
            if not (0 < settings["min_pulse_us"] < settings["max_pulse_us"] < 1000000 / freq):
                raise ValueError("Check pulse widths for " + name)
            pins.add(pin)
            channels.add(channel)
            slice_frequencies[pwm_slice] = freq

        from machine import Pin, PWM
        try:
            for name, settings in config.JOINTS.items():
                output = PWM(Pin(settings["pin"]), freq=settings["frequency"], duty_u16=0)
                self.outputs[name] = output
                self.angles[name] = settings["home_deg"]
        except Exception:
            self.stop_all("PWM setup failed")
            raise
        self.ready = True
        self.last_note = "Ready; enable the arm before moving"
        return self.status()

    def set_angle(self, joint, angle):
        if not self.enabled:
            raise ValueError("Arm stopped; press Enable arm first")
        settings = config.JOINTS[joint]
        low, high = (0, 180) if self.dry_run else (settings["min_deg"], settings["max_deg"])
        target = max(low, min(high, angle))
        if not self.dry_run:
            fraction = (target - low) / (high - low)
            pulse = settings["min_pulse_us"] + fraction * (
                settings["max_pulse_us"] - settings["min_pulse_us"])
            self.outputs[joint].duty_ns(int(pulse * 1000))
        self.angles[joint] = target

    def stop_all(self, reason="Stopped by operator"):
        self.enabled = False
        for output in self.outputs.values():
            output.duty_u16(0)
        self.last_note = reason
        return self.status()

    def handle_command(self, request):
        try:
            request = validate_command(request)
            command = request.get("command")
            if command in ("STOP_ALL", "LINK_LOST"):
                return self.stop_all("Connection lost" if command == "LINK_LOST" else "Stopped by operator")
            if command in ("HEARTBEAT", "STATUS"):
                return self.status()
            if command == "ARM_ENABLE":
                if not self.ready:
                    raise ValueError("Arm is not configured")
                if not self.enabled:
                    self.enabled = True
                    for name, target in self.angles.items():
                        self.set_angle(name, target)
                self.last_note = "Arm enabled"
            elif "axis" in request:
                self.set_angle(request["axis"], request["angle"])
                self.last_note = "Target set: " + request["axis"]
            else:
                raise ValueError("Unsupported arm command")
            return self.status()
        except Exception as exc:
            self.stop_all("Command failed")
            result = self.status()
            result["error"] = str(exc)
            return result

    def status(self):
        return {
            "type": "status",
            "mode": "simulation" if self.dry_run else "hardware",
            "ready": self.ready,
            "enabled": self.enabled,
            "targets": dict(self.angles),
            "limits": {name: [0, 180] if self.dry_run else [s["min_deg"], s["max_deg"]]
                       for name, s in config.JOINTS.items()},
            "note": self.last_note,
        }

if __name__ == "__main__":
    arm = RoverArm(dry_run=True)
    arm.setup_servos()
    for command in ("ARM_ENABLE", {"axis": "Base", "angle": 95},
                    {"axis": "Gripper", "angle": 120}, "STOP_ALL"):
        print(arm.handle_command(command))
