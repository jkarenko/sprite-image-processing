import subprocess
from PIL import Image
import argparse
from wand.image import Image as WandImage
from pathlib import Path

TOPAZ_PHOTO_CLI = "/Applications/Topaz\ Photo\ AI.app/Contents/MacOS/Topaz\ Photo\ AI --bit-depth 8 --quality 85 --overwrite --cli"
SCALE_FACTOR = 6

# Parse the command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--image-path", type=str, required=True)
parser.add_argument("--sprite-dimensions", type=str, required=True)
parser.add_argument("--upscale", action="store_true", default=True)
parser.add_argument("--stitch", action="store_true", default=True)
parser.add_argument("--filter", type=str, nargs='+', default=None)
parser.add_argument("--filter-params", type=str, nargs='+', default=None)

args = parser.parse_args()

sprite_width, sprite_height = map(int, args.sprite_dimensions.split("x"))

filter_params = {
    "radius": 2,
    "sigma": 1.5,
    "lower_percent": 10,
    "upper_percent": 90,
    "amount": 1.5,
    "threshold": 0.05,
}

if args.filter_params:
    for param in args.filter_params:
        key, value = param.split("=")
        filter_params[key] = float(value)

# Calculate the number of sprites horizontally and vertically
sprite_sheet = Image.open(args.image_path)
sprites_x = sprite_sheet.width // sprite_width
sprites_y = sprite_sheet.height // sprite_height
image_name = Path(args.image_path).stem
image_format = Path(args.image_path).suffix

# Define the directory to store individual sprites
output_dir = Path("sprites") / image_name
output_dir_originals = output_dir / "originals"
output_dir_upscaled = output_dir / "upscaled"
output_dir_filtered = output_dir / "filtered"

# Create the directories if they don't exist
for output_dir in [output_dir_originals, output_dir_upscaled, output_dir_filtered]:
    output_dir.mkdir(parents=True, exist_ok=True)

# Split the sprite sheet into individual sprites
for y in range(sprites_y):
    for x in range(sprites_x):
        left = x * sprite_width
        upper = y * sprite_height
        right = left + sprite_width
        lower = upper + sprite_height
        sprite = sprite_sheet.crop((left, upper, right, lower))
        sprite.save(output_dir_originals / f"img_{y}_{x}{image_format}")


# Apply a filter to the individual sprites
def apply_filters():
    if not args.filter:
        return
    radius = filter_params.get("radius")
    sigma = filter_params.get("sigma")
    lower_percent = filter_params.get("lower_percent")
    upper_percent = filter_params.get("upper_percent")
    amount = filter_params.get("amount")
    threshold = filter_params.get("threshold")
    
    dir = output_dir_upscaled if any(
        output_dir_upscaled.iterdir()) else output_dir_originals

    for sprite_path in dir.glob(f"*{image_format}"):
        with WandImage(filename=str(sprite_path)) as img:
            filter_functions = {
                "charcoal": lambda img: img.charcoal(radius=radius, sigma=sigma),
                "oil_paint": lambda img: img.oil_paint(radius=radius, sigma=sigma),
                "edge": lambda img: img.edge(radius=radius),
                "canny": lambda img: img.canny(radius=radius, sigma=sigma, lower_percent=lower_percent, upper_percent=upper_percent),
                "kuwahara": lambda img: img.kuwahara(radius=radius, sigma=sigma),
                "smoothen": lambda img: (img.despeckle(), img.kuwahara(radius=radius, sigma=sigma))[1],
                "negate": lambda img: img.negate(),
            }
            print(f"Applying filters {args.filter} to {sprite_path}")

            for filter in args.filter:
                if filter in filter_functions:
                    filter_functions[filter](img)
            img.save(filename=str(output_dir_filtered / sprite_path.name))


# Upscale the individual sprites with Topaz Photo AI
def apply_upscale():
    if not args.upscale or any(output_dir_upscaled.iterdir()):
        return
    print(f"Upscaling {output_dir_originals}")
    upscale_command = f"{TOPAZ_PHOTO_CLI} '{output_dir_originals}' --output '{output_dir_upscaled}'"
    print(f"Running: {upscale_command}")
    subprocess.run(upscale_command, shell=True)


# Stitch the upscaled sprites into a sprite sheet
def create_new_sheet():
    if not args.stitch:
        return
    dir = output_dir_filtered if any(output_dir_filtered.iterdir()) else output_dir_upscaled if any(
        output_dir_upscaled.iterdir()) else output_dir_originals
    print(f"Creating new sprite sheet from {dir}")
    upscaled_sprite_sheet = Image.new(
        "RGB", (sprite_width * SCALE_FACTOR * sprites_x, sprite_height * SCALE_FACTOR * sprites_y))
    for y in range(sprites_y):
        for x in range(sprites_x):
            sprite = Image.open(f"{dir}/img_{y}_{x}{image_format}")
            upscaled_sprite_sheet.paste(
                sprite, (x * sprite_width * SCALE_FACTOR, y * sprite_height * SCALE_FACTOR))

    upscaled_sprite_sheet.save(
        f"{Path('sprites') / image_name / image_name}_upscaled{image_format}", quality=65)
    print(f"New sprite sheet saved to {Path('sprites') / image_name / image_name}_upscaled{image_format}")


apply_upscale()
apply_filters()
create_new_sheet()
