#!/usr/bin/python3
#
# Filename     : test_functions_linbo.py
# Description  : Tests for the LINBO group id helper pair
#                getLinboGroupId()/splitLinboGroupId().
# Date         : 20261116
#
"""
Tests for linuxmuster_base7.functions.linbo.getLinboGroupId() and
splitLinboGroupId().

Background: on a multi-school server every school other than default-school
gets school-qualified LINBO group ids '<school>__<group>', so two schools can
use the same group name without sharing one start.conf (see issue #206 and
linuxmuster-linbo7#178). default-school keeps the plain group, so
single-school installations see no change. The helpers must round-trip, and
group names may contain '-' and a single '_' (sophomorix allows
[A-Za-z0-9_-]). The separator is '__' because the LINBO client's udhcpc
turns any DHCP nis-domain with other characters into 'bad' (linbo7#178).
"""

import pytest

pytest.importorskip('environment',
                    reason='requires linuxmuster-common (environment.py) on sys.path')

from linuxmuster_base7.functions import (  # noqa: E402
    LINBO_GROUP_SEPARATOR, getLinboGroupId, splitLinboGroupId)


@pytest.mark.parametrize('school, group, expected', [
    # default-school keeps the plain group
    ('default-school', 'raum101', 'raum101'),
    ('default-school', 'win11-efi_2', 'win11-efi_2'),
    # every other school is qualified with '__'
    ('abc', 'raum101', 'abc__raum101'),
    ('abc', 'win11-efi_2', 'abc__win11-efi_2'),
    # school names may contain '-' as well
    ('gs-nord', 'raum101', 'gs-nord__raum101'),
    ('a', 'b-x', 'a__b-x'),
    ('a-b', 'x', 'a-b__x'),
    # a single '_' in the group stays allowed
    ('abc', 'win11_edu', 'abc__win11_edu'),
])
def test_get_linbo_group_id(school, group, expected):
    assert getLinboGroupId(school, group) == expected


@pytest.mark.parametrize('group_id, expected', [
    # no '__' means default-school
    ('raum101', ('default-school', 'raum101')),
    ('win11-efi_2', ('default-school', 'win11-efi_2')),
    # otherwise split on the first '__'
    ('abc__raum101', ('abc', 'raum101')),
    ('gs-nord__win11-efi_2', ('gs-nord', 'win11-efi_2')),
    ('abc__raum__101', ('abc', 'raum__101')),
    ('abc__win11_edu', ('abc', 'win11_edu')),
])
def test_split_linbo_group_id(group_id, expected):
    assert splitLinboGroupId(group_id) == expected


@pytest.mark.parametrize('school, group', [
    ('default-school', 'raum101'),
    ('default-school', 'win11-efi_2'),
    ('abc', 'raum101'),
    ('gs-nord', 'win11-efi_2'),
    ('abc', 'win11_edu'),
    # '-' in either part must not make the ids collide
    ('a', 'b-x'),
    ('a-b', 'x'),
])
def test_round_trip(school, group):
    assert splitLinboGroupId(getLinboGroupId(school, group)) == (school, group)


def test_no_collision_between_schools():
    # school 'a' + group 'b-x' and school 'a-b' + group 'x' would both be
    # 'a-b-x' with '-' as separator
    assert getLinboGroupId('a', 'b-x') != getLinboGroupId('a-b', 'x')
    # a default-school group can never look like a qualified id
    assert getLinboGroupId('default-school', 'abc-raum101') != getLinboGroupId('abc', 'raum101')


def test_separator_is_a_double_underscore():
    assert LINBO_GROUP_SEPARATOR == '__'
