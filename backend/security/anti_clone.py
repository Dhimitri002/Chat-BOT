"""
Flora Platform — Anti-Clone / Hardware Fingerprinting
======================================================
Generates unique hardware fingerprints based on machine characteristics.
Detects VMs and emulators to prevent license farming.
"""

import hashlib
import logging
import os
import platform
import re
import socket
import subprocess
import sys
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class AntiClone:
    """
    Hardware fingerprinting and anti-tampering detection.

    Generates a stable fingerprint based on:
    - CPU info / processor ID
    - Machine UUID / serial number
    - MAC address
    - OS installation ID
    - Disk serial (when available)

    Also detects virtual machines and emulators.
    """

    # Known VM indicators
    VM_INDICATORS = [
        "virtualbox", "vmware", "qemu", "kvm", "xen", "hyper-v",
        "parallels", "virtual", "vbox", "vmtools", "qemu-ga",
        "xenbus", "vmwareguest", "hyperv", "sandbox", "docker",
        "container", "lxc", "wsl",
    ]

    VM_PROCESS_INDICATORS = [
        "vboxservice", "vboxtray", "vmwaretray", "vmwareuser",
        "vmtoolsd", "qemu-ga", "xenservice", "parallels",
    ]

    VM_MAC_PREFIXES = [
        "08:00:27",  # VirtualBox
        "00:0c:29",  # VMware
        "00:50:56",  # VMware
        "00:1c:42",  # Parallels
        "00:16:3e",  # Xen
        "52:54:00",  # QEMU/KVM
        "08:00:27",  # VirtualBox
    ]

    def __init__(self):
        self._fingerprint_cache: Optional[str] = None
        self._vm_check_cache: Optional[bool] = None

    def generate_fingerprint(self) -> str:
        """
        Generate a unique hardware fingerprint for this machine.

        Returns a SHA-256 hash of combined hardware identifiers.
        """
        if self._fingerprint_cache:
            return self._fingerprint_cache

        components = []

        # System info
        components.extend([
            platform.node() or "",
            platform.machine() or "",
            platform.processor() or "",
            platform.system() or "",
            platform.version() or "",
            sys.platform,
        ])

        # Try hardware-specific identifiers
        components.append(self._get_cpu_id() or "")
        components.append(self._get_machine_uuid() or "")
        components.append(self._get_mac_address() or "")
        components.append(self._get_disk_serial() or "")
        components.append(self._get_bios_serial() or "")

        # Combine and hash
        combined = "|".join(components)
        fingerprint = hashlib.sha256(combined.encode()).hexdigest()

        self._fingerprint_cache = fingerprint
        logger.debug(f"Hardware fingerprint: {fingerprint[:16]}...")
        return fingerprint

    def _get_cpu_id(self) -> Optional[str]:
        """Get CPU ID / serial number."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "cpu", "get", "ProcessorId"],
                    capture_output=True, text=True, timeout=5,
                )
                lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                if len(lines) > 1:
                    return lines[1]
            elif platform.system() == "Linux":
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if line.startswith("Serial") or line.startswith("model name"):
                                return line.split(":")[1].strip()
                except FileNotFoundError:
                    pass
                result = subprocess.run(
                    ["dmidecode", "-t", "processor"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if "ID:" in line or "Serial Number:" in line:
                        return line.split(":")[1].strip()
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, timeout=5,
                )
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"CPU ID detection failed: {e}")
        return None

    def _get_machine_uuid(self) -> Optional[str]:
        """Get machine UUID."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "csproduct", "get", "UUID"],
                    capture_output=True, text=True, timeout=5,
                )
                lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                if len(lines) > 1:
                    return lines[1]
            elif platform.system() == "Linux":
                for path in ["/sys/class/dmi/id/product_uuid", "/etc/machine-id"]:
                    try:
                        with open(path, "r") as f:
                            return f.read().strip()
                    except FileNotFoundError:
                        continue
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if "Hardware UUID" in line:
                        return line.split(":")[1].strip()
        except Exception as e:
            logger.debug(f"Machine UUID detection failed: {e}")

        # Fallback to node UUID
        try:
            return str(uuid.getnode())
        except Exception:
            return None

    def _get_mac_address(self) -> Optional[str]:
        """Get the primary MAC address."""
        try:
            mac = uuid.getnode()
            return ":".join(f"{(mac >> i) & 0xff:02x}" for i in (40, 32, 24, 16, 8, 0))
        except Exception as e:
            logger.debug(f"MAC address detection failed: {e}")
        return None

    def _get_disk_serial(self) -> Optional[str]:
        """Get primary disk serial number."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "diskdrive", "get", "SerialNumber"],
                    capture_output=True, text=True, timeout=5,
                )
                lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                if len(lines) > 1:
                    return lines[1]
        except Exception as e:
            logger.debug(f"Disk serial detection failed: {e}")
        return None

    def _get_bios_serial(self) -> Optional[str]:
        """Get BIOS serial number."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "bios", "get", "SerialNumber"],
                    capture_output=True, text=True, timeout=5,
                )
                lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                if len(lines) > 1:
                    return lines[1]
            elif platform.system() == "Linux":
                result = subprocess.run(
                    ["dmidecode", "-s", "system-serial-number"],
                    capture_output=True, text=True, timeout=5,
                )
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"BIOS serial detection failed: {e}")
        return None

    def detect_vm(self) -> bool:
        """
        Detect if running inside a virtual machine or emulator.

        Returns True if VM environment detected.
        """
        if self._vm_check_cache is not None:
            return self._vm_check_cache

        # Check environment variables
        vm_env_vars = ["VBOX", "VMWARE", "VIRTUALBOX", "KVM", "QEMU", "XEN"]
        for var in vm_env_vars:
            if any(var in v.upper() for v in os.environ):
                logger.info(f"VM detected via environment variable: {var}")
                self._vm_check_cache = True
                return True

        # Check system info strings
        system_strings = [
            platform.platform(),
            platform.version(),
            platform.machine(),
            platform.processor(),
        ]
        combined = " ".join(str(s).lower() for s in system_strings if s)
        for indicator in self.VM_INDICATORS:
            if indicator in combined:
                logger.info(f"VM detected via system string: {indicator}")
                self._vm_check_cache = True
                return True

        # Check MAC address
        mac = self._get_mac_address()
        if mac:
            mac_prefix = mac[:8].lower()
            if mac_prefix in self.VM_MAC_PREFIXES:
                logger.info(f"VM detected via MAC prefix: {mac_prefix}")
                self._vm_check_cache = True
                return True

        # Check running processes (Linux/macOS)
        if platform.system() != "Windows":
            try:
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True, text=True, timeout=5,
                )
                processes = result.stdout.lower()
                for indicator in self.VM_PROCESS_INDICATORS:
                    if indicator in processes:
                        logger.info(f"VM detected via process: {indicator}")
                        self._vm_check_cache = True
                        return True
            except Exception:
                pass

        self._vm_check_cache = False
        return False

    def validate_fingerprint(
        self,
        expected_fingerprint: str,
        current_fingerprint: Optional[str] = None,
    ) -> bool:
        """
        Validate the current hardware matches an expected fingerprint.

        Args:
            expected_fingerprint: The stored fingerprint
            current_fingerprint: Current fingerprint (generates if None)

        Returns True if they match.
        """
        if current_fingerprint is None:
            current_fingerprint = self.generate_fingerprint()

        match = expected_fingerprint == current_fingerprint

        if match:
            logger.debug("Hardware fingerprint matches")
        else:
            logger.warning(
                f"Hardware fingerprint mismatch: "
                f"expected={expected_fingerprint[:16]}... "
                f"got={current_fingerprint[:16]}..."
            )

        return match

    def get_machine_summary(self) -> dict:
        """Get a human-readable summary of machine identifiers."""
        return {
            "hostname": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "fingerprint": self.generate_fingerprint(),
            "mac_address": self._get_mac_address() or "unknown",
            "is_vm": self.detect_vm(),
            "python_version": sys.version,
        }
