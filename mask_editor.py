import streamlit as st
from PIL import Image, ImageOps
from streamlit_image_coordinates import streamlit_image_coordinates

from product import apply_brush, make_cutout


def edit_cutout(original, base_mask, photo_id):
    # Each uploaded photo gets independent edits.
    state_key = "cutout_edits_" + photo_id
    if state_key not in st.session_state:
        # Keep only the active photo's mask history to avoid accumulating memory.
        for old_key in list(st.session_state):
            if old_key.startswith("cutout_edits_"):
                del st.session_state[old_key]
        st.session_state[state_key] = {
            "mask": base_mask.copy(), "history": [], "revision": 0,
        }
    state = st.session_state[state_key]

    with st.expander("Fix the product cutout", expanded=False):
        st.write(
            "Red areas will be removed. Choose Restore or Remove, "
            "then click the photograph to change a circular patch."
        )
        mode = st.radio(
            "Tool", ["Remove", "Restore"], horizontal=True,
            key="brush_mode_" + photo_id,
        )
        radius = st.slider(
            "Brush radius", 3, 50, 12, key="brush_radius_" + photo_id,
            help="Measured in pixels on the editor preview. Use a small brush near edges.",
        )
        left, right = st.columns(2)
        if left.button("Undo", disabled=not state["history"], key="undo_" + photo_id):
            state["mask"] = state["history"].pop()
            state["revision"] += 1
        if right.button("Reset cutout", key="reset_" + photo_id):
            state["mask"] = base_mask.copy()
            state["history"] = []
            state["revision"] += 1

        # Show the original photo underneath a red tint on excluded areas.
        overlay = Image.new("RGBA", original.size, (255, 40, 40, 0))
        overlay.putalpha(ImageOps.invert(state["mask"]).point(lambda value: round(value * 0.45)))
        preview = Image.alpha_composite(original.convert("RGBA"), overlay).convert("RGB")
        preview.thumbnail((600, 650), Image.Resampling.LANCZOS)

        click = streamlit_image_coordinates(
            preview, width=preview.width, cursor="crosshair",
            key=f"mask_click_{photo_id}_{state['revision']}",
        )
        if click is not None and "x" in click and "y" in click:
            # The component reports displayed dimensions; account for browser scaling.
            display_width = click.get("width") or preview.width
            display_height = click.get("height") or preview.height
            x = round(click["x"] * original.width / display_width)
            y = round(click["y"] * original.height / display_height)
            actual_radius = max(1, round(radius * original.width / display_width))
            state["history"].append(state["mask"].copy())
            state["history"] = state["history"][-10:]
            state["mask"] = apply_brush(
                state["mask"], x, y, actual_radius, mode == "Restore",
            )
            # A fresh widget key prevents the same click being applied on slider reruns.
            state["revision"] += 1
            st.rerun()

        st.caption("Click individual spots. This first editor does not paint continuously while dragging.")
        st.caption("Undo remembers your last 10 clicks. Edits last for this browser session.")

    return make_cutout(original, state["mask"])
