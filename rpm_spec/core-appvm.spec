#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2010  Joanna Rutkowska <joanna@invisiblethingslab.com>
# Copyright (C) 2010  Rafal Wojtczuk  <rafal@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

%{!?version: %define version %(cat version_vm)}

Name:		qubes-core-appvm
Version:	%{version}
Release:	1
Summary:	The Qubes core files for AppVM

Group:		Qubes
Vendor:		Invisible Things Lab
License:	GPL
URL:		http://www.qubes-os.org
Requires:	/usr/bin/xenstore-read
Provides:   qubes-core-vm

%define _builddir %(pwd)/appvm

%define kde_service_dir /usr/share/kde4/services/ServiceMenus 

%description
The Qubes core files for installation inside a Qubes AppVM.

%pre

mkdir -p $RPM_BUILD_ROOT/var/lib/qubes
[ -e $RPM_BUILD_ROOT/etc/fstab ] && mv $RPM_BUILD_ROOT/etc/fstab $RPM_BUILD_ROOT/var/lib/qubes/fstab.orig

%build
make clean all

%install

mkdir -p $RPM_BUILD_ROOT/etc
cp fstab $RPM_BUILD_ROOT/etc/fstab
mkdir -p $RPM_BUILD_ROOT/etc/init.d
cp qubes_core $RPM_BUILD_ROOT/etc/init.d/
mkdir -p $RPM_BUILD_ROOT/var/lib/qubes
mkdir -p $RPM_BUILD_ROOT/usr/bin
cp qubes_add_pendrive_script qubes_penctl qvm-copy-to-vm  qvm-copy-to-vm.kde $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/%{kde_service_dir}
cp qvm-copy.desktop $RPM_BUILD_ROOT/%{kde_service_dir}
mkdir -p $RPM_BUILD_ROOT/etc/udev/rules.d
cp qubes.rules $RPM_BUILD_ROOT/etc/udev/rules.d
mkdir -p $RPM_BUILD_ROOT/etc/sysconfig
cp iptables $RPM_BUILD_ROOT/etc/sysconfig/
mkdir -p $RPM_BUILD_ROOT/mnt/incoming
mkdir -p $RPM_BUILD_ROOT/mnt/outgoing
mkdir -p $RPM_BUILD_ROOT/mnt/removable
mkdir -p $RPM_BUILD_ROOT/etc/yum.repos.d
cp ../common/qubes.repo $RPM_BUILD_ROOT/etc/yum.repos.d
mkdir -p $RPM_BUILD_ROOT/sbin   
cp ../common/qubes_serial_login $RPM_BUILD_ROOT/sbin
mkdir -p $RPM_BUILD_ROOT/etc
cp ../common/qubes_eventd_serial $RPM_BUILD_ROOT/etc/

%triggerin -- initscripts
cp /etc/qubes_eventd_serial /etc/event.d/serial


%post

usermod -L root
usermod -L user
if ! [ -f /var/lib/qubes/serial.orig ] ; then
	cp /etc/event.d/serial /var/lib/qubes/serial.orig
fi

if [ "$1" !=  1 ] ; then
# do this whole %post thing only when updating for the first time...
exit 0
fi

echo "--> Disabling SELinux..."
sed -e s/^SELINUX=.*$/SELINUX=disabled/ </etc/selinux/config >/etc/selinux/config.processed
mv /etc/selinux/config.processed /etc/selinux/config
setenforce 0

echo "--> Turning off unnecessary services..."
# FIXME: perhaps there is more elegant way to do this? 
for f in /etc/init.d/*
do
        srv=`basename $f`
        [ $srv = 'functions' ] && continue
        [ $srv = 'killall' ] && continue
        [ $srv = 'halt' ] && continue
        chkconfig $srv off
done

echo "--> Enabling essential services..."
chkconfig rsyslog on
chkconfig haldaemon on
chkconfig messagebus on
chkconfig cups on
chkconfig iptables on
chkconfig --add qubes_core || echo "WARNING: Cannot add service qubes_core!"
chkconfig qubes_core on || echo "WARNING: Cannot enable service qubes_core!"


sed -i s/^id:.:initdefault:/id:3:initdefault:/ /etc/inittab

# Remove most of the udev scripts to speed up the VM boot time
# Just leave the xen* scripts, that are needed if this VM was
# ever used as a net backend (e.g. as a VPN domain in the future)
echo "--> Removing unnecessary udev scripts..."
mkdir -p /var/lib/qubes/removed-udev-scripts
for f in /etc/udev/rules.d/*
do
    if [ $(basename $f) == "xen-backend.rules" ] ; then
        continue
    fi

    if [ $(basename $f) == "xend.rules" ] ; then
        continue
    fi

    if [ $(basename $f) == "qubes.rules" ] ; then
        continue
    fi

    if [ $(basename $f) == "90-hal.rules" ] ; then
        continue
    fi


    mv $f /var/lib/qubes/removed-udev-scripts/
done
mkdir -p /rw
#rm -f /etc/mtab
echo "--> Removing HWADDR setting from /etc/sysconfig/network-scripts/ifcfg-eth0"
mv /etc/sysconfig/network-scripts/ifcfg-eth0 /etc/sysconfig/network-scripts/ifcfg-eth0.orig
grep -v HWADDR /etc/sysconfig/network-scripts/ifcfg-eth0.orig > /etc/sysconfig/network-scripts/ifcfg-eth0

%preun
if [ "$1" = 0 ] ; then
    # no more packages left
    chkconfig qubes_core off
    mv /var/lib/qubes/fstab.orig /etc/fstab
    mv /var/lib/qubes/removed-udev-scripts/* /etc/udev/rules.d/
    mv /var/lib/qubes/serial.orig /etc/event.d
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
/etc/fstab
/etc/init.d/qubes_core
/usr/bin/qvm-copy-to-vm
/usr/bin/qvm-copy-to-vm.kde
%{kde_service_dir}/qvm-copy.desktop
%attr(4755,root,root) /usr/bin/qubes_penctl
/usr/bin/qubes_add_pendrive_script
/etc/udev/rules.d/qubes.rules
/etc/sysconfig/iptables
%dir /var/lib/qubes
%dir /mnt/incoming
%dir /mnt/outgoing
%dir /mnt/removable
/etc/yum.repos.d/qubes.repo
/sbin/qubes_serial_login
/etc/qubes_eventd_serial