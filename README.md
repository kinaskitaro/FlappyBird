# FlappyBird Game

A Python-based Flappy Bird clone built with Pygame.

## Features

- **Smooth Gameplay**: 60 FPS with fluid animations
- **Proper Scoring**: Score increases when passing pipes (not time-based)
- **High Score Persistence**: Saves your best score to a file
- **Multiple Input Methods**: Jump with spacebar or mouse click
- **Bird Animation**: Wing flapping animation with rotation based on movement
- **Sound Effects**: Jump, collision, and scoring sounds
- **Game States**: Menu, active gameplay, and game over screens
- **Error Handling**: Graceful handling of missing assets

## Requirements

- Python 3.x
- Pygame

Install Pygame:
```bash
pip install pygame
```

## How to Play

1. Run the game:
```bash
python game.py
```

2. **Controls**:
   - Press **SPACE** or **Click** to start
   - Press **SPACE** or **Click** to make the bird jump/flap
   - Avoid hitting the pipes and the ground
   - Pass through pipes to score points

3. **Game Over**:
   - Press **SPACE** or **Click** to restart and try again

## Game Configuration

You can adjust game settings in the `game.py` file under the Configuration section:

- Screen dimensions
- Physics (gravity, jump strength, pipe speed)
- Spawn rates
- Audio settings
- And more...

## File Structure

```
FlappyBird/
├── game.py              # Main game file
├── 04B_19.TTF           # Game font
├── assets/              # Game images
│   ├── background-night.png
│   ├── floor.png
│   ├── gameover.png
│   ├── message.png
│   ├── pipe-green.png
│   └── yellowbird-*.png
├── sound/               # Sound effects
│   ├── sfx_hit.wav
│   ├── sfx_point.wav
│   └── sfx_wing.wav
├── high_score.json      # Auto-generated high score file
└── README.md            # This file
```

## Credits

Original Flappy Bird game by Dong Nguyen.
This is an educational implementation for learning game development with Python.
