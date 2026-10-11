import hashlib
import io

import streamlit as st
from PIL import Image, ImageOps
from rembg import new_session, remove

from background import generate_background
from background_cleanup import edit_background
from compose import compose_scene, place_product
from harmonize import match_product_to_scene
from mask_editor import edit_cutout
from product import clean_mask, read_photo


st.set_page_config(page_title="SceneLock | Product scenes", page_icon="📷", layout="wide")
st.markdown(
    """
    <style>
    .sl-hero {
        background: linear-gradient(120deg, #163c36, #24594c);
        border-radius: 20px; padding: 30px 32px; margin-bottom: 24px;
        color: #ffffff;
    }
    .sl-hero h1 { color: #ffffff; font-size: clamp(2rem, 4vw, 3rem);
        padding: 0 0 8px; margin: 0; line-height: 1.15; }
    .sl-hero p { color: #e4eee8; margin: 0; max-width: 680px; }
    .sl-brand { color: #ccebb5; font-size: 0.82rem; font-weight: 700;
        letter-spacing: 0.12em; margin-bottom: 12px; }
    @media (max-width: 640px) { .sl-hero { padding: 24px 20px; } }
    </style>
    <div class="sl-hero">
        <div class="sl-brand">SCENELOCK · PRODUCT PHOTO STUDIO</div>
        <h1>Give your product a new scene.</h1>
        <p>Keep the product from your original photo. Choose a background,
        refine the edges, and create a picture ready to share.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_model():
    return new_session("u2net")


@st.cache_data(max_entries=3)
def prepare_product(photo_bytes):
    original = read_photo(photo_bytes)
    mask = remove(original, session=load_model(), only_mask=True).convert("L")
    return original, clean_mask(mask)


PLACEMENT_DEFAULTS = {
    "product_size": 80,
    "product_angle": 0,
    "product_horizontal": 0,
    "product_vertical": 0,
    "shadow_strength": 25,
}


def reset_placement():
    for key, value in PLACEMENT_DEFAULTS.items():
        st.session_state[key] = value


with st.sidebar:
    st.title("SceneLock")
    st.caption("Your product photo studio")
    st.markdown("**Your workflow**\n\n1. Upload a product\n2. Choose a background\n3. Adjust and download")
    st.divider()

original = None
cutout = None
chosen_background = None
product_column, background_column = st.columns(2, gap="large")

with product_column:
    with st.container(border=True):
        st.subheader("1 ·  Add your product")
        st.caption("Start with one clearly visible product. JPG, JPEG and PNG work.")
        st.caption("You can skip this step if you only want to clean and download a background.")
        product_file = st.file_uploader(
            "Product photograph", type=["jpg", "jpeg", "png"], key="product",
        )
        if product_file is not None:
            try:
                photo_bytes = product_file.getvalue()
                with st.spinner("Finding your product..."):
                    original, base_mask = prepare_product(photo_bytes)
                photo_id = hashlib.sha256(photo_bytes).hexdigest()[:20]
                cutout = edit_cutout(original, base_mask, photo_id)
                if cutout is None:
                    st.warning("The cutout is empty. Open the editor and choose Restore or Reset cutout.")
                else:
                    cutout_preview = cutout.copy()
                    cutout_preview.thumbnail((500, 340), Image.Resampling.LANCZOS)
                    st.image(cutout_preview, caption="Your product cutout — check its edges.")
            except Exception as error:
                st.error(f"Could not prepare the product: {error}")
                st.stop()
        else:
            st.info("Choose your product photo to start. A clear photo makes the cutout easier to refine.")

with background_column:
    with st.container(border=True):
        st.subheader("2 · Choose a scene")
        st.caption("Upload a saved background, or create one with AI when generation is available.")
        background_mode = st.radio(
            "Background source", ["Upload a picture", "Generate with AI"],
            horizontal=True, key="background_mode",
        )
        if background_mode == "Upload a picture":
            uploaded_background = st.file_uploader(
                "Background photograph", type=["jpg", "jpeg", "png"], key="background",
            )
            st.caption("Tip: an empty desk or plain surface gives your product room to stand out.")
            if uploaded_background is not None:
                try:
                    with Image.open(uploaded_background) as image:
                        chosen_background = ImageOps.exif_transpose(image).convert("RGBA")
                except Exception as error:
                    st.error(f"Could not open the background: {error}")
        else:
            style = st.selectbox(
                "Scene style", ["Minimal studio", "Warm wooden table", "Colourful backdrop"],
            )
            extra_details = st.text_input(
                "Extra details (optional)", placeholder="For example: pastel blue, soft daylight",
            )
            styles = {
                "Minimal studio": "An empty smooth pale beige photography surface.",
                "Warm wooden table": "An empty light oak tabletop with subtle wood grain.",
                "Colourful backdrop": "An empty pastel blue matte photography surface.",
            }
            prompt = (
                styles[style] + " Photographed directly from above. Professional product photography, "
                "soft even daylight. The centre is completely empty and clear. "
                "No products, notebooks, objects, people or text. " + extra_details
            )
            if st.button("Generate background", type="primary"):
                try:
                    with st.spinner("Creating your scene. There may be a queue..."):
                        generated = generate_background(prompt)
                    st.session_state["ai_background"] = generated
                    st.session_state["generated_style"] = style
                except Exception as error:
                    st.error(f"Background generation failed: {error}")
                    st.info("Select Upload a picture to continue with a saved background.")
            st.caption("Generation can have usage limits. Changing placement or fixing the cutout reuses your scene.")
            if "ai_background" in st.session_state:
                chosen_background = st.session_state["ai_background"].copy()
                st.caption(
                    "Current scene: " + st.session_state.get("generated_style", "Saved generated scene")
                    + ". Press Generate background to apply new choices."
                )
        if chosen_background is not None:
            chosen_background = edit_background(chosen_background)
            background_preview = chosen_background.copy()
            background_preview.thumbnail((500, 340), Image.Resampling.LANCZOS)
            st.image(background_preview, caption="Your selected background")
            background_data = io.BytesIO()
            chosen_background.save(background_data, format="PNG")
            st.download_button(
                "Download background", background_data.getvalue(), "scenelock-background.png", "image/png",
                key="download_background",
            )
            st.caption("Includes applied repairs. Preview a removal, then press Apply removal to include it in this download.")

st.subheader("3 · Finish your picture")
if cutout is not None and chosen_background is not None:
    background = chosen_background.copy()
    background.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
    for key, value in PLACEMENT_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
    with st.sidebar:
        st.subheader("Product placement")
        st.button("Reset placement", on_click=reset_placement)
        size = st.slider("Size (%)", 10, 150, key="product_size")
        angle = st.slider("Rotation (degrees)", -180, 180, key="product_angle")
        horizontal = st.slider("Move left / right", -100, 100, key="product_horizontal")
        vertical = st.slider("Move up / down", -100, 100, key="product_vertical")
        shadow_strength = st.slider("Shadow strength", 0, 70, key="shadow_strength")
        st.caption("Position 0 centres your product. Size 100 fits it into the scene before rotation.")

        st.divider()
        st.subheader("Blend into the scene")
        matching = st.checkbox("Match nearby background", value=True, key="scene_matching")
        match_strength = st.slider(
            "Match strength", 0, 100, 45, key="match_strength", disabled=not matching,
            help="Small lighting and colour adjustments. Lower this to keep the source appearance closer.",
        )
        with st.expander("Fine-tune the blend"):
            softness = st.slider(
                "Photo softness", 0.0, 1.5, 0.3, 0.1, key="photo_softness", disabled=not matching,
                help="A small amount can match a softer background. Keep it low for clear logos.",
            )
            match_grain = st.checkbox("Match photo grain", value=True, key="match_grain", disabled=not matching)
            shadow_direction = st.selectbox(
                "Shadow direction", ["Under product", "Down-right", "Down-left", "Up-right", "Up-left"],
                key="shadow_direction",
            )

    layer, clipped = place_product(background, cutout, size, angle, horizontal, vertical)
    matched_layer, match_info = match_product_to_scene(
        background, layer, match_strength if matching else 0, softness, match_grain,
    )
    result = compose_scene(background, matched_layer, shadow_strength, shadow_direction)
    if matching and match_strength > 0 and not match_info["sampled"]:
        st.info("There is too little visible background nearby to estimate a match. Try making the product smaller.")
    if clipped:
        st.warning("Part of the product is outside the picture. Make it smaller or move it towards the centre.")
    st.caption("Use the controls in the sidebar to adjust your product.")
    finished, comparison, matching_view, inspection = st.tabs(
        ["Finished scene", "Compare with original", "Before / after matching", "Check cutout"]
    )
    with finished:
        result_preview = result.copy()
        result_preview.thumbnail((1000, 700), Image.Resampling.LANCZOS)
        st.image(result_preview, caption="Your finished scene")
    with comparison:
        before, after = st.columns(2)
        with before:
            original_preview = original.copy()
            original_preview.thumbnail((600, 650), Image.Resampling.LANCZOS)
            st.image(original_preview, caption="Original photograph")
        with after:
            comparison_preview = result.copy()
            comparison_preview.thumbnail((600, 650), Image.Resampling.LANCZOS)
            st.image(comparison_preview, caption="New scene")
    with matching_view:
        unadjusted = compose_scene(background, layer, shadow_strength, shadow_direction)
        unadjusted.thumbnail((600, 650), Image.Resampling.LANCZOS)
        adjusted_preview = result.copy()
        adjusted_preview.thumbnail((600, 650), Image.Resampling.LANCZOS)
        before_match, after_match = st.columns(2)
        with before_match:
            st.image(unadjusted, caption="Before colour and texture matching")
        with after_match:
            st.image(adjusted_preview, caption="With your current matching settings")
        st.caption("Both views use the same position and shadow. Change Match strength to compare the product adjustment.")
    with inspection:
        st.image(cutout_preview, caption="Missing a piece? Open Fix the product cutout in step 1.")
        st.write("Check the product's writing, logo and edges before downloading.")
    if matching and match_strength > 0:
        st.caption("Scene matching adjusts the original product's colour and texture. Review logos and colour before exporting.")
    else:
        st.caption("Scene matching is off. The product uses your original photograph; scaling and rotation can soften details.")
    download_data = io.BytesIO()
    result.save(download_data, format="PNG")
    st.download_button(
        "Download finished picture", download_data.getvalue(), "scenelock-result.png", "image/png",
        type="primary",
    )
    st.caption(f"PNG · {result.width} × {result.height} pixels")
else:
    with st.container(border=True):
        if original is None and chosen_background is None:
            st.info("Add a product and a background above. Your finished picture will appear here.")
        elif original is None and chosen_background is not None:
            st.success("Your background is ready to download in step 2. You can also add a product in step 1 to create a scene.")
        elif cutout is None:
            st.info("Add your product photo, or restore an empty cutout, to create your scene.")
        else:
            st.info("Choose a background in step 2. Then you can position your product and download the picture.")
    with st.sidebar:
        st.info("Placement controls appear when your product and background are ready.")
