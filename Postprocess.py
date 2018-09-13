import sys
import os
import shutil
import arcpy
from distutils.dir_util import copy_tree
from getPerClass import getPerClassFunc

def main():
    # print command line arguments
    inFolder = sys.argv[1]
    # inFolder = "D:\\Shahriar\\LandsatSeries_blocks\\Relabelling\\01\\0113\\"
    # Allow overwriting of existing files
    arcpy.env.overwriteOutput = True

    # Postprocessing base working folder
    base = os.environ['TEMP']
    emptyFoldersPath = inFolder[0:2]+"\\Empty_folders"

    ###################################################
    ## Cleaning & copying working files
    ###################################################
    os.chdir(base)
    if os.path.exists('WIP'):
        os.system('rmdir WIP /S /Q')
    os.system('mkdir WIP')
    os.system('xcopy '+emptyFoldersPath+' WIP /T /E')
    os.chdir(base+"\\WIP")
    #
    block_id = ''
    pastYear = ''
    currentYear = ''

    # Then, distribute files in KML_out folder to KML_gridxx folders
    for root, dirs, files in os.walk(inFolder+"KML_Out"):
        for filename in files:
            i1 = filename.find("grid")
            i2 = filename.find("group")
            i3 = filename.find("AddClass")
            i4 = filename.find("RemoveClass")
            i5 = filename.find("CurrentYear")
            i6 = filename.find("PastYear")
            i7 = filename.find(".kmz")
            if i1 != -1:
                block_id = filename[0:11]
                label = filename[i1+4:i2-1]
                destination = "KML_grid"+label+"\\KMLs"
                shutil.copy(root + "\\" + filename, destination)
            elif i3 != -1:
                label = filename[i3+8:i7]
                destination = "KML_grid"+label+"\\AddPolygon"
                shutil.copy(root + "\\" + filename, destination)
            elif i4 != -1:
                label = filename[i4+11:i7]
                destination = "KML_grid"+label+"\\RemovePolygon"
                shutil.copy(root + "\\" + filename, destination)
            elif i5 != -1:
                currentYear = filename[i5+11:i7]  ## Current year
            else:
                pastYear = filename[i6+8:i7]   ## Past year
    # copy original image file into USGS_data folder
    copy_tree(inFolder+"USGS_data", "USGS_ref")

    finalResult = block_id + "_" + pastYear + "_" + currentYear + "_lc_ESFRef_30m"
    savePath = inFolder+"ESF_Ref\\"+finalResult+".tif"

    ###################################################
    ## Post-processing
    ###################################################

    #Get folder path
    fileFolder=os.getcwd()
    print("-- Starting postprocess for folder " + inFolder)
    if not arcpy.Exists(fileFolder+"\\finalPoints"):
        os.mkdir(fileFolder+"\\finalPoints")

    raster=fileFolder+"\\USGS_Ref"
    rasterDatabase="rster.gdb"
    rasterFinalDatabase="rasterFinal.gdb"
    if not arcpy.Exists(fileFolder+"\\"+rasterDatabase):
        arcpy.CreateFileGDB_management(fileFolder, rasterDatabase)
    if not arcpy.Exists(fileFolder+"\\"+rasterFinalDatabase):
        arcpy.CreateFileGDB_management(fileFolder, rasterFinalDatabase)
    #create points from raster

    rasterPts=fileFolder +"\\"+rasterDatabase+"\\"+"points"

    listRaster=os.listdir(raster)
    for file in listRaster:
        if os.path.splitext(file)[1]==".img":
            inputRaster=raster+"\\"+file
            #print inputRaster
            rasterPoints=fileFolder +"\\"+rasterDatabase+"\\"+"points"
            if not arcpy.Exists(rasterPoints):
                arcpy.RasterToPoint_conversion(inputRaster, rasterPoints, "Value")
                print "Raster to points is done"


    # Process: Project
    rasterPointsPrj=fileFolder +"\\"+rasterDatabase+"\\"+"pointsProjectWGS84"
    if not arcpy.Exists(rasterPointsPrj):
        rasterPointsProject=fileFolder +"\\"+rasterDatabase+"\\"+"pointsProjectWGS84"
        proCS=arcpy.SpatialReference(4326) #WGS1984
        arcpy.Project_management(rasterPoints, rasterPointsProject, proCS)
        print "convert projects is done"

    outputDatabase="output.gdb"
    if not arcpy.Exists(fileFolder+"\\"+outputDatabase):
        arcpy.CreateFileGDB_management(fileFolder, outputDatabase)

    codetoClass = {
        1:"21",
        2:"22",
        3:"25",
        4:"25",
        5:"25",
        6:"24",
        7:"23",
        8:"26",
        9:"27",
        10:"25",
        11:"28"
        }

    for i in range(1,12):

        grid="KML_grid" + str(i)
        code=i
        #print "Now is processing "+grid
        getPerClassFunc(fileFolder,grid,codetoClass,code,rasterPointsProject,outputDatabase,verbose=False)

    print "Per class part is done"

    #merge perclasses to a large class
    perClasses=[]
    tempWS=arcpy.env.workspace
    arcpy.env.workspace = fileFolder +"\\"+ outputDatabase
    for fc in arcpy.ListFeatureClasses():
        perClasses.append(fileFolder +"\\"+ outputDatabase+"\\"+fc)
        #print fc
    mergeClass=fileFolder +"\\"+ outputDatabase+"\\mergeclass"
    arcpy.Merge_management(perClasses,mergeClass)

    arcpy.env.workspace = tempWS
    print "Merge perclasses to large class is done"
    rasterCopy=fileFolder +"\\"+rasterDatabase+"\\"+"pointsProjectWGS84Copy"
    arcpy.CopyFeatures_management(rasterPointsProject, rasterCopy, "", "0", "0", "0")
    # Process: Add Field
    arcpy.AddField_management(rasterCopy, "cls_lbl", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Calculate Field
    arcpy.CalculateField_management(rasterCopy, "cls_lbl", "0", "VB", "")

    tempCopy=fileFolder+"\\tempcopy"
    os.makedirs(tempCopy)
    # Process: Select Layer By Location
    rasterCopy_ly=tempCopy+"\\rastercopy_ly"
    arcpy.MakeFeatureLayer_management(rasterCopy, rasterCopy_ly)
    arcpy.SelectLayerByLocation_management(rasterCopy_ly, "WITHIN", mergeClass, "", "NEW_SELECTION", "NOT_INVERT")

    # Process: Select Layer By Attribute
    arcpy.SelectLayerByAttribute_management(rasterCopy_ly, "SWITCH_SELECTION", "")

    # Process: Copy Features
    restPoints=fileFolder +"\\"+ outputDatabase+"\\restPoints"
    arcpy.CopyFeatures_management(rasterCopy_ly, restPoints, "", "0", "0", "0")

    wholeClass=fileFolder +"\\"+ outputDatabase+"\\wholeclasses"
    arcpy.Merge_management([mergeClass,restPoints],wholeClass)

    wholeClassProj=fileFolder +"\\"+ outputDatabase+"\\wholeclassesProjected"
    proCS=arcpy.SpatialReference(4269) #NAD83
    arcpy.Project_management(wholeClass, wholeClassProj, proCS)
    # wholeClassProj is final points

    wholeClassProjCopy=fileFolder+"\\finalPoints\\"+finalResult
    arcpy.CopyFeatures_management(wholeClassProj, wholeClassProjCopy, "", "0", "0", "0")
    print "Final points shapfile is done"
    ##
    ##

    ## Points to raster
    rasterFinal=fileFolder +"\\"+rasterFinalDatabase+"\\"+finalResult

    arcpy.env.snapRaster = inputRaster
    elevRaster = arcpy.sa.Raster(inputRaster)
    arcpy.env.extent = elevRaster.extent
    arcpy.env.outputCoordinateSystem = "PROJCS['NAD_1983_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['false_easting',0.0],PARAMETER['false_northing',0.0],PARAMETER['central_meridian',-96.0],PARAMETER['standard_parallel_1',29.5],PARAMETER['standard_parallel_2',45.5],PARAMETER['latitude_of_origin',23.0],UNIT['Meter',1.0]]"
    arcpy.env.geographicTransformations = ""
    arcpy.PointToRaster_conversion(wholeClassProj, "cls_lbl", rasterFinal, "MOST_FREQUENT", "NONE", "30")

    finalfile = arcpy.Raster(rasterFinal)
    finalfile.save(savePath)

    print "-- Postprocess is complete for file " + rasterFinal + "."

if __name__ == "__main__":
    main()