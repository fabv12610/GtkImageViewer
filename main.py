import io

import gi
import matplotlib
matplotlib.use('GTK3Agg')
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ExifTags

#Risky if it's a bomb
Image.MAX_IMAGE_PIXELS = None

GLib.set_prgname("Gtk Image Viewer")
GLib.set_application_name("Gtk Image Viewer")


class ImageEditor(Gtk.Window):
    def __init__(self):
        super().__init__(title="Python GTK3 Ultimate Image Editor")
        self.set_default_size(1024, 768)
        self.current_image = None
        self.zoom_factor = 1.0

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)

        self.create_menubar()
        self.create_toolbar()

        self.scroll_window = Gtk.ScrolledWindow()
        # Enable automatic scrollbars
        self.scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.event_box = Gtk.EventBox()

        # CRITICAL FIX: Add with viewport so panning actually moves the canvas
        self.scroll_window.add(self.event_box)

        self.image_widget = Gtk.Image()
        self.event_box.add(self.image_widget)

        self.main_box.pack_start(self.scroll_window, True, True, 0)

        # --- Dragging State Variables and Signals ---
        self.drag_in_progress = False
        self.start_x = 0
        self.start_y = 0
        self.start_h_adj = 0
        self.start_v_adj = 0

        self.event_box.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )

        self.event_box.connect("button-press-event", self.on_button_press)
        self.event_box.connect("button-release-event", self.on_button_release)
        self.event_box.connect("motion-notify-event", self.on_mouse_motion)
        # ---------------------------------------------------

    # --- UI Setup ---

    def create_menubar(self):
        menubar = Gtk.MenuBar()
        # 1. File Menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)

        for label, action in [("Open", self.on_open), ("Save", self.on_save), ("Quit", Gtk.main_quit)]:
            item = Gtk.MenuItem(label=label)
            if action != Gtk.main_quit:
                item.connect("activate", action)
            else:
                item.connect("activate", action)
            file_menu.append(item)

        # 2. View (Zoom) Menu
        view_menu = Gtk.Menu()
        view_item = Gtk.MenuItem(label="View")
        view_item.set_submenu(view_menu)

        for label, action in [("Zoom In (+20%)", self.on_zoom_in), ("Zoom Out (-20%)", self.on_zoom_out),
                              ("Actual Size (100%)", self.fit_to_window)]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", action)
            view_menu.append(item)

        # 3. Edit (Transform) Menu
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.set_submenu(edit_menu)

        for label, action in [("Rotate 90°", self.on_rotate), ("Flip Horizontal (Mirror)", self.on_mirror),
                              ("Flip Vertical", self.on_flip), ("Resize...", self.on_resize),
                              ("Crop Center 50%", self.on_crop)]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", action)
            edit_menu.append(item)

        # 4. Filter Menu
        filter_menu = Gtk.Menu()
        filter_item = Gtk.MenuItem(label="Filters")
        filter_item.set_submenu(filter_menu)

        for label, action in [("Convert to B&W", self.on_bw), ("Blur", self.on_blur), ("Sharpen", self.on_sharpen),
                              ("Find Edges", self.on_edges), ("Emboss", self.on_emboss), ("Contour", self.on_contour),
                              ("Invert Colors", self.on_invert)]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", action)
            filter_menu.append(item)

        # 5. Enhance Menu
        enhance_menu = Gtk.Menu()
        enhance_item = Gtk.MenuItem(label="Enhance")
        enhance_item.set_submenu(enhance_menu)

        for label, action in [("Brightness +20%", lambda x: self.on_enhance('brightness', 1.2)),
                              ("Brightness -20%", lambda x: self.on_enhance('brightness', 0.8)),
                              ("Contrast +20%", lambda x: self.on_enhance('contrast', 1.2)),
                              ("Contrast -20%", lambda x: self.on_enhance('contrast', 0.8)),
                              ("Color +20%", lambda x: self.on_enhance('color', 1.2)),
                              ("Color -20%", lambda x: self.on_enhance('color', 0.8))]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", action)
            enhance_menu.append(item)

        #6. Info Menu
        info_menu = Gtk.Menu()
        info_item = Gtk.MenuItem(label='Info')
        info_item.set_submenu(info_menu)

        exif_info = Gtk.MenuItem(label="Exif Info")
        exif_info.connect('activate', self.exif_info)

        hist_info = Gtk.MenuItem(label='Histogram Info')
        hist_info.connect('activate', self.histogram)

        info_menu.append(exif_info)
        info_menu.append(hist_info)

        # 7. About Menu
        about_menu = Gtk.Menu()
        about_item = Gtk.MenuItem(label='About')
        about_item.set_submenu(about_menu)

        about = Gtk.MenuItem(label="About")
        about.connect('activate', self.on_about)
        about_menu.append(about)

        # Adding to Menu
        menubar.append(file_item)
        menubar.append(view_item)
        menubar.append(edit_item)
        menubar.append(filter_item)
        menubar.append(enhance_item)
        menubar.append(info_item)
        menubar.append(about_item)
        self.main_box.pack_start(menubar, False, False, 0)

    def create_toolbar(self):
        toolbar = Gtk.Toolbar()
        self.main_box.pack_start(toolbar, False, False, 0)

        tools = [
            (Gtk.STOCK_OPEN, "Open Image", self.on_open),
            (Gtk.STOCK_SAVE, "Save Image", self.on_save),
            (None, None, None),  # Separator
            (Gtk.STOCK_ZOOM_IN, "Zoom In", self.on_zoom_in),
            (Gtk.STOCK_ZOOM_OUT, "Zoom Out", self.on_zoom_out),
            (Gtk.STOCK_ZOOM_100, "Actual Size", self.fit_to_window),
            (None, None, None),
            (Gtk.STOCK_UNDO, "Rotate 90°", self.on_rotate)
        ]

        for stock, tooltip, action in tools:
            if stock is None:
                toolbar.insert(Gtk.SeparatorToolItem(), -1)
            else:
                btn = Gtk.ToolButton(stock_id=stock)
                btn.set_tooltip_text(tooltip)
                btn.connect("clicked", action)
                toolbar.insert(btn, -1)

    # --- Core Display Logic with ZOOM ---

    def pil_to_pixbuf(self, pil_image):
        buffer = io.BytesIO()

        # Keep PNG to preserve alpha
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)

        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write(buffer.read())
        loader.close()

        return loader.get_pixbuf()

    def fit_to_window(self, widget=None, allocation=None):

        """Calculates the initial zoom factor to fit the image in the window."""
        if not self.current_image:
            return

        # Let the window draw first to get accurate dimensions,
        # or fallback to default size if not fully realized
        allocation = self.scroll_window.get_allocation()
        max_width = allocation.width if allocation.width > 1 else 1024
        max_height = allocation.height if allocation.height > 1 else 768

        img_width, img_height = self.current_image.size

        # Compute scale factor (fit to window with a slight margin)
        scale_x = (max_width - 20) / img_width
        scale_y = (max_height - 20) / img_height
        self.zoom_factor = min(scale_x, scale_y)
        self.update_display()

    def update_display(self):
        """Draws the image strictly based on the current self.zoom_factor."""
        if not self.current_image:
            return
        image = getattr(self, "display_image", self.current_image)
        img = self.current_image
        img_width, img_height = img.size

        # Resize image using the current manual or auto zoom factor
        new_width = max(1, int(img_width * self.zoom_factor))
        new_height = max(1, int(img_height * self.zoom_factor))

        resized = img.resize((new_width, new_height), Image.LANCZOS)

        # Force RGB if it's not already, to ensure 3 channels
        if resized.mode != "RGB":
            resized = resized.convert("RGB")

        channels = 3  # Since we converted to RGB
        rowstride = resized.width * channels

        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            resized.tobytes(),
            GdkPixbuf.Colorspace.RGB,
            False,  # has_alpha is False for RGB
            8,
            resized.width,
            resized.height,
            rowstride
        )

        self.image_widget.set_from_pixbuf(pixbuf)
    # --- NEW: Drag & Pan Logic ---
    def on_button_press(self, widget, event):
        if event.button == 1:
            self.drag_in_progress = True
            self.start_x = event.x_root
            self.start_y = event.y_root

            hadj = self.scroll_window.get_hadjustment()
            vadj = self.scroll_window.get_vadjustment()
            self.start_h_adj = hadj.get_value()
            self.start_v_adj = vadj.get_value()

            display = Gdk.Display.get_default()
            cursor = Gdk.Cursor.new_from_name(display, "grabbing")
            self.get_window().set_cursor(cursor)
            return True
        return False

    def on_button_release(self, widget, event):
        if event.button == 1:
            self.drag_in_progress = False
            self.get_window().set_cursor(None)
            return True
        return False

    def on_mouse_motion(self, widget, event):
        if self.drag_in_progress:
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y

            hadj = self.scroll_window.get_hadjustment()
            vadj = self.scroll_window.get_vadjustment()

            hadj.set_value(self.start_h_adj - dx)
            vadj.set_value(self.start_v_adj - dy)
            return True
        return False

    # -----------------------------

    # --- Actions ---

    def on_open(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Open Image",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        if dialog.run() == Gtk.ResponseType.OK:
            self.current_image = Image.open(dialog.get_filename())

            # Ensure compatible mode
            if self.current_image.mode not in ("RGB", "RGBA"):
                self.current_image = self.current_image.convert("RGB")

            # Fit to window first, THEN update display
            self.fit_to_window()
            self.update_display()

        dialog.destroy()

    def on_save(self, widget):
        if not self.current_image: return
        dialog = Gtk.FileChooserDialog(title="Save Image", parent=self, action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()

            if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
                filename += ".png"  # default format

            self.current_image.save(filename)
        dialog.destroy()

    def on_about(self, widget):
        dialog = Gtk.AboutDialog()
        dialog.set_title("AboutDialog")
        dialog.set_name("Gtk Image Viewer")
        dialog.set_license_type(Gtk.License.GPL_2_0)
        dialog.set_version("1.0")
        dialog.set_comments("A Gtk based image viewer")
        dialog.set_website("https://github.com/fabv12610/GtkImageViewer")
        dialog.set_website_label("Gtk Image Viewer")
        dialog.set_authors(["Fabian Binu"])
        dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_size("./resources/icon.png", 64, 64)) # Disabled to ensure it runs without the local icon
        dialog.connect('response', lambda dialog, data: dialog.destroy())
        dialog.show_all()

    # --- Zoom Controls ---
    def on_zoom_in(self, widget):
        self.zoom_factor *= 1.2
        self.update_display()

    def on_zoom_out(self, widget):
        self.zoom_factor *= 0.8
        self.update_display()

    # --- Editing & Transforms ---
    def on_rotate(self, widget):
        if self.current_image:
            self.current_image = self.current_image.rotate(-90, expand=True)
            self.update_display()

    def on_mirror(self, widget):
        if self.current_image:
            self.current_image = ImageOps.mirror(self.current_image)
            self.update_display()

    def on_flip(self, widget):
        if self.current_image:
            self.current_image = ImageOps.flip(self.current_image)
            self.update_display()

    def on_crop(self, widget):
        if self.current_image:
            w, h = self.current_image.size
            self.current_image = self.current_image.crop((w / 4, h / 4, 3 * w / 4, 3 * h / 4))
            self.update_histogram_data()
            self.update_display()

    def on_resize(self, widget, allocation):
        if self.current_image:
            self.update_histogram_data()
            self.update_display()

    # --- Filters ---
    def apply_filter(self, img_filter):
        if self.current_image:
            self.current_image = self.current_image.filter(img_filter)
            self.update_histogram_data()
            self.update_display()

    def on_bw(self, widget):
        if self.current_image:
            self.current_image = self.current_image.convert("L")
            self.update_histogram_data()
            self.update_display()

    def on_invert(self, widget):
        if self.current_image:
            if self.current_image.mode == 'RGBA':
                r, g, b, a = self.current_image.split()
                rgb_image = Image.merge('RGB', (r, g, b))
                inverted = ImageOps.invert(rgb_image)
                r2, g2, b2 = inverted.split()
                self.current_image = Image.merge('RGBA', (r2, g2, b2, a))
            else:
                self.current_image = ImageOps.invert(self.current_image.convert('RGB'))
            self.update_histogram_data()
            self.update_display()

    def on_blur(self, widget):
        self.apply_filter(ImageFilter.BLUR)
        self.update_histogram_data()

    def on_sharpen(self, widget):
        self.apply_filter(ImageFilter.SHARPEN)
        self.update_histogram_data()

    def on_edges(self, widget):
        self.apply_filter(ImageFilter.FIND_EDGES)
        self.update_histogram_data()

    def on_emboss(self, widget):
        self.apply_filter(ImageFilter.EMBOSS)
        self.update_histogram_data()

    def on_contour(self, widget):
        self.apply_filter(ImageFilter.CONTOUR)
        self.update_histogram_data()

    # --- Enhancements ---
    def on_enhance(self, mode, factor):
        if not self.current_image: return
        if mode == 'brightness':
            enhancer = ImageEnhance.Brightness(self.current_image)
        elif mode == 'contrast':
            enhancer = ImageEnhance.Contrast(self.current_image)
        elif mode == 'color':
            enhancer = ImageEnhance.Color(self.current_image)
        self.current_image = enhancer.enhance(factor)
        self.update_histogram_data()
        self.update_display()

    # --- Image Info ---
    def exif_info(self, widget):
        if not self.current_image:
            return

        exif = self.current_image.getexif()

        dialog = Gtk.Dialog(
            title="EXIF Info Viewer",
            transient_for=self,
            flags=0
        )
        dialog.set_default_size(500, 400)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)

        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)

        buffer = textview.get_buffer()

        # Tags
        tag_header = buffer.create_tag(
            "header",
            weight=700,
            scale=1.3
        )

        tag_key = buffer.create_tag(
            "key",
            weight=600
        )

        tag_value = buffer.create_tag(
            "value",
            family="monospace"
        )

        tag_spacing = buffer.create_tag(
            "spacing",
            scale=0.8
        )

        iter_ = buffer.get_start_iter()

        def add_header(text):
            buffer.insert_with_tags(iter_, text + "\n", tag_header)

        def add_kv(key, value):
            buffer.insert_with_tags(iter_, f"{key}: ", tag_key)
            buffer.insert_with_tags(iter_, f"{value}\n", tag_value)

        def add_space():
            buffer.insert_with_tags(iter_, "\n", tag_spacing)

        if not exif:
            buffer.insert(iter_, "No EXIF data found")
        else:
            data = {}
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                data[tag] = value

            def fmt_fraction(val, suffix=""):
                try:
                    if isinstance(val, tuple):
                        return f"{val[0] / val[1]:.1f}{suffix}"
                    return f"{val}{suffix}"
                except:
                    return str(val)

            def fmt_exposure(val):
                try:
                    if isinstance(val, tuple):
                        return f"{val[0]}/{val[1]}s"
                    return f"{val}s"
                except:
                    return str(val)

            # Camera
            add_header("Camera")
            add_kv("Make", data.get("Make", "-"))
            add_kv("Model", data.get("Model", "-"))
            add_kv("Lens", data.get("LensModel", "-"))
            add_space()

            # Settings
            add_header("Settings")
            add_kv("ISO", data.get("ISOSpeedRatings", "-"))
            add_kv("Aperture", "f/" + fmt_fraction(data.get("FNumber", "-")))
            add_kv("Shutter", fmt_exposure(data.get("ExposureTime", "-")))
            add_kv("Focal Length", fmt_fraction(data.get("FocalLength", "-"), "mm"))
            add_space()

            # Image
            add_header("Image")
            add_kv("Resolution", f"{self.current_image.width} x {self.current_image.height}")
            add_kv("Color Mode", self.current_image.mode)
            add_space()

            # Date
            add_header("Date")
            add_kv("Taken", data.get("DateTimeOriginal", "-"))
            add_kv("Modified", data.get("DateTime", "-"))

        scrolled.add(textview)

        box = dialog.get_content_area()
        box.set_border_width(6)
        box.pack_start(scrolled, True, True, 0)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def histogram(self, widget):
        # 1. If already open, just bring it to front and update
        if hasattr(self, 'hist_dialog') and self.hist_dialog:
            self.update_histogram_data()
            self.hist_dialog.present()
            return

        # 2. Create Non-Modal Dialog
        self.hist_dialog = Gtk.Dialog(title="Image Histogram", transient_for=self, flags=0)
        self.hist_dialog.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.hist_dialog.set_default_size(700, 500)

        # 3. Setup Matplotlib Objects
        self.hist_fig = Figure(figsize=(6, 4), dpi=100)
        self.hist_ax = self.hist_fig.add_subplot(111)
        self.hist_canvas = FigureCanvas(self.hist_fig)

        self.hist_dialog.get_content_area().pack_start(self.hist_canvas, True, True, 0)

        # 4. Handle Closing (Cleanup references)
        def on_close(d, r):
            self.hist_dialog.destroy()
            self.hist_dialog = None
            self.hist_ax = None

        self.hist_dialog.connect("response", on_close)

        # 5. Initial Draw
        self.update_histogram_data()
        self.hist_dialog.show_all()

    def update_histogram_data(self):
        if not hasattr(self, 'hist_ax') or self.hist_ax is None:
            return

        img_data = np.array(self.current_image)
        self.hist_ax.clear()

        # Case 1: Grayscale
        if img_data.ndim == 2:
            self.hist_ax.hist(img_data.ravel(), bins=255, range=(0, 255),
                              color="black", alpha=0.7, histtype="stepfilled", label="Grayscale")
            self.hist_ax.set_title("Grayscale Intensity Histogram")

        # Case 2: RGB / RGBA
        else:
            colors = [("Red", "red", 0), ("Green", "green", 1), ("Blue", "blue", 2)]
            for label, color_code, idx in colors:
                if img_data.shape[2] > idx:
                    channel = img_data[:, :, idx].ravel()
                    self.hist_ax.hist(channel, bins=255, range=(0, 255), color=color_code,
                                      alpha=0.4, label=label, histtype="stepfilled")
            self.hist_ax.set_title("RGB Intensity Histogram")

        self.hist_ax.set_xlabel("Intensity (0–255)")
        self.hist_ax.set_ylabel("Pixel Count")
        self.hist_ax.set_xlim(0, 255)
        self.hist_ax.legend(loc="upper right")

        self.hist_canvas.draw()


if __name__ == "__main__":

    win = ImageEditor()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()