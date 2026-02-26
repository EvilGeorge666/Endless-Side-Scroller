# Endless-Side-Scroller

A Python endless 2D side-scroller where you control a cowboy riding a horse through the desert.

## Gameplay
- Enemies emerge from the **right side** of the screen and move left.
- Move the **mouse** to aim the cowboy's gun.
- **Left click** to fire.
- Every enemy has **1 health** (one hit removes it).
- Survive and stack up your score.

## Run the game
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python game.py
```

## Controls
- **Mouse move**: Aim
- **Left mouse button**: Shoot
- **Esc** or window close button: Quit

## Tech notes
- The game now uses Python's built-in **Tkinter** for rendering and input.
- No third-party packages (including pygame) are required.
