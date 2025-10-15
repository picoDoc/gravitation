# AGENTS instructions

## Project overview

- Gravitation remake targeting realistic gravity + thrust physics, rendered in portrait
- Designed to run both on desktop pygame and the web through pygbag; the asyncio loop in [`main.main()`](main.py:11) must remain non-blocking to keep browser builds responsive
- The game is primarily played via pygbag, deployed on the web, and on mobile phones with a paired bluetooth controller (hence the screen aspect ratio)

## Architecture highlights

- [`main.py`](main.py) initializes pygame/joystick subsystems, hydrates scoreboard data once per boot, then defers all per-frame work to [`GameStateManager`](src/game_state_manager.py).
- Rendering, input, and timing are delegated to focused modules: [`GameRenderer`](src/game_renderer.py:3), [`InputManager`](src/input_manager.py:4), [`GameTimer`](src/timer.py:3), plus entity composition helpers in [`entity.py`](src/entity.py).
- All gameplay state transitions (menu ↔ playing, resets, completion) live inside [`GameStateManager.switch_to_menu()`](src/game_state_manager.py), [`GameStateManager.switch_to_playing()`](src/game_state_manager.py), and [`GameStateManager.update_gameplay()`](src/game_state_manager.py).

## Running code

The project uses a python venv in the directory venv. Before running any python commands or installing packages, activate it:

```
source venv/bin/activate && python --version
```

For browser-friendly builds launch through pygbag (desktop pygame also works, but pygbag is the primary target):

```
pygbag main.py
```

## Development notes

- Keep coroutine-friendly yields (`await asyncio.sleep(0)`) inside [`main.main()`](main.py) so pygbag can pump the event loop.
- Remote scoreboard/ghost APIs may fail; [`GameStateManager.initialize_scoreboard()`](src/game_state_manager.py) already falls back to empty data, so preserve that resilience.
- Portrait resolution (1440×2560) is important for playing on mobile; updating it requires auditing level art and HUD positions.
- Avoid blocking network or file system calls outside the provided [`RequestHandler`](src/custom_request.py:192) to maintain WASM compatibility.

## Running tests

Currently there are no automated tests for the project. Do not attempt to run test suites; the user will validate gameplay manually in pygame/pygbag builds.