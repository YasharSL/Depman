# Deepening log

Backlog of deepening opportunities. Status: `open`, `done`, `rejected`.

| ID | Module | Files | Strength | Friction | Deletion test | Win | Status |
|---|---|---|---|---|---|---|---|
| DL-01 | `depman.ui` package icon lookup | `ui/manager_page.py`, `ui/details_page.py` | Worth exploring | Both files repeat the "theme icon named after the package, else generic" lookup and its fallback constant. | Deleting either copy forces the other to be shared: the knowledge concentrates. | Locality: one place to later add real app icons (desktop files, flatpak exports). | open |
