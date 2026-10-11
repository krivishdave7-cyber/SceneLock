import hashlib

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates


def repair_background(image, mask):
    """Fill selected RGB pixels locally. Unselected pixels and alpha stay exact."""
    import cv2

    rgba = image.convert("RGBA")
    if mask.size != rgba.size:
        raise ValueError("The selection must match the background size.")
    selection = np.asarray(mask.convert("L")) > 0
    if not selection.any():
        return rgba.copy()
    if selection.all():
        raise ValueError("Leave some background unmarked so the repair has surrounding pixels to use.")
    source = np.array(rgba, dtype=np.uint8)
    bgr = cv2.cvtColor(source[..., :3], cv2.COLOR_RGB2BGR)
    repaired = cv2.inpaint(bgr, selection.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
    repaired = cv2.cvtColor(repaired, cv2.COLOR_BGR2RGB)
    result = source.copy()
    result[..., :3][selection] = repaired[selection]
    return Image.fromarray(result)


def mark_selection(mask, event, preview_size, radius, shape, erase=False):
    """Map display coordinates to the working image; clip drags to the picture."""
    if not event:
        return None
    display_width = event.get("width") or preview_size[0]
    display_height = event.get("height") or preview_size[1]
    if display_width <= 0 or display_height <= 0:
        return None
    sx, sy = mask.width / display_width, mask.height / display_height
    updated = mask.copy()
    drawing = ImageDraw.Draw(updated)
    value = 0 if erase else 255
    if shape == "Rectangle drag":
        if not all(key in event for key in ("x1", "y1", "x2", "y2")):
            return None
        x0, x1 = sorted((event["x1"] * sx, event["x2"] * sx))
        y0, y1 = sorted((event["y1"] * sy, event["y2"] * sy))
        if x1 < 0 or y1 < 0 or x0 >= mask.width or y0 >= mask.height:
            return None
        x0, x1 = max(0, min(mask.width - 1, round(x0))), max(0, min(mask.width - 1, round(x1)))
        y0, y1 = max(0, min(mask.height - 1, round(y0))), max(0, min(mask.height - 1, round(y1)))
        drawing.rectangle((x0, y0, x1, y1), fill=value)
    else:
        if "x" not in event or "y" not in event:
            return None
        x, y = event["x"] * sx, event["y"] * sy
        if not (0 <= x < mask.width and 0 <= y < mask.height):
            return None
        rx, ry = max(1, radius * sx), max(1, radius * sy)
        drawing.ellipse((x - rx, y - ry, x + rx, y + ry), fill=value)
    return updated


def edit_background(image):
    base = image.convert("RGBA")
    base.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
    fingerprint = hashlib.sha256(str(base.size).encode() + base.tobytes()).hexdigest()[:20]
    state_key = "background_cleanup_" + fingerprint
    if state_key not in st.session_state:
        # Retain only the active background, independently of product correction.
        for key in list(st.session_state):
            if key.startswith("background_cleanup_"):
                del st.session_state[key]
        st.session_state[state_key] = {
            "image": base.copy(), "mask": Image.new("L", base.size),
            "selection_history": [], "image_history": [],
            "revision": 0, "preview": None,
        }
    state = st.session_state[state_key]

    with st.expander("Clean up background", expanded=False):
        st.write("Mark a distraction in red, preview the repair, then apply it if it looks good.")
        shape = st.radio(
            "Selection shape", ["Brush clicks", "Rectangle drag"], horizontal=True,
            key="cleanup_shape_" + fingerprint,
        )
        tool = st.radio(
            "Selection tool", ["Mark", "Unmark"], horizontal=True,
            key="cleanup_tool_" + fingerprint,
        )
        radius = st.slider(
            "Selection brush size", 3, 60, 18, key="cleanup_radius_" + fingerprint,
            disabled=shape == "Rectangle drag",
        )
        first, second = st.columns(2)
        if first.button(
            "Undo mark", disabled=not state["selection_history"],
            key="cleanup_undo_mark_" + fingerprint,
        ):
            state["mask"] = state["selection_history"].pop()
            state["preview"] = None
            state["revision"] += 1
        if second.button(
            "Clear marks", disabled=state["mask"].getbbox() is None,
            key="cleanup_clear_" + fingerprint,
        ):
            state["mask"] = Image.new("L", base.size)
            state["selection_history"] = []
            state["preview"] = None
            state["revision"] += 1

        overlay = Image.new("RGBA", base.size, (255, 55, 55, 0))
        overlay.putalpha(state["mask"].point(lambda value: round(value * 0.5)))
        marked = Image.alpha_composite(state["image"], overlay).convert("RGB")
        marked.thumbnail((600, 500), Image.Resampling.LANCZOS)
        event = streamlit_image_coordinates(
            marked, width="content", cursor="crosshair",
            click_and_drag=shape == "Rectangle drag",
            key=f"cleanup_click_{fingerprint}_{shape}_{state['revision']}",
        )
        updated_mask = mark_selection(
            state["mask"], event, marked.size, radius, shape, tool == "Unmark",
        )
        if event is not None:
            if updated_mask is not None and updated_mask.tobytes() != state["mask"].tobytes():
                state["selection_history"].append(state["mask"].copy())
                state["selection_history"] = state["selection_history"][-10:]
                state["mask"] = updated_mask
                state["preview"] = None
            # Consume even no-op clicks so a later tool change cannot replay them.
            state["revision"] += 1
            st.rerun()

        st.caption("Brush: click individual spots. Rectangle: drag from one corner to the other.")
        st.caption("Cover the distraction and its shadow, with a small margin around them.")
        selected = np.count_nonzero(np.asarray(state["mask"]))
        if selected > base.width * base.height * 0.15:
            st.warning("Large repairs can smear texture. Start with a small distraction on a simple surface.")
        if st.button(
            "Preview removal", disabled=selected == 0,
            key="cleanup_preview_" + fingerprint, type="primary",
        ):
            try:
                with st.spinner("Repairing the selected background..."):
                    state["preview"] = repair_background(state["image"], state["mask"])
            except ImportError:
                st.error("Install the updated requirements.txt, then restart the app to enable cleanup.")
            except Exception as error:
                st.error(f"Could not repair this area: {error}")

        if state["preview"] is not None:
            preview = state["preview"].copy()
            preview.thumbnail((600, 500), Image.Resampling.LANCZOS)
            st.image(preview, caption="Proposed repair — check the surface before applying.")
            apply, discard = st.columns(2)
            if apply.button("Apply removal", key="cleanup_apply_" + fingerprint):
                state["image_history"].append((state["image"].copy(), state["mask"].copy()))
                state["image_history"] = state["image_history"][-4:]
                state["image"] = state["preview"]
                state["mask"] = Image.new("L", base.size)
                state["selection_history"] = []
                state["preview"] = None
                state["revision"] += 1
                st.rerun()
            if discard.button("Discard preview", key="cleanup_discard_" + fingerprint):
                state["preview"] = None
                state["revision"] += 1
                st.rerun()

        undo, reset = st.columns(2)
        if undo.button(
            "Undo removal", disabled=not state["image_history"],
            key="cleanup_undo_image_" + fingerprint,
        ):
            state["image"], state["mask"] = state["image_history"].pop()
            state["selection_history"] = []
            state["preview"] = None
            state["revision"] += 1
            st.rerun()
        if reset.button("Reset background", key="cleanup_reset_" + fingerprint):
            state["image"] = base.copy()
            state["mask"] = Image.new("L", base.size)
            state["selection_history"] = []
            state["image_history"] = []
            state["preview"] = None
            state["revision"] += 1
            st.rerun()

        st.caption("Keeps 10 mark changes and 4 applied repairs. Edits last for this browser session.")
        st.caption("Works best on small distractions. Detailed surfaces and large objects may leave smudges.")
    return state["image"].copy()
