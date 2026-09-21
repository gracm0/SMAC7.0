#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(realpath "$SCRIPT_DIR/..")"
LOCAL_WS="$(realpath "$REPO_DIR/../..")"

SMAC_SCRIPT="$SCRIPT_DIR/smac"
COMPOSE_FILE="$REPO_DIR/compose.yaml"


echo
echo "======================================"
echo " SMAC CLI Setup"
echo "======================================"
echo


# ============================================================
# Verify dependencies
# ============================================================

for CMD in ssh rsync sed; do
    if ! command -v "$CMD" >/dev/null 2>&1; then
        echo "ERROR: '$CMD' is required but is not installed."
        exit 1
    fi
done


# ============================================================
# Remote host
# ============================================================

read -rp "Robot SSH host (example: pi@192.168.1.42): " REMOTE_HOST

if [[ -z "$REMOTE_HOST" ]]; then
    echo "ERROR: SSH host cannot be empty."
    exit 1
fi


# ============================================================
# Test SSH
# ============================================================

echo
echo "Testing SSH connection..."

if ! ssh "$REMOTE_HOST" "true"; then
    echo
    echo "ERROR: Could not connect to:"
    echo "  $REMOTE_HOST"
    exit 1
fi

echo "SSH connection successful."


# ============================================================
# Passwordless SSH
# ============================================================

echo
echo "======================================"
echo " SSH Authentication"
echo "======================================"
echo
echo "SMAC can configure an SSH key so that commands such as"
echo "'smac push' and 'smac shell --remote' do not require"
echo "entering the robot password each time."
echo

while true; do
    read -rp "Configure passwordless SSH? [y/n]: " SETUP_KEY

    case "$SETUP_KEY" in

        y|Y|yes|YES)

            # Find an existing key, preferring ed25519.
            if [[ -f "$HOME/.ssh/id_ed25519.pub" ]]; then
                SSH_KEY="$HOME/.ssh/id_ed25519"
            elif [[ -f "$HOME/.ssh/id_rsa.pub" ]]; then
                SSH_KEY="$HOME/.ssh/id_rsa"
            else
                echo
                echo "No SSH key found."
                echo "Creating an Ed25519 key..."
                echo

                mkdir -p "$HOME/.ssh"

                ssh-keygen \
                    -t ed25519 \
                    -f "$HOME/.ssh/id_ed25519" \
                    -N ""

                SSH_KEY="$HOME/.ssh/id_ed25519"
            fi

            echo
            echo "Installing SSH key on robot..."
            echo "You may be asked for the robot password one final time."
            echo

            ssh-copy-id -i "${SSH_KEY}.pub" "$REMOTE_HOST"

            echo
            echo "Testing passwordless SSH..."

            if ssh \
                -o BatchMode=yes \
                -o PasswordAuthentication=no \
                "$REMOTE_HOST" \
                "true"
            then
                echo "Passwordless SSH configured successfully."
            else
                echo
                echo "WARNING: SSH key authentication test failed."
                echo "Remote commands may still request a password."
            fi

            break
            ;;


        n|N|no|NO)
            echo
            echo "Skipping SSH key setup."
            echo "Remote SMAC commands may request your password."
            break
            ;;


        *)
            echo "Please enter y or n."
            ;;
    esac
done


# ============================================================
# Verify ROS Humble
# ============================================================

echo
echo "Checking ROS 2 Humble installation on robot..."

if ! ssh "$REMOTE_HOST" \
    "test -f /opt/ros/humble/setup.bash"
then
    echo
    echo "ERROR: ROS 2 Humble was not found."
    echo "Expected:"
    echo "  /opt/ros/humble/setup.bash"
    exit 1
fi

echo "ROS 2 Humble found."


# ============================================================
# Remote workspace
# ============================================================

echo
echo "======================================"
echo " Remote ROS Workspace"
echo "======================================"
echo

while true; do

    read -rp "Does a ROS workspace already exist on the robot? [y/n]: " WS_EXISTS
    
    echo
    read -rp "Absolute path for new workspace: " REMOTE_WS

    # Expand ~/ relative to the remote user's home directory
    if [[ "$REMOTE_WS" == "~/"* ]]; then
        REMOTE_HOME="$(ssh "$REMOTE_HOST" 'printf "%s" "$HOME"')"
        REMOTE_WS="$REMOTE_HOME/${REMOTE_WS:2}"
    fi

    if [[ "$REMOTE_WS" != /* ]]; then
        echo "Workspace path must be absolute or start with ~/."
        echo "Examples:"
        echo "  ~/robot_ws"
        echo "  /home/smac/robot_ws"
        continue
    fi

    case "$WS_EXISTS" in

        y|Y|yes|YES)

            if ssh "$REMOTE_HOST" "test -d '$REMOTE_WS'"; then
                echo
                echo "Found workspace:"
                echo "  $REMOTE_WS"
                break
            else
                echo
                echo "Directory does not exist:"
                echo "  $REMOTE_WS"
                echo
            fi
            ;;


        n|N|no|NO)

            echo
            echo "Creating:"
            echo "  $REMOTE_WS/src"

            ssh "$REMOTE_HOST" \
                "mkdir -p '$REMOTE_WS/src'"

            echo "Workspace created."

            break
            ;;


        *)
            echo "Please enter y or n."
            ;;
    esac
done

# Existing workspaces aren't guaranteed to already have src/.
ssh "$REMOTE_HOST" "mkdir -p '$REMOTE_WS/src'"


# ============================================================
# Install SMAC CLI
# ============================================================

echo
echo "======================================"
echo " Installing SMAC CLI"
echo "======================================"
echo

mkdir -p "$HOME/.config/smac"

cat > "$HOME/.config/smac/config" <<EOF
USE_DOCKER="$USE_DOCKER"
LOCAL_WS="$LOCAL_WS"
REMOTE_HOST="$REMOTE_HOST"
REMOTE_WS="$REMOTE_WS"
COMPOSE_FILE="$COMPOSE_FILE"
EOF

mkdir -p "$HOME/bin"

ln -sf "$SMAC_SCRIPT" "$HOME/bin/smac"


# ============================================================
# Add ~/bin to PATH
# ============================================================

if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then

    if ! grep -q \
        'export PATH="$HOME/bin:$PATH"' \
        "$HOME/.bashrc" 2>/dev/null
    then
        echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
    fi

    export PATH="$HOME/bin:$PATH"
fi


echo
echo "SMAC CLI installed:"
echo "  $HOME/bin/smac"
echo