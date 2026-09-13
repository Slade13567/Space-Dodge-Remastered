# Space Dodge

A small 2D arcade dodging game I made in 10th grade with Python and Pygame.
This repository is here to preserve the project and make it easier to run.
I figured something I spent this much time making deserved a proper record.

## Overview

Pilot a ship through a fullscreen scrolling space field, avoid incoming
missiles and laser hazards, and survive until the mission is complete. The
game tracks progress as a percentage and gives the player a limited set of
heart-based lives.

## Features

- Fullscreen Pygame arcade game with a scrolling background
- Missiles arriving from several directions, with changing waves over time
- Warning-and-fire laser hazards
- Pixel-mask collision checks, lives, explosions, and game-over/win screens
- Progress percentage, sound effects, and music
- Pause, restart, and quit controls

## Controls

| Input | Action |
| --- | --- |
| `Space` | Start the game; pause/resume during play; hold to restart after game over or completion |
| Arrow keys or `W` `A` `S` `D` | Move the ship |
| Hold `Esc` | Quit from the menu or pause screen |

## Running the Game

From the project folder on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

If PowerShell blocks the activation script, use Command Prompt and run
`.venv\Scripts\activate.bat` instead. The game opens in fullscreen mode.

## What I Learned

This was my first ever programming project.

I had been learning Python for a few years before this, mostly by solving
programming and algorithmic problems. For around three years, I was mainly
focused on getting comfortable with Python syntax and building up my
algorithmic thinking. I hadn't really made anything of my own yet.

Space Dodge was the first time I finally took all of that and tried to build
something from scratch.

It was also my first real introduction to things that don't usually come up
when you're just solving programming problems, like game loops, keyboard
input, timers, collision detection, loading images and sounds, and keeping
track of different parts of a game's state.

The code definitely shows that it was my first project, but that's also why
I've kept it. It's a pretty good snapshot of the point where I stopped just
solving problems and started actually making things.

## Original Project

Space Dodge was created in 10th grade. It is being preserved and documented,
not rewritten into a modern game-engine project. The rough edges are part of
the record.

## Credits

Known music credit: **"Dick Dastardly Richardson Theme" by Lchavasse**, listed
on [Newgrounds](https://www.newgrounds.com/audio/listen/1091203) and used in
the Geometry Dash level *Dastardly*. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the available licensing
context and uncertainty around bundled media.

## License

The original source code is licensed under the MIT License. Third-party media
may have separate rights and is not automatically covered; see
[LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

