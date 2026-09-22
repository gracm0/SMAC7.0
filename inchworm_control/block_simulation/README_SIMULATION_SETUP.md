# Inchworm Simulation Setup Guide

This guide is for setting up and running the simulation from scratch, based on:
- the original `block_simulation/README.md`
- the fixes and run steps validated in this session

---

## Quick start (copy/paste)

```powershell
cd C:\Users\<USERNAME>\Documents\GitHub\SMAC7.0
pip install --upgrade pip
pip install ursina numpy colorama pyserial
python -m inchworm_control.block_simulation.sim
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

## 1) Create a virtual environment in VS Code

In VS Code:

1. Press `Ctrl+Shift+P` to open the Command Palette.
2. Select `Python: Select Interpreter`.
3. Select `+ Create Virtual Environment`.
4. Choose `Venv`, then choose the Python interpreter to use.

VS Code creates and selects the `.venv` environment for the workspace.

If PowerShell activation is blocked when opening a new terminal:

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

From the repository root, run the fully qualified module:

```powershell
cd C:\Users\<USERNAME>\Documents\GitHub\SMAC7.0
python -m inchworm_control.block_simulation.sim
```

The shorter legacy form also works after changing into `inchworm_control`:

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
- `ESC`: pause simulation and release the mouse; press again while paused to exit
- Left click while paused: resume simulation

---

## 6) Troubleshooting (including issues hit in this session)

### `ModuleNotFoundError` for local modules (`search`, `inchworm_control`, etc.)
- Run from the repository root:
- Use:
  ```powershell
  python -m inchworm_control.block_simulation.sim
  ```

### `ModuleNotFoundError` for `numpy`, `colorama`, or `serial`
- Install missing packages in the active venv:
  ```powershell
  pip install numpy colorama pyserial
  ```

### Ursina color API error (`module 'ursina.color' has no attribute 'color'`)
- Updated  to use `color.hsv(...)` in `sim.py`.


---


## 7) Summary

This repository is a Python + Ursina simulation project. The simplest setup is:

1. Press `Ctrl+Shift+P` and select `Python: Select Interpreter`.
2. Select `+ Create Virtual Environment`, choose `Venv`, and select the Python interpreter.
3. Install packages with `pip install ursina numpy colorama pyserial`
4. Run from the repository root with:
   ```powershell
  python -m inchworm_control.block_simulation.sim
   ```
