Name:           depman
Version:        0.1.2
Release:        1%{?dist}
Summary:        One window for every package manager on your Linux system

License:        MIT
URL:            https://github.com/YasharSL/Depman
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  make
Requires:       python3 >= 3.12
Requires:       python3-gobject
Requires:       gobject-introspection
Requires:       gtk4
Requires:       libadwaita >= 1.5
Requires:       polkit

%description
DepMan detects the package managers installed on the system (DNF, Zypper, APT,
Pacman, Snap, Flatpak, pip, pipx, npm and Cargo) and lists what each one
installed in its own tab. Each package has a page showing its version,
description and where its files live, with buttons to uninstall, purge, update
or reinstall it.

%prep
%autosetup -n Depman-%{version}

%build

%install
%make_install PREFIX=%{_prefix}

%files
%license LICENSE
%doc README.md
%{_bindir}/depman
%{_datadir}/depman/
%{_datadir}/applications/io.github.depman.DepMan.desktop

%changelog
* Thu Oct 08 2026 YSLdev <yashar.soleimani.dev@gmail.com> - 0.1.2-1
- Packages are now built and published by GitHub Actions

* Thu Oct 08 2026 YSLdev <yashar.soleimani.dev@gmail.com> - 0.1.0-1
- Initial release
