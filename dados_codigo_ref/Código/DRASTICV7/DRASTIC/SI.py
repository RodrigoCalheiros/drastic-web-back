from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtWidgets import *
from . import GdalTools_utils
try:
    from qgis.PyQt.QtCore import QString
except ImportError:
    QString = str
from processing.core.Processing import Processing
#from processing.core.ProcessingGdalTools_utils import ProcessingGdalTools_utils
from . import ftools_utils
from osgeo import ogr
from processing import *
from osgeo.gdalconst import GA_ReadOnly
from osgeo import gdal
from processing import ProcessingPlugin
#from processing.outputs import OutputRaster
import sys, os
import numpy
from .Ui_SI import Ui_SI
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.PyQt import QtCore, QtGui

class SI(QDialog, Ui_SI):
    
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)  
    
        self.selectButton.clicked.connect(self.fillInputFileEdit)
        self.selectButton2.clicked.connect(self.fillInputFileEdit2)
        self.selectButton3.clicked.connect(self.fillInputFileEdit3)
        self.selectButton5.clicked.connect(self.fillInputFileEdit5)
        self.selectButton6.clicked.connect(self.fillInputFileEdit6)
        self.selectButton_out.clicked.connect(self.fillOutputFileEdit)
        #self.selectButton_color.clicked.connect(self.fillOutputFileEdit_color)
        self.buttonBox.accepted.connect(self.convert)
        
        # connect help
        #self.buttonBox.button(QtGui.QDialogButtonBox.Help).clicked()"), self.help)
        
    def help(self):
        QMessageBox.about(self, "SI", """<p><b>SI Index</b></p> 
        <p><b>Definition:</b>The last feature, the SI index, corresponds to the final map, which results from the sum of the seven factor
        maps created before multiplied by the corresponding weights as defined in equation 1, according to Aller et al. (1987).  </p>
        <p><b>SI</b> = DR x DW + RR x RW + AR x AW + SR x SW + TR x TW + IR x IW + CR x CW	(1)</p>
        <p>R and W (in subscript) correspond to the rating and weight for each factor, respectively. 
        The SI interface is composed by seven input files corresponding to D, R, A, S, T, I and C raster files, and an output file corresponding to SI index map. </p>
        <p><b>Method</b></p> 
        <p>Input files = seven raster created before. The user must to define the weight values which are defined according Aller et al (1987) by default.  </p>
        <p><b>Output file:</b> SI raster file without color or SI COLORED with the colors and intervals defined according to Aller et al. (1987)</p>""")  
      
 # INPUT RASTER FILE
    def fillInputFileEdit(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
        inputFile, encoding = GdalTools_utils.FileDialog.getOpenFileName(self, self.tr( "Select the input file" ), GdalTools_utils.FileFilter.allRastersFilter(), lastUsedFilter, True)
        self.lastEncoding = encoding
        self.inputLayerCombo.addItem(inputFile)
        check = QFile(inputFile)     
        
    def fillInputFileEdit2(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
        inputFile, encoding = GdalTools_utils.FileDialog.getOpenFileName(self, self.tr( "Select the input file" ), GdalTools_utils.FileFilter.allRastersFilter(), lastUsedFilter, True)
        self.lastEncoding = encoding
        self.inputLayerCombo2.addItem(inputFile)
        check = QFile(inputFile)    
        
    def fillInputFileEdit3(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
        inputFile, encoding = GdalTools_utils.FileDialog.getOpenFileName(self, self.tr( "Select the input file" ), GdalTools_utils.FileFilter.allRastersFilter(), lastUsedFilter, True)
        self.lastEncoding = encoding
        self.inputLayerCombo3.addItem(inputFile)
        check = QFile(inputFile) 
            
            
    def fillInputFileEdit5(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
        inputFile, encoding = GdalTools_utils.FileDialog.getOpenFileName(self, self.tr( "Select the input file" ), GdalTools_utils.FileFilter.allRastersFilter(), lastUsedFilter, True)
        self.lastEncoding = encoding
        self.inputLayerCombo5.addItem(inputFile)
        check = QFile(inputFile) 
        
    def fillInputFileEdit6(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
        inputFile, encoding = GdalTools_utils.FileDialog.getOpenFileName(self, self.tr( "Select the input file" ), GdalTools_utils.FileFilter.allRastersFilter(), lastUsedFilter, True)
        self.lastEncoding = encoding
        self.inputLayerCombo6.addItem(inputFile)
        check = QFile(inputFile)
            
            
# --------------------------------------- // ----------------------------------------------------- // ------------------------------------------------------------------------------

# OUTPUT RASTER FILE
    def fillOutputFileEdit(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
        outputFile = GdalTools_utils.FileDialog.getSaveFileName(self, self.tr( "Select the raster file to save the results to" ), GdalTools_utils.FileFilter.allRastersFilter(), ".sdat")
        self.outputLayerCombo.setText(outputFile)
        

    # def fillOutputFileEdit_color(self):
    #     lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
    #     outputFile = GdalTools_utils.FileDialog.getSaveFileName(self, self.tr( "Select the raster file to save the results to" ), GdalTools_utils.FileFilter.allRastersFilter(), lastUsedFilter )
    #     self.outputLayerCombo_color.setText(outputFile)

# SI CALCULATION
    def convert(self):
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(False)
        # read D raster
        inputLayer = self.inputLayerCombo.currentText()
        # read R raster
        inputLayer2 = self.inputLayerCombo2.currentText()
        # read A raster
        inputLayer3 = self.inputLayerCombo3.currentText()
        # read T raster
        inputLayer5 = self.inputLayerCombo5.currentText()
        # read LU raster
        inputLayer6 = self.inputLayerCombo6.currentText()      
        # outpath
        outPath = self.outputLayerCombo.text()  

        gdal.AllRegister()
        
        # sum of the raster = SI
        # D
        gdalRaster = gdal.Open(str(inputLayer))
        # # multiply by weight
        # depth_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/depth_weight"
        x = gdalRaster.RasterXSize
        y = gdalRaster.RasterYSize
        # geo = gdalRaster.GetGeoTransform()
        # band = gdalRaster.GetRasterBand(1)
        # data = band.ReadAsArray(0,0,x,y)
        # mul = numpy.multiply(data, int(self.lineWeightD.value()))
        # # Create an output imagedriver with the reclassified values multiplied by the weight
        # driver = gdal.GetDriverByName( "GTiff" )
        # outData = driver.Create(str(depth_weight), x,y,1, gdal.GDT_Float32)
        # outData.GetRasterBand(1).WriteArray(mul)
        # outData.SetGeoTransform(geo)
        # outData = None
        #
        geo = gdalRaster.GetGeoTransform()
        # # pixel size
        pixelSize = geo[1]
        # extent
        minx = geo[0]
        maxy = geo[3]
        maxx = minx + geo[1]*x
        miny = maxy + geo[5]*y
        extent = str(minx) + "," + str(maxx) + "," + str(miny) + "," + str(maxy)
        band = gdalRaster.GetRasterBand(1)
        #data_d = band.ReadAsArray(0,0,x,y)
        #
        #
        # gdalRaster_d = gdal.Open(str(depth_weight))
        # x_d = gdalRaster_d.RasterXSize
        # y_d = gdalRaster_d.RasterYSize
        # geo_d = gdalRaster_d.GetGeoTransform()
        # band_d = gdalRaster_d.GetRasterBand(1)
        # data_d = band_d.ReadAsArray(0,0,x_d,y_d)


        # R
        # resampling R raster
        # gdalRaster2 = gdal.Open(str(inputLayer2))
        # # multiply by weight
        # recharge_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/recharge_weight"
        # x2 = gdalRaster2.RasterXSize
        # y2 = gdalRaster2.RasterYSize
        # geo2 = gdalRaster2.GetGeoTransform()
        # band2 = gdalRaster2.GetRasterBand(1)
        # data2 = band2.ReadAsArray(0,0,x2,y2)
        # mul2 = numpy.multiply(data2, int(self.lineWeightR.value()))
        # # Create an output imagedriver with the reclassified values multiplied by the weight
        # driver2 = gdal.GetDriverByName( "GTiff" )
        # outData2 = driver2.Create(str(recharge_weight), x2,y2,1, gdal.GDT_Float32)
        # outData2.GetRasterBand(1).WriteArray(mul2)
        # outData2.SetGeoTransform(geo2)
        # outData2 = None

        Processing.initialize()

        resamp_d = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/resamp_d.sdat"
        # Processing.runAlgorithm("saga:resampling", None, recharge_weight, True, 0, 0, extent, pixelSize, resamp_r)
        Processing.runAlgorithm("saga:resampling",
                                {'INPUT': inputLayer, 'KEEP_TYPE': True, 'SCALE_UP': 0,
                                 'SCALE_DOWN': 0,
                                 'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX': extent + '[EPSG:3763]',
                                 'TARGET_USER_SIZE': pixelSize, 'TARGET_USER_FITS': 0, 'TARGET_TEMPLATE': None,
                                 'OUTPUT': resamp_d})

        resamp_r = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/resamp_r.sdat"
        #Processing.runAlgorithm("saga:resampling", None, recharge_weight, True, 0, 0, extent, pixelSize, resamp_r)
        Processing.runAlgorithm("saga:resampling",
                       {'INPUT': inputLayer2, 'KEEP_TYPE': True, 'SCALE_UP': 0,
                        'SCALE_DOWN': 0,
                        'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX': extent+ '[EPSG:3763]',
                        'TARGET_USER_SIZE': pixelSize, 'TARGET_USER_FITS': 0, 'TARGET_TEMPLATE': None,
                        'OUTPUT': resamp_r})

        #resamp_r_dir = resamp_r + "." + "tif"
        # R
        # gdalRaster_r = gdal.Open(str(resamp_r))
        # x_r = gdalRaster_r.RasterXSize
        # y_r = gdalRaster_r.RasterYSize
        # geo_r = gdalRaster_r.GetGeoTransform()
        # band_r = gdalRaster_r.GetRasterBand(1)
        # data_r = band_r.ReadAsArray(0,0,x_r,y_r)

        # A
        # resampling A raster
        # gdalRaster3 = gdal.Open(str(inputLayer3))
        # # multiply by weight
        # aquifer_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/aquifer_weight"
        # x3 = gdalRaster3.RasterXSize
        # y3 = gdalRaster3.RasterYSize
        # geo3 = gdalRaster3.GetGeoTransform()
        # band3 = gdalRaster3.GetRasterBand(1)
        # data3 = band3.ReadAsArray(0,0,x3,y3)
        # mul3 = numpy.multiply(data3, int(self.lineWeightA.value()))
        # # Create an output imagedriver with the reclassified values multiplied by the weight
        # driver3 = gdal.GetDriverByName( "GTiff" )
        # outData3 = driver3.Create(str(aquifer_weight), x3,y3,1, gdal.GDT_Float32)
        # outData3.GetRasterBand(1).WriteArray(mul3)
        # outData3.SetGeoTransform(geo3)
        outData3 = None
        resamp_a = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/resamp_a.sdat"
        #Processing.runAlgorithm("saga:resampling", None, aquifer_weight, True, 0, 0, extent, pixelSize, resamp_a)
        Processing.runAlgorithm("saga:resampling",
                                {'INPUT': inputLayer3, 'KEEP_TYPE': True, 'SCALE_UP': 0,
                                 'SCALE_DOWN': 0,
                                 'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX': extent + '[EPSG:3763]',
                                 'TARGET_USER_SIZE': pixelSize, 'TARGET_USER_FITS': 0, 'TARGET_TEMPLATE': None,
                                 'OUTPUT': resamp_a})
        # A
        # gdalRaster_a = gdal.Open(str(resamp_a))
        # x_a = gdalRaster_a.RasterXSize
        # y_a = gdalRaster_a.RasterYSize
        # geo_a = gdalRaster_a.GetGeoTransform()
        # band_a = gdalRaster_a.GetRasterBand(1)
        # data_a = band_a.ReadAsArray(0,0,x_a,y_a)


        # T
        # resampling T raster
        # gdalRaster5 = gdal.Open(str(inputLayer5))
        # # multiply by weight
        # topography_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/topography_weight"
        # x5 = gdalRaster5.RasterXSize
        # y5 = gdalRaster5.RasterYSize
        # geo5 = gdalRaster5.GetGeoTransform()
        # band5 = gdalRaster5.GetRasterBand(1)
        # data5 = band5.ReadAsArray(0,0,x5,y5)
        # mul5 = numpy.multiply(data5, int(self.lineWeightT.value()))
        # # Create an output imagedriver with the reclassified values multiplied by the weight
        # driver5 = gdal.GetDriverByName( "GTiff" )
        # outData5 = driver5.Create(str(topography_weight), x5,y5,1, gdal.GDT_Float32)
        # outData5.GetRasterBand(1).WriteArray(mul5)
        # outData5.SetGeoTransform(geo5)
        outData5 = None
        resamp_t = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/resamp_t.sdat"
        #Processing.runAlgorithm("saga:resampling", None, topography_weight, True, 0, 0, extent, pixelSize, resamp_t)
        Processing.runAlgorithm("saga:resampling",
                                {'INPUT': inputLayer5, 'KEEP_TYPE': True, 'SCALE_UP': 0,
                                 'SCALE_DOWN': 0,
                                 'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX': extent + '[EPSG:3763]',
                                 'TARGET_USER_SIZE': pixelSize, 'TARGET_USER_FITS': 0, 'TARGET_TEMPLATE': None,
                                 'OUTPUT': resamp_t})
        # T
        # gdalRaster_t = gdal.Open(str(resamp_t))
        # x_t = gdalRaster_t.RasterXSize
        # y_t = gdalRaster_t.RasterYSize
        # geo_t = gdalRaster_t.GetGeoTransform()
        # band_t = gdalRaster_t.GetRasterBand(1)
        # data_t = band_t.ReadAsArray(0,0,x_t,y_t)
        #QMessageBox.about(self, "SI", str(data_t))

        # LU
        # resampling I raster
        # gdalRaster6 = gdal.Open(str(inputLayer6))
        # # multiply by weight
        # impact_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/LU_weight"
        # x6 = gdalRaster6.RasterXSize
        # y6 = gdalRaster6.RasterYSize
        # geo6 = gdalRaster6.GetGeoTransform()
        # band6 = gdalRaster6.GetRasterBand(1)
        # data6 = band6.ReadAsArray(0,0,x6,y6)
        # mul6 = numpy.multiply(data6, int(self.lineWeightI.value()))
        # # Create an output imagedriver with the reclassified values multiplied by the weight
        # driver6 = gdal.GetDriverByName( "GTiff" )
        # outData6 = driver6.Create(str(impact_weight), x6,y6,1, gdal.GDT_Float32)
        # outData6.GetRasterBand(1).WriteArray(mul6)
        # outData6.SetGeoTransform(geo6)
        outData6 = None
        resamp_lu = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/resamp_lu.sdat"
        #Processing.runAlgorithm("saga:resampling", None, impact_weight, True, 0, 0, extent, pixelSize, resamp_i)
        Processing.runAlgorithm("saga:resampling",
                                {'INPUT': inputLayer6, 'KEEP_TYPE': True, 'SCALE_UP': 0,
                                 'SCALE_DOWN': 0,
                                 'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX': extent + '[EPSG:3763]',
                                 'TARGET_USER_SIZE': pixelSize, 'TARGET_USER_FITS': 0, 'TARGET_TEMPLATE': None,
                                 'OUTPUT': resamp_lu})
        # LU
        # gdalRaster_i = gdal.Open(str(resamp_i))
        # x_i = gdalRaster_i.RasterXSize
        # y_i = gdalRaster_i.RasterYSize
        # geo_i = gdalRaster_i.GetGeoTransform()
        # band_i = gdalRaster_i.GetRasterBand(1)
        # data_lu = band_i.ReadAsArray(0,0,x_i,y_i)


        # sum
        #summ = data_d + data_r + data_a + data_t + data_lu

        # sum_nodata = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/sum_nodata"
        # sum_nodata_rec = sum_nodata + "." + "tif"

        # Create an output imagedriver with the reclassified values multiplied by the weight
        # Processing.runAlgorithm("gdal:rastercalculator",
        #                {'INPUT_A': resamp_d,
        #                 'BAND_A': 1,
        #                 'INPUT_B': resamp_r,
        #                 'BAND_B': 1,
        #                 'INPUT_C': resamp_a,
        #                 'BAND_C': 1,
        #                 'INPUT_D': resamp_lu,
        #                 'BAND_D': 1, 'INPUT_E': resamp_t, 'BAND_E': 1, 'INPUT_F': None, 'BAND_F': -1, 'FORMULA': 'A+B+C+D+E',
        #                 'NO_DATA': None, 'RTYPE': 5, 'EXTRA': '', 'OPTIONS': '',
        #                 'OUTPUT': outPath})

        # multiplication by weights
        D_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/D_weight_si.sdat"
        Processing.runAlgorithm("gdal:rastercalculator",
                       {'INPUT_A': inputLayer, 'BAND_A': 1, 'INPUT_B': None,
                        'BAND_B': -1, 'INPUT_C': None, 'BAND_C': -1, 'INPUT_D': None, 'BAND_D': -1, 'INPUT_E': None,
                        'BAND_E': -1, 'INPUT_F': None, 'BAND_F': -1, 'FORMULA': 'A*' + str(self.lineWeightD.value()), 'NO_DATA': None, 'RTYPE': 6,
                        'OPTIONS': '',
                        'OUTPUT': D_weight})

        R_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/R_weight_si.sdat"
        Processing.runAlgorithm("gdal:rastercalculator",
                                {'INPUT_A': inputLayer2, 'BAND_A': 1, 'INPUT_B': None,
                                 'BAND_B': -1, 'INPUT_C': None, 'BAND_C': -1, 'INPUT_D': None, 'BAND_D': -1,
                                 'INPUT_E': None,
                                 'BAND_E': -1, 'INPUT_F': None, 'BAND_F': -1,
                                 'FORMULA': 'A*' + str(self.lineWeightR.value()), 'NO_DATA': None, 'RTYPE': 6,
                                 'OPTIONS': '',
                                 'OUTPUT': R_weight})

        A_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/A_weight_si.sdat"
        Processing.runAlgorithm("gdal:rastercalculator",
                                {'INPUT_A': inputLayer3, 'BAND_A': 1, 'INPUT_B': None,
                                 'BAND_B': -1, 'INPUT_C': None, 'BAND_C': -1, 'INPUT_D': None, 'BAND_D': -1,
                                 'INPUT_E': None,
                                 'BAND_E': -1, 'INPUT_F': None, 'BAND_F': -1,
                                 'FORMULA': 'A*' + str(self.lineWeightA.value()), 'NO_DATA': None, 'RTYPE': 6,
                                 'OPTIONS': '',
                                 'OUTPUT': A_weight})

        T_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/T_weight_si.sdat"
        Processing.runAlgorithm("gdal:rastercalculator",
                                {'INPUT_A': inputLayer5, 'BAND_A': 1, 'INPUT_B': None,
                                 'BAND_B': -1, 'INPUT_C': None, 'BAND_C': -1, 'INPUT_D': None, 'BAND_D': -1,
                                 'INPUT_E': None,
                                 'BAND_E': -1, 'INPUT_F': None, 'BAND_F': -1,
                                 'FORMULA': 'A*' + str(self.lineWeightT.value()), 'NO_DATA': None, 'RTYPE': 6,
                                 'OPTIONS': '',
                                 'OUTPUT': T_weight})

        LU_weight = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/LU_weight_si.sdat"
        Processing.runAlgorithm("gdal:rastercalculator",
                                {'INPUT_A': inputLayer6, 'BAND_A': 1, 'INPUT_B': None,
                                 'BAND_B': -1, 'INPUT_C': None, 'BAND_C': -1, 'INPUT_D': None, 'BAND_D': -1,
                                 'INPUT_E': None,
                                 'BAND_E': -1, 'INPUT_F': None, 'BAND_F': -1,
                                 'FORMULA': 'A*' + str(self.lineWeightLU.value()), 'NO_DATA': None, 'RTYPE': 6,
                                 'OPTIONS': '',
                                 'OUTPUT': LU_weight})



        Processing.runAlgorithm("grass7:r.mapcalc.simple", {'a': D_weight,
                                                   'b': D_weight,
                                                   'c': R_weight,
                                                   'd': A_weight,
                                                   'e': T_weight,
                                                   'f': LU_weight,
                                                   'expression': 'A+C+D+E+F+(A-A)',
                                                   'output': outPath,
                                                   'GRASS_REGION_PARAMETER': extent + '[EPSG:3763]',
                                                   'GRASS_REGION_CELLSIZE_PARAMETER': pixelSize, 'GRASS_RASTER_FORMAT_OPT': '',
                                                   'GRASS_RASTER_FORMAT_META': ''})

        # list_raster = []
        # list_raster = list_raster + [inputLayer2] + [inputLayer3] + [inputLayer5] + [inputLayer6]
        # listt = ';'.join(list_raster)

        # Processing.runAlgorithm("saga:rastercalculator", None,
        #                         inputLayer,
        #                         listt,
        #                         "a+b+c+d+e", 3, False, 7, outPath)
        # reclassify no data values
        #Processing.runAlgorithm("saga:reclassifygridvalues", None, sum_nodata, 0, -10000100352, 0, 0, 0.0, 1.0, 2.0, 0, "0,0,0,0,0,0,0,0,0", 0, True, 0.0, False, 0.0, outPath)

        file_info_norm = QFileInfo(str(outPath))
        # QMessageBox.about(self, "teste", str(file_info_norm))
        rlayer_new_norm = QgsRasterLayer(outPath, file_info_norm.fileName(), 'gdal')
        # QMessageBox.about(self, "teste", str(rlayer_new_norm))
        QgsProject.instance().addMapLayer(rlayer_new_norm)
        self.iface.canvas.setExtent(rlayer_new_norm.extent())
        # set the map canvas layer set
        self.iface.canvas.setLayers([rlayer_new_norm])

        QMessageBox.information(self, self.tr( "Finished" ), self.tr( "SI completed." ) )
    
        # colorfile = 'C:/OSGeo4W64/apps/qgis/python/plugins/SI/colorfile.clr'
        # outPath_color = self.outputLayerCombo_color.text()
        # from colorize import raster2png
        #
        # raster2png(outPath, colorfile , outPath_color,1, False)
        #
        # if self.checkcolor.isChecked():
        #     # add result into canvas
        #     file_info = QFileInfo(outPath_color)
        #     if file_info.exists():
        #         layer_name = file_info.baseName()
        #     else:
        #         return False
        #     rlayer_new = QgsRasterLayer(outPath_color, layer_name)
        #     if rlayer_new.isValid():
        #         QgsMapLayerRegistry.instance().addMapLayer(rlayer_new)
        #         layer = QgsMapCanvasLayer(rlayer_new)
        #         layerList = [layer]
        #         extent = self.iface.canvas.setExtent(rlayer_new.extent())
        #         self.iface.canvas.setLayerSet(layerList)
        #         self.iface.canvas.setVisible(True)
        #         return True
        #     else:
        #         return False
        #     QMessageBox.information(self, self.tr( "Finished" ), self.tr( "SI completed." ) )
        #
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(True) 