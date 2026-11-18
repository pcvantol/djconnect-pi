from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

import pytest

from Tools import pi_rc7_guard as guard

BOOT = '01234567-89ab-cdef-0123-456789abcdef'


class FakeSystem:
    unit_root = Path('/etc/systemd/system')
    guard_root = unit_root

    def __init__(self):
        self.boot_id = BOOT
        self.calls = []
        self.loaded = False
        self.guards = {}
        self.foreign = set()
        self.claimed = False
        self.fail_command = None
        self.cgroup_populated = False
        self.units = {}
        for i, unit in enumerate(guard.UNITS):
            service = unit in guard.SERVICES
            self.units[unit] = {'LoadState': 'loaded', 'ActiveState': 'inactive' if service or i == 3 else 'active',
                                'SubState': 'dead' if service else 'waiting',
                                'UnitFileState': 'static' if service else ('disabled' if i == 3 else 'enabled'),
                                'FragmentPath': str(self.unit_root / unit), 'DropInPaths': '',
                                'SuccessAction': 'none', 'FailureAction': 'none', 'JobTimeoutAction': 'none',
                                'OnSuccess': '', 'OnFailure': ''}
            if service:
                self.units[unit].update(ExecCondition='', MainPID='0', ControlPID='0', ControlGroup='', Type='oneshot', KillMode='control-group', SendSIGKILL='yes', ExecStartPre='', ExecStartPost='', ExecStop='', ExecStopPost='',
                                        InvocationID='', Result='success', ExecMainCode='0', ExecMainStatus='0')
            else:
                self.units[unit]['Unit'] = unit.removesuffix('.timer') + '.service'
        self.fragments = {unit: hashlib.sha256(unit.encode()).hexdigest() for unit in guard.UNITS}

    def boot(self):
        return self.boot_id

    def properties(self, unit):
        result = self.units[unit].copy()
        if self.loaded and unit in self.guards:
            result['DropInPaths'] = str(self.guard_root / (unit + '.d') / guard.GUARD_NAME)
            result['ExecCondition'] = '{ path=/usr/bin/false ; argv[]=/usr/bin/false ; ignore_errors=no ; pid=1 ; code=exited ; status=1 }'
        return result

    def fragment(self, unit):
        return self.fragments[unit]

    def guard_available(self, unit):
        if unit in self.foreign:
            raise guard.GuardError('GUARD_FOREIGN_DROPIN')

    def create_guard(self, unit):
        assert self.claimed
        value = guard.FileIdentity(1, len(self.guards) + 1, hashlib.sha256(guard.CONTENT).hexdigest())
        self.guards[unit] = value
        self.calls.append(('guard', unit))
        return value

    def guard_identity(self, unit):
        return self.guards[unit]

    def cgroup_empty(self, group):
        return not self.cgroup_populated

    def remove_guard(self, unit, identity):
        assert self.guards[unit] == identity
        self.calls.append(('remove', unit))
        del self.guards[unit]

    def run(self, *arguments):
        self.calls.append(arguments)
        if arguments[0] == self.fail_command:
            raise guard.GuardError('GUARD_SYSTEMD_UNAVAILABLE')
        if arguments[0] == 'daemon-reload':
            self.loaded = True
        elif arguments[0] in {'stop', 'start'}:
            for unit in arguments[1:]:
                old_active = self.units[unit]['ActiveState']
                self.units[unit]['ActiveState'] = 'active' if arguments[0] == 'start' else 'inactive'
                if arguments[0] == 'start' and unit in self.guards and self.loaded:
                    self.units[unit].update(ActiveState='inactive', MainPID='0', ControlPID='0', Result='exec-condition')
                if arguments[0] == 'stop' and unit in guard.SERVICES and old_active == 'activating':
                    self.units[unit].update(ActiveState='failed', Result='signal', ExecMainCode='2', ExecMainStatus='15')
                if arguments[0] == 'stop' and unit in guard.SERVICES:
                    self.units[unit].update(MainPID='0', ControlPID='0')
        elif arguments[0] in {'enable', 'disable'}:
            self.units[arguments[1]]['UnitFileState'] = 'enabled' if arguments[0] == 'enable' else 'disabled'
        return ''

    def claim(self):
        assert not self.claimed
        self.calls.append(('claim',))
        self.claimed = True


def held_system():
    system = FakeSystem()
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    transaction.hold(system.claim)
    return system, transaction


def test_durable_claim_precedes_every_guard_and_stop_and_drain():
    system, transaction = held_system()
    assert system.calls[0] == ('claim',)
    assert system.calls[1:5] == [('guard', unit) for unit in guard.SERVICES]
    assert system.calls[5:] == [('daemon-reload',), ('stop', *guard.TIMERS), ('stop', *guard.SERVICES)]
    assert transaction.drained and not transaction.restored
    assert set(system.guards) == set(guard.SERVICES)


@pytest.mark.parametrize('unit', guard.UNITS)
@pytest.mark.parametrize(('key', 'value'), [('LoadState', 'not-found'), ('ActiveState', 'failed'),
                                         ('UnitFileState', 'masked'), ('FragmentPath', '/foreign'),
                                         ('DropInPaths', '/foreign'), ('FailureAction', 'reboot'),
                                         ('OnFailure', 'foreign.service')])
def test_initial_unknown_units_reject_before_any_claim_or_effect(unit, key, value):
    system = FakeSystem()
    system.units[unit][key] = value
    transaction = guard.TransactionGuard(system)
    with pytest.raises(guard.GuardError):
        transaction.prepare()
    assert not system.calls and not system.claimed


@pytest.mark.parametrize('unit', guard.SERVICES)
def test_unloaded_foreign_guard_directory_also_rejects_before_claim(unit):
    system = FakeSystem()
    system.foreign.add(unit)
    transaction = guard.TransactionGuard(system)
    with pytest.raises(guard.GuardError, match='FOREIGN'):
        transaction.prepare()
    assert not system.calls


@pytest.mark.parametrize('unit', guard.TIMERS)
def test_wrong_trigger_rejects_before_effect(unit):
    system = FakeSystem()
    system.units[unit]['Unit'] = 'foreign.service'
    with pytest.raises(guard.GuardError, match='TRIGGER'):
        guard.TransactionGuard(system).prepare()
    assert not system.calls


def test_readiness_changes_after_prepare_do_not_burn_claim():
    system = FakeSystem()
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    system.units[guard.TIMERS[0]]['ActiveState'] = 'inactive'
    with pytest.raises(guard.GuardError, match='READINESS'):
        transaction.hold(system.claim)
    assert not system.calls


def test_foreign_guard_after_prepare_does_not_burn_claim():
    system = FakeSystem()
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    system.foreign.add(guard.SERVICES[0])
    with pytest.raises(guard.GuardError, match='FOREIGN'):
        transaction.hold(system.claim)
    assert not system.calls


def test_claim_failure_has_zero_guard_or_service_effects():
    system = FakeSystem()
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    def fail():
        raise OSError('synthetic fsync failure')
    with pytest.raises(OSError):
        transaction.hold(fail)
    assert not system.calls


@pytest.mark.parametrize('failure', ['daemon-reload', 'stop'])
def test_started_failure_never_removes_guard_or_refunds_claim(failure):
    system = FakeSystem()
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    system.fail_command = failure
    with pytest.raises(guard.GuardError):
        transaction.hold(system.claim)
    assert system.claimed and len(system.guards) == 4
    assert not any(call[0] == 'remove' for call in system.calls)


def test_remaining_cgroup_process_blocks_drain_even_with_zero_mainpid():
    system = FakeSystem()
    system.units[guard.SERVICES[0]]['ControlGroup'] = '/system.slice/djconnect-watchdog.service'
    system.cgroup_populated = True
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    with pytest.raises(guard.GuardError, match='NOT_DRAINED'):
        transaction.hold(system.claim)
    assert system.claimed and len(system.guards) == 4 and not transaction.drained


def test_native_failure_keeps_all_guards_no_restore_or_replay():
    system, transaction = held_system()
    calls = list(system.calls)
    with pytest.raises(guard.GuardError, match='RELEASE'):
        transaction.restore(lambda: False, system.fragments)
    assert system.calls == calls and len(system.guards) == 4 and system.claimed


def test_boot_change_keeps_all_guards():
    system, transaction = held_system()
    system.boot_id = '11234567-89ab-cdef-0123-456789abcdef'
    with pytest.raises(guard.GuardError, match='BOOT'):
        transaction.verify_held()
    assert len(system.guards) == 4 and not transaction.restored


@pytest.mark.parametrize('unit', guard.SERVICES)
def test_changed_owned_inode_keeps_all_guards_before_release(unit):
    system, transaction = held_system()
    system.guards[unit] = dataclasses.replace(system.guards[unit], inode=100)
    with pytest.raises(guard.GuardError, match='OWNERSHIP'):
        transaction.verify_held()
    assert len(system.guards) == 4


@pytest.mark.parametrize('unit', guard.UNITS)
def test_unapproved_installer_fragment_change_is_never_accepted(unit):
    system, transaction = held_system()
    originals = dict(system.fragments)
    system.fragments[unit] = 'f' * 64
    with pytest.raises(guard.GuardError, match='FRAGMENT'):
        transaction.verify_held(originals)
    assert len(system.guards) == 4


def test_hostile_reload_reenable_does_not_release_and_restore_is_explicitly_unqualified():
    system, transaction = held_system()
    system.fragments = {unit: 'f' * 64 for unit in guard.UNITS}
    for unit in guard.TIMERS:
        system.units[unit].update(UnitFileState='enabled', ActiveState='active')
    system.run('daemon-reload')
    transaction.verify_held(system.fragments)
    calls = list(system.calls)
    with pytest.raises(guard.GuardError, match='RELEASE_NOT_QUALIFIED'):
        transaction.restore(lambda: True, system.fragments)
    assert system.calls == calls and len(system.guards) == 4 and not transaction.restored
    assert system.claimed


def test_guard_must_be_persistent_across_reboot_not_under_run():
    assert guard.Systemd.guard_root == Path('/etc/systemd/system')
    assert guard.Systemd.guard_root == guard.Systemd.unit_root


def test_real_claim_persists_and_different_transaction_cannot_replay(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, 'secure_directory', lambda _: None)
    first = guard.durable_claim(tmp_path / 'ledger', 'a' * 64, '123', {'manifest': 'synthetic'})
    assert first.exists()
    with pytest.raises(FileExistsError):
        guard.durable_claim(tmp_path / 'ledger', 'a' * 64, '124', {'manifest': 'synthetic'})
    assert first.exists()


@pytest.mark.parametrize('failed_sync', range(1, 6))
def test_each_directory_sync_failure_prevents_claim_return_and_first_effect(tmp_path, monkeypatch, failed_sync):
    monkeypatch.setattr(guard, 'secure_directory', lambda _: None)
    original = guard.sync_directory
    calls = []
    def sync(path):
        calls.append(path)
        if len(calls) == failed_sync:
            raise OSError('synthetic sync failure')
        original(path)
    monkeypatch.setattr(guard, 'sync_directory', sync)
    with pytest.raises(OSError):
        guard.durable_claim(tmp_path / 'ledger', 'a' * 64, '123', {'manifest': 'synthetic'})
    assert len(calls) == failed_sync


@pytest.mark.parametrize(('namespace', 'transaction'), [('a' * 63, '123'), ('g' * 64, '123'),
                                                     ('a' * 64, '../123'), ('a' * 64, '0')])
def test_invalid_claim_identity_never_creates_namespace(tmp_path, namespace, transaction):
    with pytest.raises(guard.GuardError, match='CLAIM'):
        guard.durable_claim(tmp_path / 'ledger', namespace, transaction, {})
    assert not (tmp_path / 'ledger').exists()


def test_systemctl_empty_condition_array_is_the_only_admitted_missing_field(monkeypatch):
    system = guard.Systemd()
    data = FakeSystem().units[guard.SERVICES[0]].copy()
    data.pop('ExecCondition')
    monkeypatch.setattr(system, 'run', lambda *args: '\n'.join(k + '=' + v for k, v in data.items()))
    assert system.properties(guard.SERVICES[0])['ExecCondition'] == ''
    data.pop('ControlGroup')
    with pytest.raises(guard.GuardError, match='UNKNOWN'):
        system.properties(guard.SERVICES[0])


@pytest.mark.parametrize('unit', guard.SERVICES)
@pytest.mark.parametrize('hook', ['ExecStartPre', 'ExecStartPost', 'ExecStop', 'ExecStopPost'])
def test_lifecycle_hooks_reject_before_claim_and_cannot_run_on_skip(unit, hook):
    system = FakeSystem()
    system.units[unit][hook] = '/synthetic-marker-only'
    with pytest.raises(guard.GuardError, match='LIFECYCLE'):
        guard.TransactionGuard(system).prepare()
    assert not system.calls and not system.claimed


def test_same_invocation_controlled_sigterm_drain_is_admitted_without_hiding_failure():
    system = FakeSystem()
    unit = guard.SERVICES[0]
    system.units[unit].update(ActiveState='activating', MainPID='123', ControlGroup='/system.slice/djconnect-watchdog.service', InvocationID='a' * 32)
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    transaction.hold(system.claim)
    assert transaction.drained and system.units[unit]['ActiveState'] == 'failed'
    assert system.units[unit]['Result'] == 'signal' and system.units[unit]['ExecMainStatus'] == '15'
    assert not any(c[0] == 'reset-failed' for c in system.calls)


@pytest.mark.parametrize(('key', 'value'), [('InvocationID', 'b' * 32), ('Result', 'timeout'),
                                         ('ExecMainCode', '1'), ('ExecMainStatus', '9'), ('MainPID', '123')])
def test_failed_drain_wrong_identity_or_cause_remains_uncertain(key, value):
    system = FakeSystem()
    unit = guard.SERVICES[0]
    system.units[unit].update(ActiveState='activating', MainPID='123', InvocationID='a' * 32)
    transaction = guard.TransactionGuard(system)
    transaction.prepare()
    original = system.run
    def run(*args):
        result = original(*args)
        if args == ('stop', *guard.SERVICES):
            system.units[unit][key] = value
        return result
    system.run = run
    with pytest.raises(guard.GuardError, match='DRAIN'):
        transaction.hold(system.claim)
    assert system.claimed and len(system.guards) == 4 and not transaction.drained


def test_actual_denial_checker_does_not_accept_cli_success_alone():
    system, transaction = held_system()
    transaction.prove_denied_starts()
    first = guard.SERVICES[0]
    original = system.properties
    def properties(unit):
        data = original(unit)
        if unit == first:
            data['ExecCondition'] = data['ExecCondition'].replace('status=1', 'status=0')
        return data
    system.properties = properties
    with pytest.raises(guard.GuardError, match='START_NOT_DENIED'):
        transaction.prove_denied_starts()


def test_file_data_fsync_failure_burns_namespace_and_does_not_return_claim(tmp_path, monkeypatch):
    import os
    import stat
    monkeypatch.setattr(guard, 'secure_directory', lambda _: None)
    original = os.fsync
    def fail_file(descriptor):
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError('synthetic file data fsync failure')
        original(descriptor)
    monkeypatch.setattr(guard.os, 'fsync', fail_file)
    with pytest.raises(OSError):
        guard.durable_claim(tmp_path / 'ledger', 'a' * 64, '123', {})
    assert (tmp_path / 'ledger' / ('a' * 64)).is_dir()
    with pytest.raises(FileExistsError):
        guard.durable_claim(tmp_path / 'ledger', 'a' * 64, '124', {})


def test_no_production_guard_removal_api_exists():
    assert not hasattr(guard.Systemd, 'remove_guard')
