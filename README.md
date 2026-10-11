# SceneLock — background cleanup and matching update

A Python/Streamlit prototype for creating product scenes while using the product from the original photograph.

## Update your existing project on Windows

1. Stop Streamlit by pressing Ctrl+C in its terminal.
2. Make a backup copy of your existing Python files.
3. Copy all seven Python files and requirements.txt from this folder into your existing SceneLOK project folder. Replace the same-named Python files. Keep your .venv folder and photographs. The new background_cleanup.py must sit beside app.py. This update also includes harmonize.py and the matching controls.
4. Run these commands in the terminal inside your existing project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Use Python 3.12 (rembg currently supports 3.11–3.13).

## Remove distractions from the background

After selecting a background, open **Clean up background** in step 2. Choose **Mark** and click spots using **Brush clicks**, or drag a box using **Rectangle drag**. **Unmark**, **Undo mark** and **Clear marks** fix the selection. Cover the object and its shadow with a small margin.

Click **Preview removal**, inspect the repaired surface, then choose **Apply removal** or **Discard preview**. Only applying updates the composed scene and final download. **Undo removal** keeps four repairs; **Reset background** restores the selected source. Switching to a different background starts fresh. Product mask edits stay separate. The working scene is capped at 1200 pixels on its longest side.

For cleanup only, skip the product upload: upload your photograph as the background in step 2, apply a repair, then click **Download background** beneath its preview. It saves a PNG of the current background with applied repairs, without a product or red selection overlay. Pending previews are not included. Undo and Reset also update this download. Background generation is available without a product, but only the Generate button makes that service call.

This is local OpenCV Telea inpainting, not generative object reconstruction. It uses surrounding pixels and is most suitable for small distractions on simple surfaces. Large objects, lettering, structured wood grain and detailed surfaces can smear. Unselected background pixels and alpha remain unchanged. It operates before the separate product layer is composited, so cleanup does not erase that product.

## Match the product to its scene

The sidebar's **Match nearby background** option samples visible pixels around the placed cutout. It applies bounded exposure and ambient colour adjustments and optionally adds a little grain if the surrounding photo is noisier. Photo softness is adjustable; keep it low for lettering. A contact shadow and optional direction help seat the product on the surface.

- Start with Match strength 45, Photo softness 0.3 and Match photo grain enabled.
- Compare **Before / after matching**. Both views use the same placement and shadow.
- Uncheck matching or set Match strength to 0 to preserve the placed cutout's RGB exactly.
- Matching starts from the original placed cutout on every rerun; it never compounds previous corrections.
- It runs locally with NumPy/SciPy/Pillow, makes no generation calls and needs no extra package.
- It preserves the alpha silhouette and does not redraw the product. When enabled, it changes colour/texture; it is not pixel-preserving and is not a physical relighting or perspective model. A tabletop's colour is only a rough clue to ambient light. Reflective, transparent and strongly mismatched lighting may still look wrong.

## Cutout correction controls

The page follows three steps: add a product, choose a scene, then finish and download. Upload a picture is selected by default, so you can use the app without calling the background generator. The finished picture has separate scene, comparison and cutout views. Reset placement restores the starting size, angle, position and shadow without changing the cutout or background.

After uploading a product, open **Fix the product cutout**.

- Red tint means that area will be removed.
- **Remove** erases a circular patch from the mask.
- **Restore** brings a circular patch back from the original photograph.
- **Undo** remembers the last ten clicks.
- **Reset cutout** restores the AI's initial cleaned mask.
- Use a small brush near edges. Click spots; continuous drag painting is not implemented.

Corrections update the final composition and download. They persist across sliders and background changes in the current browser session. Uploading another product starts a new correction history. A new session or server restart clears them.

## Existing controls

AI background generation, uploaded backgrounds, size, rotation, position, shadow strength and PNG export are included. Changing placement or the cutout reuses the existing background. Only the Generate button calls the hosted image model.

## Scope and honest claims

- Start with one opaque product. The initial automatic mask keeps its largest connected component; use Restore if this removes a genuine disconnected product part.
- Product RGB values begin with the input photo. Scene matching modifies their appearance when enabled. Scaling and rotation resample pixels, and partially transparent edges blend with the new background. Do not claim the result is pixel-for-pixel identical to the source.
- The mask can be wrong; manual review is essential to product completeness.
- Shadows are a visual approximation, not physical lighting reconstruction.
- The public FLUX demo has free quotas, queues and changing availability. It is a prototype dependency, not guaranteed production hosting. Upload a previously generated background if it is unavailable.
- Code syntax, matching invariants, alpha preservation, deterministic grain, placement/shadow behaviour, real OpenCV small-object repair, unselected-pixel preservation, simulated brush/rectangle selection, preview/apply/discard/undo/reset and download flow were checked offline. Live generation and real browser selection gestures still need testing on your computer.

## Credits

- Streamlit: https://streamlit.io/
- rembg and its U2Net model integration: https://github.com/danielgatis/rembg
- U2Net: https://github.com/xuebinqin/U-2-Net
- Pillow: https://pillow.readthedocs.io/
- NumPy and SciPy: https://numpy.org/ and https://scipy.org/
- OpenCV local inpainting: https://docs.opencv.org/4.x/df/d3d/tutorial_py_inpainting.html
- streamlit-image-coordinates by blackary: https://github.com/blackary/streamlit-image-coordinates
- FLUX.1-schnell by Black Forest Labs: https://huggingface.co/black-forest-labs/FLUX.1-schnell
- Hosted demo used by background.py: https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell
- Gradio Python client: https://github.com/gradio-app/gradio

This was made with the help of Chat-GPT.according to complaince of the hackathon guidelines.
