#!/bin/bash
# OpenTrons Custom Serial Module Installation Script

set -e  # Exit on error

PATCH_FILE="custom_serial_module.patch"
PACKAGE_DIR="ot_custom_serial_module"
BACKUP_DIR="/tmp/opentrons_backup_$(date +%Y%m%d_%H%M%S)"
OPENTRONS_DIR="/opt/opentrons-robot-server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}OpenTrons Custom Serial Module Installer${NC}"
echo "========================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root${NC}"
   exit 1
fi

# Check if patch file exists
if [[ ! -f "$PATCH_FILE" ]]; then
    echo -e "${RED}Error: Patch file '$PATCH_FILE' not found${NC}"
    exit 1
fi

# Check if package directory exists
if [[ ! -d "$PACKAGE_DIR" ]]; then
    echo -e "${RED}Error: Package directory '$PACKAGE_DIR' not found${NC}"
    exit 1
fi

# Check if OpenTrons directory exists
if [[ ! -d "$OPENTRONS_DIR" ]]; then
    echo -e "${RED}Error: OpenTrons directory '$OPENTRONS_DIR' not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Creating backup at $BACKUP_DIR${NC}"
mkdir -p "$BACKUP_DIR"
cp -r "$OPENTRONS_DIR" "$BACKUP_DIR/"

echo -e "${YELLOW}Installing Python package${NC}"
pip install -e "$(realpath "$PACKAGE_DIR/..")"

echo -e "${YELLOW}Testing patch application (dry run)${NC}"
cd "$OPENTRONS_DIR"
if ! patch --dry-run -p1 < "$(realpath "$PATCH_FILE")" > /dev/null 2>&1; then
    echo -e "${RED}Error: Patch cannot be applied cleanly${NC}"
    echo "Please check for conflicts or ensure you're using the correct OpenTrons version"
    exit 1
fi

echo -e "${YELLOW}Applying patch${NC}"
if patch -p1 < "$(realpath "$PATCH_FILE")"; then
    echo -e "${GREEN}✅ Patch applied successfully${NC}"
else
    echo -e "${RED}Error: Failed to apply patch${NC}"
    echo "Restoring backup..."
    rm -rf "$OPENTRONS_DIR"
    cp -r "$BACKUP_DIR/$(basename "$OPENTRONS_DIR")" "$OPENTRONS_DIR"
    exit 1
fi

echo -e "${YELLOW}Restarting OpenTrons services${NC}"
if systemctl restart opentrons-robot-server; then
    echo -e "${GREEN}✅ OpenTrons services restarted${NC}"
else
    echo -e "${RED}Warning: Failed to restart services${NC}"
    echo "You may need to restart manually: systemctl restart opentrons-robot-server"
fi

echo
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo
echo "Usage in protocols:"
echo "  custom_module = protocol.load_module('customSerialModuleV1', 1)"
echo "  custom_module = protocol.load_module('custom serial module', 1)"
echo
echo "To uninstall:"
echo "  patch -R -p1 < $PATCH_FILE"
echo "  pip uninstall ot-custom-serial-module"
echo "  systemctl restart opentrons-robot-server"
echo
echo "Backup created at: $BACKUP_DIR"