import sys
import random
from datetime import datetime
from collections import deque

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
)

import pyqtgraph as pg


class GroundStation(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rover Control Station")
        self.resize(1300, 800)

        # Store last 60 sensor readings
        self.max_points = 60

        self.time_data = deque(maxlen=self.max_points)

        self.temp_data = deque(maxlen=self.max_points)
        self.pressure_data = deque(maxlen=self.max_points)

        self.accel_x_data = deque(maxlen=self.max_points)
        self.accel_y_data = deque(maxlen=self.max_points)
        self.accel_z_data = deque(maxlen=self.max_points)

        self.counter = 0

        self.build_ui()
        self.start_demo_telemetry()

        self.log("Ground station initialized")
        self.log("DEMO MODE - ROS 2 not connected")


    # =========================================================
    # MAIN UI
    # =========================================================

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # ---------------- HEADER ----------------

        header = QHBoxLayout()

        title = QLabel("Rover Control Station")
        title.setObjectName("title")

        self.connection = QLabel("DEMO MODE")
        self.connection.setObjectName("connection")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("ROS 2:"))
        header.addWidget(self.connection)

        main_layout.addLayout(header)


        # ---------------- MAIN AREA ----------------

        content = QHBoxLayout()

        # Left side
        left_column = QVBoxLayout()

        left_column.addWidget(
            self.create_drive_panel()
        )

        left_column.addWidget(
            self.create_servo_panel()
        )

        # Right side
        right_column = QVBoxLayout()

        right_column.addWidget(
            self.create_sensor_panel()
        )

        right_column.addWidget(
            self.create_graph_panel()
        )

        content.addLayout(left_column, 1)
        content.addLayout(right_column, 2)

        main_layout.addLayout(content)


        # ---------------- LOG ----------------

        log_group = QGroupBox("System Log")

        log_layout = QVBoxLayout()

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        log_layout.addWidget(self.log_box)

        log_group.setLayout(log_layout)

        main_layout.addWidget(log_group)


        # ---------------- STOP ----------------

        stop_button = QPushButton(
            "STOP ALL SERVOS"
        )

        stop_button.setObjectName(
            "emergency"
        )

        stop_button.clicked.connect(
            self.stop_all
        )

        main_layout.addWidget(
            stop_button
        )

        self.apply_style()


    # =========================================================
    # DRIVE PANEL
    # =========================================================

    def create_drive_panel(self):

        group = QGroupBox(
            "Drive Controls"
        )

        layout = QGridLayout()

        forward = QPushButton("Forward")
        backward = QPushButton("Reverse")
        left = QPushButton("Left")
        right = QPushButton("Right")
        stop = QPushButton("Stop")

        forward.clicked.connect(
            lambda:
            self.send_command("DRIVE_FORWARD")
        )

        backward.clicked.connect(
            lambda:
            self.send_command("DRIVE_REVERSE")
        )

        left.clicked.connect(
            lambda:
            self.send_command("DRIVE_LEFT")
        )

        right.clicked.connect(
            lambda:
            self.send_command("DRIVE_RIGHT")
        )

        stop.clicked.connect(
            lambda:
            self.send_command("DRIVE_STOP")
        )

        layout.addWidget(
            forward,
            0,
            1
        )

        layout.addWidget(
            left,
            1,
            0
        )

        layout.addWidget(
            stop,
            1,
            1
        )

        layout.addWidget(
            right,
            1,
            2
        )

        layout.addWidget(
            backward,
            2,
            1
        )

        group.setLayout(layout)

        return group


    # =========================================================
    # SERVO PANEL
    # =========================================================

    def create_servo_panel(self):

        group = QGroupBox(
            "Servo Controls"
        )

        layout = QGridLayout()

        servos = [
            "Base",
            "Shoulder",
            "Elbow",
            "Wrist"
        ]

        for row, servo in enumerate(servos):

            label = QLabel(servo)

            minus = QPushButton("-")
            plus = QPushButton("+")

            minus.clicked.connect(
                lambda checked,
                s=servo:
                self.move_servo(s, -5)
            )

            plus.clicked.connect(
                lambda checked,
                s=servo:
                self.move_servo(s, 5)
            )

            layout.addWidget(
                label,
                row,
                0
            )

            layout.addWidget(
                minus,
                row,
                1
            )

            layout.addWidget(
                plus,
                row,
                2
            )


        # Gripper

        gripper = QLabel(
            "Gripper"
        )

        open_button = QPushButton(
            "Open"
        )

        close_button = QPushButton(
            "Close"
        )

        open_button.clicked.connect(
            lambda:
            self.send_command(
                "GRIPPER_OPEN"
            )
        )

        close_button.clicked.connect(
            lambda:
            self.send_command(
                "GRIPPER_CLOSE"
            )
        )

        layout.addWidget(
            gripper,
            4,
            0
        )

        layout.addWidget(
            open_button,
            4,
            1
        )

        layout.addWidget(
            close_button,
            4,
            2
        )

        group.setLayout(layout)

        return group


    # =========================================================
    # SENSOR VALUES
    # =========================================================

    def create_sensor_panel(self):

        group = QGroupBox(
            "Live Sensor Readings"
        )

        layout = QGridLayout()

        self.temperature = QLabel("-- °C")
        self.pressure = QLabel("-- kPa")

        self.accel_x = QLabel("-- m/s²")
        self.accel_y = QLabel("-- m/s²")
        self.accel_z = QLabel("-- m/s²")

        self.altitude = QLabel("-- m")

        sensors = [

            (
                "Temperature",
                self.temperature
            ),

            (
                "Pressure",
                self.pressure
            ),

            (
                "Acceleration X",
                self.accel_x
            ),

            (
                "Acceleration Y",
                self.accel_y
            ),

            (
                "Acceleration Z",
                self.accel_z
            ),

            (
                "Altitude",
                self.altitude
            )
        ]

        for row, (name, value) in enumerate(sensors):

            layout.addWidget(
                QLabel(name),
                row,
                0
            )

            value.setObjectName(
                "sensorValue"
            )

            layout.addWidget(
                value,
                row,
                1
            )

        group.setLayout(layout)

        return group


    # =========================================================
    # GRAPHS
    # =========================================================

    def create_graph_panel(self):

        group = QGroupBox(
            "Live Telemetry"
        )

        layout = QVBoxLayout()


        # ---------------- TEMPERATURE ----------------

        self.temp_plot = pg.PlotWidget()

        self.temp_plot.setTitle(
            "Temperature"
        )

        self.temp_plot.setLabel(
            "left",
            "Temperature",
            units="°C"
        )

        self.temp_plot.setLabel(
            "bottom",
            "Time",
            units="s"
        )

        self.temp_plot.showGrid(
            x=True,
            y=True,
            alpha=0.2
        )

        self.temp_curve = (
            self.temp_plot.plot(
                pen=pg.mkPen(width=2)
            )
        )

        layout.addWidget(
            self.temp_plot
        )


        # ---------------- PRESSURE ----------------

        self.pressure_plot = pg.PlotWidget()

        self.pressure_plot.setTitle(
            "Pressure"
        )

        self.pressure_plot.setLabel(
            "left",
            "Pressure",
            units="kPa"
        )

        self.pressure_plot.setLabel(
            "bottom",
            "Time",
            units="s"
        )

        self.pressure_plot.showGrid(
            x=True,
            y=True,
            alpha=0.2
        )

        self.pressure_curve = (
            self.pressure_plot.plot(
                pen=pg.mkPen(width=2)
            )
        )

        layout.addWidget(
            self.pressure_plot
        )


        # ---------------- ACCELERATION ----------------

        self.accel_plot = pg.PlotWidget()

        self.accel_plot.setTitle(
            "Acceleration"
        )

        self.accel_plot.setLabel(
            "left",
            "Acceleration",
            units="m/s²"
        )

        self.accel_plot.setLabel(
            "bottom",
            "Time",
            units="s"
        )

        self.accel_plot.showGrid(
            x=True,
            y=True,
            alpha=0.2
        )


        self.accel_x_curve = (
            self.accel_plot.plot(
                name="X"
            )
        )

        self.accel_y_curve = (
            self.accel_plot.plot(
                name="Y"
            )
        )

        self.accel_z_curve = (
            self.accel_plot.plot(
                name="Z"
            )
        )


        layout.addWidget(
            self.accel_plot
        )


        group.setLayout(layout)

        return group


    # =========================================================
    # COMMANDS
    # =========================================================

    def send_command(
        self,
        command
    ):

        # ======================================
        # ROS 2 WILL GO HERE LATER
        # ======================================
        #
        # msg = String()
        # msg.data = command
        #
        # self.publisher.publish(msg)
        #
        # ======================================

        self.log(
            f"Command sent: {command}"
        )


    def move_servo(
        self,
        servo,
        amount
    ):

        if amount > 0:

            command = (
                f"{servo.upper()}_PLUS"
            )

        else:

            command = (
                f"{servo.upper()}_MINUS"
            )

        self.send_command(
            command
        )


    def stop_all(self):

        self.send_command(
            "STOP_ALL"
        )

        self.log(
            "SOFTWARE STOP ACTIVATED"
        )


    # =========================================================
    # DEMO TELEMETRY
    # =========================================================

    def start_demo_telemetry(self):

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_demo_sensors
        )

        # Update every second
        self.timer.start(1000)


    def update_demo_sensors(self):

        # ---------------------------------------
        # Fake values for GUI testing
        # ---------------------------------------

        temperature = random.uniform(
            23.0,
            26.0
        )

        pressure = random.uniform(
            100.5,
            101.8
        )

        accel_x = random.uniform(
            -0.20,
            0.20
        )

        accel_y = random.uniform(
            -0.20,
            0.20
        )

        accel_z = random.uniform(
            9.70,
            9.90
        )

        altitude = random.uniform(
            180.0,
            182.0
        )


        # ---------------------------------------
        # Update numbers
        # ---------------------------------------

        self.temperature.setText(
            f"{temperature:.1f} °C"
        )

        self.pressure.setText(
            f"{pressure:.2f} kPa"
        )

        self.accel_x.setText(
            f"{accel_x:.2f} m/s²"
        )

        self.accel_y.setText(
            f"{accel_y:.2f} m/s²"
        )

        self.accel_z.setText(
            f"{accel_z:.2f} m/s²"
        )

        self.altitude.setText(
            f"{altitude:.1f} m"
        )


        # ---------------------------------------
        # Save graph history
        # ---------------------------------------

        self.counter += 1

        self.time_data.append(
            self.counter
        )

        self.temp_data.append(
            temperature
        )

        self.pressure_data.append(
            pressure
        )

        self.accel_x_data.append(
            accel_x
        )

        self.accel_y_data.append(
            accel_y
        )

        self.accel_z_data.append(
            accel_z
        )


        # ---------------------------------------
        # Update graphs
        # ---------------------------------------

        self.temp_curve.setData(
            list(self.time_data),
            list(self.temp_data)
        )

        self.pressure_curve.setData(
            list(self.time_data),
            list(self.pressure_data)
        )

        self.accel_x_curve.setData(
            list(self.time_data),
            list(self.accel_x_data)
        )

        self.accel_y_curve.setData(
            list(self.time_data),
            list(self.accel_y_data)
        )

        self.accel_z_curve.setData(
            list(self.time_data),
            list(self.accel_z_data)
        )


    # =========================================================
    # LOG
    # =========================================================

    def log(
        self,
        message
    ):

        current_time = (
            datetime.now().strftime(
                "%H:%M:%S"
            )
        )

        self.log_box.append(
            f"[{current_time}] {message}"
        )


    # =========================================================
    # STYLING
    # =========================================================

    def apply_style(self):

        self.setStyleSheet("""

        QMainWindow {
            background-color: #f5f7fa;
        }


        QLabel {
            color: #17202a;
            font-size: 14px;
        }


        QLabel#title {
            color: #17202a;

            font-size: 30px;
            font-weight: bold;

            padding: 10px;
        }


        QLabel#connection {
            color: #d68910;

            font-size: 16px;
            font-weight: bold;
        }


        QLabel#sensorValue {
            color: #117a43;

            font-size: 15px;
            font-weight: bold;
        }


        QGroupBox {

            background-color: white;

            color: #17202a;

            border: 1px solid #d5dce3;
            border-radius: 8px;

            margin-top: 20px;

            padding: 15px;

            font-size: 17px;
            font-weight: bold;
        }


        QGroupBox::title {

            subcontrol-origin: margin;

            left: 12px;

            padding: 0 5px;
        }


        QPushButton {

            background-color: #2874a6;

            color: white;

            border: none;
            border-radius: 6px;

            padding: 12px;

            font-size: 14px;

            min-height: 20px;
        }


        QPushButton:hover {

            background-color: #21618c;
        }


        QPushButton:pressed {

            background-color: #1b4f72;
        }


        QTextEdit {

            background-color: white;

            color: #17202a;

            border: 1px solid #ccd1d1;
            border-radius: 5px;

            font-family: Consolas;
            font-size: 13px;
        }


        QPushButton#emergency {

            background-color: #c0392b;

            color: white;

            font-size: 20px;
            font-weight: bold;

            min-height: 55px;
        }


        QPushButton#emergency:hover {

            background-color: #a93226;
        }

        """)


# =============================================================
# START APPLICATION
# =============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = GroundStation()

    window.show()

    sys.exit(
        app.exec_()
    )