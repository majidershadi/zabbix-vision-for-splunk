#!/usr/bin/env python3
"""Linux-only opt-in wrapper for fixed, locally configured UserParameter commands.

Stdout/stderr are inherited unchanged. Audit records never include command text,
arguments, environment, stdout or stderr. No network access or automatic retry.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
import uuid

SCHEMA = 'zabbix_userparameter_execution/v1'
NAME = re.compile(r'[A-Za-z0-9_.-]{1,128}')


def read_config(path, key):
    if not Path(path).is_absolute() or not NAME.fullmatch(key):
        raise ValueError('Absolute configuration path and simple item key required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'r', encoding='utf-8') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022 or info.st_uid not in (0, os.geteuid()):
            raise ValueError('Configuration ownership or permissions rejected')
        if info.st_size > 65536:
            raise ValueError('Configuration too large')
        config = json.load(handle)
    command = config['commands'][key]
    argv, timeout, log_file = command['argv'], command['timeout_seconds'], config['log_file']
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and '\x00' not in a for a in argv):
        raise ValueError('Fixed argv list required')
    if not Path(argv[0]).is_absolute() or not Path(log_file).is_absolute():
        raise ValueError('Absolute executable and log paths required')
    if type(timeout) is not int or not 1 <= timeout <= 300:
        raise ValueError('Timeout must be 1–300 seconds')
    command_id = command['command_id']
    if not isinstance(command_id, str) or not NAME.fullmatch(command_id):
        raise ValueError('Invalid command identifier')
    return argv, timeout, log_file, command_id


def append_record(path, record):
    # Operator provisions the parent directory. Refuse a symlink at the log path.
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o640)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise ValueError('Execution log ownership or permissions rejected')
        payload = (json.dumps(record, separators=(',', ':')) + '\n').encode('utf-8')
        fcntl.flock(fd, fcntl.LOCK_EX)
        if os.write(fd, payload) != len(payload):
            raise OSError('Incomplete execution log write')
        os.fsync(fd)
    finally:
        os.close(fd)


def run(config_path, key):
    argv, timeout, log_file, command_id = read_config(config_path, key)
    record = {'schema': SCHEMA, 'invocation_id': str(uuid.uuid4()),
              'userparameter_key': key, 'command_id': command_id, 'pid': os.getpid()}
    append_record(log_file, dict(record, phase='start', status='started', timestamp=int(time.time())))
    started = time.monotonic()
    process = None
    status, code = 'spawn_failed', 125

    def interrupted(signum, frame):
        raise InterruptedError()

    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        process = subprocess.Popen(argv, shell=False, start_new_session=True)
        code = process.wait(timeout=timeout)
        code = 128 - code if code < 0 else code
        status = 'success' if code == 0 else 'failure'
    except subprocess.TimeoutExpired:
        status, code = 'timeout', 124
    except InterruptedError:
        status, code = 'interrupted', 130
    except OSError:
        status, code = 'spawn_failed', 125
    finally:
        # Ignore further termination while stopping the process group and auditing.
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        try:
            if process is not None and status in ('timeout', 'interrupted'):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            append_record(log_file, dict(record, phase='end', status=status,
                timestamp=int(time.time()), duration_ms=round((time.monotonic()-started)*1000, 3), exit_code=code))
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--key', required=True)
    args = parser.parse_args()
    try:
        return run(args.config, args.key)
    except Exception:
        # No command details, file contents or exception strings in diagnostics.
        sys.stderr.write('UserParameter wrapper failed; inspect local configuration and execution log.\n')
        return 125


if __name__ == '__main__':
    sys.exit(main())
