## Install and run

```bash
git clone --depth=1 git@github.com:denizisik1/vipa.git
cd vipa
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/init.py
```

## Run (already installed)

```bash
cd vipa
[[ -d .venv ]] || python3 -m venv .venv
source .venv/bin/activate
python3 src/init.py
```

## Remove

```bash
cd ..
rm -rf vipa
rm -rf "$HOME/.config/vipa"
```
