# Installing and distributing DepMan

## Releases

Pushing a `vX.Y.Z` tag makes GitHub Actions (`.github/workflows/release.yml`) run the checks,
build the `.deb`, `.rpm` and Arch package, and publish them as a GitHub Release. The tag must
match `version` in `pyproject.toml`, or the release job stops.

## Install on your own machine

Build the package and install it with apt, which pulls in GTK and libadwaita:

```sh
sudo apt install debhelper dh-python pybuild-plugin-pyproject python3-all python3-setuptools python3-pytest
make deb                                   # writes dist/depman_0.1.1_all.deb
sudo apt install ./dist/depman_0.1.1_all.deb
depman                                     # also appears in the app menu as "DepMan"
```

Remove it with `sudo apt remove depman`.

Without building a package you can run it straight from the folder with `python3 -m depman`.

## Before you publish

1. **Create a GPG key** (`gpg --full-generate-key`). Every apt repository is signed.
2. **Check the maintainer** name and e-mail in `debian/control` and `debian/changelog`; they
   become public.
3. For each release, add an entry to `debian/changelog` (`dch -v 0.2.0`), bump `version` in
   `pyproject.toml`, `packaging/arch/PKGBUILD` and `packaging/fedora/depman.spec`, and push a
   `vX.Y.Z` git tag: the Arch and Fedora recipes download that tag from GitHub.

## Option A: Launchpad PPA (easiest for Ubuntu users)

Launchpad builds and hosts the package; users add it with one command.

1. Create a Launchpad account, upload your GPG key, sign the Ubuntu Code of Conduct, and
   create a PPA named `depman`.
2. Build a signed source package and upload it:

   ```sh
   sudo apt install devscripts dput
   debuild -S -sa                          # creates ../depman_0.1.1_source.changes
   dput ppa:YOUR_LAUNCHPAD_ID/depman ../depman_0.1.1_source.changes
   ```

   Run this from a copy of the repo on a Linux filesystem, not from a Windows-mounted folder.
3. The release name in `debian/changelog` (`noble`) decides which Ubuntu release it is built
   for. To publish for another release, upload again with that name and a version such as
   `0.1.1~oracular1`.
4. Users install with:

   ```sh
   sudo add-apt-repository ppa:YOUR_LAUNCHPAD_ID/depman
   sudo apt install depman
   ```

## Option B: your own apt repository (works on Debian too)

An apt repository is a folder of static files, so any web host works, including GitHub Pages.

1. Create the repository with `reprepro`:

   ```sh
   sudo apt install reprepro
   mkdir -p repo/conf
   cat > repo/conf/distributions <<'EOF'
   Codename: stable
   Components: main
   Architectures: amd64 arm64
   SignWith: YOUR_GPG_KEY_ID
   EOF
   reprepro -b repo includedeb stable dist/depman_0.1.1_all.deb
   gpg --export YOUR_GPG_KEY_ID > repo/depman.gpg
   ```

2. Upload the `repo/` folder (without `conf/` and `db/`) to your host.
3. Users install with:

   ```sh
   sudo curl -fsSL https://YOUR_HOST/depman.gpg -o /etc/apt/keyrings/depman.gpg
   echo "deb [signed-by=/etc/apt/keyrings/depman.gpg] https://YOUR_HOST stable main" \
     | sudo tee /etc/apt/sources.list.d/depman.list
   sudo apt update && sudo apt install depman
   ```

For a new release, run `reprepro includedeb` again with the new `.deb` and re-upload.

## The official Ubuntu and Debian archives

Getting into the default repositories means going through Debian: file an "Intent to Package"
bug, meet Debian policy (manual page, a real license, a `debian/watch` file), and find a
Debian Developer to sponsor the upload. Ubuntu then imports it from Debian. This takes weeks
to months; start with a PPA.
