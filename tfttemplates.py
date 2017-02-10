#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
import tftmenu
from tftutility import *

##################################################################################
# CONSTANTS
##################################################################################
BUTTON_AXIS_ROWS = 0
BUTTON_AXIS_COLUMNS = 1
BUTTON_STEP_UP = 1
BUTTON_STEP_DOWN = -1

##################################################################################
# Button Templates
##################################################################################
# Buttons2x3Headers is a 2 column x 3 row grid of buttons under a header for text
Buttons2x3Headers = {DisplayResolution.Small320x240:
                     {ButtonTuple.Columns: 2,
                      ButtonTuple.Rows: 3,
                      ButtonTuple.ColumnsStart: 10,
                      ButtonTuple.RowsStart: 55,
                      ButtonTuple.ColumnsSpacing: 6,
                      ButtonTuple.RowsSpacing: 6,
                      ButtonTuple.Width: 147,
                      ButtonTuple.Height: 54},
                     DisplayResolution.Large480x320:
                     {ButtonTuple.Columns: 2,
                      ButtonTuple.Rows: 3,
                      ButtonTuple.ColumnsStart: 14,
                      ButtonTuple.RowsStart: 64,
                      ButtonTuple.ColumnsSpacing: 8,
                      ButtonTuple.RowsSpacing: 8,
                      ButtonTuple.Width: 222,
                      ButtonTuple.Height: 75}
                     }

Buttons2x2HeaderFooter = {DisplayResolution.Small320x240:
                          {ButtonTuple.Columns: 2,
                           ButtonTuple.Rows: 2,
                           ButtonTuple.ColumnsStart: 10,
                           ButtonTuple.RowsStart: 63,
                           ButtonTuple.ColumnsSpacing: 6,
                           ButtonTuple.RowsSpacing: 6,
                           ButtonTuple.Width: 147,
                           ButtonTuple.Height: 54},
                          DisplayResolution.Large480x320:
                          {ButtonTuple.Columns: 2,
                           ButtonTuple.Rows: 2,
                           ButtonTuple.ColumnsStart: 14,
                           ButtonTuple.RowsStart: 81,
                           ButtonTuple.ColumnsSpacing: 8,
                           ButtonTuple.RowsSpacing: 8,
                           ButtonTuple.Width: 222,
                           ButtonTuple.Height: 75}
                          }

# Buttons3x3Headers is a 3 column x 3 row grid of buttons under a header for text
Buttons3x3Headers = {DisplayResolution.Small320x240:
                     {ButtonTuple.Columns: 3,
                      ButtonTuple.Rows: 3,
                      ButtonTuple.ColumnsStart: 11,
                      ButtonTuple.RowsStart: 55,
                      ButtonTuple.ColumnsSpacing: 6,
                      ButtonTuple.RowsSpacing: 6,
                      ButtonTuple.Width: 96,
                      ButtonTuple.Height: 54},
                     DisplayResolution.Large480x320:
                     {ButtonTuple.Columns: 3,
                      ButtonTuple.Rows: 3,
                      ButtonTuple.ColumnsStart: 14,
                      ButtonTuple.RowsStart: 64,
                      ButtonTuple.ColumnsSpacing: 8,
                      ButtonTuple.RowsSpacing: 8,
                      ButtonTuple.Width: 145,
                      ButtonTuple.Height: 75}
                     }

Buttons3x2HeaderFooter = {DisplayResolution.Small320x240:
                          {ButtonTuple.Columns: 3,
                           ButtonTuple.Rows: 2,
                           ButtonTuple.ColumnsStart: 11,
                           ButtonTuple.RowsStart: 55,
                           ButtonTuple.ColumnsSpacing: 6,
                           ButtonTuple.RowsSpacing: 6,
                           ButtonTuple.Width: 96,
                           ButtonTuple.Height: 54},
                          DisplayResolution.Large480x320:
                          {ButtonTuple.Columns: 3,
                           ButtonTuple.Rows: 2,
                           ButtonTuple.ColumnsStart: 14,
                           ButtonTuple.RowsStart: 64,
                           ButtonTuple.ColumnsSpacing: 8,
                           ButtonTuple.RowsSpacing: 8,
                           ButtonTuple.Width: 145,
                           ButtonTuple.Height: 75}
                          }

# Buttons2x4FullScreen is a full screen, 2 column x 4 row grid of buttons
Buttons2x4FullScreen = {DisplayResolution.Small320x240:
                        {ButtonTuple.Columns: 2,
                         ButtonTuple.Rows: 4,
                         ButtonTuple.ColumnsStart: 11,
                         ButtonTuple.RowsStart: 11,
                         ButtonTuple.ColumnsSpacing: 8,
                         ButtonTuple.RowsSpacing: 6,
                         ButtonTuple.Width: 145,
                         ButtonTuple.Height: 50},
                        DisplayResolution.Large480x320:
                        {ButtonTuple.Columns: 2,
                         ButtonTuple.Rows: 4,
                         ButtonTuple.ColumnsStart: 14,
                         ButtonTuple.RowsStart: 14,
                         ButtonTuple.ColumnsSpacing: 8,
                         ButtonTuple.RowsSpacing: 8,
                         ButtonTuple.Width: 222,
                         ButtonTuple.Height: 67}
                        }

# Buttons3x4FullScreen is a full screen, 3 column x 4 row grid of buttons
Buttons3x4FullScreen = {DisplayResolution.Small320x240:
                        {ButtonTuple.Columns: 3,
                         ButtonTuple.Rows: 4,
                         ButtonTuple.ColumnsStart: 11,
                         ButtonTuple.RowsStart: 11,
                         ButtonTuple.ColumnsSpacing: 8,
                         ButtonTuple.RowsSpacing: 6,
                         ButtonTuple.Width: 94,
                         ButtonTuple.Height: 50},
                        DisplayResolution.Large480x320:
                        {ButtonTuple.Columns: 3,
                         ButtonTuple.Rows: 4,
                         ButtonTuple.ColumnsStart: 14,
                         ButtonTuple.RowsStart: 14,
                         ButtonTuple.ColumnsSpacing: 8,
                         ButtonTuple.RowsSpacing: 8,
                         ButtonTuple.Width: 145,
                         ButtonTuple.Height: 67}
                        }

# Buttons4x4FullScreen is a full screen, 4 column x 4 row grid of buttons
Buttons4x4FullScreen = {DisplayResolution.Small320x240:
                        {ButtonTuple.Columns: 4,
                         ButtonTuple.Rows: 4,
                         ButtonTuple.ColumnsStart: 11,
                         ButtonTuple.RowsStart: 11,
                         ButtonTuple.ColumnsSpacing: 6,
                         ButtonTuple.RowsSpacing: 6,
                         ButtonTuple.Width: 70,
                         ButtonTuple.Height: 50},
                        DisplayResolution.Large480x320:
                        {ButtonTuple.Columns: 4,
                         ButtonTuple.Rows: 4,
                         ButtonTuple.ColumnsStart: 14,
                         ButtonTuple.RowsStart: 14,
                         ButtonTuple.ColumnsSpacing: 8,
                         ButtonTuple.RowsSpacing: 8,
                         ButtonTuple.Width: 107,
                         ButtonTuple.Height: 67}
                        }

# Buttons2x1Bottom is a 2 column x 1 row grid of buttons located at the bottom
Buttons1x1Bottom = {DisplayResolution.Small320x240:
                    {ButtonTuple.Columns: 1,
                     ButtonTuple.Rows: 1,
                     ButtonTuple.ColumnsStart: 87,
                     ButtonTuple.RowsStart: 175,
                     ButtonTuple.ColumnsSpacing: 0,
                     ButtonTuple.RowsSpacing: 0,
                     ButtonTuple.Width: 146,
                     ButtonTuple.Height: 54},
                    DisplayResolution.Large480x320:
                    {ButtonTuple.Columns: 1,
                     ButtonTuple.Rows: 1,
                     ButtonTuple.ColumnsStart: 129,
                     ButtonTuple.RowsStart: 231,
                     ButtonTuple.ColumnsSpacing: 0,
                     ButtonTuple.RowsSpacing: 0,
                     ButtonTuple.Width: 222,
                     ButtonTuple.Height: 75}
                    }

Buttons1x1BottomLeft = {DisplayResolution.Small320x240:
                        {ButtonTuple.Columns: 1,
                         ButtonTuple.Rows: 1,
                         ButtonTuple.ColumnsStart: 164,
                         ButtonTuple.RowsStart: 175,
                         ButtonTuple.ColumnsSpacing: 0,
                         ButtonTuple.RowsSpacing: 0,
                         ButtonTuple.Width: 145,
                         ButtonTuple.Height: 54},
                        DisplayResolution.Large480x320:
                        {ButtonTuple.Columns: 1,
                         ButtonTuple.Rows: 1,
                         ButtonTuple.ColumnsStart: 244,
                         ButtonTuple.RowsStart: 231,
                         ButtonTuple.ColumnsSpacing: 0,
                         ButtonTuple.RowsSpacing: 0,
                         ButtonTuple.Width: 222,
                         ButtonTuple.Height: 75}
                        }

Buttons1x1BottomRight = {DisplayResolution.Small320x240:
                         {ButtonTuple.Columns: 1,
                          ButtonTuple.Rows: 1,
                          ButtonTuple.ColumnsStart: 11,
                          ButtonTuple.RowsStart: 175,
                          ButtonTuple.ColumnsSpacing: 0,
                          ButtonTuple.RowsSpacing: 0,
                          ButtonTuple.Width: 145,
                          ButtonTuple.Height: 54},
                         DisplayResolution.Large480x320:
                         {ButtonTuple.Columns: 1,
                          ButtonTuple.Rows: 1,
                          ButtonTuple.ColumnsStart: 247,
                          ButtonTuple.RowsStart: 231,
                          ButtonTuple.ColumnsSpacing: 0,
                          ButtonTuple.RowsSpacing: 0,
                          ButtonTuple.Width: 222,
                          ButtonTuple.Height: 75}
                         }

Buttons1x1BottomFullWidth = {DisplayResolution.Small320x240:
                             {ButtonTuple.Columns: 1,
                              ButtonTuple.Rows: 1,
                              ButtonTuple.ColumnsStart: 11,
                              ButtonTuple.RowsStart: 175,
                              ButtonTuple.ColumnsSpacing: 0,
                              ButtonTuple.RowsSpacing: 0,
                              ButtonTuple.Width: 298,
                              ButtonTuple.Height: 54},
                             DisplayResolution.Large480x320:
                             {ButtonTuple.Columns: 1,
                              ButtonTuple.Rows: 1,
                              ButtonTuple.ColumnsStart: 14,
                              ButtonTuple.RowsStart: 231,
                              ButtonTuple.ColumnsSpacing: 0,
                              ButtonTuple.RowsSpacing: 0,
                              ButtonTuple.Width: 452,
                              ButtonTuple.Height: 75}
                             }

# Buttons2x1Bottom is a 2 column x 1 row grid of buttons located at the bottom
Buttons2x1Bottom = {DisplayResolution.Small320x240:
                    {ButtonTuple.Columns: 2,
                     ButtonTuple.Rows: 1,
                     ButtonTuple.ColumnsStart: 11,
                     ButtonTuple.RowsStart: 175,
                     ButtonTuple.ColumnsSpacing: 8,
                     ButtonTuple.RowsSpacing: 6,
                     ButtonTuple.Width: 145,
                     ButtonTuple.Height: 54},
                    DisplayResolution.Large480x320:
                    {ButtonTuple.Columns: 2,
                     ButtonTuple.Rows: 1,
                     ButtonTuple.ColumnsStart: 14,
                     ButtonTuple.RowsStart: 231,
                     ButtonTuple.ColumnsSpacing: 8,
                     ButtonTuple.RowsSpacing: 8,
                     ButtonTuple.Width: 222,
                     ButtonTuple.Height: 75}
                    }

# Buttons2x1Bottom is a 3 column x 1 row grid of buttons located at the bottom
Buttons3x1Bottom = {DisplayResolution.Small320x240:
                    {ButtonTuple.Columns: 3,
                     ButtonTuple.Rows: 1,
                     ButtonTuple.ColumnsStart: 11,
                     ButtonTuple.RowsStart: 175,
                     ButtonTuple.ColumnsSpacing: 8,
                     ButtonTuple.RowsSpacing: 6,
                     ButtonTuple.Width: 94,
                     ButtonTuple.Height: 54},
                    DisplayResolution.Large480x320:
                    {ButtonTuple.Columns: 3,
                     ButtonTuple.Rows: 1,
                     ButtonTuple.ColumnsStart: 14,
                     ButtonTuple.RowsStart: 231,
                     ButtonTuple.ColumnsSpacing: 8,
                     ButtonTuple.RowsSpacing: 8,
                     ButtonTuple.Width: 145,
                     ButtonTuple.Height: 75}
                    }

ButtonsFullScreen = {DisplayResolution.Small320x240:
                     {ButtonTuple.Columns: 1,
                      ButtonTuple.Rows: 1,
                      ButtonTuple.ColumnsStart: 0,
                      ButtonTuple.RowsStart: 0,
                      ButtonTuple.ColumnsSpacing: 0,
                      ButtonTuple.RowsSpacing: 0,
                      ButtonTuple.Width: 320,
                      ButtonTuple.Height: 240},
                     DisplayResolution.Large480x320:
                     {ButtonTuple.Columns: 1,
                      ButtonTuple.Rows: 1,
                      ButtonTuple.ColumnsStart: 0,
                      ButtonTuple.RowsStart: 0,
                      ButtonTuple.ColumnsSpacing: 0,
                      ButtonTuple.RowsSpacing: 0,
                      ButtonTuple.Width: 480,
                      ButtonTuple.Height: 320},
                     }

button_templates = ([Buttons2x3Headers,
                     Buttons2x2HeaderFooter,
                     Buttons3x3Headers,
                     Buttons3x2HeaderFooter,
                     Buttons2x4FullScreen,
                     Buttons3x4FullScreen,
                     Buttons4x4FullScreen,
                     Buttons1x1Bottom,
                     Buttons1x1BottomLeft,
                     Buttons1x1BottomRight,
                     Buttons1x1BottomFullWidth,
                     Buttons2x1Bottom,
                     Buttons3x1Bottom,
                     ButtonsFullScreen])


def get_buttons(template, direction=ButtonDirection.LeftRightTopBottom, blank=False, names=None, actions=None, 
                actions_right=None, background_color=None, border_color=None, border_width=None, font=None,
                font_color=None, font_size=None, font_h_align=None, font_v_align=None, font_h_padding=None, 
                font_v_padding=None, font_pad=False):
    if names is None:
        names = []
    if actions is None:
        actions = []
    if actions_right is None:
        actions_right = []
    if background_color is None:
        background_color = Defaults.default_background_color
    if border_color is None:
        border_color = Defaults.default_border_color
    if border_width is None:
        border_width = Defaults.default_button_border_width
    if font is None:
        font = Defaults.default_button_font
    if font_color is None:
        font_color = Defaults.default_button_font_color
    if font_size is None:
        font_size = Defaults.default_button_font_size
    if font_h_align is None:
        font_h_align = Defaults.default_button_font_h_align
    if font_v_align is None:
        font_v_align = Defaults.default_button_font_v_align
    if font_h_padding is None:
        font_h_padding = Defaults.default_button_font_h_padding
    if font_v_padding is None:
        font_v_padding = Defaults.default_button_font_v_padding
    button_template = button_templates[template][Defaults.tft_resolution]
    buttons = []
    button_id = 0
    axis_primary = BUTTON_AXIS_ROWS
    axis_primary_start = 0
    axis_primary_end = 0
    axis_primary_step = BUTTON_STEP_UP
    axis_secondary_start = 0
    axis_secondary_end = 0
    axis_secondary_step = BUTTON_STEP_UP
    width = button_template[ButtonTuple.Width]
    width_spacing = width + button_template[ButtonTuple.ColumnsSpacing]
    height = button_template[ButtonTuple.Height]
    height_spacing = height + button_template[ButtonTuple.RowsSpacing]
    rows = button_template[ButtonTuple.Rows]
    cols = button_template[ButtonTuple.Columns]
    x_start = button_template[ButtonTuple.ColumnsStart]
    y_start = button_template[ButtonTuple.RowsStart]
    # Code to create the buttons in the correct direction.  Default is defined in the get_buttons call and is
    # set to BUTTON_DIR_LEFT_RIGHT_TOP_BOTTOM.   See pattern comments to see how a 3x3 grid of buttons would be
    # built using a particular direction.
    if direction == ButtonDirection.LeftRightTopBottom:    # 1 2 3
        axis_primary_end = rows                            # 4 5 6
        axis_secondary_end = cols                          # 7 8 9
    elif direction == ButtonDirection.RightLeftTopBottom:
        axis_primary_end = rows                            # 3 2 1
        axis_secondary_start = cols - 1                    # 6 5 4
        axis_secondary_end -= 1                            # 7 8 9
        axis_secondary_step = BUTTON_STEP_DOWN
    elif direction == ButtonDirection.TopBottomLeftRight:  # 1 4 7
        axis_primary = BUTTON_AXIS_COLUMNS                 # 2 5 8
        axis_primary_end = cols                            # 3 6 9
        axis_secondary_end = rows
    elif direction == ButtonDirection.TopBottomRightLeft:  # 7 4 1
        axis_primary = BUTTON_AXIS_COLUMNS                 # 8 5 2
        axis_primary_start = cols - 1                      # 9 6 3
        axis_primary_end -= 1
        axis_primary_step = BUTTON_STEP_DOWN
        axis_secondary_end = rows
    elif direction == ButtonDirection.LeftRightBottomTop:  # 7 8 9
        axis_primary_start = rows - 1                      # 4 5 6
        axis_primary_end -= 1                              # 1 2 3
        axis_primary_step = BUTTON_STEP_DOWN
        axis_secondary_end = cols
    elif direction == ButtonDirection.RightLeftBottomTop:  # 9 8 7
        axis_primary_start = rows - 1                      # 6 5 4
        axis_primary_end -= 1                              # 3 2 1
        axis_primary_step = BUTTON_STEP_DOWN
        axis_secondary_start = cols - 1
        axis_secondary_end -= 1
        axis_secondary_step = BUTTON_STEP_DOWN
    elif direction == ButtonDirection.BottomTopLeftRight:  # 3 6 9
        axis_primary = BUTTON_AXIS_COLUMNS                 # 2 5 8
        axis_primary_end = cols                            # 1 4 7
        axis_secondary_start = rows - 1
        axis_secondary_end -= 1
        axis_secondary_step = BUTTON_STEP_DOWN
    elif direction == ButtonDirection.BottomTopRightLeft:  # 9 6 3
        axis_primary = BUTTON_AXIS_COLUMNS                 # 8 5 2
        axis_primary_start = cols - 1                      # 7 4 1
        axis_primary_end -= 1
        axis_primary_step = BUTTON_STEP_DOWN
        axis_secondary_start = rows - 1
        axis_secondary_end -= 1
        axis_secondary_step = BUTTON_STEP_DOWN
    else:
        logger.warning("Invalid Button Direction.  Using default of Left to Right then Top to Bottom")
        axis_primary_end = rows
        axis_secondary_end = cols
    for primary in range(axis_primary_start, axis_primary_end, axis_primary_step):
        for secondary in range(axis_secondary_start, axis_secondary_end, axis_secondary_step):
            if blank:
                text = None
            elif len(names) - 1 >= button_id:
                text = names[button_id]
            else:
                text = unicode(button_id + 1)
            if actions and len(actions) - 1 >= button_id:
                action = actions[button_id]
            else:
                action = tftmenu.Action(DisplayAction.NoAction)
            if actions_right is not None and actions_right and len(actions_right) - 1 >= button_id:
                action_right = actions_right[button_id]
            else:
                action_right = None
            if isinstance(background_color, list):
                if len(background_color) - 1 < button_id or background_color[button_id] is None:
                    temp_background_color = Defaults.default_background_color
                else:
                    temp_background_color = background_color[button_id]            
            else:
                temp_background_color = background_color
            if isinstance(border_color, list):
                if len(border_color) - 1 < button_id or border_color[button_id] is None:
                    temp_border_color = Defaults.default_button_border_color
                else:
                    temp_border_color = border_color[button_id]            
            else:
                temp_border_color = border_color
            if isinstance(border_width, list):
                if len(border_width) - 1 < button_id or border_width[button_id] is None:
                    temp_border_width = Defaults.default_button_border_width
                else:
                    temp_border_width = border_width[button_id]            
            else:
                temp_border_width = border_width
            if isinstance(font, list):
                if len(font) - 1 < button_id or font[button_id] is None:
                    temp_font = Defaults.default_button_font
                else:
                    temp_font = font[button_id]            
            else:
                temp_font = font
            if isinstance(font_color, list):
                if len(font_color) - 1 < button_id or font_color[button_id] is None:
                    temp_font_color = Defaults.default_button_font_color
                else:
                    temp_font_color = font_color[button_id]            
            else:
                temp_font_color = font_color
            if isinstance(font_size, list):
                if len(font_size) - 1 < button_id or font_size[button_id] is None:
                    temp_font_size = Defaults.default_button_font_size
                else:
                    temp_font_size = font_size[button_id]            
            else:
                temp_font_size = font_size
            if isinstance(font_h_align, list):
                if len(font_h_align) - 1 < button_id or font_h_align[button_id] is None:
                    temp_font_align = Defaults.default_button_font_h_align
                else:
                    temp_font_align = font_h_align[button_id]
            else:
                temp_font_align = font_h_align
            if isinstance(font_h_padding, list):
                if len(font_h_padding) - 1 < button_id or font_h_padding[button_id] is None:
                    temp_font_h_padding = Defaults.default_button_font_h_padding
                else:
                    temp_font_h_padding = font_h_padding[button_id]
            else:
                temp_font_h_padding = font_h_padding
            if isinstance(font_v_align, list):
                if len(font_v_align) - 1 < button_id or font_v_align[button_id] is None:
                    temp_font_valign = Defaults.default_button_font_v_align
                else:
                    temp_font_valign = font_v_align[button_id]
            else:
                temp_font_valign = font_v_align
            if isinstance(font_v_padding, list):
                if len(font_v_padding) - 1 < button_id or font_v_padding[button_id] is None:
                    temp_font_v_padding = Defaults.default_button_font_v_padding
                else:
                    temp_font_v_padding = font_v_padding[button_id]
            else:
                temp_font_v_padding = font_v_padding
            if axis_primary == BUTTON_AXIS_ROWS:
                buttons.append(
                    tftmenu.Button(tftmenu.ButtonLine(text=text, font_size=temp_font_size, font_color=temp_font_color,
                                                      font=temp_font, font_h_align=temp_font_align,
                                                      font_h_padding=temp_font_h_padding, font_v_align=temp_font_valign,
                                                      font_v_padding=temp_font_v_padding, font_pad=font_pad),
                                   x_start + (secondary * width_spacing), y_start + (primary * height_spacing),
                                   width, height, temp_background_color, temp_border_color, temp_border_width,
                                   action, action_right))
            else:
                buttons.append(
                    tftmenu.Button(tftmenu.ButtonLine(text=text, font_size=temp_font_size, font_color=temp_font_color,
                                                      font=temp_font, font_h_align=temp_font_align,
                                                      font_h_padding=temp_font_h_padding, font_v_align=temp_font_valign,
                                                      font_v_padding=temp_font_v_padding, font_pad=font_pad),
                                   x_start + (primary * width_spacing), y_start + (secondary * height_spacing),
                                   width, height, temp_background_color, temp_border_color, temp_border_width,
                                   action, action_right))
            button_id += 1
    return buttons
