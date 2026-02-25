#!/usr/bin/env bash
#
# linode-bastion.sh – spin up a cheap Linode for reverse‑SSH tunnelling,
#                     then optionally destroy it.
#
# Usage:
#   linode-bastion.sh up    # create the server and print connection info
#   linode-bastion.sh down  # destroy the server (stop paying)
#
# Requirements: linode-cli, jq, curl, an existing SSH public key.
#
# The script is deliberately verbose (echo statements) so a screen‑reader
# can narrate each step.

set -euo pipefail

# ----------------------------------------------------------------------
# USER‑CONFIGURATION – edit these once if you want different defaults
# ----------------------------------------------------------------------
LINODE_LABEL="homelab-bastion-$(date +%s)"   # unique name each run
LINODE_TYPE="g6-nanode-1"                # cheapest Linode (1 vCPU, 1 GB RAM)
LINODE_REGION="eu-central"               # Frankfurt region (low latency in EU)
LINODE_IMAGE="linode/ubuntu22.04"        # Ubuntu 22.04 LTS (change to archlinux if you wish)
SSH_KEY_LABEL="homelab-key-$(whoami)"       # name for the imported key on Linode
# ----------------------------------------------------------------------

die() { echo "❌ $*" >&2; exit 1; }

# ----------------------------------------------------------------------
# Verify we have an API token
# ----------------------------------------------------------------------
[[ -z "${LINODE_TOKEN:-}" ]] && die "Export LINODE_TOKEN with your Linode API token before running."

# ----------------------------------------------------------------------
# Import SSH key (if not already present)
# ----------------------------------------------------------------------
import_ssh_key() {
    local pubkey_path="${HOME}/.ssh/ssh_tunnel.pub"
    
    # Check if key exists, if not offer to create it
    if [[ ! -f "$pubkey_path" ]]; then
        echo "⚠️  SSH key not found at $pubkey_path"
        echo "Would you like to generate a new key pair? [y/N]"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "🔑 Generating new ED25519 key pair..."
            ssh-keygen -t ed25519 -f "${HOME}/.ssh/ssh_tunnel" -C "homelab-bastion" -N ""
            chmod 600 "${HOME}/.ssh/ssh_tunnel"
            chmod 644 "${HOME}/.ssh/ssh_tunnel.pub"
            echo "✅ Key pair created at ${HOME}/.ssh/ssh_tunnel"
        else
            die "Cannot proceed without SSH key at $pubkey_path"
        fi
    fi

    if linode-cli sshkeys list --json | jq -r '.[].label' | grep -qx "$SSH_KEY_LABEL"; then
        echo "🔑 SSH key \"$SSH_KEY_LABEL\" already exists on Linode."
    else
        echo "🔑 Importing SSH key \"$SSH_KEY_LABEL\" to Linode..."
        linode-cli sshkeys create --label "$SSH_KEY_LABEL" --ssh_key "$(cat "$pubkey_path")"
    fi
}

# ----------------------------------------------------------------------
# Create the Linode instance
# ----------------------------------------------------------------------
create_linode() {
    # Prompt for root password
    echo "🔐 Enter root password for the Linode bastion:"
    read -s ROOT_PASSWORD
    echo
    echo "🔐 Confirm password:"
    read -s ROOT_PASSWORD_CONFIRM
    echo
    
    if [[ "$ROOT_PASSWORD" != "$ROOT_PASSWORD_CONFIRM" ]]; then
        die "Passwords do not match!"
    fi
    
    if [[ ${#ROOT_PASSWORD} -lt 8 ]]; then
        die "Password must be at least 8 characters long!"
    fi
    
    echo "🚀 Creating Linode \"$LINODE_LABEL\" ($LINODE_TYPE, $LINODE_IMAGE)…"
    linode-cli linodes create \
        --label "$LINODE_LABEL" \
        --type "$LINODE_TYPE" \
        --region "$LINODE_REGION" \
        --image "$LINODE_IMAGE" \
        --root_pass "$ROOT_PASSWORD" \
        --authorized_keys "$(cat "${HOME}/.ssh/ssh_tunnel.pub")" \
        --tags "homelab,bastion" \
        --json > /tmp/linode-create.json

    LINODE_ID=$(jq -r '.[0].id' /tmp/linode-create.json)

    echo "⏳ Waiting for Linode $LINODE_ID to reach the "running" state…"
    while true; do
        STATUS=$(linode-cli linodes view "$LINODE_ID" --json | jq -r '.[0].status')
        [[ "$STATUS" == "running" ]] && break
        sleep 2
    done

    LINODE_IP=$(linode-cli linodes view "$LINODE_ID" --json | jq -r '.[0].ipv4[0]')
    echo "✅ Linode is up! Public IP: $LINODE_IP"
}

# ----------------------------------------------------------------------
# Print the reverse‑SSH systemd unit for the TARGET VM
# ----------------------------------------------------------------------
print_reverse_ssh_snippet() {
    cat <<EOF

# --------------------------------------------------------------
# Paste the following into a root‑owned file on the TARGET VM:
#   /etc/systemd/system/reverse-ssh.service
# --------------------------------------------------------------
[Unit]
Description=Reverse SSH tunnel to Linode bastion
After=network-online.target
Wants=network-online.target

[Service]
User=YOUR_USERNAME_HERE
ExecStart=/usr/bin/ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /home/YOUR_USERNAME_HERE/.ssh/ssh_tunnel -N -R 2222:localhost:22 root@${LINODE_IP}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
# --------------------------------------------------------------

# SETUP STEPS ON YOUR TARGET VM:
# 
# 1. If you don't have the SSH key yet, generate it:
#    ssh-keygen -t ed25519 -f ~/.ssh/ssh_tunnel -C "homelab-bastion"
#    chmod 600 ~/.ssh/ssh_tunnel
#    chmod 644 ~/.ssh/ssh_tunnel.pub
#
#    NOTE: The script automatically adds your public key to the Linode,
#    so you should be able to connect WITHOUT running ssh-copy-id!
#
# 2. Test the connection works without password:
#    ssh -i ~/.ssh/ssh_tunnel root@${LINODE_IP}
#    (should connect without asking for password)
#
# 3. Save the systemd service file above to:
#    sudo nano /etc/systemd/system/reverse-ssh.service
#    (replace YOUR_USERNAME_HERE with your actual username from 'whoami')
#
# 4. Enable and start the service:
#    sudo systemctl daemon-reload
#    sudo systemctl enable --now reverse-ssh.service
#    sudo systemctl status reverse-ssh.service
#
# --------------------------------------------------------------
# HOW TO CONNECT FROM YOUR LAPTOP:
# 
# Once the reverse tunnel is running on your target VM, you can
# SSH into it from anywhere via the Linode bastion:
#
#    ssh -J root@${LINODE_IP} -p 2222 localhost
#
# Or in two steps:
#    ssh root@${LINODE_IP}           # Connect to bastion
#    ssh -p 2222 localhost           # Connect to your target VM
# --------------------------------------------------------------

EOF
    echo "✅ Linode bastion is ready at ${LINODE_IP}"
    echo "📋 Follow the setup steps above to configure your target VM"
}

# ----------------------------------------------------------------------
# Destroy the Linode (stop paying)
# ----------------------------------------------------------------------
destroy_linode() {
    echo "🔍 Looking for Linodes with 'homelab-bastion' in the label..."
    LINODES=$(linode-cli linodes list --json | jq -r '.[] | select(.label | contains("homelab-bastion")) | .id')
    
    if [[ -z "$LINODES" ]]; then
        echo "ℹ️  No bastion Linodes found to destroy."
        return
    fi
    
    for id in $LINODES; do
        LABEL=$(linode-cli linodes view "$id" --json | jq -r '.[0].label')
        echo "🗑️  Destroying Linode $id ($LABEL)..."
        linode-cli linodes delete "$id"
        echo "✅ Destroyed $LABEL"
    done
}

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
case "${1:-}" in
    up)
        import_ssh_key
        create_linode
        print_reverse_ssh_snippet
        ;;
    down)
        destroy_linode
        ;;
    *)
        die "Usage: $0 {up|down}"
        ;;
esac