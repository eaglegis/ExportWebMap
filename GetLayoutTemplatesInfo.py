# Retrieve metadata for all .pagx available in the specified folder
#    each .pagx is considered as a layout template in a printing service.
#    


# Import required modules
#
import sys
import os
import arcpy
import json
import glob
import re
import xml.dom.minidom as DOM

# default location
#
_defTmpltFolder = os.path.join(arcpy.GetInstallInfo()['InstallDir'], r"Resources\ArcToolBox\Templates\ExportWebMapTemplates")

# Defining a custom JSONEncoder for MapDocument object
#
class LayoutEncoder(json.JSONEncoder):
    def default(self, layout):
        if isinstance(layout, arcpy._mp.Layout):
            d = {}

            # Layout_Template name
            d["layoutTemplate"] = layout.name

            # Page size & unit
            d["pageSize"] = [layout.pageWidth, layout.pageHeight]
            d["pageUnits"] = layout.pageUnits

            # Size of the mapframe element on the layout
            mapFrames = layout.listElements("MAPFRAME_ELEMENT")
            mf = None
            if (len(mapFrames) == 1): # if there is only one mapframe element, use that
                mf = mapFrames[0]
            elif (len(mapFrames) > 1):
                webMapFrames = layout.listElements("MAPFRAME_ELEMENT", "WEBMAP_MAP_FRAME") # if the layout has 1+ mapframe elements, look for one with a specific name
                if (len(webMapFrames) == 1):
                    mf = webMapFrames[0]
                else:
                    arcpy.AddWarning("Layout '{0}' has more than one map frames but none named 'WEBMAP_MAP_FRAME'.".format(layout.name))
            else: 
                arcpy.AddWarning("Layout '{0}' has no map frames.".format(layout.name))

            if (mf != None):
                d["webMapFrameSize"] = [mf.elementWidth, mf.elementHeight]

            # Layout options containing information about layout elements
            lo = {}
            d["layoutOptions"] = lo
            lo["hasTitleText"] = False
            lo["hasAuthorText"] = False
            lo["hasCopyrightText"] = False
            lo["hasLegend"] = False

            # Is a legend element available whose parent dataframe name is same as the active dataframe's name
            if (mf != None):
                for lgd in layout.listElements("LEGEND_ELEMENT"):
                    if (lgd.mapFrame.name == mf.name):
                        lo["hasLegend"] = True
                        break

            # Availability of text elements - both predefined and user-defined
            ct = []     #an array contains custom text elements - each as a separate dictionary
            lo["customTextElements"] = ct
            for t in layout.listElements("TEXT_ELEMENT"):
                try:    #processing dynamic-text-elements with xml tags
                    x = DOM.parseString(t.text)
                    r = x.childNodes[0]
                    if (r.tagName == "dyn") and (r.getAttribute("type") == "layout") and (r.getAttribute("property") == "metadata"): #predefined with specific dynamic-text (i.e. xml tag)
                        if (r.getAttribute("attribute") == "title"):
                            lo["hasTitleText"] = True
                        if (r.getAttribute("attribute") == "contactname"):
                            lo["hasAuthorText"] = True
                        if (r.getAttribute("attribute") == "credits"):
                            lo["hasCopyrightText"] = True
                except: #find all other text elements who names are embedded within a pair of opening and closing curly braces
                    if (re.search(r"^({).*(})$", t.name) is not None):
                        ct.append({t.name.replace('{', '').replace('}',''): t.text}) #removing opening and closing curly braces from the name

            return d
        return json.JSONEncoder.default(self, layout)


# Main module
#
def main():
    # Get the value of the input parameter
    #
    tmpltFolder = arcpy.GetParameterAsText(0)

    ## When empty, it falls back to the default template location like ExportWebMap tool does
    ##
    if (len(tmpltFolder) == 0):
        tmpltFolder = _defTmpltFolder

    # Getting a list of all file paths with .pagx extensions
    #    createing Layout objects and putting them in an array
    #
    layouts    = []
    for f in glob.glob(os.path.join(tmpltFolder, "*.pagx")):
        try:    #throw exception when the Layout File is corrupted
            l = arcpy.mp.ConvertLayoutFileToLayout(f)
            l.name = os.path.splitext(os.path.basename(f))[0] #setting the layout name as the file name to be used in PagXEncoder
            layouts.append(l)
        except:
            arcpy.AddWarning("Unable to open layout file (.pagx) named {0}".format(os.path.basename(f)))
            

    # Encoding the array of MapDocument to JSON using a custom JSONEncoder class
    #
    try:
        outJSON = json.dumps(layouts, cls=LayoutEncoder, indent=2)
    except Exception as err:
        arcpy.AddError(str(err))

    # Set output parameter
    #
    arcpy.SetParameterAsText(1, outJSON)
    
    # Clean up
    #
    del layouts


if __name__ == "__main__":
    main()
