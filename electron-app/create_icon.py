"""
Create a simple icon.ico file for the Electron app.
This is a placeholder - replace with your actual icon.
"""

from PIL import Image, ImageDraw
import os

def create_icon():
    """Create a simple icon.ico file"""
    # Create a 256x256 icon
    size = 256
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "P" logo
    draw.ellipse([20, 20, size-20, size-20], fill='#764ba2', outline='white', width=10)
    draw.text((size//2, size//2), 'P', fill='white', anchor='mm', font_size=120)
    
    # Save as ICO
    icon_path = os.path.join(os.path.dirname(__file__), 'build', 'icon.ico')
    os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    
    # Create multiple sizes for ICO
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    for s in sizes:
        resized = img.resize(s, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Save as multi-resolution ICO
    img.save(icon_path, format='ICO', sizes=[(img.width, img.height) for img in images])
    print(f"Created icon at: {icon_path}")
    return icon_path

if __name__ == "__main__":
    try:
        create_icon()
    except ImportError:
        print("PIL/Pillow not installed. Creating simple placeholder...")
        # Fallback: create a simple text file as placeholder
        icon_path = os.path.join(os.path.dirname(__file__), 'build', 'icon.ico')
        os.makedirs(os.path.dirname(icon_path), exist_ok=True)
        with open(icon_path, 'wb') as f:
            # Minimal ICO header (will need proper icon later)
            f.write(b'\x00\x00\x01\x00')  # ICO signature
        print(f"Created placeholder at: {icon_path}")
        print("Note: Replace with actual icon.ico file for production")

