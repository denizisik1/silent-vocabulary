A Qt desktop app for vocabulary practice with IPA pronunciation.

Words come from CSV lists and are shown a few at a time at random, with
selectable fields: article, word, meaning, pronunciation, example, translation,
plural. Missing pronunciations can be retrieved from a configurable dictionary
source, with a backup source and a headless-browser fallback when a plain HTTP
request is not enough. A daemon can show a new word on a fixed interval through
desktop notifications, with a tray icon for control while the window is closed.

German is the only language with shipped lists so far. The language selector
disables entries whose CSV files do not exist yet.

Linux and Python 3 only. Notifications need `notify-send` or a Freedesktop
notification service on the session bus.

##### Install and run

```bash
git clone --depth=1 git@github.com:denizisik1/silent-vocabulary.git
cd silent-vocabulary
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/init.py
```

`.env` is optional. Without it the values from `.env.example` apply as code
defaults; copy the file and edit it to change vocabulary paths, HTTP headers,
dictionary URLs or startup defaults. A missing `.env`, or one whose keys and
values diverge from `.env.example`, is reported at startup as a warning and a
notification, not as an error.

##### Desktop launcher (GNOME / app switcher icon)

```bash
chmod +x assets/silent-vocabulary.sh
mkdir -p ~/.local/bin ~/.local/share/applications ~/.local/share/icons/hicolor/256x256/apps
ln -sf "$(pwd)/assets/silent-vocabulary.sh" ~/.local/bin/silent-vocabulary
ln -sf "$(pwd)/assets/silent-vocabulary.desktop" ~/.local/share/applications/silent-vocabulary.desktop
ln -sf "$(pwd)/assets/icon.png" ~/.local/share/icons/hicolor/256x256/apps/silent-vocabulary.png
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```

`~/.local/bin` has to be on your `PATH`. The launcher uses `.venv/bin/python`
when that interpreter exists and falls back to `python3`.

##### Run (already installed)

```bash
cd silent-vocabulary
[[ -d .venv ]] || python3 -m venv .venv
source .venv/bin/activate
python3 src/init.py
```

##### Remove

```bash
cd ..
rm -rf silent-vocabulary
rm -f "$HOME/.local/bin/silent-vocabulary"
rm -f "$HOME/.local/share/applications/silent-vocabulary.desktop"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/silent-vocabulary.png"
rm -rf "$HOME/.config/silent-vocabulary"
rm -rf "${XDG_DATA_HOME:-$HOME/.local/share}/silent-vocabulary"
```

##### Files

Shipped vocabulary under `vocabulary/` is read-only, optionally enforced with
file permissions from the settings tab. Added and removed words are kept as a
per-language overlay of `additions.csv` and `removals.csv` under
`${XDG_DATA_HOME:-$HOME/.local/share}/silent-vocabulary/`, so the original CSVs
are never rewritten; the overlay can be exported as a zip archive. Window size,
theme, zoom, daemon interval and source settings live in
`~/.config/silent-vocabulary/silent-vocabulary.toml`.

##### Development

```bash
make x
```

Runs black, flake8, pylint, mypy, bandit and pytest. Individual targets are in
the `Makefile`.
