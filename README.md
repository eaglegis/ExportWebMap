# ArcGIS Export Web Map

This script takes the state of a web map in a web application and returns a printable page layout or basic map of the specified area of interest in vector or image. If there are too many items in the legend, it will create a new page for the legend to go onto (PDF only).


## Requirements

* ArcGIS Pro 2.6+/ArcGIS Enterprise 10.8.1+


## Installation Instructions

* Download this repository and unzip the contents to your machine. 
* Open ArcGIS Pro and navigate to the downloaded directory.
* Open the "Get Layout Templates Info" script tool in the Export Web Map Toolbox.
* Set the location where the layout templates (.pagx) are located.
* Run the "Get Layout Templates Info" script tool.
* Open the "Export Web Map" script tool in the Export Web Map Toolbox.
* Set the location where the layout templates (.pagx) are located.
* Run the "Export Web Map" script tool.
* Share the "Export Web Map" output result as a web tool to ArcGIS Server in "Synchronous" execution mode.
* Add the "Get Layout Templates Info" output result to this web tool.
* Publish the web tool.


## Resources

* [GitHub](https://github.com/eaglegis)
* [Twitter](https://twitter.com/eaglegis)
* [ArcGIS Pro Python](https://pro.arcgis.com/en/pro-app/latest/arcpy)


## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.