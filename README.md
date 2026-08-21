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
cp .env.example .env
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
file permissions from the settings tab. Pronunciations that ship with the
project live next to the word lists in `vocabulary/pronunciations/<language>.csv`
and are merged onto them at load time, so a fresh clone already has IPA without
asking any dictionary; `<language>-failures.csv` next to it lists the words no
source could answer. Added and removed words are kept as a
per-language overlay of `additions.csv` and `removals.csv` under
`${XDG_DATA_HOME:-$HOME/.local/share}/silent-vocabulary/`, so the original CSVs
are never rewritten; the overlay can be exported as a zip archive. Window size,
theme, zoom, daemon interval and source settings live in
`~/.config/silent-vocabulary/silent-vocabulary.toml`.

An entry is identified by its word, its word class and its article, so
homographs such as `der Weg` and `weg`, or `der See` and `die See`, are kept as
separate entries. When a typed word matches more than one of them, removing a
word or retrieving a pronunciation asks which entry is meant instead of
guessing.

##### Filling a language with pronunciations

The shipped pronunciation file is written once per language by a developer, not
by users. The Fetch IPA button in the app keeps writing single pronunciations to
the user overlay as before.

```bash
python3 src/fetch_pronunciations.py german --dry-run
python3 src/fetch_pronunciations.py german --delay 3 --limit 200
python3 src/fetch_pronunciations.py german --browser-fallback --fast
```

`german` is the language to fill. Flags:

- `--dry-run` lists the words that still need IPA and exits.
- `--delay` seconds to wait between words, jittered by a quarter (default: 3).
- `--limit` fetch at most this many words, then stop.
- `--strategy` `primary_first` or `basic_first`. Defaults to the strategy saved
  by the app.
- `--browser-fallback` allow the browser when a source refuses the plain
  request.
- `--headless` keep the browser window hidden.
- `--fast` give the browser a few seconds to find IPA, then move on, and skip
  the extra wait after a miss.
- `--retry-failed` try words already marked as failed, instead of skipping them.
- `--max-consecutive-failures` stop when this many words fail in a row
  (default: 10).

Every word that still lacks a pronunciation is fetched one at a time. Between
every word there is a jittered pause of about `--delay` seconds; that pause
stays in the same range for the whole run. After a miss, without `--fast`, an
extra wait is added: `--delay` doubled for each miss in a row (6s, 12s, 24s,
... with the default delay), never more than five minutes. A success resets
that streak, so the next miss starts at the short extra wait again. `--fast`
skips the extra wait and keeps only the usual gap between words. A success is
written to `vocabulary/pronunciations/german.csv` immediately, so the run can be
interrupted at any point; starting it again picks up the words that are still
missing. Ten failures in a row stop the run, which is the sign of a source that
has started refusing requests: wait a while, then continue. Thousands of words
take hours, so run it in a terminal you can leave alone, in a few sessions if
you prefer, and commit the file when you are happy with the diff.

Every attempt says what it did, in the terminal and in the results box of the
app, so a word that comes back empty can be told apart from a source that turned
the request away. Each word starts a block of its own, a marker tells the lines
apart, and a terminal that accepts colour gets one:

```
[143/3734] Abbau
    plain request answered 216682 bytes for https://en.pons.com/.../Abbau
  - primary/basic read the page but it holds no phonetics
  ~ primary/browser skipped, the page was read already and holds no IPA
  - backup/basic failed: HTTP 403 for https://www.collinsdictionary.com/.../Abbau
  ~ browser started, it stays open for the rest of the run
  ~ browser ticked the Cloudflare checkbox
  + saved Abbau [ˈapˌbaʊ̯] from backup
```

A plus is a success, a minus a failure, a tilde a step worth knowing about, and
an unmarked line is detail. Piped output and `NO_COLOR` drop the colour and keep
the markers.

Plain HTTP requests are used by default and are tried before anything else.
`--browser-fallback` additionally allows the browser, but only for a source that
refused the plain request: when a page was read in full and simply holds no
pronunciation, the browser is skipped, because it would load the same page
again. One browser is started for the whole run and reused for every word after
that; it is only replaced when it stops working. The browser waits until the
page holds the pronunciation of the word that was asked for, not merely until
the HTML is large, so a shell that Collins paints in later is not mistaken for
the entry. A pronunciation that belongs to a neighbour on the same page (a
suggested word, an English translation) is ignored. `--headless` keeps its window
hidden for a run you leave alone. `--fast` gives the browser a few seconds to
find IPA and then moves on, so a source that sits on an open page does not hold
up the rest of the run, and a miss is not followed by a growing pause. The
browser timings otherwise come from the browser settings of the app.

The browser keeps its own profile under
`${XDG_DATA_HOME:-$HOME/.local/share}/silent-vocabulary/browser-profile/`, one
for bulk runs and one for the app, so a site that asks once for a Cloudflare
checkbox is answered once and its cookie carries the rest of the run and the
runs after it. A checkbox that appears anyway is ticked automatically. Delete
the folder if a profile ever gets in the way.

##### Words that no source knows

A word that fails is written to `vocabulary/pronunciations/<language>-failures.csv`
with the reason, and left out of every later run, so a long run never waits on
the same hopeless words twice. The file is part of the repository: delete a line
to try that word again, empty the file to try all of them, or keep it as a record
of what has to be filled in by hand from the Vocabulary tab. `--retry-failed`
ignores the file for one run without changing it, and a word that answers later
is dropped from it automatically.

##### Development

```bash
make -f validate.mk x
```

Runs black, flake8, pylint, mypy, bandit and pytest. Individual targets are in
`validate.mk`.
