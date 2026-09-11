# Inchworm Simulation Setup Guide

This guide is for setting up and running the simulation from scratch, based on:
- the original `block_simulation/README.md`
- the fixes and run steps validated in this session

---

## Quick start (copy/paste)

```powershell
cd C:\Users\<USERNAME>\Documents\GitHub\SMAC7.0
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install ursina numpy colorama pyserial
cd .\inchworm_control
python -m block_simulation.sim
```

---

## Requirements

- Python **3.12+** (3.12 recommended in the original README)
- A virtual environment (`.venv`)
- Required packages:
  - `ursina`
  - `numpy`
  - `colorama`
  - `pyserial`

---

## 1) Create and activate a virtual environment (Windows / PowerShell)

From repo root (`SMAC7.0`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## 2) Install dependencies

Use `pip install ...` commands directly:

```powershell
pip install --upgrade pip
pip install ursina
pip install numpy
pip install colorama
pip install pyserial
```

You can also do it in one line:

```powershell
pip install ursina numpy colorama pyserial
```

---

## 3) Run the simulation (important)

Change into `inchworm_control` and run as a module:

```powershell
cd C:\Users\<USERNAME>\Documents\GitHub\SMAC7.0\inchworm_control
python -m block_simulation.sim
```

Do **not** run by direct file path (`python ...\sim.py`), because package imports can fail in this project layout.

---

## 4) First-use workflow in the simulation

From the original README flow:

1. Build a structure in the world.
2. Press `L` to identify known substructures.
3. Press `P` once to calculate path + generate/overwrite `steps.txt`.
4. Press `N` to move the inchworm step-by-step.

> Note from original README: press `L` then `P` for intended behavior.

---

## 5) Controls (from original README)

- `WASD`: move
- Mouse: camera rotation
- `Space`: jump
- Left click: place block
- Right click: remove block
- `L`: identify known substructures
- `P`: calculate full path/steps
- `N`: move inchworm to next block
- `G`: generate pyramid
- `F`: toggle flying
- `Q` / `E`: fly up/down
- `1` `2` `3` `4`: switch camera viewpoints
- `ESC`: exit simulation

---

## 6) Troubleshooting (including issues hit in this session)

### `ModuleNotFoundError` for local modules (`search`, `inchworm_control`, etc.)
- Run from `...\inchworm_control`
- Use:
  ```powershell
  python -m block_simulation.sim
  ```

### `ModuleNotFoundError` for `numpy`, `colorama`, or `serial`
- Install missing packages in the active venv:
  ```powershell
  pip install numpy colorama pyserial
  ```

### Ursina color API error (`module 'ursina.color' has no attribute 'color'`)
- Updated  to use `color.hsv(...)` in `sim.py`.


---

## 7) Code changes made during setup

These are the repo-specific fixes that were needed to get the project running reliably in this environment:

- Fixed package import structure in `block_simulation` so modules import correctly when launched with `python -m block_simulation.sim`.
- Converted internal imports from plain module names to relative package imports (for example: `from .search import search`, `from .config import *`, `from .sim_data import SimData`).
- Removed the side-effect import from `block_simulation/__init__.py` that was calling `BP.blueprint()` during import.
- Installed missing Python dependencies in the venv: `numpy`, `colorama`, `pyserial`.
- Patched Ursina compatibility in `sim.py` by replacing the deprecated call:
  ```python
  color.color(0, 0, random.uniform(0.9, 1))
  ```
  with:
  ```python
  color.hsv(0, 0, random.uniform(0.9, 1))
  ```
- Confirmed the simulation starts successfully once launched from the correct working directory with the module entry point.

---

## 8) Summary

This repository is a Python + Ursina simulation project. The simplest setup is:

1. Create `.venv`
2. Activate it
3. Install packages with `pip install ursina numpy colorama pyserial`
4. Run from `inchworm_control` with:
   ```powershell
   python -m block_simulation.sim
   ```

This is the exact working path that was validated in this session.

