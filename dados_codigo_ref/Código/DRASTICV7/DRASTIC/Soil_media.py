from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtWidgets import *
from .Ui_Soil_media import Ui_Soil_media
from . import GdalTools_utils
from qgis.PyQt import QtCore, QtGui
try:
    from qgis.PyQt.QtCore import QString
except ImportError:
    QString = str
import os, sys
from processing.core.Processing import Processing
from osgeo import ogr
from . import ftools_utils
from osgeo import gdal
import numpy
from qgis.PyQt import QtCore, QtGui

class Soil_media(QDialog, Ui_Soil_media):
    
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        
        self.selectButton.clicked.connect(self.fillInputFileEdit)
        self.inputLayerCombo.currentIndexChanged.connect(self.fillInputAttrib)
        self.selectButton3.clicked.connect(self.fillOutputFileEdit)
        self.buttonAdd.clicked.connect(self.actionAdd)
        self.buttonRemove.clicked.connect(self.actionRemove)
        self.buttonBox.accepted.connect(self.convert)
        self.buttonAttribute.clicked.connect(self.attributeTable)
        
        # connect help
        #QObject.connect(self.buttonBox.button(QtGui.QDialogButtonBox.Help), SIGNAL("clicked()"), self.help)
        
        
    # INPUT VECTOR FILE
    def fillInputFileEdit(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedVectorFilter()
        inputFile, encoding = GdalTools_utils.FileDialog.getOpenFileName(self, self.tr( "Select the input file" ), GdalTools_utils.FileFilter.allVectorsFilter(), lastUsedFilter, True)
        self.lastEncoding = encoding
        self.loadFields(inputFile)
        self.inputLayerCombo.addItem(inputFile)
        check = QFile(inputFile)    
        
    def fillInputAttrib(self, inputFile):
        self.layer = QgsVectorLayer(self.inputLayerCombo.currentText(), (QFileInfo(str(self.inputLayerCombo.currentText()))).baseName(), "ogr")
        self.lineAttrib.clear()    
        changedField = ftools_utils.getFieldList(self.layer)
        for f in changedField:
            if f.type() == QVariant.Int or f.type() == QVariant.String or f.type()==QVariant.Double:
                self.lineAttrib.addItem(unicode(f.name()))   
                
    def loadFields(self, vectorFile = QString()):
        if vectorFile == None:
            return
        try:
            (fields, names) = GdalTools_utils.getVectorFields(vectorFile)
        except Exception as e:
            QErrorMessage(self).showMessage( str(e) )          
        self.inputLayerCombo.clearEditText()
        ncodec = QTextCodec.codecForName(self.lastEncoding)    
    
    # ------------------------------ // ------------------------------------ // ----------------------------    
    
    def help(self):
        QMessageBox.about(self, "Soil Media", """<p><b>Soil factor</b></p> 
        <p><b>Definition:</b>The S factor comprises the influence of soil thickness and texture on pollution attenuation. 
        The required information is obtained in soil maps and other bibliographical sources. This feature acts identically to the Aquifer Media feature. </p>
        <p><b>Method</b></p> 
        <p>Input file = soil map. The user must to define the attribute and the cell size. </p>
        <p><b>Ratings:</b>The ratings are adopted by Aller et al. but the user can modify the values, add or remove lines. 
        Additionally, the users can modify the provided descriptions or introduce their own descriptions. A third option is available through a button (<b>Attribute Table</b>), created to import the input attribute table. 
        This option is faster than the others. </p>
        <p><b>Output file:</b> Aquifer Media raster file</p>""")    
    
    # OUTPUT RASTER FILE
    def fillOutputFileEdit(self):
        lastUsedFilter = GdalTools_utils.FileFilter.lastUsedRasterFilter()
        outputFile = GdalTools_utils.FileDialog.getSaveFileName(self, self.tr( "Select the raster file to save the results to" ),  '.sdat', lastUsedFilter  )
        self.inputLayerCombo3.setText(outputFile)
    
    # -------------------------------- // --------------------------------- // -------------------------------        
    
    # BUTTON ADD AND REMOVE CLASSES
    def actionAdd(self):
        n = self.tableWidget.rowCount()
        self.tableWidget.insertRow(n)
        n = self.tableWidget.rowCount()
        return True
                   
    def actionRemove(self):
        n = self.tableWidget.rowCount()
        for i in range(1,n):
            self.tableWidget.removeRow(n-1)
        n = self.tableWidget.rowCount()
        return True
    
    # ---------------------------------- // ----------------------------- // ------------------------------------        
    
    # CONVERT SHAPEFILE TO RASTER
    def convert(self):    
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(False)
        inputLayer = self.inputLayerCombo.currentText()
        # layer information
        layer = QgsVectorLayer(inputLayer, inputLayer , "ogr")
        vectorlayer_vector = layer.dataProvider()
        # extent
        extent_rect = vectorlayer_vector.extent()
        xmin = extent_rect.xMinimum()
        xmax = extent_rect.xMaximum()
        ymin = extent_rect.yMinimum()
        ymax = extent_rect.yMaximum()
        extent = str(xmin) + "," + str(xmax) + "," + str(ymin) + "," + str(ymax)
        # attribute
        Elevation = self.lineAttrib.currentText()
        # cellsize
        cellSize = int(self.linePix.value())
        outPath = self.inputLayerCombo3.text() 
        # read fields and add a new column with the indexes
        fields = layer.fields()
        new_field = QgsField("Indexes", QVariant.Int)
        layer_new = vectorlayer_vector.addAttributes([new_field])
        layer.updateFields()
        newFieldIndex = vectorlayer_vector.fieldNameIndex(new_field.name())
        allAttrs = vectorlayer_vector.attributeIndexes()
        # editing the new column
        numberRows = int(self.tableWidget.rowCount())
        numberColumns = int(self.tableWidget.columnCount())
        classes = ''
        lista = []
        for i in range(0,numberRows):
            for j in range(0,numberColumns):
                self.line = self.tableWidget.item(i,j)
                lista = lista + [str(self.line.text())]
               
        # list of description on tool table
        lista_table = lista
        # [xistos argilosos, argilitos, 2, rocha metamorfica/ignea, 3, ...]
        
        field_names = [field.name() for field in fields]
        n = len(field_names)
        lista_attrib = []
        for i in range(0,n):
            f = field_names[i]
            if f==str(Elevation):
                number = i
                for feat in layer.getFeatures():
                    attrb = feat.attributes()
                    attribute_read = attrb[number]
                    lista_attrib = lista_attrib + [str(attribute_read)]
        # list of description on attribute table of shapefile
        lista_attributes = lista_attrib   
        # [xistos argilosos, argilitos, xistos argilosos, argilitos, till glaciar, ...]
    
        # obtain the indexes of the description of shapefile attribute table
        description_common = set(lista_attributes).intersection(lista_table)
        listDescription = list(description_common)
        # [xistos argilosos, argilitos, till glaciar]
        listElem = []
        listElements = []
        for j in range(0,len(listDescription)):
            elem = lista_table.index(listDescription[j])
            listElements = listElements + [elem]
            # [0,6]
            elem_index = lista_table[int(elem+1)]
            listElem = listElem + [int(elem_index)]
            # [2,5]
            
        for l in range(0, len(listElem)):
            layer.startEditing()
            exp = QgsExpression(str(listElem[l]))
            #exp.prepare(fields)
            elemDescription = lista_table[listElements[l]]
            for f in layer.getFeatures():
                # get attributes of column defined by the user
                attrb_elem = f[number]
                if attrb_elem==elemDescription: 
                    f[newFieldIndex] = exp.evaluate()
                    layer.updateFeature(f)  
            layer.commitChanges()   
        list_attrb_newField = []
        for features in layer.getFeatures():
            attrb_newField = features.attributes()
            attrb_newField_read = attrb_newField[number+1]
          
        # update and read the new field
        fieldsNew = layer.fields()
        field_names_new = [newField.name() for newField in fieldsNew]          
        parameter_indexes = field_names_new[newFieldIndex]        
        
        Processing.initialize()
        soil = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/soil"
        Processing.runAlgorithm("saga:rasterize",
         {'INPUT': inputLayer, 'FIELD': parameter_indexes, 'OUTPUT': 2, 'MULTIPLE': 4,
          'LINE_TYPE': 0, 'POLY_TYPE': 0, 'GRID_TYPE': 3,
          'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX': extent+' [EPSG:3763]',
          'TARGET_USER_SIZE': cellSize, 'TARGET_USER_FITS': 0,
          'GRID': outPath})
        #soil_complete = soil + "." + "tif"
        
        #Processing.runAlgorithm("grass:v.to.rast.attribute", None, inputLayer, 0, parameter_indexes, extent, cellSize, -1.0, 0.0001, outPath)
        
        #Processing.runAlgorithm("grass7:r.surf.idw", None, soil_complete , 12, False, extent, cellSize, outPath)
        
        
        #soil_weight = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/soil_weight"
        #soil_weight_complete = soil_weight + "." + "tif"
        
        ## multiply by the weight
        #soil_media = soil + "." + "tif"
        #gdalRaster = gdal.Open(str(soil_media))
        #x = gdalRaster.RasterXSize
        #y = gdalRaster.RasterYSize
        #geo = gdalRaster.GetGeoTransform()
        #band = gdalRaster.GetRasterBand(1)
        #data = band.ReadAsArray(0,0,x,y)    
        #mul = numpy.multiply(data, int(self.lineWeight.value()))
        ## Create an output imagedriver with the reclassified values multiplied by the weight
        #driver = gdal.GetDriverByName( "GTiff" ) 
        #outData = driver.Create(str(soil_weight_complete), x,y,1, gdal.GDT_Float32)
        #outData.GetRasterBand(1).WriteArray(mul)
        #outData.SetGeoTransform(geo)  
        #outData = None        
        
        ## eliminate no data values
        #if self.lineWeight.value()==5:
            #error = -499995
        #elif self.lineWeight.value()==4:
            #error = -399996
        #elif self.lineWeight.value()==3:
            #error = -299997
        #elif self.lineWeight.value()==2:
            #error = -199998
        
        #QMessageBox.about(self, "aquifer", str(error))             

        ## reclassify no data values
        #Processing.initialize()
        #Processing.runAlgorithm("saga:reclassifygridvalues", None, soil_weight_complete, 0, error, 0, 0, 0.0, 1.0, 2.0, 0, "0,0,0,0,0,0,0,0,0", 0, True, 0.0, False, 0.0, outPath)
 
        # add result into canvas
        # file_info = QFileInfo(outPath)
        # if file_info.exists():
        #     layer_name = file_info.baseName()
        # else:
        #     return False
        # rlayer_new = QgsRasterLayer(outPath, layer_name)
        # if rlayer_new.isValid():
        #     QgsMapLayerRegistry.instance().addMapLayer(rlayer_new)
        #     layer = QgsMapCanvasLayer(rlayer_new)
        #     layerList = [layer]
        #     extent = self.iface.canvas.setExtent(rlayer_new.extent())
        #     self.iface.canvas.setLayerSet(layerList)
        #     self.iface.canvas.setVisible(True)
        #     return True
        # else:
        #     return False
        # QMessageBox.information(self, self.tr( "Finished" ), self.tr( "Aquifer media completed." ) )
        # add result into canvas
        file_info_norm = QFileInfo(str(outPath))
        # QMessageBox.about(self, "teste", str(file_info_norm))
        rlayer_new_norm = QgsRasterLayer(outPath, file_info_norm.fileName(), 'gdal')
        # QMessageBox.about(self, "teste", str(rlayer_new_norm))
        QgsProject.instance().addMapLayer(rlayer_new_norm)
        self.iface.canvas.setExtent(rlayer_new_norm.extent())
        # set the map canvas layer set
        self.iface.canvas.setLayers([rlayer_new_norm])
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(True)           
    
    def attributeTable(self):
        inputLayer = self.inputLayerCombo.currentText()
        # layer information
        layer = QgsVectorLayer(inputLayer, inputLayer , "ogr")
        # attribute
        Elevation = self.lineAttrib.currentText()        
        fields = layer.fields()
        field_names = [field.name() for field in fields]
        n = len(field_names)
        lista_attrib = []
        for i in range(0,n):
            f = field_names[i]
            if f==str(Elevation):
                number = i
                for feat in layer.getFeatures():
                    attrb = feat.attributes()
                    attribute_read = attrb[number] #reads the attribute one by one
                    lista_attrib = lista_attrib + [str(attribute_read)]
        # list of description on attribute table of shapefile
        lista_attributes = lista_attrib  
        len_attb = len(lista_attributes)
        
        # delete duplicate names
        lista_att_dupl = []
        [lista_att_dupl.append(i) for i in lista_attributes if not i in lista_att_dupl]        
        
        # save the description of shapefile in tool table and delete all the other information, such as indexes and other descriptions
        numberRows = int(self.tableWidget.rowCount())
        self.tableWidget.clearContents()
        lista_i = []

        for i in range(0,numberRows):     
            lista_i = lista_i + [i]
        
        for j in range(0,len(lista_att_dupl)):
            self.tableWidget.setItem(j, 0, QTableWidgetItem(lista_att_dupl[j]))
            
        # remove the lines with no values
        for a in range(0, numberRows):
            if self.tableWidget.item(a,0)== None:
                self.actionRemove()    