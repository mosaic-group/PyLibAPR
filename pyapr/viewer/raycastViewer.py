from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph.opengl as gl
import timeit
import pyqtgraph as pg
import pyapr
import math
import matplotlib.pyplot as plt
import numpy as np

class MainWindowImage(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindowImage, self).__init__()

        cw = QtGui.QWidget()
        self.setCentralWidget(cw)

        cw.setMouseTracking(True)

        self.layout = QtGui.QGridLayout()
        cw.setLayout(self.layout)
        self.layout.setSpacing(0)

        self.pg_win = pg.GraphicsView()
        self.view = pg.ViewBox()
        self.view.setAspectLocked()
        self.pg_win.setCentralItem(self.view)
        self.layout.addWidget(self.pg_win, 0, 0, 3, 1)

        # add a slider
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)

        self.slider.valueChanged.connect(self.valuechange)

        self.slider.sliderReleased.connect(self.sliderReleased)

        self.setGeometry(300, 300, self.full_size, self.full_size)

        self.layout.addWidget(self.slider, 1, 0)

        self.slider.setRange(0, self.number_angles)

        # add a histogram

        self.hist = pg.HistogramLUTWidget()

        self.layout.addWidget(self.hist, 0, 1)

        self.hist.item.sigLevelsChanged.connect(self.histogram_updated)

        # add a drop box for LUT selection

        self.comboBox = QtGui.QComboBox(self)
        self.comboBox.move(20, 20)
        self.comboBox.addItem('viridis')
        self.comboBox.addItem('plasma')
        self.comboBox.addItem('inferno')
        self.comboBox.addItem('magma')
        self.comboBox.addItem('cividis')
        self.comboBox.addItem('Greys')
        self.comboBox.addItem('Greens')
        self.comboBox.addItem('Oranges')
        self.comboBox.addItem('Reds')
        self.comboBox.addItem('bone')
        self.comboBox.addItem('Pastel1')

        self.comboBox.currentTextChanged.connect(self.updatedLUT)

        self.view.mousePressEvent = self.MousePress

        self.view.mouseMoveEvent = self.MouseMove

        self.view.mouseReleaseEvent = self.MouseRelease

        self.view.wheelEvent = self.WheelEvent

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            # back a frame
            new_radius = self.raycaster_ref.get_radius() + 0.01
            self.raycaster_ref.set_radius(new_radius)
            self.update_slice(self.apr_ref.level_max() - 1)


        if event.key() == QtCore.Qt.Key_Down:
            # forward a frame
            new_radius = self.raycaster_ref.get_radius() - 0.01
            self.raycaster_ref.set_radius(new_radius)
            self.update_slice(self.apr_ref.level_max() - 1)

        if event.key() == QtCore.Qt.Key_R:
            # forward a frame
            if self.fix:
                self.fix = False
            else:
                self.fix = True

            self.view.setMouseEnabled(self.fix, self.fix)
            print(self.fix)


    def WheelEvent(self,event):
        new_radius = max(self.raycaster_ref.get_radius() + event.delta()/1000, 0.1)
        self.raycaster_ref.set_radius(new_radius)
        self.update_slice(self.apr_ref.level_max())



    def MousePress(self, event):
        self.org_pos = event.pos()

    def MouseMove(self, event):
        # pos = self.w.cameraPosition()
        diff = self.org_pos - event.pos()
        self.org_pos = event.pos()

        print(diff)

        #self.current_theta += diff.x()/self.angle_scale

        self.raycaster_ref.increment_angle(diff.x()/self.angle_scale)
        self.raycaster_ref.increment_phi(diff.y()/self.angle_scale)

        self.update_slice(self.apr_ref.level_max() - 1)

    def MouseRelease(self, event):

        diff = self.org_pos - event.pos()
        self.org_pos = event.pos()

        self.raycaster_ref.increment_angle(diff.x()/self.angle_scale)
        self.raycaster_ref.increment_phi(diff.y() / self.angle_scale)



        self.update_slice(self.apr_ref.level_max())

    fix = False

    number_angles = 100
    current_view = 0

    angle_scale = 200

    array_int = np.array(1)
    img_ref = 0
    par_ref = 0

    array_list = []
    img_list = []

    x_num = 0
    z_num = 0
    y_num = 0

    full_size = 1000
    scale_sc = 10

    min_x = 0
    min_y = 0

    hist_min = 0
    hist_max = 200

    lut = 0
    lut_back = 0

    # parameters to be played with
    grad_th = 0

    app_ref = 0

    org_pos = 0
    current_phi = 0
    current_theta = 0

    def updatedLUT(self):
        # monitors the event of the drop box being manipulated
        self.setLUT(self.comboBox.currentText())

    def setLUT(self, string):

        call_dict = {
            'viridis': plt.cm.viridis,
            'plasma': plt.cm.plasma,
            'inferno': plt.cm.inferno,
            'magma': plt.cm.magma,
            'cividis': plt.cm.cividis,
            'Greys': plt.cm.Greys,
            'Greens': plt.cm.Greens,
            'Oranges': plt.cm.Oranges,
            'Reds': plt.cm.Reds,
            'bone': plt.cm.bone,
            'Pastel1': plt.cm.Pastel1
        }

        # color map integration using LUT
        self.cmap = call_dict[string]

        self.lut = self.cmap(np.linspace(0.0, 1.0, 512))
        self.lut = self.lut * 255

        #self.lut[1, :] = 0
        self.img_list[0].setLookupTable(self.lut, True)

    def valuechange(self):
        size = self.slider.value()
        self.raycaster_ref.set_phi(-3.14 + 2*size*3.14/self.number_angles)
        #for i in range(self.apr_ref.level_max()-4, self.apr_ref.level_max()-3):
        self.update_slice(self.apr_ref.level_max()-1)

    def sliderReleased(self):
        size = self.slider.value()
        self.raycaster_ref.set_phi(-3.14 + 2*size*3.14/self.number_angles)
        for i in range(self.apr_ref.level_max()-1, self.apr_ref.level_max()+1):
            self.update_slice(i)


    def histogram_updated(self):
        hist_range = self.hist.item.getLevels()

        self.hist_min = hist_range[0]
        self.hist_max = hist_range[1]

        self.img_list[0].setLevels([self.hist_min, self.hist_max], True)

    def update_slice(self, level):

        sz = pow(2, self.apr_ref.level_max() - level)
        self.raycaster_ref.set_level_delta(level - self.apr_ref.level_max())

        self.raycaster_ref.get_view(self.apr_ref, self.parts_ref, self.tree_parts_ref, self.array_list[level])
        self.img_list[0].setImage(self.array_list[level], True)

        img_sz_x = self.array_list[level].shape[1] * sz
        img_sz_y = self.array_list[level].shape[0] * sz

        self.img_list[0].setRect(QtCore.QRectF(self.min_x, self.min_y, img_sz_x, img_sz_y))
        self.img_list[0].setLevels([self.hist_min, self.hist_max], True)


        #self.view.addItem(self.img_list[level])

    def set_image(self, apr, parts, tree_parts):


        for i in range(0, apr.level_max() + 1):

            sz = pow(2, self.apr_ref.level_max() - i)
            xl = math.floor(apr.x_num(apr.level_max())/sz)
            yl = math.floor(apr.y_num(apr.level_max())/sz)

            self.array_list.append(np.zeros([xl, yl], dtype=np.uint16))
            self.img_list.append(pg.ImageItem())

        for i in range(max(1,apr.level_max()-4), apr.level_max()+1):

            self.raycaster_ref.set_level_delta(i-apr.level_max())
            self.raycaster_ref.get_view(apr, parts, tree_parts, self.array_list[i])
            self.img_list[0].setImage(self.array_list[i])

            sz = pow(2, self.apr_ref.level_max() - i)
            img_sz_x = self.array_list[i].shape[1] * sz
            img_sz_y = self.array_list[i].shape[0] * sz

            self.img_list[0].setRect(QtCore.QRectF(self.min_x, self.min_y, img_sz_x, img_sz_y))

        self.view.addItem(self.img_list[0])


        # self.raycaster_ref.get_view(apr, parts, tree_parts, self.img_buff)

        self.img_list[1].setImage(self.array_list[apr.level_max()-1])
        self.hist.setImageItem(self.img_list[1])

        self.apr_ref = apr
        self.parts_ref = parts
        self.tree_parts_ref = tree_parts



def raycast_viewer(apr, parts):

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pg.setConfigOption('imageAxisOrder', 'row-major')

    app = QtGui.QApplication([])

    ## Create window with GraphicsView widget
    win = MainWindowImage()

    win.show()

    win.apr_ref = apr

    win.app_ref = app

    raycaster = pyapr.viewer.raycaster()

    raycaster.set_z_anisotropy(3)
    raycaster.set_radius(0.7)

    win.view.setMouseEnabled(False, False)

    win.raycaster_ref = raycaster

    win.raycaster_ref.set_angle(win.current_theta)
    win.raycaster_ref.set_phi(win.current_phi)

    tree_parts = pyapr.FloatParticles()

    pyapr.viewer.get_down_sample_parts(apr, parts, tree_parts)

    win.set_image(apr, parts, tree_parts)

    QtGui.QApplication.instance().exec_()