#!/usr/bin/python3
#
# Filename     : test_import_devices.py
# Description  : Tests for the LINBO group ids that import_devices.py writes
#                into the DHCP config, the link csv and the start.conf/grub
#                cfg file names.
# Date         : 20261116
#
"""
Tests for the use of getLinboGroupId() in linuxmuster_base7.cli.import_devices.

default-school output must stay byte-for-byte identical (plain group names),
every other school gets the qualified id '<school>__<group>' in the DHCP
extensions-path/nis-domain options, the start.conf/grub cfg link sources and
the start.conf.<id>/<id>.cfg files (see issue #206). getDevicesArray() is
stubbed with the rows it would return, and the LINBO directories of the
environment module are pointed to tmp_path.
"""

import io

import pytest

environment = pytest.importorskip('environment',
                                  reason='requires linuxmuster-common (environment.py) on sys.path')

from linuxmuster_base7.cli import import_devices  # noqa: E402

# rows as getDevicesArray() returns them: the hostname already carries the
# school prefix for non-default schools, the group does not
DHCP_ROWS = {
    'default-school': [['pc01', 'raum101', '00:11:22:33:44:55', '10.0.0.1', '', 'pc', '1']],
    'abc': [['abc-pc01', 'raum101', '00:11:22:33:44:56', '10.0.0.2', '', 'pc', '1']],
}
LINK_ROWS = {
    'default-school': [
        ['pc01', 'raum101', '00:11:22:33:44:55', '10.0.0.1', '1'],
        ['pc02', 'raum101', '00:11:22:33:44:57', 'DHCP', '1'],
    ],
    'abc': [
        ['abc-pc01', 'raum101', '00:11:22:33:44:56', '10.0.0.2', '1'],
        ['abc-pc02', 'win11-efi_2', 'AA:11:22:33:44:58', 'DHCP', '1'],
    ],
}


def stubDevicesArray(monkeypatch, rows):
    def getDevicesArray(fieldnrs='', subnet='', pxeflag='', school='default-school'):
        return rows[school]
    monkeypatch.setattr(import_devices, 'getDevicesArray', getDevicesArray)


@pytest.fixture
def linbodir(tmp_path, monkeypatch):
    linbo_dir = tmp_path / 'srv' / 'linbo'
    grub_dir = linbo_dir / 'boot' / 'grub'
    tpl_dir = tmp_path / 'templates'
    (grub_dir / 'hostcfg').mkdir(parents=True)
    tpl_dir.mkdir()
    # unconfigured default start.conf (no Cache) and forced netboot template
    (linbo_dir / 'start.conf').write_text('[LINBO]\nServer = 10.0.0.1\nGroup = \n')
    (tpl_dir / 'grub.cfg.forced_netboot').write_text('# forced netboot\n')
    monkeypatch.setattr(environment, 'LINBODIR', str(linbo_dir))
    monkeypatch.setattr(environment, 'LINBOGRUBDIR', str(grub_dir))
    monkeypatch.setattr(environment, 'LINBOTPLDIR', str(tpl_dir))
    return linbo_dir


def test_dhcp_default_school_unchanged(monkeypatch):
    stubDevicesArray(monkeypatch, DHCP_ROWS)
    outfile = io.StringIO()
    import_devices.processDevicesForSubnet(outfile, '10.0.0.0/24', 'default-school')
    assert outfile.getvalue() == (
        '# subnet 10.0.0.0/24\n'
        'host pc01 {\n'
        '  option host-name "pc01";\n'
        '  hardware ethernet 00:11:22:33:44:55;\n'
        '  fixed-address 10.0.0.1;\n'
        '  option extensions-path "raum101";\n'
        '  option nis-domain "raum101";\n'
        '}\n'
    )


def test_dhcp_other_school_qualified(monkeypatch):
    stubDevicesArray(monkeypatch, DHCP_ROWS)
    outfile = io.StringIO()
    import_devices.processDevicesForSubnet(outfile, '10.0.0.0/24', 'abc')
    assert outfile.getvalue() == (
        '# subnet 10.0.0.0/24\n'
        'host abc-pc01 {\n'
        '  option host-name "abc-pc01";\n'
        '  hardware ethernet 00:11:22:33:44:56;\n'
        '  fixed-address 10.0.0.2;\n'
        '  option extensions-path "abc__raum101";\n'
        '  option nis-domain "abc__raum101";\n'
        '}\n'
    )


def test_links_default_school_unchanged(monkeypatch, linbodir):
    stubDevicesArray(monkeypatch, LINK_ROWS)
    pxe_groups = import_devices.doPxeGroupsBySchool(school='default-school')
    assert pxe_groups == ['raum101']
    links = (linbodir / 'boot' / 'links' / 'default-school.csv').read_bytes().decode()
    grub_dir = environment.LINBOGRUBDIR
    assert links == (
        f'start.conf.raum101;{linbodir}/start.conf-10.0.0.1\r\n'
        f'../raum101.cfg;{grub_dir}/hostcfg/pc01.cfg\r\n'
        f'start.conf.raum101;{linbodir}/start.conf-00:11:22:33:44:57\r\n'
        f'../raum101.cfg;{grub_dir}/hostcfg/pc02.cfg\r\n'
    )


def test_links_other_school_qualified(monkeypatch, linbodir):
    stubDevicesArray(monkeypatch, LINK_ROWS)
    pxe_groups = import_devices.doPxeGroupsBySchool(school='abc')
    assert pxe_groups == ['abc__raum101', 'abc__win11-efi_2']
    links = (linbodir / 'boot' / 'links' / 'abc.csv').read_bytes().decode()
    grub_dir = environment.LINBOGRUBDIR
    assert links == (
        f'start.conf.abc__raum101;{linbodir}/start.conf-10.0.0.2\r\n'
        f'../abc__raum101.cfg;{grub_dir}/hostcfg/abc-pc01.cfg\r\n'
        f'start.conf.abc__win11-efi_2;{linbodir}/start.conf-aa:11:22:33:44:58\r\n'
        f'../abc__win11-efi_2.cfg;{grub_dir}/hostcfg/abc-pc02.cfg\r\n'
    )


@pytest.mark.parametrize('school, group_id, host', [
    ('default-school', 'raum101', 'pc01'),
    ('abc', 'abc__raum101', 'abc-pc01'),
])
def test_startconf_grubcfg_and_links(monkeypatch, linbodir, school, group_id, host):
    stubDevicesArray(monkeypatch, LINK_ROWS)
    versionfile = linbodir / 'linbo-version'
    versionfile.write_text('LINBO 4.3.12: Codename\n')
    monkeypatch.setattr(environment, 'LINBOVERFILE', str(versionfile))
    import_devices.generateGrubConfigsForGroups(school)
    grub_dir = linbodir / 'boot' / 'grub'
    # doLinboStartconf()/doGrubCfg() create the files under the group id ...
    assert (linbodir / ('start.conf.' + group_id)).is_file()
    assert (grub_dir / (group_id + '.cfg')).is_file()
    # ... and doAllGroupLinks() points the host links at them
    assert (linbodir / ('start.conf-' + LINK_ROWS[school][0][3])).resolve() == \
        (linbodir / ('start.conf.' + group_id)).resolve()
    assert (grub_dir / 'hostcfg' / (host + '.cfg')).resolve() == \
        (grub_dir / (group_id + '.cfg')).resolve()


# --- migration of existing installations (issue #206) ---------------------

PLAIN_STARTCONF = '[LINBO]\nServer = 10.0.0.1\nCache = /dev/sda4\nGroup=raum101\n'
MANAGED = '# managed by linuxmuster\n'


def writeLegacyLinks(linbodir, school, groups):
    links_dir = linbodir / 'boot' / 'links'
    links_dir.mkdir(parents=True, exist_ok=True)
    rows = ''.join('start.conf.%s;%s/start.conf-10.0.0.%d\r\n' % (g, linbodir, i + 2)
                   for i, g in enumerate(groups))
    (links_dir / (school + '.csv')).write_text(rows)


def runImport(monkeypatch, linbodir, school, rows=None):
    stubDevicesArray(monkeypatch, rows or LINK_ROWS)
    versionfile = linbodir / 'linbo-version'
    versionfile.write_text('LINBO 4.3.12: Codename\n')
    monkeypatch.setattr(environment, 'LINBOVERFILE', str(versionfile))
    monkeypatch.setattr(environment, 'MANAGEDSTR', MANAGED.strip())
    import_devices.generateGrubConfigsForGroups(school)


def test_migration_copies_start_conf_and_sets_group(monkeypatch, linbodir):
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF)
    writeLegacyLinks(linbodir, 'abc', ['raum101'])
    runImport(monkeypatch, linbodir, 'abc')
    migrated = (linbodir / 'start.conf.abc__raum101').read_text()
    assert migrated.count('Group') == 1
    assert 'Group = abc__raum101\n' in migrated
    assert 'Cache = /dev/sda4\n' in migrated
    # the plain file stays behind untouched
    assert (linbodir / 'start.conf.raum101').read_text() == PLAIN_STARTCONF


def test_migration_only_for_groups_the_school_used_before(monkeypatch, linbodir):
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF)
    (linbodir / 'start.conf.win11-efi_2').write_text(PLAIN_STARTCONF.replace('raum101', 'win11-efi_2'))
    writeLegacyLinks(linbodir, 'abc', ['raum101'])
    runImport(monkeypatch, linbodir, 'abc')
    # win11-efi_2 is new for school abc: it gets the unconfigured template,
    # not the copy of a plain group another school may own
    new_group = (linbodir / 'start.conf.abc__win11-efi_2').read_text()
    assert new_group == (linbodir / 'start.conf').read_text()


def test_migration_without_legacy_links_uses_the_template(monkeypatch, linbodir):
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF)
    runImport(monkeypatch, linbodir, 'abc')
    assert (linbodir / 'start.conf.abc__raum101').read_text() == \
        (linbodir / 'start.conf').read_text()


def test_migration_never_overwrites_a_qualified_file(monkeypatch, linbodir):
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF)
    (linbodir / 'start.conf.abc__raum101').write_text('[LINBO]\nGroup = abc__raum101\nCache = /dev/sdb1\n')
    writeLegacyLinks(linbodir, 'abc', ['raum101'])
    runImport(monkeypatch, linbodir, 'abc')
    assert 'Cache = /dev/sdb1\n' in (linbodir / 'start.conf.abc__raum101').read_text()


def test_migration_is_idempotent(monkeypatch, linbodir):
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF)
    writeLegacyLinks(linbodir, 'abc', ['raum101'])
    runImport(monkeypatch, linbodir, 'abc')
    first = (linbodir / 'start.conf.abc__raum101').read_text()
    # the second run reads the csv the first one wrote (qualified names)
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF + 'Autostart = yes\n')
    runImport(monkeypatch, linbodir, 'abc')
    assert (linbodir / 'start.conf.abc__raum101').read_text() == first


def test_migration_copies_an_unmanaged_grub_cfg(monkeypatch, linbodir):
    grub_dir = linbodir / 'boot' / 'grub'
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF)
    (grub_dir / 'raum101.cfg').write_text('# hand written\nmenuentry x {}\n')
    writeLegacyLinks(linbodir, 'abc', ['raum101'])
    runImport(monkeypatch, linbodir, 'abc')
    assert (grub_dir / 'abc__raum101.cfg').read_text() == '# hand written\nmenuentry x {}\n'


def test_migration_does_not_copy_a_managed_grub_cfg(monkeypatch, linbodir):
    grub_dir = linbodir / 'boot' / 'grub'
    # no Cache in the start.conf: the cfg is the forced netboot template
    (linbodir / 'start.conf.raum101').write_text('[LINBO]\nServer = 10.0.0.1\nGroup=raum101\n')
    (grub_dir / 'raum101.cfg').write_text(MANAGED + 'menuentry old {}\n')
    writeLegacyLinks(linbodir, 'abc', ['raum101'])
    runImport(monkeypatch, linbodir, 'abc')
    # regenerated instead of copied
    assert (grub_dir / 'abc__raum101.cfg').read_text() == '# forced netboot\n'


def test_default_school_is_not_migrated(monkeypatch, linbodir):
    (linbodir / 'start.conf.raum101').write_text(PLAIN_STARTCONF)
    writeLegacyLinks(linbodir, 'default-school', ['raum101'])
    runImport(monkeypatch, linbodir, 'default-school')
    assert (linbodir / 'start.conf.raum101').read_text() == PLAIN_STARTCONF
    assert not list(linbodir.glob('start.conf.*__*'))


def test_read_legacy_link_groups_ignores_qualified_and_foreign_rows(linbodir):
    links_dir = linbodir / 'boot' / 'links'
    links_dir.mkdir(parents=True)
    (links_dir / 'abc.csv').write_text(
        'start.conf.raum101;/srv/linbo/start.conf-10.0.0.2\r\n'
        '../raum101.cfg;/srv/linbo/boot/grub/hostcfg/abc-pc01.cfg\r\n'
        'start.conf.abc__win11;/srv/linbo/start.conf-10.0.0.3\r\n')
    assert import_devices.readLegacyLinkGroups('abc') == {'raum101'}
    assert import_devices.readLegacyLinkGroups('default-school') == set()
    assert import_devices.readLegacyLinkGroups('other') == set()
