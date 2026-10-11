from PIL import Image
from gradio_client import Client


def generate_background(prompt):
    # Hosted public demo: availability and daily quotas apply.
    client = Client("black-forest-labs/FLUX.1-schnell")
    output = client.predict(prompt, 42, True, 768, 1024, 4, api_name="/infer")
    with Image.open(output[0]) as picture:
        return picture.convert("RGBA")
