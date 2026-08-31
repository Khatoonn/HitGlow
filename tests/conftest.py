import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Un mode video (meme headless, via le driver dummy) doit etre pose pour
# que Surface.convert_alpha() fonctionne dans le code teste (labels de
# render_frame, overlay de calibration).
import pygame  # noqa: E402

pygame.display.init()
pygame.display.set_mode((1, 1))
