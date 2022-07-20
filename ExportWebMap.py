#-------------------------------------------------------------
# Name:                 Export Web Map
# Purpose:              This script takes the state of a web map in a web application 
#                       (for example, included services, layer visibility settings, and client-side graphics) 
#                       and returns a printable page layout or basic map of the specified area of interest
#                       in vector (such as pdf, svg etc.) or image (e.g. png, jpeg etc.).
#                       If there are too many items in the legend, it will create a new page for the legend
#                       to go onto (PDF only). As at ArcGIS Pro 2.9.2 the legend.isOverflowing property is
#                       not in the ArcPy library, so uses custom logic to work out when to export legend
#                       to second page.
# Author:               Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:         30/05/2022
# Last Updated:         30/05/2022
# ArcGIS Version:       ArcGIS Pro 2.6+/ArcGIS Enterprise 10.8.1+
#--------------------------------

# Import required modules
#
import sys
import os
import arcpy
import uuid

# constants
#
SERVER_PROD_NAME = 'Server'
PRO_PROD_NAME = 'ArcGISPro'
PAGX_FILE_EXT = "pagx"
MAP_ONLY = 'map_only'

# default location and current product name
#
_defTmpltFolder = os.path.join(arcpy.GetInstallInfo()['InstallDir'], r"Resources\ArcToolBox\Templates\ExportWebMapTemplates")
_prodName = arcpy.GetInstallInfo()['ProductName']
_isMapOnly = False

# export only map without any layout elements
#
def exportMap(result, outfile, outFormat):
    mapView = result.ArcGISProject.listMaps()[0].defaultView

    w = result.outputSizeWidth
    h = result.outputSizeHeight
    dpi = int(result.DPI) #a workaround for now for a bug

    try:
        if outFormat == "png8" or outFormat == "png32":
            if (outFormat == "png8"):
                colorMode = "8-BIT_ADAPTIVE_PALETTE"
            else:
                colorMode = "32-BIT_WITH_ALPHA"
            mapView.exportToPNG(outfile, w, h, dpi, None, colorMode)
        elif outFormat == "pdf":
            mapView.exportToPDF(outfile, w, h, dpi)
        elif outFormat == "jpg":
            mapView.exportToJPEG(outfile, w, h, dpi, None, '24-BIT_TRUE_COLOR', 100)
        elif outFormat == "gif":
            mapView.exportToGIF(outfile, w, h, dpi)
        elif outFormat == "eps":
            mapView.exportToEPS(outfile, w, h, dpi)
        elif outFormat == "svg":
            mapView.exportToSVG(outfile, w, h, dpi, False)
        elif outFormat == "svgz":
            mapView.exportToSVG(outfile, w, h, dpi, True)
        elif outFormat == "aix":
            mapView.exportToAIX(outfile, w, h, dpi)
        elif outFormat == "tiff":
            mapView.exportToTIFF(outfile, w, h, dpi, False, "32-BIT_WITH_ALPHA", "DEFLATE", True) #return geoTIFF_tags
    except Exception as err:
        arcpy.AddError("error raised..." + str(err))
        raise

# export layout
#
def exportLayout(result, outfile, outFormat):
    layout = result.ArcGISProject.listLayouts()[0]
    legend = layout.listElements("LEGEND_ELEMENT", "*")[0]
    dpi = result.DPI
    # Set page units to centimeter
    layout.pageUnits = "CENTIMETER"
    
    # Work out the max number of items that can be added into the legend
    maxItems = int((legend.elementHeight * legend.elementWidth)/10)
    arcpy.AddMessage("Maximum number of legend items for this layout - {}...".format(str(maxItems)))    
    arcpy.AddMessage("Number of legend items visible for this map - {}...".format(str(len(legend.items))))    

    try:
        if outFormat == "png8" or outFormat == "png32":
            if (outFormat == "png8"):
                colorMode = "8-BIT_ADAPTIVE_PALETTE"
            else:
                colorMode = "32-BIT_WITH_ALPHA"
            layout.exportToPNG(outfile, dpi, colorMode)
        elif outFormat == "pdf":
            # If there too many legend items to fit
            if (len(legend.items) > maxItems):             
                # Move legend of the page
                legend.elementPositionX = -5000
                legend.elementPositionY = -5000
                arcpy.AddMessage("Creating first page of PDF...")
                layout.exportToPDF(outfile, dpi)

                legendFile = generateUniqueFileName(outFormat)
                # Move all elements of the page
                pageElements = layout.listElements()
                for pageElement in pageElements:
                    pageElement.elementPositionX = -5000
                    pageElement.elementPositionY = -5000
                # Resize element for whole page and move to top left
                legend.elementWidth = layout.pageWidth - 2
                legend.elementHeight = layout.pageHeight - 2
                legend.elementPositionX = 1
                legend.elementPositionY = layout.pageHeight - 1
                # Show legend title
                legend.showTitle = True
                # layout.exportToPAGX(r"E:\Tools & Scripts\ArcGIS Export Web Map\test.pagx")
                arcpy.AddMessage("Creating second page of PDF...")
                layout.exportToPDF(legendFile, dpi)
                pdfOutfile = arcpy.mp.PDFDocumentOpen(outfile)
                pdfOutfile.appendPages(legendFile)
                pdfOutfile.saveAndClose()
            else:
                layout.exportToPDF(outfile, dpi)
        elif outFormat == "jpg":
            layout.exportToJPEG(outfile, dpi)
        elif outFormat == "gif":
            layout.exportToGIF(outfile, dpi)
        elif outFormat == "eps":
            layout.exportToEPS(outfile, dpi)
        elif outFormat == "svg":
            layout.exportToSVG(outfile, dpi, False)
        elif outFormat == "svgz":
            layout.exportToSVG(outfile, dpi, True)
        elif outFormat == "aix":
            layout.exportToAIX(outfile, dpi)
        elif outFormat == "tiff":
            layout.exportToTIFF(outfile, dpi, "32-BIT_WITH_ALPHA", "DEFLATE")
    except Exception as err:
        arcpy.AddError("error raised..." + str(err))
        raise



# generating a unique name for each output file
def generateUniqueFileName(outFormat):
    guid = str(uuid.uuid1())
    fileName = ""
    fileExt = outFormat

    #changing the file extension for few instances
    if outFormat == "png8" or outFormat == "png32":
        fileExt = "png"
    elif outFormat == "tiff":
        fileExt = "tif"

    fileName = '{}.{}'.format(guid, fileExt)
    fullFileName = os.path.join(arcpy.env.scratchFolder, fileName)
    return fullFileName

# Main module
#
def main():
    # Get the value of the input parameter
    #
    WebMap_as_JSON = arcpy.GetParameterAsText(0)
    outfilename = arcpy.GetParameterAsText(1)
    format = arcpy.GetParameterAsText(2).lower()
    layoutTemplatesFolder = arcpy.GetParameterAsText(3).strip()
    layoutTemplate = arcpy.GetParameterAsText(4).lower()

    if (layoutTemplate.lower() == MAP_ONLY):
        _isMapOnly = True
        layoutTemplate = None
    else:
        _isMapOnly = False

    # Special logic while being executed in ArcGIS Pro 
    # - so that a Geoprocessing result can be acquired without needing any json to begin to feed in
    # - this is to make the publishing experience easier
    if (WebMap_as_JSON.replace(' ', '') == '#'):
        WebMap_as_JSON = '#'
        if (_prodName == PRO_PROD_NAME):
            return
        elif (_prodName == SERVER_PROD_NAME):
            arcpy.AddIDMessage('ERROR', 590, 'WebMap_as_JSON')
        else:
            arcpy.AddIDMessage('ERROR', 120004, _prodName)

    # generate a new output filename when the output_filename parameter is empty or the script is running on server
    if outfilename.isspace() or _prodName == SERVER_PROD_NAME:
        outfilename = generateUniqueFileName(format)

    # constructing the full path for the layout file (.pagx)
    if not _isMapOnly:
        # use the default location when Layout_Templates_Folder parameter is not set
        tmpltFolder = _defTmpltFolder if not layoutTemplatesFolder else layoutTemplatesFolder
        layoutTemplate = os.path.join(tmpltFolder, '{}.{}'.format(layoutTemplate, PAGX_FILE_EXT))

    
    
    #Convert the webmap to a map document
    try:
        arcpy.AddMessage("Converting Web Map JSON to ArcGIS Project...")
        result = arcpy.mp.ConvertWebMapToArcGISProject(WebMap_as_JSON, layoutTemplate)
        
        #Export...
        if (_isMapOnly):
            if (result.outputSizeWidth == 0) or (result.outputSizeHeight == 0):
                arcpy.AddIDMessage('ERROR', 1305)
            exportMap(result, outfilename, format)
        else:
            exportLayout(result, outfilename, format)

    except Exception as err:
        arcpy.AddError(str(err))


    
    # Set output parameter
    #
    arcpy.SetParameterAsText(1, outfilename)


if __name__ == "__main__":
    main()
