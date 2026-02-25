#!/bin/bash

# Security Tools Installation Script for Debian/Ubuntu-based systems
# Installs common penetration testing tools via apt.

echo "Starting installation of security tools..."

# Update package lists
echo "Updating package lists..."
sudo apt update

# Install Standard Tools via APT
# We use apt directly to ensure non-interactive installation
TOOLS=(
    nmap
    wireshark
    sqlmap
    hydra
    john
    aircrack-ng
    gobuster
    bettercap
)

echo "Installing standard tools: ${TOOLS[*]}"
sudo apt install -y "${TOOLS[@]}"

# Install Metasploit Framework
echo "Installing Metasploit Framework..."
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
chmod 755 msfinstall
./msfinstall

# Install SecLists (Useful wordlists)
if [ ! -d "$HOME/SecLists" ]; then
    echo "Cloning SecLists..."
    git clone https://github.com/danielmiessler/SecLists.git "$HOME/SecLists"
else
    echo "SecLists already exists in $HOME/SecLists"
fi

# Cleanup
rm msfinstall

echo ""
echo "--------------------------------------------------------"
echo "Installation Complete!"
echo "--------------------------------------------------------"
echo "Notes:"
echo "1. Wireshark: You may need to add your user to the 'wireshark' group to capture packets without sudo:"
echo "   sudo usermod -aG wireshark \$USER"
echo ""
echo "2. Burp Suite: This tool requires manual download/installation."
echo "   Download the Community Edition script from: https://portswigger.net/burp/releases"
echo "   Then run the installer script."
echo "--------------------------------------------------------"
