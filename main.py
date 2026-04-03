import gi
import io

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from PIL import Image, ImageFilter, ImageEnhance, ImageOps


class ImageEditor(Gtk.Window):
    def __init__(self):
        super().__init__(title="Python GTK3 Ultimate Image Editor")
        self.set_default_size(1024, 768)
        self.current_image = None
        self.zoom_factor = 1.0  # 1.0 = 100%

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)

        self.create_menubar()
        self.create_toolbar()

        self.scroll_window = Gtk.ScrolledWindow()
        self.image_widget = Gtk.Image()
        self.scroll_window.add(self.image_widget)
        self.main_box.pack_start(self.scroll_window, True, True, 0)

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

        #6. About Menu
        about_menu = Gtk.Menu()
        about_item = Gtk.MenuItem(label='About')
        about_item.set_submenu(about_menu)

        menubar.append(file_item)
        menubar.append(view_item)
        menubar.append(edit_item)
        menubar.append(filter_item)
        menubar.append(enhance_item)
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
        pil_image.save(buffer, format="PNG")
        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write(buffer.getvalue())
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

    # --- Actions ---

    def on_open(self, widget):
        dialog = Gtk.FileChooserDialog("Open Image", self, Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
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
            self.current_image.save(dialog.get_filename())
        dialog.destroy()

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
        box.add(Gtk.Label(label="Width:"));
        box.add(w_entry);
        box.add(Gtk.Label(label="Height:"));
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




win = ImageEditor()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()