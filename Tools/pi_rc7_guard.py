"""Non-integrated rc.7 scheduling guard; never deployment or restore authority.

The owning installer must authenticate target/boot/release/configuration and
qualify this component before calling it. Hold-only: release/restore is deliberately unsupported. No CLI, installer or device action
runs on import. Unknown results intentionally leave owned guards in place.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

SERVICES = tuple('djconnect-' + name + '.service' for name in
                 ('watchdog', 'updater', 'maintenance', 'nightly-reboot'))
TIMERS = tuple(name.removesuffix('.service') + '.timer' for name in SERVICES)
UNITS = tuple(unit for pair in zip(SERVICES, TIMERS, strict=True) for unit in pair)
CONTENT = b'[Service]\nExecCondition=\nExecCondition=/usr/bin/false\nExecStop=\nExecStopPost=\n'
GUARD_NAME = '90-djconnect-rc7-transaction.conf'
POLICY = {'LoadState', 'ActiveState', 'SubState', 'UnitFileState', 'FragmentPath',
          'DropInPaths', 'SuccessAction', 'FailureAction', 'JobTimeoutAction',
          'OnSuccess', 'OnFailure'}


class GuardError(ValueError):
    """Static diagnostic only; no command output, private paths or contents."""


def need(value: bool, code: str) -> None:
    if not value:
        raise GuardError(code)


@dataclass(frozen=True)
class FileIdentity:
    device: int
    inode: int
    sha256: str


def checked_file(path: Path, maximum: int = 32768) -> tuple[bytes, FileIdentity]:
    """One no-follow descriptor, bounded regular root-owned nonwritable bytes."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_uid == 0
             and not before.st_mode & 0o022 and before.st_size <= maximum, 'GUARD_FILE_INVALID')
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
        need(len(raw) <= maximum and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'GUARD_FILE_CHANGED')
    return raw, FileIdentity(before.st_dev, before.st_ino, hashlib.sha256(raw).hexdigest())


def secure_directory(path: Path) -> None:
    metadata = path.lstat()
    need(stat.S_ISDIR(metadata.st_mode) and metadata.st_uid == 0
         and not metadata.st_mode & 0o022, 'GUARD_DIRECTORY_INVALID')


def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_claim(root: Path, namespace: str, transaction: str, binding: dict) -> Path:
    """Never refund. Every new directory entry and file data synced before return."""
    need(re.fullmatch(r'[0-9a-f]{64}', namespace) is not None
         and re.fullmatch(r'[1-9][0-9]{0,19}', transaction) is not None, 'GUARD_CLAIM_INVALID')
    # The parent is caller-authenticated root-owned state, never a supplied endpoint.
    secure_directory(root.parent)
    try:
        root.mkdir(mode=0o700)
    except FileExistsError:
        pass
    secure_directory(root)
    sync_directory(root)
    sync_directory(root.parent)
    # The manifest/instance namespace itself is the durable exclusive claim.
    # A new workflow/transaction identifier cannot replay the same grant.
    namespace_path = root / namespace
    namespace_path.mkdir(mode=0o700)
    secure_directory(namespace_path)
    sync_directory(namespace_path)
    sync_directory(root)
    claim = root / namespace / transaction
    fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        raw = json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()
        need(len(raw) <= 8192, 'GUARD_CLAIM_INVALID')
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(claim.parent)
    return claim


@dataclass(frozen=True)
class UnitSnapshot:
    name: str
    enabled: str
    active: str
    fragment_sha256: str


class Systemd:
    """Fixed eight-unit Linux adapter; commands are closed and output is bounded."""
    unit_root = Path('/etc/systemd/system')
    guard_root = Path('/etc/systemd/system')

    def run(self, *arguments: str) -> str:
        result = subprocess.run(['/usr/bin/systemctl', *arguments], stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=20, check=False,
                                env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
        need(result.returncode == 0 and len(result.stdout) <= 32768
             and len(result.stderr) <= 8192, 'GUARD_SYSTEMD_UNAVAILABLE')
        return result.stdout.decode('utf-8', errors='strict')

    def boot(self) -> str:
        value = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        need(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', value)
             is not None, 'GUARD_BOOT_INVALID')
        return value

    def properties(self, unit: str) -> dict[str, str]:
        need(unit in UNITS, 'GUARD_UNIT_INVALID')
        extra = {'ExecCondition', 'MainPID', 'ControlPID', 'ControlGroup', 'Type', 'KillMode', 'SendSIGKILL', 'ExecStartPre', 'ExecStartPost',
                 'ExecStop', 'ExecStopPost', 'InvocationID', 'Result', 'ExecMainCode', 'ExecMainStatus'} if unit in SERVICES else {'Unit'}
        result = self.run('show', unit, '--property=' + ','.join(sorted(POLICY | extra)), '--no-pager', '--all')
        rows = result.splitlines()
        need(all('=' in row for row in rows), 'GUARD_UNIT_UNKNOWN')
        data = dict(row.split('=', 1) for row in rows)
        need(len(data) == len(rows), 'GUARD_UNIT_UNKNOWN')
        # systemctl omits an empty ExecCondition command-array, even with --all.
        # Only this known empty-array representation is normalized; every other
        # requested property and every held (nonempty) command remains mandatory.
        if unit in SERVICES:
            for field in ('ExecCondition', 'ExecStartPre', 'ExecStartPost', 'ExecStop', 'ExecStopPost'):
                data.setdefault(field, '')
        need(set(data) == POLICY | extra, 'GUARD_UNIT_UNKNOWN')
        return data

    def fragment(self, unit: str) -> str:
        secure_directory(self.unit_root)
        return checked_file(self.unit_root / unit)[1].sha256

    def cgroup_empty(self, group: str) -> bool:
        need(group.startswith('/system.slice/djconnect-') and '..' not in group
             and re.fullmatch(r'/system.slice/djconnect-[a-z-]+\.service', group) is not None,
             'GUARD_CGROUP_UNKNOWN')
        root = Path('/sys/fs/cgroup') / group.removeprefix('/')
        if not root.exists():
            return True
        # cgroup.events populated includes descendant cgroups, unlike just
        # inspecting MainPID or the top-level cgroup.procs list.
        raw = (root / 'cgroup.events').read_bytes()
        need(len(raw) <= 1024, 'GUARD_CGROUP_UNKNOWN')
        fields = dict(row.split() for row in raw.decode('ascii').splitlines())
        need(fields.get('populated') in {'0', '1'}, 'GUARD_CGROUP_UNKNOWN')
        return fields['populated'] == '0'

    def guard_available(self, unit: str) -> None:
        need(unit in SERVICES, 'GUARD_UNIT_INVALID')
        for root in (self.unit_root, Path('/run/systemd/system')):
            path = root / (unit + '.d')
            need(not path.exists() and not path.is_symlink(), 'GUARD_FOREIGN_DROPIN')

    def create_guard(self, unit: str) -> FileIdentity:
        need(unit in SERVICES, 'GUARD_UNIT_INVALID')
        secure_directory(self.guard_root)
        directory = self.guard_root / (unit + '.d')
        directory.mkdir(mode=0o700)  # Existing/foreign directory rejects, never reused.
        secure_directory(directory)
        path = directory / GUARD_NAME
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(CONTENT)
            stream.flush()
            os.fsync(stream.fileno())
        sync_directory(directory)
        sync_directory(self.guard_root)
        return checked_file(path, 1024)[1]

    def guard_identity(self, unit: str) -> FileIdentity:
        directory = self.guard_root / (unit + '.d')
        secure_directory(directory)
        need(sorted(p.name for p in directory.iterdir()) == [GUARD_NAME], 'GUARD_OWNERSHIP_CHANGED')
        raw, identity = checked_file(directory / GUARD_NAME, 1024)
        need(raw == CONTENT, 'GUARD_OWNERSHIP_CHANGED')
        return identity



class TransactionGuard:
    """Caller owns identity/authority/claim, installation and native success proof.

    This hold-only object cannot install, remove guards or grant a deployment. A newly constructed object
    cannot restore a previous transaction. No finally/unwind removes a guard.
    """
    def __init__(self, system: Systemd):
        self.system = system
        self.boot = system.boot()
        self.snapshots: dict[str, UnitSnapshot] = {}
        self.guards: dict[str, FileIdentity] = {}
        self.claimed = False
        self.restored = False
        self.drained = False
        self.drain_invocations: dict[str, str] = {}

    def same_boot(self) -> None:
        need(self.system.boot() == self.boot, 'GUARD_BOOT_CHANGED')

    def inspect(self, unit: str, *, held: bool) -> dict[str, str]:
        self.same_boot()
        data = self.system.properties(unit)
        need(data['LoadState'] == 'loaded' and data['ActiveState'] in
             ({'active', 'inactive', 'activating', 'failed'} if held and unit in self.drain_invocations
              else {'active', 'inactive', 'activating'} if unit in SERVICES else {'active', 'inactive'})
             and data['UnitFileState'] in {'enabled', 'disabled', 'static'}
             and data['FragmentPath'] == str(self.system.unit_root / unit)
             and all(data[key] == 'none' for key in ('SuccessAction', 'FailureAction', 'JobTimeoutAction'))
             and data['OnSuccess'] == data['OnFailure'] == '', 'GUARD_UNIT_UNKNOWN')
        expected = str(self.system.guard_root / (unit + '.d') / GUARD_NAME) if held and unit in SERVICES else ''
        need(data['DropInPaths'] == expected, 'GUARD_FOREIGN_DROPIN')
        if unit in SERVICES:
            need(data['Type'] == 'oneshot' and data['KillMode'] == 'control-group'
                 and data['SendSIGKILL'] == 'yes', 'GUARD_DRAIN_POLICY_INVALID')
            need(all(data[key] == '' for key in ('ExecStartPre', 'ExecStartPost', 'ExecStop', 'ExecStopPost')),
                 'GUARD_LIFECYCLE_HOOK_INVALID')
            if data['ActiveState'] == 'failed':
                need(data['InvocationID'] == self.drain_invocations.get(unit)
                     and data['Result'] == 'signal' and data['ExecMainCode'] == '2'
                     and data['ExecMainStatus'] == '15'
                     and data['MainPID'] == data['ControlPID'] == '0', 'GUARD_DRAIN_UNCERTAIN')
                if data['ControlGroup']:
                    need(self.system.cgroup_empty(data['ControlGroup']), 'GUARD_DRAIN_UNCERTAIN')
            condition = data['ExecCondition']
            if held:
                need(re.fullmatch(r'\{ path=/usr/bin/false ; argv\[\]=/usr/bin/false ; ignore_errors=no ; [^\r\n]* \}', condition)
                     is not None, 'GUARD_NOT_LOADED')
                need(unit in self.guards and self.system.guard_identity(unit) == self.guards[unit], 'GUARD_OWNERSHIP_CHANGED')
            else:
                need(condition == '', 'GUARD_FOREIGN_CONDITION')
        else:
            need(data['Unit'] == unit.removesuffix('.timer') + '.service', 'GUARD_TRIGGER_CHANGED')
        return data

    def prepare(self) -> None:
        need(not self.snapshots and not self.claimed, 'GUARD_ALREADY_USED')
        captured = {}
        for unit in UNITS:
            data = self.inspect(unit, held=False)
            if unit in SERVICES:
                self.system.guard_available(unit)
            captured[unit] = UnitSnapshot(unit, data['UnitFileState'], data['ActiveState'], self.system.fragment(unit))
        self.same_boot()
        self.snapshots = captured

    def hold(self, claim) -> None:
        need(len(self.snapshots) == 8 and not self.claimed and not self.guards, 'GUARD_NOT_PREPARED')
        # Revalidate the entire initial observation immediately before the claim.
        for unit, before in self.snapshots.items():
            data = self.inspect(unit, held=False)
            if unit in SERVICES:
                self.system.guard_available(unit)
            need((data['UnitFileState'], data['ActiveState'], self.system.fragment(unit))
                 == (before.enabled, before.active, before.fragment_sha256), 'GUARD_READINESS_CHANGED')
        self.same_boot()
        claim()  # Must durably bind target/manifest/transaction before any guard/stop.
        self.claimed = True
        self.same_boot()
        for unit in SERVICES:
            self.guards[unit] = self.system.create_guard(unit)
        self.system.run('daemon-reload')
        self.verify_held()
        # Stop timers only after loaded service guards fence all trigger paths.
        self.system.run('stop', *TIMERS)
        # Bind exactly the invocation observed immediately before OUR stop.
        # A killed activating oneshot may become failed/signal, not inactive.
        for unit in SERVICES:
            data = self.inspect(unit, held=True)
            if data['ActiveState'] in {'active', 'activating'}:
                need(re.fullmatch(r'[0-9a-f]{32}', data['InvocationID']) is not None,
                     'GUARD_DRAIN_UNCERTAIN')
                self.drain_invocations[unit] = data['InvocationID']
        self.system.run('stop', *SERVICES)
        for unit in SERVICES:
            data = self.inspect(unit, held=True)
            need(data['ActiveState'] in {'inactive', 'failed'} and data['MainPID'] == data['ControlPID'] == '0', 'GUARD_SERVICE_NOT_DRAINED')
            if data['ControlGroup']:
                need(self.system.cgroup_empty(data['ControlGroup']), 'GUARD_SERVICE_NOT_DRAINED')
        self.drained = True
        self.verify_held()

    def verify_held(self, replacement_fragments: dict[str, str] | None = None) -> None:
        need(self.claimed and len(self.guards) == 4 and not self.restored, 'GUARD_NOT_HELD')
        need(replacement_fragments is None or set(replacement_fragments) == set(UNITS), 'GUARD_FRAGMENT_SET_INVALID')
        for unit, before in self.snapshots.items():
            self.inspect(unit, held=True)
            allowed = {before.fragment_sha256}
            if replacement_fragments is not None:
                allowed.add(replacement_fragments[unit])
            need(self.system.fragment(unit) in allowed, 'GUARD_FRAGMENT_CHANGED')
        self.same_boot()

    def prove_denied_starts(self, replacement_fragments: dict[str, str] | None = None) -> None:
        """Qualification only: inspect real skip status, never infer from CLI zero."""
        need(self.drained, 'GUARD_NOT_DRAINED')
        self.verify_held(replacement_fragments)
        for unit in SERVICES:
            self.system.run('start', unit)
            data = self.inspect(unit, held=True)
            need(data['ActiveState'] == 'inactive' and data['MainPID'] == data['ControlPID'] == '0'
                 and re.search(r'code=exited ; status=1(?:/[^ ;}]+)? ', data['ExecCondition']) is not None,
                 'GUARD_START_NOT_DENIED')
            if data['ControlGroup']:
                need(self.system.cgroup_empty(data['ControlGroup']), 'GUARD_START_NOT_DENIED')
        self.verify_held(replacement_fragments)

    def restore(self, *_args, **_kwargs) -> None:
        # Deliberately unsupported until the producer explicitly defines an
        # all-unit persistent release commit and acknowledgment-loss semantics.
        # Never partially unlink four guards or rearm scheduling on uncertainty.
        raise GuardError('GUARD_RELEASE_NOT_QUALIFIED')
