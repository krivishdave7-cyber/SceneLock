# SceneLock

SceneLock helps turn an ordinary product photo into a styled scene.

I built it with small online sellers in mind. The idea is simple: start with a photo of your actual product, choose a background, and adjust the result until you're happy with it.

## What you can do

- Remove a product’s background automatically.
- Fix the cutout manually with Remove and Restore controls.
- Upload a background or generate one using FLUX.1-schnell.
- Resize, rotate, and reposition the product.
- Adjust colour matching, softness, and shadows.
- Remove small distractions from a background.
- Download the finished scene or the cleaned background as a PNG.

## Getting started on Windows

Install Python 3.14, then download this repository using **Code → Download ZIP** and extract it.

Open the extracted folder in VS Code. Open a PowerShell terminal inside the folder containing `app.py`, then run:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the **Local URL** shown in the terminal. Keep the terminal running while using SceneLock.

The first product upload may take longer because the background-removal model needs to download.

### Running it again

Once installation is complete, open a terminal in the same folder and run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

To stop the app, press **Ctrl+C** in the terminal.

## Using SceneLock

### 1. Add your product

Upload a JPG or PNG. A clear photo of one opaque product against a contrasting background is a good starting point.

Check the automatic cutout. Use **Remove** to erase unwanted areas and **Restore** to bring missing parts back. Undo and reset are available if you make a mistake.

### 2. Choose your background

Upload a background or use the generation option.

You can also clean up small distractions in the background. Mark the area, preview the removal, and apply it when you're satisfied. For background cleanup alone, you can skip uploading a product.

### 3. Refine and download

Adjust the product’s size, angle, and position. Try the matching and shadow controls, then compare the result before and after matching.

Download the finished scene as a PNG. If you only cleaned a background, use **Download background**.

## How it works

The interface runs on Streamlit. Product background removal uses rembg with a pretrained U2Net model.

Pillow, NumPy, and SciPy handle image processing, matching, and composition. Background cleanup uses OpenCV’s Telea inpainting, which fills selected areas using surrounding pixels.

Optional background generation connects to a hosted FLUX.1-schnell demo through the Gradio client.

## Things to keep in mind

SceneLock is a prototype, and the results still need a human check.

- Automatic cutouts can miss edges or small product parts.
- Matching changes the product’s colour and appearance. Check colours, labels, and logos before using an image.
- Shadows are an approximation. The app does not reconstruct physical lighting or change the product’s perspective.
- Background cleanup works best on small distractions and simple surfaces. Large objects or detailed textures can leave smudges.
- Background generation requires internet access and depends on the hosted service’s quotas, queues, and availability.
- Edits are kept in the current session. Download your results before closing or restarting the app.

## Development and AI assistance

SceneLock began as a prototype before the Banana Hacks hacking window. Later work included setup and Python compatibility fixes.

ChatGPT assisted with coding and troubleshooting. The project uses existing pretrained models and open-source libraries; I did not train those models.

## Credits

Thanks to the tools and projects that made SceneLock possible:

- [Streamlit](https://streamlit.io/)
- [rembg](https://github.com/danielgatis/rembg)
- [U2Net](https://github.com/xuebinqin/U-2-Net)
- [Pillow](https://pillow.readthedocs.io/)
- [NumPy](https://numpy.org/)
- [SciPy](https://scipy.org/)
- [OpenCV](https://opencv.org/)
- [streamlit-image-coordinates](https://github.com/blackary/streamlit-image-coordinates)
- [FLUX.1-schnell by Black Forest Labs](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
- [Hosted FLUX.1-schnell demo](https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell)
- [Gradio](https://github.com/gradio-app/gradio)

Third-party tools and models retain their own licences.
