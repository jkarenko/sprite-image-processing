# Sprite Image Processing

A Python script that processes sprite images using Topaz Photo AI and ImageMagick.

## Installation

1. Clone the repository
2. Navigate to the project directory: `cd sprite-image-processing`
3. Install Poetry if you haven't already: `pip install poetry`
4. Install the project dependencies: `poetry install`

## Requirements

1. Topaz Photo AI
2. ImageMagick ^7
3. Python ^3.11
4. Poetry

## Usage

To use the script, you need:
1. An image file containing the sprites
2. The dimensions of the sprites in the image
3. (optional) The filters to apply to the image

```bash
python main.py --image-path ~/Downloads/qfg3.jpeg --sprite-dimensions 320x200 --filter smoothen
```
