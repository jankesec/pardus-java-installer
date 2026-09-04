#!/usr/bin/env python3
import os
import signal
import subprocess
import sys

import PackageManager


def cancel_process(pid_str):
    if not pid_str.isdigit():
        print(f"Invalid PID: {pid_str}")
        sys.exit(1)

    pid = int(pid_str)
    if pid <= 1:
        print(f"Refusing to signal system PID: {pid}")
        sys.exit(1)

    # Verify that the target process is an Actions.py instance
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read()
            if b"Actions.py" not in cmdline and b"pardus-java-installer" not in cmdline:
                print(f"Refusing to signal non-installer process: {pid}")
                sys.exit(1)
    except (FileNotFoundError, ProcessLookupError):
        # Target process has already terminated
        sys.exit(0)
    except PermissionError:
        print(f"Permission denied accessing /proc/{pid}")
        sys.exit(1)

    try:
        os.kill(pid, signal.SIGINT)
    except ProcessLookupError:
        # Process terminated before signal dispatch
        sys.exit(0)
    except Exception as e:
        print(f"Failed to send signal to PID {pid}: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        cancel_process(sys.argv[1])
    elif len(sys.argv) == 3:
        operation = sys.argv[1]
        package = sys.argv[2]
        path = None
    elif len(sys.argv) == 4:
        operation = sys.argv[1]
        package = sys.argv[2]
        path = sys.argv[3]
    else:
        print("Usage: ./Actions.py operation package (path)")
        sys.exit(1)

    cmd = PackageManager.get_command(operation, package=package, path=path)
    print(f"Action Command: {cmd}")
    if cmd:
        proc = None
        try:
            proc = subprocess.Popen(cmd)
            code = proc.wait()
            sys.exit(code)
        except KeyboardInterrupt:
            if proc and proc.poll() is None:  # still runs?
                proc.terminate()  # SIGTERM
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()  # SIGKILL
            sys.exit(130)
        except Exception as e:
            print("Exception happened on process run:", e)
            print(sys.argv)
            sys.exit(1)
    else:
        print(f"Not valid command tuple: ({operation},{package},{path})")
        sys.exit(1)
