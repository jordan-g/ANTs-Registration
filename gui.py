import numpy as np
import sys
import nibabel as nib
import pyqtgraph as pg
import cv2
import subprocess
import matplotlib.cm as cm

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from controller import Controller

class PreviewWindow(QMainWindow):
    def __init__(self, controller):
        QMainWindow.__init__(self)

        self.controller = controller

        self.controller.preview_window = self

        self.fixed_image_z  = 0
        self.moving_image_z = 0

        self.overlay_alpha = 0.5

        self.fixed_image         = None
        self.moving_image        = None
        self.warped_moving_image = None

        self.moving_image_channel = 0
        self.warped_moving_image_channel = 0

        # Create main widget
        self.main_widget = QWidget(self)
        self.main_widget.setMinimumSize(QSize(1300, 700))
        self.resize(1300, 700)

        # Create main layout
        self.main_layout = QGridLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # create heading widgets
        widget = self.create_heading_widget("Fixed Image ▼")
        self.main_layout.addWidget(widget, 0, 0)

        widget = self.create_heading_widget("Moving Image ▼")
        self.main_layout.addWidget(widget, 0, 1)

        widget = self.create_heading_widget("Warped Moving Image ▼")
        self.main_layout.addWidget(widget, 0, 2)

        # Create PyQTGraph widget
        self.pg_widget = pg.GraphicsLayoutWidget()
        self.pg_widget.setBackground(None)
        self.pg_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.pg_widget.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.main_layout.addWidget(self.pg_widget, 1, 0, 1, 3)

        self.fixed_image_viewbox = self.pg_widget.addViewBox(lockAspect=True, name='fixed_image', row=0, col=0, invertY=True)
        self.fixed_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.fixed_image_viewbox.setBackgroundColor((255, 255, 255, 50))
        self.fixed_image_item = pg.ImageItem()
        self.fixed_image_viewbox.addItem(self.fixed_image_item)

        self.moving_image_viewbox = self.pg_widget.addViewBox(lockAspect=True, name='moving_image', row=0, col=1, invertY=True)
        self.moving_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.moving_image_viewbox.setBackgroundColor((255, 255, 255, 50))
        self.moving_image_item = pg.ImageItem()
        self.moving_image_viewbox.addItem(self.moving_image_item)

        self.warped_moving_image_viewbox = self.pg_widget.addViewBox(lockAspect=True, name='warped_moving_image', row=0, col=2, invertY=True)
        self.warped_moving_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.warped_moving_image_viewbox.setBackgroundColor((255, 255, 255, 50))
        self.warped_moving_image_item = pg.ImageItem()
        self.warped_moving_image_viewbox.addItem(self.warped_moving_image_item)

        self.fixed_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.moving_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.warped_moving_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)

        # self.moving_image_viewbox.setXLink('fixed_image')
        # self.moving_image_viewbox.setYLink('fixed_image')

        self.warped_moving_image_viewbox.setYLink('fixed_image')
        self.warped_moving_image_viewbox.setYLink('fixed_image')

        # self.bottom_widget = QWidget(self)
        # self.main_layout.addWidget(self.bottom_widget)
        # self.bottom_layout = QHBoxLayout(self.bottom_widget)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        label = QLabel("Z: ")
        layout.addWidget(label)
        self.fixed_image_z_slider = QSlider()
        self.fixed_image_z_slider = QSlider(Qt.Horizontal)
        self.fixed_image_z_slider.setFocusPolicy(Qt.StrongFocus)
        self.fixed_image_z_slider.setTickPosition(QSlider.NoTicks)
        self.fixed_image_z_slider.setTickInterval(1)
        self.fixed_image_z_slider.setSingleStep(1)
        self.fixed_image_z_slider.setMinimum(0)
        self.fixed_image_z_slider.setMaximum(0)
        self.fixed_image_z_slider.setValue(0)
        self.fixed_image_z_slider.sliderMoved.connect(self.update_fixed_image_z)
        self.fixed_image_z_slider.sliderReleased.connect(self.update_fixed_image_z)
        layout.addWidget(self.fixed_image_z_slider)
        self.main_layout.addWidget(widget, 2, 0)
        
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        label = QLabel("Z: ")
        layout.addWidget(label)
        self.moving_image_z_slider = QSlider()
        self.moving_image_z_slider = QSlider(Qt.Horizontal)
        self.moving_image_z_slider.setFocusPolicy(Qt.StrongFocus)
        self.moving_image_z_slider.setTickPosition(QSlider.NoTicks)
        self.moving_image_z_slider.setTickInterval(1)
        self.moving_image_z_slider.setSingleStep(1)
        self.moving_image_z_slider.setMinimum(0)
        self.moving_image_z_slider.setMaximum(0)
        self.moving_image_z_slider.setValue(0)
        self.moving_image_z_slider.sliderMoved.connect(self.update_moving_image_z)
        self.moving_image_z_slider.sliderReleased.connect(self.update_moving_image_z)
        layout.addWidget(self.moving_image_z_slider)
        self.main_layout.addWidget(widget, 2, 1)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        label = QLabel("Z: ")
        layout.addWidget(label)
        self.warped_moving_image_z_slider = QSlider()
        self.warped_moving_image_z_slider = QSlider(Qt.Horizontal)
        self.warped_moving_image_z_slider.setFocusPolicy(Qt.StrongFocus)
        self.warped_moving_image_z_slider.setTickPosition(QSlider.NoTicks)
        self.warped_moving_image_z_slider.setTickInterval(1)
        self.warped_moving_image_z_slider.setSingleStep(1)
        self.warped_moving_image_z_slider.setMinimum(0)
        self.warped_moving_image_z_slider.setMaximum(0)
        self.warped_moving_image_z_slider.setValue(0)
        self.warped_moving_image_z_slider.sliderMoved.connect(self.update_warped_moving_image_z)
        self.warped_moving_image_z_slider.sliderReleased.connect(self.update_warped_moving_image_z)
        layout.addWidget(self.warped_moving_image_z_slider)
        self.main_layout.addWidget(widget, 2, 2)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        label = QLabel("Channel: ")
        layout.addWidget(label)
        self.moving_image_channel_combobox = QComboBox()
        self.moving_image_channel_combobox.currentIndexChanged.connect(self.update_moving_image_channel)
        layout.addWidget(self.moving_image_channel_combobox)
        self.main_layout.addWidget(widget, 3, 1)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        label = QLabel("Channel: ")
        layout.addWidget(label)
        self.warped_moving_image_channel_combobox = QComboBox()
        self.warped_moving_image_channel_combobox.currentIndexChanged.connect(self.update_warped_moving_image_channel)
        layout.addWidget(self.warped_moving_image_channel_combobox)
        self.main_layout.addWidget(widget, 3, 2)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.registration_channel_checkbox = QCheckBox("Use this channel for registration")
        self.registration_channel_checkbox.clicked.connect(self.toggle_registration_channel)
        self.registration_channel_checkbox.setChecked(True)
        layout.addWidget(self.registration_channel_checkbox)
        self.main_layout.addWidget(widget, 4, 1)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        label = QLabel("Alpha: ")
        layout.addWidget(label)
        self.overlay_alpha_slider = QSlider()
        self.overlay_alpha_slider = QSlider(Qt.Horizontal)
        self.overlay_alpha_slider.setFocusPolicy(Qt.StrongFocus)
        self.overlay_alpha_slider.setTickPosition(QSlider.NoTicks)
        self.overlay_alpha_slider.setTickInterval(1)
        self.overlay_alpha_slider.setSingleStep(1)
        self.overlay_alpha_slider.setMinimum(0)
        self.overlay_alpha_slider.setMaximum(100)
        self.overlay_alpha_slider.setValue(50)
        self.overlay_alpha_slider.sliderMoved.connect(self.update_overlay_alpha)
        self.overlay_alpha_slider.sliderReleased.connect(self.update_overlay_alpha)
        layout.addWidget(self.overlay_alpha_slider)
        self.main_layout.addWidget(widget, 4, 2)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.select_moving_image_button = QPushButton("Add moving image channel(s)...")
        self.select_moving_image_button.clicked.connect(self.select_moving_image)
        layout.addWidget(self.select_moving_image_button)
        layout.addStretch()
        self.delete_moving_image_button = QPushButton("Remove channel")
        self.delete_moving_image_button.clicked.connect(self.delete_moving_image)
        layout.addWidget(self.delete_moving_image_button)
        self.main_layout.addWidget(widget, 5, 1)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.select_warped_moving_image_button = QPushButton("Add warped image channel(s)...")
        self.select_warped_moving_image_button.clicked.connect(self.select_warped_moving_image)
        layout.addWidget(self.select_warped_moving_image_button)
        layout.addStretch()
        self.delete_warped_moving_image_button = QPushButton("Remove channel")
        self.delete_warped_moving_image_button.clicked.connect(self.delete_warped_moving_image)
        layout.addWidget(self.delete_warped_moving_image_button)
        self.main_layout.addWidget(widget, 5, 2)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(25, 0, 25, 0)
        self.translation_checkbox = QCheckBox("Translation")
        self.translation_checkbox.clicked.connect(self.toggle_translation)
        self.translation_checkbox.setChecked(self.controller.params["translation"])
        layout.addWidget(self.translation_checkbox)
        layout.addStretch()
        self.rigid_checkbox = QCheckBox("Rigid")
        self.rigid_checkbox.clicked.connect(self.toggle_rigid)
        self.rigid_checkbox.setChecked(self.controller.params["rigid"])
        layout.addWidget(self.rigid_checkbox)
        layout.addStretch()
        self.affine_checkbox = QCheckBox("Affine")
        self.affine_checkbox.clicked.connect(self.toggle_affine)
        self.affine_checkbox.setChecked(self.controller.params["affine"])
        layout.addWidget(self.affine_checkbox)
        layout.addStretch()
        self.syn_checkbox = QCheckBox("SyN")
        self.syn_checkbox.clicked.connect(self.toggle_syn)
        self.syn_checkbox.setChecked(self.controller.params["syn"])
        layout.addWidget(self.syn_checkbox)
        self.main_layout.addWidget(widget, 6, 2)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        # layout.addStretch()
        self.select_fixed_image_button = QPushButton("Select fixed image...")
        self.select_fixed_image_button.clicked.connect(self.select_fixed_image)
        layout.addWidget(self.select_fixed_image_button)
        layout.addStretch()
        self.main_layout.addWidget(widget, 7, 0)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.syn_params_button = QPushButton("Parameters...")
        self.syn_params_button.clicked.connect(self.show_params)
        layout.addWidget(self.syn_params_button)
        layout.addStretch()
        self.show_shell_command_button = QPushButton("Show Shell Command...")
        self.show_shell_command_button.clicked.connect(self.show_shell_command)
        layout.addWidget(self.show_shell_command_button)
        layout.addStretch()
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.controller.register)
        self.register_button.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.register_button)
        self.main_layout.addWidget(widget, 7, 2)

        self.setCentralWidget(self.main_widget)

        self.shell_command_window = ShellCommandWindow()
        self.param_window = ParamWindow(self, self.controller)

        self.show()

    def create_heading_widget(self, text):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        layout.addStretch()
        label = QLabel(text)
        layout.addWidget(label)
        layout.addStretch()

        return widget

    def update_fixed_image(self, image):
        if self.fixed_image_z >= image.shape[2]:
            self.fixed_image_z = 0
            self.fixed_image_z_slider.setValue(self.fixed_image_z)

        self.fixed_image = image.astype(np.uint8)
        if len(self.fixed_image.shape) > 3:
            self.fixed_image = self.fixed_image[:, :, :, 0]
        self.fixed_image_item.setImage(cv2.cvtColor(self.fixed_image[:, :, self.fixed_image_z], cv2.COLOR_GRAY2RGB), levels=(0, 255))
        self.fixed_image_viewbox.autoRange()

        self.fixed_image_z_slider.setMaximum(self.fixed_image.shape[2]-1)
        self.warped_moving_image_z_slider.setMaximum(self.fixed_image.shape[2]-1)
    
    def update_moving_image(self, image):
        if self.moving_image_z >= image.shape[2]:
            self.moving_image_z = 0
            self.moving_image_z_slider.setValue(self.moving_image_z)

        self.moving_image = image.astype(np.uint8)
        if len(self.moving_image.shape) > 3:
            self.moving_image = self.moving_image[:, :, :, 0]
        self.moving_image_item.setImage(cv2.cvtColor(self.moving_image[:, :, self.moving_image_z], cv2.COLOR_GRAY2RGB), levels=(0, 255))
        self.moving_image_viewbox.autoRange()

        self.moving_image_z_slider.setMaximum(self.moving_image.shape[2]-1)
    
    def update_warped_moving_image(self, image):
        self.warped_moving_image = image.astype(np.uint8)
        if len(self.warped_moving_image.shape) > 3:
            self.warped_moving_image = self.warped_moving_image[:, :, :, 0]

        fixed_image = cv2.cvtColor(self.fixed_image[:, :, self.fixed_image_z], cv2.COLOR_GRAY2RGB)

        cm_hot = cm.get_cmap('hot')
        image = (cm_hot(self.warped_moving_image[:, :, self.fixed_image_z])*255.0)[:, :, :3].astype(np.uint8)

        alpha = 0.5

        cv2.addWeighted(image, alpha, fixed_image, 1 - alpha, 0, fixed_image)

        self.warped_moving_image_item.setImage(fixed_image, levels=(0, 255))
        self.warped_moving_image_viewbox.autoRange()

        self.warped_moving_image_z_slider.setMaximum(self.warped_moving_image.shape[2]-1)

    def update_warped_moving_image_z(self):
        self.fixed_image_z = self.warped_moving_image_z_slider.sliderPosition()

        self.fixed_image_z_slider.setValue(self.fixed_image_z)

        self.fixed_image_item.setImage(cv2.cvtColor(self.fixed_image[:, :, self.fixed_image_z], cv2.COLOR_GRAY2RGB), levels=(0, 255))

        if self.warped_moving_image is not None:
            fixed_image = cv2.cvtColor(self.fixed_image[:, :, self.fixed_image_z], cv2.COLOR_GRAY2RGB)

            cm_hot = cm.get_cmap('hot')
            image = (cm_hot(self.warped_moving_image[:, :, self.fixed_image_z])*255.0)[:, :, :3].astype(np.uint8)

            cv2.addWeighted(image, self.overlay_alpha, fixed_image, 1 - self.overlay_alpha, 0, fixed_image)

            self.warped_moving_image_item.setImage(fixed_image, levels=(0, 255))

    def update_fixed_image_z(self):
        self.fixed_image_z = self.fixed_image_z_slider.sliderPosition()

        self.warped_moving_image_z_slider.setValue(self.fixed_image_z)

        self.fixed_image_item.setImage(cv2.cvtColor(self.fixed_image[:, :, self.fixed_image_z], cv2.COLOR_GRAY2RGB), levels=(0, 255))

        if self.warped_moving_image is not None:
            fixed_image = cv2.cvtColor(self.fixed_image[:, :, self.fixed_image_z], cv2.COLOR_GRAY2RGB)

            cm_hot = cm.get_cmap('hot')
            image = (cm_hot(self.warped_moving_image[:, :, self.fixed_image_z])*255.0)[:, :, :3].astype(np.uint8)

            cv2.addWeighted(image, self.overlay_alpha, fixed_image, 1 - self.overlay_alpha, 0, fixed_image)

            self.warped_moving_image_item.setImage(fixed_image, levels=(0, 255))
   
    def update_moving_image_z(self):
        self.moving_image_z = self.moving_image_z_slider.sliderPosition()

        self.moving_image_item.setImage(cv2.cvtColor(self.moving_image[:, :, self.moving_image_z], cv2.COLOR_GRAY2RGB), levels=(0, 255))

    def select_fixed_image(self):
        video_paths = QFileDialog.getOpenFileNames(self, 'Select fixed image.', '', 'NIFTI Files (*.nii )')[0]
        
        if len(video_paths) > 0:
            fixed_image = nib.load(video_paths[0]).get_fdata()
            self.update_fixed_image(fixed_image)

            self.controller.fixed_image_path = video_paths[0]

        self.update_shell_command()

    def select_moving_image(self):
        video_paths = QFileDialog.getOpenFileNames(self, 'Select moving image(s).', '', 'NIFTI Files (*.nii )')[0]

        video_paths = [ video_path for video_path in video_paths if video_path not in self.controller.moving_image_paths ]
        
        if len(video_paths) > 0:
            moving_image = nib.load(video_paths[0]).get_fdata()
            self.update_moving_image(moving_image)
            
            self.controller.add_moving_images(video_paths)

            self.moving_image_channel_combobox.addItems(video_paths)
            self.moving_image_channel_combobox.setCurrentIndex(len(self.controller.moving_image_paths)-1)
            self.moving_image_channel = len(self.controller.moving_image_paths)-1

            if len(self.controller.moving_image_paths) == 1:
                self.registration_channel_checkbox.setChecked(True)

        self.update_shell_command()

    def select_warped_moving_image(self):
        video_paths = QFileDialog.getOpenFileNames(self, 'Select warped image(s).', '', 'NIFTI Files (*.nii)')[0]

        video_paths = [ video_path for video_path in video_paths if video_path not in self.controller.warped_moving_image_paths ]
        
        if len(video_paths) > 0:
            warped_moving_image = nib.load(video_paths[0]).get_fdata()
            self.update_warped_moving_image(warped_moving_image)
            
            self.controller.add_warped_moving_images(video_paths)

            self.warped_moving_image_channel_combobox.addItems(video_paths)
            self.warped_moving_image_channel_combobox.setCurrentIndex(len(self.controller.warped_moving_image_paths)-1)
            self.warped_moving_image_channel = len(self.controller.warped_moving_image_paths)-1

    def update_warped_moving_image_combobox(self):
        self.warped_moving_image_channel_combobox.clear()
        self.warped_moving_image_channel_combobox.addItems(self.controller.warped_moving_image_paths)
        self.warped_moving_image_channel_combobox.setCurrentIndex(len(self.controller.warped_moving_image_paths)-1)
        self.warped_moving_image_channel = len(self.controller.warped_moving_image_paths)-1

    def show_warped_moving_image(self):
        try:
            warped_moving_image = nib.load(self.controller.warped_moving_image_paths[self.warped_moving_image_channel]).get_fdata()
            self.update_warped_moving_image(warped_moving_image)
        except:
            self.warped_moving_image_item.setImage(None)

    def update_moving_image_channel(self, i):
        if i >= 0:
            self.moving_image_channel = i
            moving_image = nib.load(self.controller.moving_image_paths[self.moving_image_channel]).get_fdata()
            self.update_moving_image(moving_image)

            self.registration_channel_checkbox.setChecked(i == self.controller.registration_channel)

    def update_warped_moving_image_channel(self, i):
        if i >= 0 and self.warped_moving_image is not None:
            self.warped_moving_image_channel = i
            warped_moving_image = nib.load(self.controller.warped_moving_image_paths[self.warped_moving_image_channel]).get_fdata()
            self.update_warped_moving_image(warped_moving_image)

    def delete_moving_image(self):
        self.controller.remove_moving_image(self.moving_image_channel)
        
        self.moving_image_channel_combobox.removeItem(self.moving_image_channel)

        self.moving_image_channel = 0

        self.toggle_registration_channel()

        if len(self.controller.moving_image_paths) > 0:
            self.update_moving_image_channel(self.moving_image_channel)
        else:
            self.moving_image_item.setImage(None)
            self.moving_image_z_slider.setMaximum(0)

        self.update_shell_command()

    def delete_warped_moving_image(self):
        self.controller.remove_warped_moving_image(self.warped_moving_image_channel)
        
        self.warped_moving_image_channel_combobox.removeItem(self.warped_moving_image_channel)

        self.warped_moving_image_channel = 0

        if len(self.controller.warped_moving_image_paths) > 0:
            self.update_warped_moving_image_channel(self.warped_moving_image_channel)
        else:
            self.warped_moving_image_item.setImage(None)

    def toggle_registration_channel(self):
        use_channel_for_registration = self.registration_channel_checkbox.isChecked()

        if use_channel_for_registration:
            self.controller.registration_channel = max(0, self.moving_image_channel_combobox.currentIndex())
        else:
            if len(self.controller.moving_image_paths) >= 2:
                self.controller.registration_channel = [ i for i in range(len(self.controller.moving_image_paths)) if i != self.moving_image_channel_combobox.currentIndex ][0]
            else:
                self.registration_channel_checkbox.setChecked(True)

        self.update_shell_command()

    def toggle_translation(self):
        self.controller.params["translation"] = self.translation_checkbox.isChecked()

        self.param_window.update_widgets()

        self.update_shell_command()

    def toggle_rigid(self):
        self.controller.params["rigid"] = self.rigid_checkbox.isChecked()

        self.param_window.update_widgets()

        self.update_shell_command()

    def toggle_affine(self):
        self.controller.params["affine"] = self.affine_checkbox.isChecked()

        self.param_window.update_widgets()

        self.update_shell_command()

    def toggle_syn(self):
        self.controller.params["syn"] = self.syn_checkbox.isChecked()

        self.param_window.update_widgets()

        self.update_shell_command()

    def show_params(self):
        self.param_window.show()

    def update_shell_command(self):
        self.controller.create_shell_command()
        self.shell_command_window.set_shell_command(self.controller.shell_command)

    def show_shell_command(self):
        self.shell_command_window.show()

    def update_overlay_alpha(self):
        self.overlay_alpha = self.overlay_alpha_slider.sliderPosition()/100.0

        self.update_warped_moving_image_z()

class ShellCommandWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # Create main widget
        self.main_widget = QWidget(self)
        self.resize(600, 600)

        # Create main layout
        self.main_layout = QGridLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.shell_command_text = QTextEdit()
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.shell_command_text.setCurrentFont(font)
        self.shell_command_text.setReadOnly(True)
        self.main_layout.addWidget(self.shell_command_text, 0, 0)

        self.setCentralWidget(self.main_widget)

    def set_shell_command(self, shell_command):
        self.shell_command_text.setPlainText(shell_command)

class ParamWindow(QMainWindow):
    def __init__(self, preview_window, controller):
        QMainWindow.__init__(self)

        self.controller     = controller
        self.preview_window = preview_window

        self.main_param_widgets = {}

        self.translation_param_widgets = {}
        self.translation_metric_param_widgets = {}

        self.rigid_param_widgets = {}
        self.rigid_metric_param_widgets = {}

        self.affine_param_widgets = {}
        self.affine_metric_param_widgets = {}

        self.syn_param_widgets = {}
        self.syn_metric_param_widgets = {}

        # Create main widget
        self.main_widget = QWidget(self)
        self.setFixedWidth(550)
        self.resize(600, 600)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.main_widget)
        self.scroll_area.setWidgetResizable(True)

        # Create main layout
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        main_form_widget = QWidget(self)
        self.main_form_layout = QFormLayout(main_form_widget)
        self.main_layout.addWidget(main_form_widget)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.translation_checkbox = QCheckBox("Translation")
        self.translation_checkbox.clicked.connect(self.toggle_translation)
        self.translation_checkbox.setChecked(True)
        layout.addWidget(self.translation_checkbox)
        self.main_layout.addWidget(widget)

        self.translation_group_box = QGroupBox("Translation Parameters")
        self.translation_group_layout = QVBoxLayout(self.translation_group_box)
        self.translation_group_layout.setContentsMargins(0, 0, 0, 0)
        translation_form_widget = QWidget(self)
        self.translation_group_layout.addWidget(translation_form_widget)
        self.translation_form_layout = QFormLayout(translation_form_widget)
        self.main_layout.addWidget(self.translation_group_box)

        self.translation_metric_group_box = QGroupBox()
        self.translation_metric_form_layout = QFormLayout(self.translation_metric_group_box)
        self.translation_group_layout.addWidget(self.translation_metric_group_box)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.rigid_checkbox = QCheckBox("Rigid transform")
        self.rigid_checkbox.clicked.connect(self.toggle_rigid)
        self.rigid_checkbox.setChecked(True)
        layout.addWidget(self.rigid_checkbox)
        self.main_layout.addWidget(widget)

        self.rigid_group_box = QGroupBox("Rigid Transform Parameters")
        self.rigid_group_layout = QVBoxLayout(self.rigid_group_box)
        self.rigid_group_layout.setContentsMargins(0, 0, 0, 0)
        rigid_form_widget = QWidget(self)
        self.rigid_group_layout.addWidget(rigid_form_widget)
        self.rigid_form_layout = QFormLayout(rigid_form_widget)
        self.main_layout.addWidget(self.rigid_group_box)

        self.rigid_metric_group_box = QGroupBox()
        self.rigid_metric_form_layout = QFormLayout(self.rigid_metric_group_box)
        self.rigid_group_layout.addWidget(self.rigid_metric_group_box)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.affine_checkbox = QCheckBox("Affine transform")
        self.affine_checkbox.clicked.connect(self.toggle_affine)
        self.affine_checkbox.setChecked(True)
        layout.addWidget(self.affine_checkbox)
        self.main_layout.addWidget(widget)

        self.affine_group_box = QGroupBox("Affine Transform Parameters")
        self.affine_group_layout = QVBoxLayout(self.affine_group_box)
        self.affine_group_layout.setContentsMargins(0, 0, 0, 0)
        affine_form_widget = QWidget(self)
        self.affine_group_layout.addWidget(affine_form_widget)
        self.affine_form_layout = QFormLayout(affine_form_widget)
        self.main_layout.addWidget(self.affine_group_box)

        self.affine_metric_group_box = QGroupBox()
        self.affine_metric_form_layout = QFormLayout(self.affine_metric_group_box)
        self.affine_group_layout.addWidget(self.affine_metric_group_box)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        self.syn_checkbox = QCheckBox("SyN transform")
        self.syn_checkbox.clicked.connect(self.toggle_syn)
        self.syn_checkbox.setChecked(True)
        layout.addWidget(self.syn_checkbox)
        self.main_layout.addWidget(widget)

        self.syn_group_box = QGroupBox("SyN Transform Parameters")
        self.syn_group_layout = QVBoxLayout(self.syn_group_box)
        self.syn_group_layout.setContentsMargins(0, 0, 0, 0)
        syn_form_widget = QWidget(self)
        self.syn_group_layout.addWidget(syn_form_widget)
        self.syn_form_layout = QFormLayout(syn_form_widget)
        self.main_layout.addWidget(self.syn_group_box)

        self.syn_metric_group_box = QGroupBox()
        self.syn_metric_form_layout = QFormLayout(self.syn_metric_group_box)
        self.syn_group_layout.addWidget(self.syn_metric_group_box)

        self.main_layout.addStretch()

        self.update_widgets()

        self.setCentralWidget(self.scroll_area)

    def toggle_translation(self):
        self.preview_window.translation_checkbox.setChecked(self.translation_checkbox.isChecked())
        self.translation_group_box.setEnabled(self.translation_checkbox.isChecked())

        self.controller.params["translation"] = self.translation_checkbox.isChecked()

        self.preview_window.update_shell_command()

        self.update_form_layout(self.translation_metric_form_layout)
        self.update_form_layout(self.translation_form_layout)

    def toggle_rigid(self):
        self.preview_window.rigid_checkbox.setChecked(self.rigid_checkbox.isChecked())
        self.rigid_group_box.setEnabled(self.rigid_checkbox.isChecked())

        self.controller.params["rigid"] = self.rigid_checkbox.isChecked()

        self.preview_window.update_shell_command()

        self.update_form_layout(self.rigid_metric_form_layout)
        self.update_form_layout(self.rigid_form_layout)

    def toggle_affine(self):
        self.preview_window.affine_checkbox.setChecked(self.affine_checkbox.isChecked())
        self.affine_group_box.setEnabled(self.affine_checkbox.isChecked())

        self.controller.params["affine"] = self.affine_checkbox.isChecked()

        self.preview_window.update_shell_command()

        self.update_form_layout(self.affine_metric_form_layout)
        self.update_form_layout(self.affine_form_layout)

    def toggle_syn(self):
        self.preview_window.syn_checkbox.setChecked(self.syn_checkbox.isChecked())
        self.syn_group_box.setEnabled(self.syn_checkbox.isChecked())

        self.controller.params["syn"] = self.syn_checkbox.isChecked()

        self.preview_window.update_shell_command()

        self.update_form_layout(self.syn_metric_form_layout)
        self.update_form_layout(self.syn_form_layout)

    def update_widgets(self):
        self.translation_checkbox.setChecked(self.preview_window.translation_checkbox.isChecked())
        self.translation_group_box.setEnabled(self.translation_checkbox.isChecked())

        self.rigid_checkbox.setChecked(self.preview_window.rigid_checkbox.isChecked())
        self.rigid_group_box.setEnabled(self.rigid_checkbox.isChecked())

        self.affine_checkbox.setChecked(self.preview_window.affine_checkbox.isChecked())
        self.affine_group_box.setEnabled(self.affine_checkbox.isChecked())

        self.syn_checkbox.setChecked(self.preview_window.syn_checkbox.isChecked())
        self.syn_group_box.setEnabled(self.syn_checkbox.isChecked())

        self.update_form_layout(self.main_form_layout)
        self.update_form_layout(self.translation_form_layout)
        self.update_form_layout(self.translation_metric_form_layout)
        self.update_form_layout(self.rigid_form_layout)
        self.update_form_layout(self.rigid_metric_form_layout)
        self.update_form_layout(self.affine_form_layout)
        self.update_form_layout(self.affine_metric_form_layout)
        self.update_form_layout(self.syn_form_layout)
        self.update_form_layout(self.syn_metric_form_layout)

    def add_text_param(self, name, label, form_layout, widget_dictionary, param_dictionary):
        text_box = QLineEdit()
        text_box.setFixedWidth(300)
        text_box.setText(param_dictionary[name])
        text_box.textEdited.connect(lambda:self.update_text_param(name, widget_dictionary, param_dictionary))
        form_layout.addRow("{}: ".format(label), text_box)

        widget_dictionary[name] = text_box

    def add_combobox_param(self, name, label, form_layout, widget_dictionary, param_dictionary, options, form_layout_to_update=None):
        combobox = QComboBox()
        combobox.setFixedWidth(300)
        combobox.addItems(options)
        combobox.setCurrentText(param_dictionary[name])
        combobox.currentIndexChanged.connect(lambda:self.update_combobox_param(name, widget_dictionary, param_dictionary, form_layout, form_layout_to_update=form_layout_to_update))
        form_layout.addRow("{}: ".format(label), combobox)

        widget_dictionary[name] = combobox

    def update_text_param(self, name, widget_dictionary, param_dictionary):
        param_dictionary[name] = widget_dictionary[name].text()

        self.preview_window.update_shell_command()

    def update_combobox_param(self, name, widget_dictionary, param_dictionary, form_layout, form_layout_to_update=None):
        param_dictionary[name] = widget_dictionary[name].currentText()

        self.preview_window.update_shell_command()

        if form_layout_to_update is not None:
            self.update_form_layout(form_layout_to_update)

    def update_form_layout(self, form_layout):
        if form_layout is self.main_form_layout:
            self.clear_layout(self.main_form_layout)

            self.add_text_param("prefix", "Transform prefix", self.main_form_layout, self.main_param_widgets, self.controller.params)
            self.add_combobox_param("initial_moving_transform", "Initial moving transform", self.main_form_layout, self.main_param_widgets, self.controller.params, ["Geometric Center", "Image Intensities", "Image Origins"])
        elif form_layout is self.translation_form_layout:
            self.clear_layout(self.translation_form_layout)

            if self.translation_checkbox.isChecked():
                self.translation_group_box.show()

                self.add_text_param("gradient_step", "Gradient step", self.translation_form_layout, self.translation_param_widgets, self.controller.translation_params)
                self.add_text_param("num_iterations", "Number of iterations", self.translation_form_layout, self.translation_param_widgets, self.controller.translation_params)
                self.add_text_param("convergence_threshold", "Convergence threshold", self.translation_form_layout, self.translation_param_widgets, self.controller.translation_params)
                self.add_text_param("convergence_window_size", "Convergence window size", self.translation_form_layout, self.translation_param_widgets, self.controller.translation_params)
                self.add_text_param("shrink_factors", "Shrink factors", self.translation_form_layout, self.translation_param_widgets, self.controller.translation_params)
                self.add_text_param("gaussian_sigma", "Gaussian smoothing sigma", self.translation_form_layout, self.translation_param_widgets, self.controller.translation_params)
                self.add_combobox_param("metric", "Metric", self.translation_form_layout, self.translation_param_widgets, self.controller.translation_params, ["Cross-Correlation", "Mutual Information"], form_layout_to_update=self.translation_metric_form_layout)
            else:
                self.translation_group_box.hide()
        elif form_layout is self.translation_metric_form_layout:
            self.clear_layout(self.translation_metric_form_layout)
            
            self.translation_metric_group_box.setTitle("{} Metric Parameters".format(self.controller.translation_params["metric"]))

            if self.controller.translation_params["metric"] == "Cross-Correlation":
                self.add_text_param("metric_weight", "Metric weight", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_cross_correlation_params)
                self.add_text_param("radius", "Radius", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_cross_correlation_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_cross_correlation_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_cross_correlation_params)
            elif self.controller.translation_params["metric"] == "Mutual Information":
                self.add_text_param("metric_weight", "Metric weight", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_mutual_information_params)
                self.add_text_param("num_bins", "Number of bins", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_mutual_information_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_mutual_information_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.translation_metric_form_layout, self.translation_metric_param_widgets, self.controller.translation_mutual_information_params)

        elif form_layout is self.rigid_form_layout:
            self.clear_layout(self.rigid_form_layout)

            if self.rigid_checkbox.isChecked():
                self.rigid_group_box.show()
                
                self.add_text_param("gradient_step", "Gradient step", self.rigid_form_layout, self.rigid_param_widgets, self.controller.rigid_params)
                self.add_text_param("num_iterations", "Number of iterations", self.rigid_form_layout, self.rigid_param_widgets, self.controller.rigid_params)
                self.add_text_param("convergence_threshold", "Convergence threshold", self.rigid_form_layout, self.rigid_param_widgets, self.controller.rigid_params)
                self.add_text_param("convergence_window_size", "Convergence window size", self.rigid_form_layout, self.rigid_param_widgets, self.controller.rigid_params)
                self.add_text_param("shrink_factors", "Shrink factors", self.rigid_form_layout, self.rigid_param_widgets, self.controller.rigid_params)
                self.add_text_param("gaussian_sigma", "Gaussian smoothing sigma", self.rigid_form_layout, self.rigid_param_widgets, self.controller.rigid_params)
                self.add_combobox_param("metric", "Metric", self.rigid_form_layout, self.rigid_param_widgets, self.controller.rigid_params, ["Cross-Correlation", "Mutual Information"], form_layout_to_update=self.rigid_metric_form_layout)
            else:
                self.rigid_group_box.hide()
        elif form_layout is self.rigid_metric_form_layout:
            self.rigid_metric_group_box.setTitle("{} Metric Parameters".format(self.controller.rigid_params["metric"]))

            self.clear_layout(self.rigid_metric_form_layout)

            if self.controller.rigid_params["metric"] == "Cross-Correlation":
                self.add_text_param("metric_weight", "Metric weight", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_cross_correlation_params)
                self.add_text_param("radius", "Radius", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_cross_correlation_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_cross_correlation_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_cross_correlation_params)
            elif self.controller.rigid_params["metric"] == "Mutual Information":
                self.add_text_param("metric_weight", "Metric weight", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_mutual_information_params)
                self.add_text_param("num_bins", "Number of bins", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_mutual_information_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_mutual_information_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.rigid_metric_form_layout, self.rigid_metric_param_widgets, self.controller.rigid_mutual_information_params)
        elif form_layout is self.affine_form_layout:
            if self.affine_checkbox.isChecked():
                self.affine_group_box.show()
                
                self.clear_layout(self.affine_form_layout)

                self.add_text_param("gradient_step", "Gradient step", self.affine_form_layout, self.affine_param_widgets, self.controller.affine_params)
                self.add_text_param("num_iterations", "Number of iterations", self.affine_form_layout, self.affine_param_widgets, self.controller.affine_params)
                self.add_text_param("convergence_threshold", "Convergence threshold", self.affine_form_layout, self.affine_param_widgets, self.controller.affine_params)
                self.add_text_param("convergence_window_size", "Convergence window size", self.affine_form_layout, self.affine_param_widgets, self.controller.affine_params)
                self.add_text_param("shrink_factors", "Shrink factors", self.affine_form_layout, self.affine_param_widgets, self.controller.affine_params)
                self.add_text_param("gaussian_sigma", "Gaussian smoothing sigma", self.affine_form_layout, self.affine_param_widgets, self.controller.affine_params)
                self.add_combobox_param("metric", "Metric", self.affine_form_layout, self.affine_param_widgets, self.controller.affine_params, ["Cross-Correlation", "Mutual Information"], form_layout_to_update=self.affine_metric_form_layout)
            else:
                self.affine_group_box.hide()
        elif form_layout is self.affine_metric_form_layout:
            self.affine_metric_group_box.setTitle("{} Metric Parameters".format(self.controller.affine_params["metric"]))

            self.clear_layout(self.affine_metric_form_layout)

            if self.controller.affine_params["metric"] == "Cross-Correlation":
                self.add_text_param("metric_weight", "Metric weight", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_cross_correlation_params)
                self.add_text_param("radius", "Radius", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_cross_correlation_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_cross_correlation_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_cross_correlation_params)
            elif self.controller.affine_params["metric"] == "Mutual Information":
                self.add_text_param("metric_weight", "Metric weight", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_mutual_information_params)
                self.add_text_param("num_bins", "Number of bins", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_mutual_information_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_mutual_information_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.affine_metric_form_layout, self.affine_metric_param_widgets, self.controller.affine_mutual_information_params)
        elif form_layout is self.syn_form_layout:
            if self.syn_checkbox.isChecked():
                self.syn_group_box.show()

                self.clear_layout(self.syn_form_layout)

                self.add_text_param("gradient_step", "Gradient step", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_text_param("update_field_variance", "Update field variance", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_text_param("total_field_variance", "Total field variance", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_text_param("num_iterations", "Number of iterations", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_text_param("convergence_threshold", "Convergence threshold", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_text_param("convergence_window_size", "Convergence window size", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_text_param("shrink_factors", "Shrink factors", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_text_param("gaussian_sigma", "Gaussian smoothing sigma", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params)
                self.add_combobox_param("metric", "Metric", self.syn_form_layout, self.syn_param_widgets, self.controller.syn_params, ["Cross-Correlation", "Mutual Information"], form_layout_to_update=self.syn_metric_form_layout)
            else:
                self.syn_group_box.hide()
        elif form_layout is self.syn_metric_form_layout:
            self.syn_metric_group_box.setTitle("{} Metric Parameters".format(self.controller.syn_params["metric"]))

            self.clear_layout(self.syn_metric_form_layout)

            if self.controller.syn_params["metric"] == "Cross-Correlation":
                self.add_text_param("metric_weight", "Metric weight", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_cross_correlation_params)
                self.add_text_param("radius", "Radius", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_cross_correlation_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_cross_correlation_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_cross_correlation_params)
            elif self.controller.syn_params["metric"] == "Mutual Information":
                self.add_text_param("metric_weight", "Metric weight", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_mutual_information_params)
                self.add_text_param("num_bins", "Number of bins", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_mutual_information_params)
                self.add_combobox_param("sampling_strategy", "Sampling strategy", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_mutual_information_params, ["None", "Regular", "Random"])
                self.add_text_param("sampling_percentage", "Sampling percentage", self.syn_metric_form_layout, self.syn_metric_param_widgets, self.controller.syn_mutual_information_params)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Enable Retina support
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)

    controller = Controller()

    preview_window = PreviewWindow(controller)

    app.exec_()