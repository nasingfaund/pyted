#
from __future__ import annotations
from typing import TYPE_CHECKING

import tkinter
from tkinter import ttk

import pyted.pyted_widget_types as pyted_widget_types
if TYPE_CHECKING:
    from pyted.pyted_code.pyted_core import PytedCore

FILLER_TEXT = '        .        '


class UserForm:
    """User Form

    """

    def __init__(self, pyted_core: PytedCore):
        self.pyted_core = pyted_core
        self.widgets = pyted_core.widgets

        self.filler_labels = []
        self.proposed_widget = None
        self.proposed_widget_frame = None
        self.proposed_widget_location = None
        self.proposed_widget_tab = None
        self.mouse_button1_pressed = False
        self.widget_to_deselect_if_not_moved = None

        self.user_frame = None

    def draw_user_frame(self):
        # set up inside of User Frame
        #

        # Find top level widget, assign tk_name to user_frame, and get name
        pyte_widget = self.widgets.find_top_widget()
        if self.user_frame is not None:
            self.user_frame.destroy()
        self.user_frame = ttk.Frame(self.pyted_core.background_user_frame)
        self.user_frame.bind("<Motion>", self.user_motion_callback)
        self.user_frame.bind("<Button-1>", self.pyted_core.empty_label_click_callback)
        self.user_frame.bind("<ButtonRelease-1>", self.pyted_core.widget_release)
        self.user_frame.bind('<Leave>', self.pyted_core.user_frame_leave_callback)
        self.user_frame.grid(row=0, column=0)
        pyte_widget.tk_name = self.user_frame

        # Create and fill Frames with filler labels
        # first create containers before placing non-container widgets
        self.fill_tk_container_widget(pyte_widget)

        return pyte_widget

    def fill_tk_container_widget(self, parent_pyte_widget: pyted_widget_types.PytedGridContainerWidget) -> None:
        """
        Fill a tk container widget

        Fills a tk container widget corresponding to a pyte_widget. The container widget is filled with (blank) label
        widgets or widgets corresponding to pyte widgets. Where there are child container widgets, these are filled out
        recursively.

        :param parent_pyte_widget: pyte container
        :return:
        """

        for i_col in range(int(parent_pyte_widget.number_columns)):
            for i_row in range(int(parent_pyte_widget.number_rows)):
                self.new_filler_label(parent_pyte_widget.tk_name, i_col, i_row)

        for pyte_widget in self.widgets.widget_list:
            if pyte_widget.parent == parent_pyte_widget.name:
                if (int(pyte_widget.column) >= int(parent_pyte_widget.number_columns) or
                        int(pyte_widget.row) >= int(parent_pyte_widget.number_rows)):
                    pyte_widget.remove = True
                elif isinstance(pyte_widget, pyted_widget_types.Frame):
                    self.place_pyte_widget(pyte_widget)
                    self.fill_tk_container_widget(pyte_widget)
                else:
                    self.place_pyte_widget(pyte_widget)

    def new_filler_label(self, container: tkinter.Widget, column: int, row: int) -> None:
        """
        Create and place a new filler label

        Creates a new filler label in the given frame (or TopLevel) at the given column or row and adds it to the list
        of filler labels.

        :param container: pointer to tk container
        :param column: column for new filler label
        :param row: row for new filler label
        :return:
        """
        new_label = ttk.Label(container, text=FILLER_TEXT)
        new_label.grid(row=row, column=column)
        new_label.bind("<Motion>", self.user_motion_callback)
        # new_label.bind("<Button-1>", self.empty_label_click_callback)
        new_label.bind("<Button-1>", lambda
                       event, arg1=self.widgets.find_pyte_widget_from_tk(container):
                       self.pyted_core.widget_click(event, arg1)
                       )
        new_label.bind("<ButtonRelease-1>", self.pyted_core.widget_release)
        self.filler_labels.append(new_label)

    def place_pyte_widget(self, pyte_widget: pyted_widget_types.PytedPlacedWidget, tk_frame=None,
                          column=None, row=None) -> tkinter.Widget:
        """
        Create a tk_widget and places in a container

        Creates a tk_widget from a pyte_widget and places it into a container. The widget may be a container but if it
        is a container the widgets inside the container will not be placed. There must be a filler_widget already at
        the location and this is removed.

        The pyte_widget is by default placed in the frame defined by the pyte_widget and in the column, row defined in
        the pyte_widget. It is possible to instead define where the widget is placed, for example when the user is
        moving the widget.

        :param pyte_widget: pyte widget to be placed onto the user form
        :param tk_frame: frame to place widget on, if none specified then use parent widget defined in pyte_widget
        :param row: row in parent widget, if none specified then row defined in pyte_widget
        :param column: column in parent widget, if none specified then column defined in pyte_widget
        :return:
        """

        # work out parent_tk_frame
        if tk_frame is None:
            parent_tk_widget = self.widgets.find_tk_parent(pyte_widget)
        else:
            parent_tk_widget = tk_frame
        if parent_tk_widget is None:
            raise Exception('widget in project missing parent')
        # work out row and column
        if column is None:
            tk_column = pyte_widget.column
        else:
            tk_column = column
        if row is None:
            tk_row = pyte_widget.row
        else:
            tk_row = row

        # remove filler label
        if not parent_tk_widget.grid_slaves(row=tk_row, column=tk_column) == []:
            filler_widget = parent_tk_widget.grid_slaves(row=tk_row, column=tk_column)[0]
            filler_widget.grid_forget()
            self.filler_labels.remove(filler_widget)
            filler_widget.destroy()
        tk_new_widget = self.new_tk_widget(pyte_widget, parent_tk_widget)
        tk_new_widget.grid(row=tk_row, column=tk_column, sticky=pyte_widget.sticky)
        try:
            remove = pyte_widget.remove
        except AttributeError:
            remove = False
        if remove:
            tk_new_widget.grid_remove()
            self.new_filler_label(parent_tk_widget, row=tk_row, column=tk_column)

        return tk_new_widget

    def new_tk_widget(self, pyte_widget: pyted_widget_types.PytedPlacedWidget, tk_parent=None) -> tkinter.Widget:
        """
        Create a tk_widget from a pyte widget. Normally the tk_widget will have the parent as specified in the
        pyte_widget but this can be over-ridden for example if the tk_widget is going to be put into a selection_frame.

        :param pyte_widget:
        :param tk_parent: tk_container to put widget in, if none then take parent from pyte_widget
        :return:
        """
        if tk_parent is None:
            parent_id = self.widgets.find_tk_parent(pyte_widget)
        else:
            parent_id = tk_parent
        if parent_id is None:
            raise Exception('widget in project missing parent')
        new_w_class = pyte_widget.type
        tk_new_widget = new_w_class(parent_id)
        pyte_widget.tk_name = tk_new_widget
        for k, v in vars(pyte_widget).items():
            self.pyted_core.update_widget_attribute(pyte_widget, k, '', init=True)

        if isinstance(pyte_widget, pyted_widget_types.Frame):
            tk_new_widget.bind("<Motion>", self.user_motion_callback)
            # tk_new_widget.bind("<Button-1>", self.empty_label_click_callback)
            tk_new_widget.bind("<Button-1>", lambda
                               event, arg1=pyte_widget:
                               self.pyted_core.widget_click(event, arg1)
                               )
            tk_new_widget.bind("<ButtonRelease-1>", self.pyted_core.widget_release)
        else:
            tk_new_widget.bind('<Motion>', self.user_motion_callback)
            # tk_new_widget.bind("<B1-Motion>", self.widget_move)
            tk_new_widget.bind("<Button-1>", lambda
                               event, arg1=pyte_widget:
                               self.pyted_core.widget_click(event, arg1)
                               )
            tk_new_widget.bind("<ButtonRelease-1>", self.pyted_core.widget_release)
        return tk_new_widget

    def empty_tk_container_widget(self, parent_pyte_widget: pyted_widget_types.PytedGridContainerWidget) -> None:
        """
        Empty a tk container widget

        Empty a tk container widget corresponding to the pyte_widget of child widgets. All the label widgets in the
        container are removed (including from filler_labels list). tk widgets corresponding to pyte widgets are removed
        but the pyte widget remains in the widgets list. Where there are child container widgets, these are emptied
        recursively.

        :param parent_pyte_widget: pyte container
        :return:
        """

        for child_widget in parent_pyte_widget.tk_name.grid_slaves():
            if child_widget in self.filler_labels:
                self.filler_labels.remove(child_widget)
            elif isinstance(self.widgets.get_pyte_widget(child_widget), pyted_widget_types.Frame):
                self.empty_tk_container_widget(self.widgets.get_pyte_widget(child_widget))
            child_widget.destroy()

    def user_motion_callback(self, event):
        """
        Call back method when mouse is moved in user frame, either in blank space, filler label or widget

        If no specific widget is chosen in the widget toolbox (in other words the pointer is chosen in the toolbox) and
        the mouse button 1 is pressed and a widget is selected then move the selected widget.

        If a widget is chosen in the widget toolbox a check is made to see if the location of the mouse is
        different to the existing proposed widget to insert (including if no proposed widget exists). If the mouse is
        in a different location then insert new proposed widget.

        :param event: the tkinter event object
        :return: None
        """
        if self.pyted_core.widget_in_toolbox_chosen is None:
            # print('<<<<', self.selected_widget.name, self.mouse_button1_pressed)
            if self.pyted_core.selected_widget is not None and self.mouse_button1_pressed:
                # selection widget chosen so may need to move widget
                self.pyted_core.widget_move(event)
        else:
            # toolbox widget chosen so may need to insert proposed widget into user_frame
            frame, grid_location = self.pyted_core.find_grid_location(self.widgets.find_top_widget(), event.x_root, event.y_root)

            old_proposed_widget = self.proposed_widget
            old_proposed_widget_frame = self.proposed_widget_frame
            old_proposed_widget_location = self.proposed_widget_location

            # insert new frame into a notebook?
            if isinstance(frame, pyted_widget_types.Notebook) and isinstance(self.proposed_widget, tkinter.Frame):
                if self.proposed_widget_frame != frame:
                    self.proposed_widget = self.pyted_core.widget_in_toolbox_chosen.type(frame.tk_name)
                    self.proposed_widget_frame = frame
                    self.proposed_widget_location = [0, 0]
                    number_columns = self.pyted_core.widget_in_toolbox_chosen.number_columns
                    number_rows = self.pyted_core.widget_in_toolbox_chosen.number_rows
                    self.proposed_widget['borderwidth'] = 2
                    self.proposed_widget['relief'] = tkinter.GROOVE
                    # tk_widget[attr] = getattr(pyte_widget, attr)
                    for i_column in range(number_columns):
                        for i_row in range(number_rows):
                            # self.new_filler_label(self.proposed_widget, i_column, i_row)
                            new_label = ttk.Label(self.proposed_widget, text=FILLER_TEXT)
                            new_label.grid(row=i_row, column=i_column)
                            new_label.bind("<Motion>", self.user_motion_callback)
                            new_label.bind("<Button-1>", self.pyted_core.inserted_widget_click)
                            # new_label.bind("<ButtonRelease-1>", self.widget_release)
                            self.filler_labels.append(new_label)
                    # self.proposed_widget.grid(column=grid_location[0], row=grid_location[1])
                    frame.tk_name.add(self.proposed_widget)
                    frame.tk_name.select(self.proposed_widget)
                    self.proposed_widget.bind('<Motion>', self.user_motion_callback)
                    self.proposed_widget.bind('<Button-1>', self.pyted_core.inserted_widget_click)

            # insert a widget if there is a label widget
            elif self.proposed_widget_location != grid_location or self.proposed_widget_frame != frame:
                if grid_location[0] >= 0 and grid_location[1] >= 0:
                    try:
                        widget_under_mouse = frame.tk_name.grid_slaves(row=grid_location[1],
                                                                       column=grid_location[0])[0]
                    except IndexError:
                        widget_under_mouse = None
                else:
                    widget_under_mouse = None
                # widget is under mouse unless mouse is not in the user_frame area
                if widget_under_mouse is not None:
                    if widget_under_mouse in self.filler_labels:
                        self.proposed_widget_frame = frame
                        self.proposed_widget_location = grid_location
                        if self.pyted_core.widget_in_toolbox_chosen is pyted_widget_types.Frame:
                            self.proposed_widget = self.pyted_core.widget_in_toolbox_chosen.type(frame.tk_name)
                            number_columns = self.pyted_core.widget_in_toolbox_chosen.number_columns
                            number_rows = self.pyted_core.widget_in_toolbox_chosen.number_rows
                            self.proposed_widget['borderwidth'] = 2
                            self.proposed_widget['relief'] = tkinter.GROOVE
                            # tk_widget[attr] = getattr(pyte_widget, attr)
                            for i_column in range(number_columns):
                                for i_row in range(number_rows):
                                    # self.new_filler_label(self.proposed_widget, i_column, i_row)
                                    new_label = ttk.Label(self.proposed_widget, text=FILLER_TEXT)
                                    new_label.grid(row=i_row, column=i_column)
                                    new_label.bind("<Motion>", self.user_motion_callback)
                                    new_label.bind("<Button-1>", self.pyted_core.inserted_widget_click)
                                    # new_label.bind("<ButtonRelease-1>", self.widget_release)
                                    self.filler_labels.append(new_label)
                        elif self.pyted_core.widget_in_toolbox_chosen is pyted_widget_types.Notebook:
                            self.proposed_widget = self.pyted_core.widget_in_toolbox_chosen.type(frame.tk_name)
                            # self.proposed_widget['height'] = 75
                            # self.proposed_widget['width'] = 100
                            self.proposed_widget_tab = tkinter.Frame(self.proposed_widget)
                            number_columns = pyted_widget_types.Frame.number_columns
                            number_rows = pyted_widget_types.Frame.number_rows
                            self.proposed_widget_tab['borderwidth'] = 2
                            self.proposed_widget_tab['relief'] = tkinter.GROOVE
                            # tk_widget[attr] = getattr(pyte_widget, attr)
                            for i_column in range(number_columns):
                                for i_row in range(number_rows):
                                    # self.new_filler_label(self.proposed_widget, i_column, i_row)
                                    new_label = ttk.Label(self.proposed_widget_tab, text=FILLER_TEXT)
                                    new_label.grid(row=i_row, column=i_column)
                                    new_label.bind("<Motion>", self.user_motion_callback)
                                    new_label.bind("<Button-1>", self.pyted_core.inserted_widget_click)
                                    # new_label.bind("<ButtonRelease-1>", self.widget_release)
                                    self.filler_labels.append(new_label)
                            self.proposed_widget.add(self.proposed_widget_tab, text='tab 1')
                        elif hasattr(self.pyted_core.widget_in_toolbox_chosen, 'text'):
                            text = self.widgets.generate_unique_name(self.pyted_core.widget_in_toolbox_chosen)
                            if hasattr(self.pyted_core.widget_in_toolbox_chosen, 'value'):
                                self.proposed_widget = self.pyted_core.widget_in_toolbox_chosen.type(frame.tk_name,
                                                                                                         text=text,
                                                                                                         value=text)
                            else:
                                self.proposed_widget = self.pyted_core.widget_in_toolbox_chosen.type(frame.tk_name,
                                                                                                         text=text)
                        else:
                            self.proposed_widget = self.pyted_core.widget_in_toolbox_chosen.type(frame.tk_name)

                        self.proposed_widget.grid(column=grid_location[0], row=grid_location[1])
                        self.proposed_widget.bind('<Motion>', self.user_motion_callback)
                        self.proposed_widget.bind('<Button-1>', self.pyted_core.inserted_widget_click)

                        widget_under_mouse.destroy()
                        # print('new inserted widget x, y', event.x_root, event.y_root, grid_location)
            # replace old proposed widget with filler label (including if mouse moved out of user_frame)
            # print('here:', old_proposed_widget_location)
            if (old_proposed_widget_location != grid_location or old_proposed_widget_frame != frame) and\
                    old_proposed_widget_location is not None:
                if old_proposed_widget is not None and old_proposed_widget != self.proposed_widget:
                    old_proposed_widget.destroy()
                    self.new_filler_label(old_proposed_widget_frame.tk_name,
                                          old_proposed_widget_location[0], old_proposed_widget_location[1])