#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo " SMAC Development Environment Setup"
echo "======================================"
echo

while true; do
    read -rp "Use the Docker ROS 2 Humble environment? [y/n]: " RESPONSE

    case "$RESPONSE" in
        y|Y|yes|YES)
            USE_DOCKER=true
            break
            ;;

        n|N|no|NO)
            USE_DOCKER=false
            break
            ;;

        *)
            echo "Please enter y or n."
            ;;
    esac
done

# Export it so setup_cli.sh can see it.
export USE_DOCKER

echo
echo "Setting up SMAC CLI..."
"$SCRIPT_DIR/setup_cli.sh"

if [[ "$USE_DOCKER" == "true" ]]; then
    echo
    echo "Setting up Docker environment..."
    "$SCRIPT_DIR/setup_docker.sh"
else
    echo
    echo "Skipping Docker setup."
fi

echo
echo "======================================"
echo " Setup Complete!"
echo "======================================"
echo
echo "Run:"
echo "  smac --help"
echo