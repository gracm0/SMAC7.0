#!/usr/bin/env python3
"""ROS 2 Humble servo debugger. All servo API values are DEGREES."""

import argparse
import math
import time
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from std_msgs.msg import Float32, String
import yaml
from pathlib import Path

# Calibrate these against the physical robot before interpreting the pose.
# Each entry is (minimum servo degrees, maximum, straight-pose servo degrees, sign).
JOINT_CALIBRATION = [(0.0, 180.0, 100.0, 1.0)] * 5
JOINT_OFFSETS_M = (0.0316, 0.0115, 0.0643, 0.0643, 0.0117)
JOINT_AXES = ('z', 'x', 'x', 'x', 'z')
TIP_OFFSET_M = 0.0318  # From joint 5 along its local Z axis.
GRIPPER_OPEN = 30.0
GRIPPER_CLOSED = 150.0
STALE_SECONDS = 1.0


def setup_motors():
    global JOINT_CALIBRATION
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    with open(f"{script_dir}/inchworm_motor_config.yaml", 'r') as file:
        # Parse the YAML content and load it into a Python dictionary
        config = yaml.safe_load(file)

    joint_calibrations = []
    for i in range(5):
        sign = 1.0
        if i == 3:
            sign = -1.0
        joint_calibrations.append((0.0, 360.0, config['motor_offsets'][f'theta{i+1}'], sign))

    JOINT_CALIBRATION = joint_calibrations

def rotation(axis, angle):
    c, s = math.cos(angle), math.sin(angle)
    if axis == 'x':
        return np.array(((1, 0, 0), (0, c, -s), (0, s, c)))
    return np.array(((c, -s, 0), (s, c, 0), (0, 0, 1)))


def forward_kinematics(servo_degrees):
    """Translate along parent Z, then rotate about local joint axis.

    Returns base, J1..J5, tip positions and J1..J5 post-rotation frames.
    The tip is 3.18 cm from joint 5 along its local Z axis.
    """
    p, frame = np.zeros(3), np.eye(3)
    points, frames = [p.copy()], []
    for value, offset, axis, calibration in zip(
            servo_degrees, JOINT_OFFSETS_M, JOINT_AXES, JOINT_CALIBRATION):
        p = p + frame @ np.array((0, 0, offset))
        _, _, zero, sign = calibration
        frame = frame @ rotation(axis, math.radians(sign * (value - zero)))
        points.append(p.copy())
        frames.append(frame.copy())
    points.append(p + frame @ np.array((0, 0, TIP_OFFSET_M)))
    return np.array(points), frames


class ServoState:
    def __init__(self, grippers_per_end):
        self.names = [f'joint_{i}' for i in range(1, 6)] + [
            f'{end}_gripper_{i}' for end in ('base', 'tip')
            for i in range(1, grippers_per_end + 1)]
        self.targets = dict(zip(self.names, [c[2] for c in JOINT_CALIBRATION]
                                + [GRIPPER_OPEN] * (2 * grippers_per_end)))
        self.actual = {name: None for name in self.names}
        self.received = {name: None for name in self.names}
        self.has_received = False

    def update_actual_angle(self, servo_name, angle_degrees):
        """Call from your ROS subscriber. Partial feedback is supported.

        Convert radians/ticks to calibrated SERVO degrees in your callback.
        Feedback is intentionally not clamped to target limits.
        """
        if servo_name not in self.actual:
            raise ValueError(f'Unknown servo: {servo_name}')
        value = float(angle_degrees)
        if not math.isfinite(value):
            raise ValueError('Feedback must be finite')
        self.actual[servo_name] = value
        self.received[servo_name] = time.monotonic()


def make_ros_node(state):
    from rclpy.node import Node

    class InchwormDebuggerNode(Node):
        def __init__(self):
            super().__init__('inchworm_debugger')
            self.state = state

            self.position_sub = self.create_subscription(
                String,
                "/motor_position",
                self.motor_pos_callback,
                10
            )

            # Create publisher for current motor positions
            self.command_pub = self.create_publisher(
                String,
                "/motor_command",
                10
            )


        def motor_pos_callback(self, msg):
            angles = msg.data.split(",")
            for i in range(5):
                self.state.update_actual_angle(f'joint_{i+1}', float(angles[i]))

                # Set first "target" values to be initial values
                if not self.state.has_received:
                    self.state.targets[f'joint_{i+1}'] = float(angles[i])
            self.state.has_received = True

        def send_targets(self, targets):
            msg = String()
            msg.data = ""

            # Add joints
            for i in range(1,6):
                msg.data += f"{targets[f'joint_{i}']},"

            # Add grippers
            msg.data += f"{targets[f'base_gripper_1']}, {targets[f'tip_gripper_1']}"
            self.command_pub.publish(msg)

    return InchwormDebuggerNode()


class DebuggerUI:
    def __init__(self, root, state, send_targets, args, pump_ros):
        self.root, self.state, self.args = root, state, args
        self.send_targets, self.pump_ros = send_targets, pump_ros
        self.last_tick = time.monotonic()
        self.last_draw = 0.0
        self.last_send = 0.0
        self.labels, self.variables = {}, {}
        self.live = tk.BooleanVar(value=False)
        root.title('Inchworm servo and kinematics debugger')
        root.geometry('1250x790')
        panel = ttk.Frame(root, padding=12)
        panel.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(panel, text='Servo angles (degrees)', font=('', 14, 'bold')).pack(anchor='w')
        ttk.Label(panel, text='Targets: orange dashed | Measured: blue\n'
                  'Base is fixed at world origin.').pack(anchor='w', pady=8)
        for index, name in enumerate(state.names):
            row = ttk.LabelFrame(panel, text=name, padding=4)
            row.pack(fill=tk.X, pady=2)
            minimum, maximum = JOINT_CALIBRATION[index][:2] if index < 5 else (30, 150)
            variable = tk.DoubleVar(value=state.targets[name])
            self.variables[name] = variable
            tk.Scale(row, from_=minimum, to=maximum, resolution=0.1,
                     orient=tk.HORIZONTAL, variable=variable, length=210,
                     command=lambda value, n=name: self.set_target(n, value)).pack(side=tk.LEFT)
            label = ttk.Label(row, text='Actual: no feedback', width=25)
            label.pack(side=tk.LEFT, padx=5)
            self.labels[name] = label
            if index >= 5:
                for title, value in [('Open', GRIPPER_OPEN), ('Close', GRIPPER_CLOSED)]:
                    ttk.Button(row, text=title, width=6,
                               command=lambda n=name, v=value: self.choose(n, v)).pack(side=tk.LEFT)
        ttk.Button(panel, text='Send all targets', command=self.send).pack(fill=tk.X, pady=(10, 4))
        ttk.Checkbutton(panel, text='Live send (10 Hz)', variable=self.live).pack(anchor='w')
        self.status = ttk.Label(panel, wraplength=450, text=(
            'DEMO: simulated feedback, no ROS or hardware.' if args.demo else
            'ROS active. Command/feedback hooks are #TODO. No measured pose yet.'))
        self.status.pack(anchor='w', pady=8)
        plot_panel = ttk.Frame(root)
        plot_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.figure = Figure(figsize=(7, 7), dpi=100)
        self.axes = self.figure.add_subplot(111, projection='3d')
        self.axes.set(xlabel='X (cm)', ylabel='Y (cm)', zlabel='Z (cm)',
                      xlim=(-25, 25), ylim=(-25, 25), zlim=(-25, 25))
        self.axes.set_box_aspect((1, 1, 1))
        self.axes.view_init(elev=20, azim=35)
        self.target_line, = self.axes.plot([], [], [], 'o--', color='darkorange', label='Target')
        self.actual_line, = self.axes.plot([], [], [], 'o-', color='tab:blue', label='Measured')
        self.axes.legend(loc='upper left')
        self.annotations = []
        self.extra_lines = []
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(self.canvas, plot_panel)
        self.tick()

    def set_target(self, name, value):
        self.state.targets[name] = float(value)

    def choose(self, name, value):
        self.variables[name].set(value)
        self.set_target(name, value)

    def send(self):
        # Do not send any targets until the first targets are recieved
        if not self.state.has_received:
            return
        self.send_targets(dict(self.state.targets))
        self.status.config(text=('DEMO: simulated servos follow targets.' if self.args.demo else
                                 'Command hook called. Delivery requires implementing #TODO.'))
        

    def grippers(self, points, frames, values, color):
        """Schematic jaws only: actual gripper dimensions were not supplied."""
        for end, center, frame in [('base', points[0], np.eye(3)),
                                   ('tip', points[-1], frames[-1])]:
            for i in range(1, self.args.grippers_per_end + 1):
                angle = values[f'{end}_gripper_{i}']
                if angle is None:
                    continue
                opening = np.clip((150.0 - angle) / 120.0, 0, 1)
                gap = 0.002 + 0.008 * opening
                y = (i - (self.args.grippers_per_end + 1) / 2) * 0.015
                jaw = np.array([[-gap, y, -0.008], [-gap, y, 0],
                                [gap, y, 0], [gap, y, -0.008]])
                world = (jaw @ frame.T + center) * 100
                line, = self.axes.plot(*world.T, color=color, alpha=0.7)
                self.extra_lines.append(line)

    def draw(self, now):
        for artist in self.annotations + self.extra_lines:
            artist.remove()
        self.annotations, self.extra_lines = [], []
        names = self.state.names[:5]
        points, frames = forward_kinematics([self.state.targets[n] for n in names])
        self.target_line.set_data_3d(*(points * 100).T)
        self.grippers(points, frames, self.state.targets, 'darkorange')
        for i, (point, frame) in enumerate(zip(points[1:6], frames)):
            n = names[i]
            actual = self.state.actual[n]
            label = f'J{i+1} T:{self.state.targets[n]:.1f} A:'
            label += '--' if actual is None else f'{actual:.1f}'
            if actual is not None and now - self.state.received[n] > STALE_SECONDS:
                label += ' stale'
            self.annotations.append(self.axes.text(*(point * 100), label, fontsize=8))
            axis = frame[:, 0 if JOINT_AXES[i] == 'x' else 2]
            segment = np.array([point - axis * 0.008, point + axis * 0.008]) * 100
            line, = self.axes.plot(*segment.T, color='gray', linewidth=2)
            self.extra_lines.append(line)
        if all(self.state.actual[n] is not None for n in names):
            actual_points, actual_frames = forward_kinematics(
                [self.state.actual[n] for n in names])
            stale = any(now - self.state.received[n] > STALE_SECONDS for n in names)
            self.actual_line.set_data_3d(*(actual_points * 100).T)
            self.actual_line.set_alpha(0.3 if stale else 1)
            self.grippers(actual_points, actual_frames, self.state.actual, 'tab:blue')
            self.axes.set_title('Measured pose STALE' if stale else 'Target and measured pose')
        else:
            self.actual_line.set_data_3d([], [], [])
            self.axes.set_title('Waiting for feedback from all five joints')
        self.canvas.draw_idle()

    def tick(self):
        if not self.pump_ros():
            self.root.destroy()
            return
        now = time.monotonic()
        dt = min(now - self.last_tick, 0.2)
        self.last_tick = now
        if self.args.demo:
            for name in self.state.names:
                current = self.state.actual[name]
                current = self.state.targets[name] if current is None else current
                step = np.clip(self.state.targets[name] - current, -60 * dt, 60 * dt)
                self.state.update_actual_angle(name, current + step)
        if now - self.last_draw >= 0.1:
            for name, label in self.labels.items():
                actual = self.state.actual[name]
                if actual is None:
                    label.config(text='Actual: no feedback')
                else:
                    age = now - self.state.received[name]
                    suffix = f' STALE {age:.1f}s' if age > STALE_SECONDS else ''
                    label.config(text=f'Actual: {actual:.1f}°{suffix}')
            self.draw(now)
            self.last_draw = now
        if self.live.get() and now - self.last_send >= 0.1:
            self.send()
            self.last_send = now
        self.root.after(10, self.tick)


def main(args=None):
    setup_motors()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Simulated feedback; no ROS needed')
    parser.add_argument('--grippers-per-end', type=int, choices=(1, 2), default=1)
    options, ros_args = parser.parse_known_args(args)
    state = ServoState(options.grippers_per_end)
    node = executor = root = None
    ros = None
    try:
        if options.demo:
            pump, send = lambda: True, lambda targets: None
        else:
            import rclpy
            from rclpy.executors import SingleThreadedExecutor, ExternalShutdownException
            ros = rclpy
            ros.init(args=ros_args)
            node = make_ros_node(state)
            executor = SingleThreadedExecutor()
            executor.add_node(node)

            def pump():
                if not ros.ok():
                    return False
                try:
                    executor.spin_once(timeout_sec=0.0)
                except ExternalShutdownException:
                    return False
                return ros.ok()

            send = node.send_targets

        # Setup debug UI
        root = tk.Tk()
        while(not state.has_received):
            pump()
        DebuggerUI(root, state, send, options, pump)
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass
        if executor is not None:
            executor.shutdown()
        if node is not None:
            node.destroy_node()
        if ros is not None and ros.ok():
            ros.shutdown()


if __name__ == '__main__':
    main()