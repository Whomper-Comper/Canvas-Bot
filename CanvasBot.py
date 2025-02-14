import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image
import os
import io
from datetime import datetime, timedelta

# Determine the base directory and persistent canvas file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANVAS_FILE = os.path.join(BASE_DIR, "canvas.png")

# Define canvas dimensions
GRID_WIDTH, GRID_HEIGHT = 71, 95  # Logical grid size
PIXEL_SIZE = 10  # Each logical pixel is drawn as 10x10
CANVAS_WIDTH, CANVAS_HEIGHT = GRID_WIDTH * PIXEL_SIZE, GRID_HEIGHT * PIXEL_SIZE

# Load existing canvas or create a new white one if it doesn't exist
if os.path.exists(CANVAS_FILE):
    canvas = Image.open(CANVAS_FILE).convert("RGB")
else:
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
    canvas.save(CANVAS_FILE)

# Define 16 allowed colors
ALLOWED_COLORS = {
    "red": (255, 0, 0),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "indigo": (75, 0, 130),
    "violet": (238, 130, 238),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "lime": (0, 255, 0),
    "purple": (128, 0, 128),
    "gold": (255, 215, 0)
}

# Create color choices for the command
COLOR_CHOICES = [
    app_commands.Choice(name=color, value=color)
    for color in sorted(ALLOWED_COLORS.keys())
]

# Whitelist: user IDs that bypass the cooldown
WHITELIST = {1284967683246264443} #it's a me

# Cooldown period (5 minutes)
COOLDOWN_DURATION = timedelta(minutes=5)
user_last_usage = {}

# Set up bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="draw", description="Draw a pixel on the canvas at coordinates (x, y)")
@app_commands.describe(
    x="Column (0-94)",
    y="Row (0-70)"
)
@app_commands.choices(color=COLOR_CHOICES)
async def draw(interaction: discord.Interaction, x: int, y: int, color: str):
    # Validate coordinates
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
        await interaction.response.send_message(f"Coordinates out of bounds. Use values between 0-94 for x and 0-70 for y.", ephemeral=True)
        return

    # Validate color
    color_key = color.lower()
    if color_key not in ALLOWED_COLORS:
        available = ", ".join(ALLOWED_COLORS.keys())
        await interaction.response.send_message(f"Invalid color. Choose one of: {available}.", ephemeral=True)
        return

    user_id = interaction.user.id
    current_time = datetime.now()
    
    if user_id not in WHITELIST:
        last_used = user_last_usage.get(user_id)
        if last_used and (current_time - last_used) < COOLDOWN_DURATION:
            remaining = COOLDOWN_DURATION - (current_time - last_used)
            remaining_seconds = int(remaining.total_seconds())
            await interaction.response.send_message(f"You must wait {remaining_seconds} more seconds before drawing again.", ephemeral=True)
            return

    user_last_usage[user_id] = current_time

    # Calculate pixel position in the scaled canvas
    pixel_x = x * PIXEL_SIZE
    pixel_y = y * PIXEL_SIZE
    chosen_color = ALLOWED_COLORS[color_key]

    # Draw a PIXEL_SIZE x PIXEL_SIZE block
    for dx in range(PIXEL_SIZE):
        for dy in range(PIXEL_SIZE):
            canvas.putpixel((pixel_x + dx, pixel_y + dy), chosen_color)

    # Save the updated canvas
    canvas.save(CANVAS_FILE)

    # Send the updated image
    with io.BytesIO() as image_binary:
        canvas.save(image_binary, 'PNG')
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename="canvas.png")
        await interaction.response.send_message(file=file)

@bot.tree.command(name="canvas", description="Show the current canvas")
async def canvas_cmd(interaction: discord.Interaction):
    with io.BytesIO() as image_binary:
        canvas.save(image_binary, 'PNG')
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename="canvas.png")
        await interaction.response.send_message(file=file)
# Replace "YOUR_BOT_TOKEN" with your actual bot token.
bot.run("YOUR_BOT_TOKEN")