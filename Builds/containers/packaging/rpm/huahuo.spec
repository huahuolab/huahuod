%define huahuo_version %(echo $huahuo_RPM_VERSION)
%define rpm_release %(echo $RPM_RELEASE)
%define rpm_patch %(echo $RPM_PATCH)
%define _prefix /opt/ripple
Name:           huahuo
# Dashes in Version extensions must be converted to underscores
Version:        %{huahuo_version}
Release:        %{rpm_release}%{?dist}%{rpm_patch}
Summary:        huahuo daemon

License:        MIT
URL:            http://ripple.com/
Source0:        huahuo.tar.gz
Source1:        validator-keys.tar.gz

BuildRequires:  protobuf-static openssl-static cmake zlib-static ninja-build

%description
huahuo

%package devel
Summary: Files for development of applications using xrpl core library
Group: Development/Libraries
Requires: openssl-static, zlib-static

%description devel
core library for development of standalone applications that sign transactions.

%prep
%setup -c -n huahuo -a 1

%build
cd huahuo
mkdir -p bld.release
cd bld.release
cmake .. -G Ninja -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_BUILD_TYPE=Release -Dstatic=true -DCMAKE_VERBOSE_MAKEFILE=ON -Dlocal_protobuf=ON
# build VK
cd ../../validator-keys-tool
mkdir -p bld.release
cd bld.release
# Install a copy of the huahuo artifacts into a local VK build dir so that it
# can use them to build against (VK needs xrpl_core lib to build). We install
# into a local build dir instead of buildroot because we want VK to have
# relative paths embedded in debug info, otherwise check-buildroot (rpmbuild)
# will complain
mkdir xrpl_dir
DESTDIR="%{_builddir}/validator-keys-tool/bld.release/xrpl_dir"  cmake --build ../../huahuo/bld.release --target install -- -v
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%{_builddir}/validator-keys-tool/bld.release/xrpl_dir/opt/ripple -Dstatic=true -DCMAKE_VERBOSE_MAKEFILE=ON
cmake --build . --parallel -- -v

%pre
test -e /etc/pki/tls || { mkdir -p /etc/pki; ln -s /usr/lib/ssl /etc/pki/tls; }

%install
rm -rf $RPM_BUILD_ROOT
DESTDIR=$RPM_BUILD_ROOT cmake --build huahuo/bld.release --target install -- -v
install -d ${RPM_BUILD_ROOT}/etc/opt/ripple
install -d ${RPM_BUILD_ROOT}/usr/local/bin
ln -s %{_prefix}/etc/huahuo.cfg ${RPM_BUILD_ROOT}/etc/opt/ripple/huahuo.cfg
ln -s %{_prefix}/etc/validators.txt ${RPM_BUILD_ROOT}/etc/opt/ripple/validators.txt
ln -s %{_prefix}/bin/huahuo ${RPM_BUILD_ROOT}/usr/local/bin/huahuo
install -D validator-keys-tool/bld.release/validator-keys ${RPM_BUILD_ROOT}%{_bindir}/validator-keys
install -D ./huahuo/Builds/containers/shared/huahuo.service ${RPM_BUILD_ROOT}/usr/lib/systemd/system/huahuo.service
install -D ./huahuo/Builds/containers/packaging/rpm/50-huahuo.preset ${RPM_BUILD_ROOT}/usr/lib/systemd/system-preset/50-huahuo.preset
install -D ./huahuo/Builds/containers/shared/update-huahuo.sh ${RPM_BUILD_ROOT}%{_bindir}/update-huahuo.sh
install -D ./huahuo/Builds/containers/shared/update-huahuo-cron ${RPM_BUILD_ROOT}%{_prefix}/etc/update-huahuo-cron
install -D ./huahuo/Builds/containers/shared/huahuo-logrotate ${RPM_BUILD_ROOT}/etc/logrotate.d/huahuo
install -d $RPM_BUILD_ROOT/var/log/huahuo
install -d $RPM_BUILD_ROOT/var/lib/huahuo

%post
USER_NAME=huahuo
GROUP_NAME=huahuo

getent passwd $USER_NAME &>/dev/null || useradd $USER_NAME
getent group $GROUP_NAME &>/dev/null || groupadd $GROUP_NAME

chown -R $USER_NAME:$GROUP_NAME /var/log/huahuo/
chown -R $USER_NAME:$GROUP_NAME /var/lib/huahuo/
chown -R $USER_NAME:$GROUP_NAME %{_prefix}/

chmod 755 /var/log/huahuo/
chmod 755 /var/lib/huahuo/

chmod 644 %{_prefix}/etc/update-huahuo-cron
chmod 644 /etc/logrotate.d/huahuo
chown -R root:$GROUP_NAME %{_prefix}/etc/update-huahuo-cron

%files
%doc huahuo/README.md huahuo/LICENSE
%{_bindir}/huahuo
/usr/local/bin/huahuo
%{_bindir}/update-huahuo.sh
%{_prefix}/etc/update-huahuo-cron
%{_bindir}/validator-keys
%config(noreplace) %{_prefix}/etc/huahuo.cfg
%config(noreplace) /etc/opt/ripple/huahuo.cfg
%config(noreplace) %{_prefix}/etc/validators.txt
%config(noreplace) /etc/opt/ripple/validators.txt
%config(noreplace) /etc/logrotate.d/huahuo
%config(noreplace) /usr/lib/systemd/system/huahuo.service
%config(noreplace) /usr/lib/systemd/system-preset/50-huahuo.preset
%dir /var/log/huahuo/
%dir /var/lib/huahuo/

%files devel
%{_prefix}/include
%{_prefix}/lib/*.a
%{_prefix}/lib/cmake/ripple

%changelog
* Wed May 15 2019 Mike Ellery <mellery451@gmail.com>
- Make validator-keys use local huahuo build for core lib

* Wed Aug 01 2018 Mike Ellery <mellery451@gmail.com>
- add devel package for signing library

* Thu Jun 02 2016 Brandon Wilson <bwilson@ripple.com>
- Install validators.txt

