"""Executable identities are discovered locally, never supplied by an HTTP client."""
import hashlib
import ntpath
import os
import sys


def canonical(path):
    if not isinstance(path, str) or not 4 <= len(path) <= 1024:
        raise ValueError("Invalid executable identity")
    value = ntpath.normcase(ntpath.normpath(path))
    drive, tail = ntpath.splitdrive(value)
    if len(drive) != 2 or drive[1] != ":" or not tail.startswith("\\") or not value.endswith(".exe"):
        raise ValueError("A local absolute executable is required")
    if any(c in tail for c in '*?\x00:') or any(ord(c) < 32 for c in value):
        raise ValueError("Invalid executable identity")
    return value


def executable_id(path):
    return hashlib.sha256(canonical(path).encode("utf-8")).hexdigest()


def protected(path):
    path = canonical(path)
    if os.name == "nt":
        from .windows_security import system_directory
        system = ntpath.normcase(str(system_directory().parent))
    else:
        system = "c:\\windows"
    # Protect OS executables, this runtime, and companion installation as a whole.
    runtime = ntpath.normcase(ntpath.dirname(sys.executable))
    own = ntpath.normcase(ntpath.dirname(ntpath.dirname(__file__)))
    return any(path == root or path.startswith(root.rstrip("\\/") + "\\")
               for root in (system, runtime, own)) or ntpath.basename(path) in {
                   "system.exe", "registry.exe", "netsentinel.exe", "netsentinel-companion.exe"}
