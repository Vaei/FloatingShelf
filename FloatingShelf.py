import maya.cmds as cmds
import maya.mel as mel
import json
import os
import glob

class FloatingShelfStatics:
    title = "Floating Shelf"
    version = "100"
    version_flags = "-beta"
    BUTTON_SIZE = 40
    DEFAULT_ICON = "commandButton.png"
    ICONS = {
        "add_shelf": "addBookmark.png",
        "delete_shelf": "delete.png",
        "set_default": "Bool_Mode2.png",
        "rename_shelf": "BluePencil.png",
        "add_button": "addClip_100.png",
        "info": "info.png",
    }
    SHELF_PREFS_PATH = os.path.join(cmds.internalVar(userPrefDir=True), "floating_shelves.json")

    @staticmethod
    def get_version():
        return ".".join(FloatingShelfStatics.version) + FloatingShelfStatics.version_flags

class FloatingShelfUI:
    # Helpers to load and save preferences
    @staticmethod
    def load_shelf_prefs():
        """Load the shelf preferences from the JSON file."""
        if os.path.exists(FloatingShelfStatics.SHELF_PREFS_PATH):
            try:
                with open(FloatingShelfStatics.SHELF_PREFS_PATH, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                cmds.warning("Corrupted shelf preferences detected. Resetting preferences.")
        # Return a clean default state if file is missing or corrupted
        return {"Default": [], "_default": "Default"}

    @staticmethod
    def save_shelf_prefs(shelf_data):
        with open(FloatingShelfStatics.SHELF_PREFS_PATH, "w") as f:
            json.dump(shelf_data, f, indent=4)

    @staticmethod
    def clear_layout(layout):
        """Delete all children of the given layout."""
        children = cmds.layout(layout, query=True, childArray=True) or []
        for child in children:
            cmds.deleteUI(child)

    @staticmethod
    def close_layout_dialog():
        """Close the layout dialog if it is open."""
        cmds.layoutDialog(dismiss="Close")

    def close_window(self):
        if cmds.dockControl("floatingShelfDock", exists=True):
            cmds.deleteUI("floatingShelfDock")
        if cmds.window("floatingShelfUI", exists=True):
            cmds.deleteUI("floatingShelfUI")

    def __init__(self):
        # Toggle the window if it is already open with each activation
        # Note: without evalDeferred, Maya will hard crash when closing the window due to the layoutDialog not being closed yet
        if cmds.dockControl("floatingShelfDock", exists=True):
            cmds.layoutDialog(dismiss="Close")
            cmds.evalDeferred(lambda: self.close_window(), lowestPriority=True)
            return
        if cmds.window("floatingShelfUI", exists=True):
            cmds.layoutDialog(dismiss="Close")
            cmds.evalDeferred(lambda: self.close_window(), lowestPriority=True)
            return

        self.shelves = self.load_shelf_prefs()
        self.default_shelf = self.shelves.get("_default", "Default")
        self.last_window_width = None  # Track the last window width for resize handling

        # Ensure at least one shelf exists
        if not self.shelves or "Default" not in self.shelves:
            cmds.warning("No shelves found. Creating a 'Default' shelf.")
            self.shelves = {"Default": [], "_default": "Default"}
            self.save_shelf_prefs(self.shelves)

        # Validate the default shelf
        if self.default_shelf not in self.shelves:
            cmds.warning(f"Default shelf '{self.default_shelf}' not found. Switching to 'Default'.")
            self.default_shelf = "Default"
            self.shelves["_default"] = "Default"

        self.current_shelf = self.default_shelf
        self.save_shelf_prefs(self.shelves)
        self.create_ui()

    def delete_ui(self):
        """Delete the main UI window."""
        if cmds.window("floatingShelfUI", exists=True):
            cmds.deleteUI("floatingShelfUI", window=True)
        if cmds.dockControl("floatingShelfDock", exists=True):
            cmds.deleteUI("floatingShelfDock", control=True)

    def create_ui(self):
        """Create the main floating shelf UI as a dockable window."""
        self.window = cmds.window("floatingShelfUI", title="Floating Shelf", sizeable=True, widthHeight=(400, 300), closeCommand=self.delete_ui)
        self.layout = cmds.formLayout("floatingShelfLayout", parent=self.window)

        cmds.scriptJob(uiDeleted=[self.window, lambda: self.delete_ui()])

        # Top toolbar
        self.toolbar = cmds.rowLayout(
            parent=self.layout,
            numberOfColumns=6,
            columnWidth5=(100, 25, 25, 25, 25),
            adjustableColumn=1,
            columnAlign=(1, "center"),
        )
        self.shelf_menu = cmds.optionMenu(parent=self.toolbar, changeCommand=self.change_shelf)
        self.update_dropdown_menu()
        cmds.iconTextButton(image=FloatingShelfStatics.ICONS["add_shelf"], ann="Add New Shelf", width=25, height=25, command=self.add_shelf)
        cmds.iconTextButton(image=FloatingShelfStatics.ICONS["set_default"], ann="Set Default Shelf", width=25, height=25, command=self.set_default_shelf)
        cmds.iconTextButton(image=FloatingShelfStatics.ICONS["rename_shelf"], ann="Rename Shelf", width=25, height=25, command=self.rename_shelf)
        cmds.iconTextButton(image=FloatingShelfStatics.ICONS["delete_shelf"], ann="Delete Shelf", width=25, height=25, command=self.delete_shelf)
        cmds.iconTextButton(image=FloatingShelfStatics.ICONS["info"], ann="About", width=25, height=25, command=self.about)

        # Scrollable layout for shelf buttons
        self.scroll_layout = cmds.scrollLayout(parent=self.layout, childResizable=True)
        self.button_grid = cmds.gridLayout(
            parent=self.scroll_layout,
            cellWidthHeight=(FloatingShelfStatics.BUTTON_SIZE, FloatingShelfStatics.BUTTON_SIZE),
            autoGrow=True,
            numberOfColumns=1,
        )

        # Attach layouts
        cmds.formLayout(
            self.layout, edit=True,
            attachForm=[
                (self.toolbar, "top", 5), (self.toolbar, "left", 5), (self.toolbar, "right", 5),
                (self.scroll_layout, "left", 5), (self.scroll_layout, "right", 5), (self.scroll_layout, "bottom", 5),
            ],
            attachControl=[
                (self.scroll_layout, "top", 5, self.toolbar),
            ]
        )

        # Load the current shelf
        self.load_shelf(self.current_shelf)

        # Create the dockControl
        cmds.dockControl(
            "floatingShelfDock",
            label="Floating Shelf",
            area="right",
            moveable=True,
            content=self.window,
            floating=True
        )

        self.monitor_window_resize()

    def close_menu(self, *_):
        """Close the floating shelf window."""
        cmds.deleteUI(self.window, window=True)
        if cmds.dockControl("floatingShelfDock", exists=True):
            cmds.deleteUI("floatingShelfDock", control=True)

    def monitor_window_resize(self):
        """Monitor window resizing."""
        if not cmds.window(self.window, exists=True):
            return

        if cmds.formLayout(self.layout, exists=True):
            window_width = cmds.formLayout(self.layout, query=True, width=True)

            # Check if the width has changed (ignore None on the first run)
            if self.last_window_width is None or self.last_window_width != window_width:
                self.update_grid_columns(window_width)
                self.last_window_width = window_width

        cmds.evalDeferred(lambda: self.monitor_window_resize(), lp=True)

    def update_grid_columns(self, window_width):
        """Update number of columns in the grid layout."""
        columns = max(1, int((window_width - 10) / FloatingShelfStatics.BUTTON_SIZE))
        cmds.gridLayout(self.button_grid, edit=True, numberOfColumns=columns)

    def update_dropdown_menu(self):
        """Rebuild the dropdown menu with all shelves."""
        cmds.optionMenu(self.shelf_menu, edit=True, deleteAllItems=True)  # Clear existing items
        for shelf_name in self.shelves.keys():
            if shelf_name != "_default":
                cmds.menuItem(label=shelf_name, parent=self.shelf_menu)

        # Set the dropdown to the current shelf
        if self.current_shelf in self.shelves:
            cmds.optionMenu(self.shelf_menu, edit=True, value=self.current_shelf)

    def add_shelf(self, *_):
        """Add a new shelf and update the dropdown menu."""
        result = cmds.promptDialog(
            title="New Shelf",
            message="Enter Shelf Name:",
            button=["OK", "Cancel"],
            defaultButton="OK",
            cancelButton="Cancel",
            dismissString="Cancel",
        )
        if result == "OK":
            shelf_name = cmds.promptDialog(query=True, text=True)
            if shelf_name and shelf_name not in self.shelves:
                self.shelves[shelf_name] = []  # Add new shelf to data
                self.current_shelf = shelf_name
                self.save_shelf_prefs(self.shelves)
                self.update_dropdown_menu()  # Rebuild dropdown menu
                self.load_shelf(shelf_name)  # Load the new shelf
            else:
                cmds.warning(f"Shelf '{shelf_name}' already exists or is invalid.")

    def create_about_dialog(self):
        """Create the about dialog."""
        cmds.columnLayout(adjustableColumn=True)
        version = FloatingShelfStatics.get_version()
        cmds.text(label=f"{FloatingShelfStatics.title} v{version}")
        cmds.text(label="A floating shelf tool for Maya.")
        cmds.text(label="Created by: Jared Taylor")
        cmds.text(label="https://github.com/Vaei/FloatingShelf")
        cmds.separator(style="none", height=10)
        cmds.button(label="Close", command=lambda _: self.close_layout_dialog())

    def about(self, *_):
        """Display information about the tool."""
        cmds.layoutDialog(parent=self.window, title="About", ui=lambda: self.create_about_dialog())

    def delete_shelf(self, *_):
        """Delete the current shelf and update the dropdown menu."""
        if self.current_shelf == "Default":
            cmds.warning("Cannot delete the Default shelf.")
            return

        confirm = cmds.confirmDialog(
            title="Delete Shelf",
            message=f"Are you sure you want to delete the shelf '{self.current_shelf}'?",
            button=["Yes", "No"],
            defaultButton="No",
            cancelButton="No",
            dismissString="No",
        )
        if confirm == "Yes":
            del self.shelves[self.current_shelf]

            # If the deleted shelf was the default, set a new default shelf
            if self.current_shelf == self.shelves.get("_default"):
                self.shelves["_default"] = "Default" if "Default" in self.shelves else next(iter(self.shelves.keys()))

            # Update to a safe shelf (Default or the first available one)
            self.current_shelf = self.shelves["_default"]
            self.save_shelf_prefs(self.shelves)

            self.update_dropdown_menu()
            self.load_shelf(self.current_shelf)

    def rename_shelf(self, *_):
        """Rename the current shelf."""
        if self.current_shelf == "Default":
            cmds.warning("Cannot rename the Default shelf.")
            return
        result = cmds.promptDialog(title="Rename Shelf", message="Rename Shelf:", text=self.current_shelf, button=["OK", "Cancel"])
        if result == "OK":
            new_name = cmds.promptDialog(query=True, text=True)
            if new_name and new_name != self.current_shelf:
                self.shelves[new_name] = self.shelves.pop(self.current_shelf)
                if self.current_shelf == self.default_shelf:
                    self.shelves["_default"] = new_name
                self.current_shelf = new_name
                self.save_shelf_prefs(self.shelves)
                self.update_dropdown_menu()
                self.load_shelf(new_name)

    def set_default_shelf(self, *_):
        """Set the current shelf as default."""
        self.shelves["_default"] = self.current_shelf
        self.default_shelf = self.current_shelf
        self.save_shelf_prefs(self.shelves)
        cmds.inViewMessage(amg=f"Default shelf set to: {self.current_shelf}", pos="topCenter", fade=True)

    def load_shelf(self, shelf_name):
        """Load all buttons for the given shelf."""
        if shelf_name not in self.shelves:
            cmds.warning(f"Shelf '{shelf_name}' does not exist. Switching to default shelf.")
            self.current_shelf = self.shelves["_default"]

            # Ensure the default shelf exists
            if self.current_shelf not in self.shelves:
                cmds.warning("Default shelf not found. Creating a new 'Default' shelf.")
                self.shelves = {"Default": [], "_default": "Default"}
                self.current_shelf = "Default"
                self.save_shelf_prefs(self.shelves)

        # Clear and load the shelf
        self.clear_layout(self.button_grid)
        for button_data in self.shelves.get(self.current_shelf, []):
            self.create_button(button_data)

        # Add the "+" button
        self.create_add_button()

    def change_shelf(self, shelf_name):
        """Handle switching to a different shelf."""
        if shelf_name in self.shelves:
            self.current_shelf = shelf_name
            self.load_shelf(shelf_name)  # Refresh the shelf UI
            cmds.optionMenu(self.shelf_menu, edit=True, value=shelf_name)  # Update dropdown selection
        else:
            cmds.warning(f"Shelf '{shelf_name}' does not exist.")

    def create_add_button(self):
        """Create the add button."""
        cmds.shelfButton(
            parent=self.button_grid,
            image=FloatingShelfStatics.ICONS["add_button"],
            width=FloatingShelfStatics.BUTTON_SIZE,
            height=FloatingShelfStatics.BUTTON_SIZE,
            command=self.add_button,
        )

    def add_button(self, *_):
        """Add a new button."""
        result = cmds.promptDialog(title="New Button", message="Enter Button Label:", button=["OK", "Cancel"])
        if result == "OK":
            button_label = cmds.promptDialog(query=True, text=True)
            button_data = {
                "label": button_label,
                "command": f'print("{button_label} clicked")',
                "icon": FloatingShelfStatics.DEFAULT_ICON,
                "tooltip": button_label,
                "type": "python",
            }
            self.shelves[self.current_shelf].append(button_data)
            self.save_shelf_prefs(self.shelves)
            self.load_shelf(self.current_shelf)

    def create_button(self, button_data):
        """Create a button in the current shelf."""

        button = cmds.shelfButton(
            parent=self.button_grid,
            image=button_data.get("icon", FloatingShelfStatics.DEFAULT_ICON),
            width=FloatingShelfStatics.BUTTON_SIZE,
            height=FloatingShelfStatics.BUTTON_SIZE,
            imageOverlayLabel=button_data["label"],
            annotation=button_data.get("tooltip", button_data["label"]),
            style="iconAndTextVertical",  # Centers the icon and label
            scaleIcon=False,
            font="smallFixedWidthFont",
            command=lambda: self.run_button_command(button_data),
            noDefaultPopup=True,
        )

        # Add a right-click menu for editing
        popup = cmds.popupMenu(parent=button)
        cmds.menuItem(label="Move Left", command=lambda _: self.move_button_left(button_data), enable=self.can_move_button(button_data, -1))
        cmds.menuItem(label="Move Right", command=lambda _: self.move_button_right(button_data), enable=self.can_move_button(button_data, 1))
        cmds.menuItem(label="Set Label", command=lambda _: self.set_button_label(button_data))
        cmds.menuItem(label="Edit Command", command=lambda _: self.edit_button_command(button_data))
        cmds.menuItem(label="Change Icon", command=lambda _: self.change_button_icon(button_data, button))
        cmds.menuItem(label="Delete", command=lambda _: self.delete_button(button, button_data))

    @staticmethod
    def run_button_command(button_data):
        """Run the command assigned to the button."""
        try:
            if button_data["type"] == "python":
                exec(button_data["command"], {}, {})
            elif button_data["type"] == "mel":
                mel.eval(button_data["command"])
        except Exception as e:
            cmds.warning(f"Failed to execute button command: {e}")

    def move_button(self, button_data, direction):
        """Move a button in the given direction."""
        shelf = self.shelves[self.current_shelf]
        index = shelf.index(button_data)
        if 0 <= index + direction < len(shelf):
            shelf[index + direction], shelf[index] = shelf[index], shelf[index + direction]
            self.save_shelf_prefs(self.shelves)
            self.load_shelf(self.current_shelf)

    def move_button_left(self, button_data):
        cmds.evalDeferred(lambda:  self.move_button(button_data, -1))

    def move_button_right(self, button_data):
        cmds.evalDeferred(lambda:  self.move_button(button_data, 1))

    def can_move_button(self, button_data, direction):
        """Check if the button can be moved in the given direction."""
        shelf = self.shelves[self.current_shelf]
        index = shelf.index(button_data)
        return 0 <= index + direction < len(shelf)

    def set_button_label(self, button_data):
        """Set a new label for the button."""
        result = cmds.promptDialog(title="Set Label", message="Enter Button Label:", text=button_data["label"], button=["OK", "Cancel"])
        if result == "OK":
            new_label = cmds.promptDialog(query=True, text=True)
            if new_label:
                button_data["label"] = new_label
                button_data["tooltip"] = new_label
                self.save_shelf_prefs(self.shelves)
                self.load_shelf(self.current_shelf)

    def edit_button_command(self, button_data):
        """Open a dialog to edit the button's command and type."""
        if cmds.window("editCommandWindow", exists=True):
            cmds.deleteUI("editCommandWindow")

        # Create a new window for editing
        window = cmds.window("editCommandWindow", title="Edit Command", sizeable=False, widthHeight=(400, 300))
        layout = cmds.formLayout()

        # Command type options (Python or MEL)
        command_type_radio = cmds.radioButtonGrp(
            label="Command Type:",
            numberOfRadioButtons=2,
            labelArray2=["Python", "MEL"],
            select=1 if button_data["type"] == "python" else 2,
        )

        # Multiline text field for editing the command
        command_field = cmds.scrollField(text=button_data["command"], wordWrap=True, height=200)

        # Save and Cancel buttons
        save_button = cmds.button(label="Save", command=lambda _: save_changes())
        cancel_button = cmds.button(label="Cancel", command=lambda _: cmds.deleteUI(window))

        # Attach elements
        cmds.formLayout(
            layout, edit=True,
            attachForm=[
                (command_type_radio, "top", 10), (command_type_radio, "left", 10), (command_type_radio, "right", 10),
                (command_field, "left", 10), (command_field, "right", 10),
                (save_button, "left", 10), (cancel_button, "right", 10),
            ],
            attachControl=[
                (command_field, "top", 10, command_type_radio),
                (save_button, "top", 10, command_field),
                (cancel_button, "top", 10, command_field),
            ],
        )

        # Save changes
        def save_changes():
            command_type = "python" if cmds.radioButtonGrp(command_type_radio, query=True, select=True) == 1 else "mel"
            new_command = cmds.scrollField(command_field, query=True, text=True)

            # Update button data
            button_data["type"] = command_type
            button_data["command"] = new_command
            self.save_shelf_prefs(self.shelves)

            cmds.deleteUI(window)

        cmds.showWindow(window)

    @staticmethod
    def get_all_maya_icons():
        maya_icon_paths_str = os.getenv("MAYA_FILE_ICON_PATH", "")
        xbm_lang_paths_str = os.getenv("XBMLANGPATH", "")
        path_separator = ';' if os.name == 'nt' else ':'
        maya_icon_paths = maya_icon_paths_str.split(path_separator)
        xbm_lang_paths = xbm_lang_paths_str.split(path_separator)
        all_paths = list(set(maya_icon_paths + xbm_lang_paths))
        all_icons = []
        image_extensions = ['*.png', '*.svg', '*.bmp', '*.jpg', '*.jpeg', '*.xpm']
        for path in all_paths:
            if os.path.isdir(path):
                for extension in image_extensions:
                    all_icons.extend(glob.glob(os.path.join(path, extension)))
        all_icons = list(set(all_icons))
        all_icons.sort()
        return all_icons

    def create_icon_browser(self, button_data, button):
        """Creates the icon browser for selecting an icon."""
        all_icons = self.get_all_maya_icons()

        def update_icon_preview(*args):
            selected_icon = cmds.textScrollList(icon_list, query=True, selectItem=True)
            if selected_icon:
                icon_path = selected_icon[0]  # Assuming the full path is stored in the list

                # Create a temporary image plane to get the image size
                temp_image_plane = cmds.imagePlane(fileName=icon_path)[0]
                width = cmds.getAttr(temp_image_plane + ".width")
                height = cmds.getAttr(temp_image_plane + ".height")
                cmds.delete(temp_image_plane)  # Clean up the temporary image plane

                # Define the maximum dimensions for the image control
                max_width, max_height = 300, 150

                # Calculate the scaling factor while maintaining the aspect ratio
                scale = min(max_width / width, max_height / height)

                # Calculate new dimensions
                new_width = int(width * scale)
                new_height = int(height * scale)

                # Update the image control with the scaled dimensions
                cmds.image(image_control, edit=True, image=icon_path, width=new_width, height=new_height)

        def filter_icons(*args):
            filter_text = cmds.textField(text_field, query=True, text=True).lower()
            filtered_items = [icon for icon in all_icons if filter_text in icon.lower()]
            cmds.textScrollList(icon_list, edit=True, removeAll=True)
            cmds.textScrollList(icon_list, edit=True, append=filtered_items if filtered_items else all_icons)

        def apply_icon_and_close(icon, *args):
            cmds.shelfButton(button, edit=True, image=icon)
            self.save_shelf_prefs(self.shelves)
            self.close_layout_dialog()

        def browse_image(*args):
            file_path = cmds.fileDialog2(fileMode=1, fileFilter="Image Files (*.png *.svg *.bmp *.jpg *.jpeg)")
            if file_path:
                apply_icon_and_close(file_path[0])

        def select_image(*args):
            selected_icon = cmds.textScrollList(icon_list, query=True, selectItem=True)
            if selected_icon:
                apply_icon_and_close(selected_icon[0])

        main_layout = cmds.formLayout(numberOfDivisions=100)

        text_field = cmds.textField(placeholderText="Filter:", changeCommand=filter_icons)
        icon_list = cmds.textScrollList(numberOfRows=8, allowMultiSelection=False, selectCommand=update_icon_preview,
                                        height=150)
        image_control = cmds.image(width=300, height=150)

        select_button = cmds.button(label="Select", command=lambda x: select_image(button_data))
        browse_button = cmds.button(label="Browse", command=lambda x: browse_image(button_data))

        cmds.formLayout(main_layout, edit=True,
                        attachForm=[
                            (text_field, 'top', 5),
                            (text_field, 'left', 5),
                            (text_field, 'right', 5),
                            (icon_list, 'left', 5),
                            (icon_list, 'right', 5),
                            (image_control, 'left', 5),
                            (image_control, 'right', 5),
                            (select_button, 'left', 5),
                            (browse_button, 'right', 5),
                            (icon_list, 'bottom', 190),
                            (select_button, 'bottom', 5),
                            (browse_button, 'bottom', 5)
                        ],
                        attachControl=[
                            (icon_list, 'top', 5, text_field),
                            (image_control, 'top', 5, icon_list),
                            (select_button, 'top', 5, image_control),
                            (browse_button, 'top', 5, image_control),
                            (select_button, 'bottom', 5, icon_list),
                            (browse_button, 'bottom', 5, icon_list)
                        ],
                        attachPosition=[
                            (select_button, 'right', 5, 50),
                            (browse_button, 'left', 5, 50)
                        ])

        cmds.textScrollList(icon_list, edit=True, append=all_icons)

    def change_button_icon(self, button_data, button):
        if cmds.window("iconBrowserWindow", exists=True):
            cmds.deleteUI("iconBrowserWindow")

        cmds.layoutDialog(parent=self.window, title="Select Icon", ui=lambda: self.create_icon_browser(button_data, button))

    def delete_button(self, button, button_data):
        """Delete a button and refresh the layout using deferred commands to ensure stability."""
        try:
            # Ensure the button exists before attempting to delete
            if cmds.control(button, exists=True):
                # Defer the deletion of the button to ensure any UI updates related to the button are completed
                cmds.evalDeferred(lambda: cmds.deleteUI(button, control=True))

            # Check if the button data still exists in the shelf before attempting to modify the list
            if button_data in self.shelves[self.current_shelf]:
                self.shelves[self.current_shelf].remove(button_data)
                # Save the updated shelf preferences
                self.save_shelf_prefs(self.shelves)
                # Defer reloading the shelf to avoid potential conflicts caused by immediate UI changes
                cmds.evalDeferred(lambda: self.load_shelf(self.current_shelf))

        except Exception as e:
            cmds.warning(f"Failed to delete button: {e}")

if __name__ == '__main__':
    # Dev only helper for reopening the window each time the script runs
    FloatingShelfUI()
