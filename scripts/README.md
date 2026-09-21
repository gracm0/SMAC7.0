# SMAC Development Environment

This repository includes development tools for working with the SMAC ROS 2 system locally and on a remote robot.

The `smac` command-line tool provides a common interface for:

* Building the ROS workspace
* Running a ROS 2 Humble development environment through Docker
* Developing directly on a machine with ROS 2 Humble installed
* Synchronizing source code to a remote robot
* Building code on the remote robot
* Opening local and remote development shells
* Running ROS commands remotely

The local computer is treated as the primary development environment. Source code can be synchronized directly to the robot using `rsync`, so pushing changes to Git is not required when testing code remotely.

---

# Requirements

## Local Computer

The following tools are required:

* Git
* SSH client
* `rsync`
* Bash

On Ubuntu:

```bash
sudo apt update
sudo apt install git openssh-client rsync
```

You must also have **one** of the following:

1. ROS 2 Humble installed locally, or
2. Docker Engine with the Docker Compose plugin

Docker is useful when developing on an operating system that does not natively support ROS 2 Humble.

## Remote Robot

The remote robot must have:

* SSH enabled
* ROS 2 Humble installed
* `rsync` installed

ROS Humble is expected at:

```text
/opt/ros/humble/setup.bash
```

The setup script will verify that ROS Humble exists on the robot.

---

# Workspace Structure

The repository must be cloned inside the `src` directory of a ROS workspace.

For example:

```text
smac_ws/
├── build/
├── install/
├── log/
└── src/
    └── SMAC7.0/
        ├── compose.yaml
        ├── Dockerfile
        ├── README.md
        ├── scripts/
        │   ├── smac
        │   ├── setup.sh
        │   ├── setup_cli.sh
        │   └── setup_docker.sh
        └── ...
```

Create a workspace and clone the repository:

```bash
mkdir -p ~/smac_ws/src
cd ~/smac_ws/src

git clone <repository-url>
```

---

# Initial Setup

From the repository directory, run:

```bash
./scripts/setup.sh
```

If necessary, make the setup scripts executable first:

```bash
chmod +x scripts/setup.sh
chmod +x scripts/setup_cli.sh
chmod +x scripts/setup_docker.sh
chmod +x scripts/smac
```

The setup process will configure both the local development environment and the connection to the remote robot.

---

# Remote Robot Setup

The setup script will ask for the SSH address of the robot.

For example:

```text
Robot SSH host: smac@smac-smac.local
```

An IP address may also be used:

```text
smac@192.168.1.100
```

The setup script will test the SSH connection and verify that ROS 2 Humble is installed.

## SSH Authentication

The setup script can configure SSH key authentication.

If enabled, an SSH key will be created if one does not already exist and installed on the robot.

You may need to enter the robot's password once during setup.

Afterward, commands such as:

```bash
smac push
smac shell --remote
smac build --remote
```

can connect to the robot without repeatedly asking for a password.

---

# Remote Workspace

During setup, you will be asked whether a ROS workspace already exists on the robot.

If one already exists, enter its path:

```text
~/smac7_ws
```

or:

```text
/home/smac/smac7_ws
```

Paths beginning with `~/` are automatically expanded relative to the remote user's home directory.

If the workspace does not exist, select `no` and provide the desired path. The setup script will create the workspace and its `src` directory.

For example:

```text
Does a ROS workspace already exist on the robot? [y/n]: n

Workspace path:
~/smac7_ws
```

creates:

```text
/home/smac/smac7_ws/
└── src/
```

---

# Docker Setup

The setup script will ask whether Docker should be used for local development.

## Using Docker

Select Docker if your local computer does not have ROS 2 Humble installed.

For example, a computer running a newer Ubuntu release can use the provided ROS 2 Humble Docker environment while the Raspberry Pi continues to run Ubuntu 22.04 and ROS 2 Humble natively.

The Docker environment provides:

* ROS 2 Humble
* `colcon`
* `rosdep`
* ROS desktop tools
* GUI application support
* Host networking for ROS 2 communication
* Access to the local ROS workspace

The workspace is mounted into the container at:

```text
/robot_ws
```

## Native ROS 2 Humble

If your computer already runs ROS 2 Humble, Docker is optional.

Select:

```text
Use the Docker ROS 2 Humble environment? [y/n]: n
```

Local commands will run directly in the native ROS environment instead.

---

# The `smac` Command

Setup installs the `smac` development command.

Run:

```bash
smac --help
```

to display available commands.

The same commands are intended to work regardless of whether the local environment uses Docker or native ROS 2 Humble.

---

# Local Shell

Open the local development environment:

```bash
smac shell
```

When Docker is enabled, this starts the development container if necessary and opens a Bash shell inside `robot-dev`.

When using native ROS 2 Humble, it opens a shell with the local workspace environment configured.

---

# Remote Shell

Open a shell on the robot:

```bash
smac shell --remote
```

The command connects through SSH, enters the configured remote workspace, and sources:

```bash
/opt/ros/humble/setup.bash
```

and, if it exists:

```bash
install/setup.bash
```

ROS commands can then be used normally.

---

# Synchronizing Code

To copy the current source code to the robot:

```bash
smac push
```

The synchronization uses `rsync`.

Conceptually:

```text
Local computer                         Robot

smac_ws/src/                           smac7_ws/src/
     │                                      ▲
     └────────────── rsync ─────────────────┘
```

This allows code to be tested on the robot without committing and pushing every change through Git.

## Important

The local workspace is considered the authoritative development copy.

Files deleted locally may also be deleted from the corresponding synchronized location on the robot.

Do not use the remote workspace as the only copy of important source changes.

Use Git for permanent version control.

---

# Building

## Build Everything

```bash
smac build
```

or:

```bash
smac build --all
```

This performs:

```text
Local build
    │
    ▼
smac push
    │
    ▼
Remote build
```

Equivalent workflow:

```text
Local Computer                         Robot
──────────────                         ─────

colcon build
      │
      │ rsync
      └──────────────────────────────► src/
                                        │
                                        ▼
                                   colcon build
```

---

## Local Build Only

```bash
smac build --local
```

When Docker is enabled, the build runs inside the ROS 2 Humble container.

When Docker is disabled, the build runs directly on the local machine.

The build uses:

```bash
colcon build --symlink-install
```

---

## Remote Build

```bash
smac build --remote
```

This first synchronizes the current source code:

```bash
smac push
```

and then runs:

```bash
colcon build --symlink-install
```

inside the configured workspace on the robot.

---

# Running Commands Remotely

Commands can be executed on the robot without manually opening an SSH session.

Syntax:

```bash
smac run --remote <command>
```

For example:

```bash
smac run --remote ros2 topic list
```

or:

```bash
smac run --remote ros2 node list
```

ROS launch files can also be started this way:

```bash
smac run --remote ros2 launch <package> <launch-file>
```

Before executing the command, SMAC automatically:

1. Connects to the robot over SSH
2. Enters the configured ROS workspace
3. Sources ROS 2 Humble
4. Sources the workspace
5. Executes the requested command

---

# Docker Commands

When Docker support is enabled, the Docker environment can be managed through SMAC.

## Status

```bash
smac docker status
```

## Build Image

```bash
smac docker build
```

Use this after changing the `Dockerfile` or other image configuration.

## Stop Environment

```bash
smac docker down
```

The next:

```bash
smac shell
```

will start the development container again automatically.

Docker-specific commands are unavailable when the environment was configured to use native ROS 2 Humble.

---

# Configuration

Machine-specific SMAC configuration is stored in:

```text
~/.config/smac/config
```

An example configuration is:

```bash
USE_DOCKER="true"
LOCAL_WS="/home/user/smac_ws"
REMOTE_HOST="smac@smac-smac.local"
REMOTE_WS="/home/smac/smac7_ws"
COMPOSE_FILE="/home/user/smac_ws/src/SMAC7.0/compose.yaml"
```

This file is generated during setup and should not need to be edited manually under normal circumstances.

The `smac` executable itself remains part of the repository so improvements to the CLI are immediately available without generating a new copy of the script.

---

# Typical Development Workflow

Start a local development shell:

```bash
smac shell
```

Edit the source code normally using your preferred editor.

Build locally:

```bash
smac build --local
```

When ready to test on the robot:

```bash
smac build --remote
```

This synchronizes the source and builds it on the robot.

Run a ROS command remotely:

```bash
smac run --remote ros2 topic list
```

Or enter the robot directly:

```bash
smac shell --remote
```

For a complete local and remote build:

```bash
smac build
```

Git remains the permanent version-control mechanism, while `smac push` provides fast synchronization during development.

---

# Troubleshooting

## `smac: command not found`

Make sure `~/bin` is on your `PATH`.

Open a new terminal after running setup, or run:

```bash
source ~/.bashrc
```

Then verify:

```bash
which smac
```

---

## Cannot Connect to Robot

Test SSH directly:

```bash
ssh smac@smac-smac.local
```

Check that:

* The robot is powered on
* Both machines are reachable over the network
* SSH is running on the robot
* The hostname or IP address is correct

---

## Remote Commands Ask for a Password

Run the setup script again and enable SSH key authentication, or configure SSH keys manually.

You can test key authentication with:

```bash
ssh smac@smac-smac.local
```

---

## ROS Nodes Cannot See Each Other

Verify that the local and remote environments use the same ROS domain ID.

For example:

```bash
echo $ROS_DOMAIN_ID
```

Also make sure:

```bash
ROS_LOCALHOST_ONLY=0
```

or that `ROS_LOCALHOST_ONLY` is unset.

When Docker is used, the SMAC development container uses host networking so ROS 2 DDS traffic can communicate directly with devices on the network.

---

## Docker Permission Denied

If Docker reports permission errors accessing:

```text
/var/run/docker.sock
```

add your user to the Docker group:

```bash
sudo usermod -aG docker $USER
```

Then fully log out and log back in.

Verify with:

```bash
docker info
```

---

# Development Model

The intended SMAC development architecture is:

```text
                    Developer Laptop
                           │
               ┌───────────┴───────────┐
               │                       │
        Native ROS Humble        Docker Humble
               │                       │
               └───────────┬───────────┘
                           │
                     Local Workspace
                           │
                           │ rsync
                           ▼
                    Raspberry Pi
                           │
                    ROS 2 Humble
                           │
                    Remote Workspace
                           │
                    Physical Robot
```

This keeps the development workflow consistent across different developer machines while keeping the robot on its stable ROS 2 Humble environment.
