#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(realpath "$SCRIPT_DIR/..")"

COMPOSE_FILE="$REPO_DIR/compose.yaml"


echo
echo "======================================"
echo " Docker Environment Setup"
echo "======================================"
echo


# ============================================================
# Verify Docker
# ============================================================

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not installed."
    echo
    echo "Install Docker Engine and run this setup again."
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: Docker Compose plugin is not installed."
    exit 1
fi


# ============================================================
# Verify Docker daemon access
# ============================================================

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Cannot access the Docker daemon."
    echo
    echo "Make sure Docker is running and your user has"
    echo "permission to access it."
    exit 1
fi


# ============================================================
# GUI access
# ============================================================

echo "Configuring GUI access..."

if command -v xhost >/dev/null 2>&1; then
    xhost +local:docker
else
    echo
    echo "WARNING: xhost is not installed."
    echo "GUI applications such as RViz may not work."
fi


# ============================================================
# Build image
# ============================================================

echo
echo "Building Docker image..."

docker compose -f "$COMPOSE_FILE" build


# ============================================================
# Start container
# ============================================================

echo
echo "Starting development container..."

docker compose -f "$COMPOSE_FILE" up -d


# ============================================================
# ROS dependencies
# ============================================================

echo
echo "Installing ROS dependencies..."

docker compose -f "$COMPOSE_FILE" exec robot-dev bash -lc \
    "source /opt/ros/humble/setup.bash && \
     rosdep update && \
     rosdep install \
        --from-paths /robot_ws/src \
        --ignore-src \
        -r \
        -y"


# ============================================================
# Initial build
# ============================================================

echo
echo "Building local workspace..."

docker compose -f "$COMPOSE_FILE" exec robot-dev bash -lc \
    "source /opt/ros/humble/setup.bash && \
     cd /robot_ws && \
     colcon build --symlink-install"


echo
echo "Docker environment setup complete."