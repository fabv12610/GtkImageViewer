import gi
import io

gi.require_version('Gtk', '3.0')
# 1. Added Gdk to the imports for EventMask and Cursors
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ExifTags

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

        # --- NEW: Added EventBox to capture mouse events ---
        self.event_box = Gtk.EventBox()
        self.scroll_window.add(self.event_box)

        self.image_widget = Gtk.Image()
        self.event_box.add(self.image_widget)
        # ---------------------------------------------------

        self.main_box.pack_start(self.scroll_window, True, True, 0)

        # --- NEW: Dragging State Variables and Signals ---
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
                              ("Actual Size (100%)", self.on_zoom_reset)]:
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
                              ("Color +20%", lambda x: self.on_enhance('color', 1.2))]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", action)
            enhance_menu.append(item)

        #6. Info Menu
        info_menu = Gtk.Menu()
        info_item = Gtk.MenuItem(label='Info')
        info_item.set_submenu(info_menu)

        exif_info = Gtk.MenuItem(label="Exif Info")
        exif_info.connect('activate', self.exif_info)
        info_menu.append(exif_info)

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
            (Gtk.STOCK_ZOOM_100, "Actual Size", self.on_zoom_reset),
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

    def update_display(self):
        if self.current_image:
            # Apply zoom only to the display, not the actual underlying image data
            display_w = max(1, int(self.current_image.width * self.zoom_factor))
            display_h = max(1, int(self.current_image.height * self.zoom_factor))

            # Create a temporary scaled copy for the GTK View
            display_img = self.current_image.resize((display_w, display_h), Image.Resampling.BILINEAR)

            pixbuf = self.pil_to_pixbuf(display_img)
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
        dialog = Gtk.FileChooserDialog(title="Open Image", parent=self, action=Gtk.FileChooserAction.OPEN, )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        if dialog.run() == Gtk.ResponseType.OK:
            self.current_image = Image.open(dialog.get_filename())
            # Convert to RGB to ensure compatibility with all filters (especially if it was a palette image like GIF)
            if self.current_image.mode != 'RGB' and self.current_image.mode != 'RGBA':
                self.current_image = self.current_image.convert('RGB')
            self.zoom_factor = 1.0
            self.update_display()
        dialog.destroy()

    def on_save(self, widget):
        if not self.current_image: return
        dialog = Gtk.FileChooserDialog("Save Image", self, Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
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

    def on_zoom_reset(self, widget):
        self.zoom_factor = 1.0
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
            self.update_display()

    def on_resize(self, widget):
        if not self.current_image: return
        dialog = Gtk.Dialog(title="Resize", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        w_entry, h_entry = Gtk.Entry(text=str(self.current_image.width)), Gtk.Entry(text=str(self.current_image.height))
        box.add(Gtk.Label(label="Width:"))
        box.add(w_entry)
        box.add(Gtk.Label(label="Height:"))
        box.add(h_entry)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            try:
                self.current_image = self.current_image.resize((int(w_entry.get_text()), int(h_entry.get_text())),
                                                               Image.Resampling.LANCZOS)
                self.update_display()
            except ValueError:
                pass
        dialog.destroy()

    # --- Filters ---
    def apply_filter(self, img_filter):
        if self.current_image:
            self.current_image = self.current_image.filter(img_filter)
            self.update_display()

    def on_bw(self, widget):
        if self.current_image:
            self.current_image = self.current_image.convert("L")
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
            self.update_display()

    def on_blur(self, widget):
        self.apply_filter(ImageFilter.BLUR)

    def on_sharpen(self, widget):
        self.apply_filter(ImageFilter.SHARPEN)

    def on_edges(self, widget):
        self.apply_filter(ImageFilter.FIND_EDGES)

    def on_emboss(self, widget):
        self.apply_filter(ImageFilter.EMBOSS)

    def on_contour(self, widget):
        self.apply_filter(ImageFilter.CONTOUR)

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
        self.update_display()

    # --- Image Info ---
    def exif_info(self, widget):
        if not self.current_image:
            return

        exif = self.current_image.getexif()

        if not exif:
            text = "No EXIF data found"
        else:
            lines = []
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                lines.append(f"{tag}: {value}")
            text = "\n".join(lines)

        # Create dialog
        dialog = Gtk.Dialog(
            title="EXIF Info Viewer",
            transient_for=self,
            flags=0
        )
        dialog.set_default_size(500, 400)

        # Add close button
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)

        # Create scrollable area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Create text view
        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_monospace(True)

        buffer = textview.get_buffer()
        buffer.set_text(text)

        scrolled.add(textview)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)

        # Add to dialog
        box = dialog.get_content_area()
        box.add(scrolled)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    win = ImageEditor()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()