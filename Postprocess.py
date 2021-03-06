import sys
import os
import shutil
import arcpy
from distutils.dir_util import copy_tree
from subFunctions import *
#import getPerClassFunc
#from makeExcel import makeExcelFile

def main():
    # print command line arguments
    if len(sys.argv) == 1:
        print('Please enter full path to sample block files folder ')
        inFolder = raw_input('(for example H:\\Desktop\\Relabelling\\01\\0130): ') +"\\"
    else:
        inFolder = sys.argv[1]

    # Allow overwriting of existing files
    arcpy.env.overwriteOutput = True

    # Postprocessing base working folder
    base = os.environ['TEMP']
    tempFolder = base+"\\WIP"
    project_dir = os.getcwd()
    finalResult = ''

    ###################################################
    ## Cleaning & copying working files
    ###################################################
    os.chdir(base)
    if not os.path.exists(project_dir+'\\Empty_folders'):
        print('Empty folders not found for copying.')
        sys.exit()
    if os.path.exists('WIP'):
        os.system('rmdir WIP /S /Q')
    os.system('mkdir WIP')
    os.system('xcopy "'+project_dir+'\\Empty_folders" WIP /T /E')
    os.chdir(tempFolder)
    #
    block_id = ''
    year_flag = 1

    # Then, distribute files in KML_out folder to KML_gridxx folders
    if not os.path.exists(inFolder+"KML_Out"):
        print('KML_Out folder does not exist!')
        sys.exit()
    for root, dirs, files in os.walk(inFolder+"KML_Out"):
        if not files: # if directory is empty
            print('KML_Out folder is empty!')
            sys.exit()
        for filename in files:
            i1 = filename.find("grid")
            i2 = filename.find("group")
            i3 = filename.find("AddClass")
            i4 = filename.find("RemoveClass")
            i5 = filename.find("FirstYear")
            i6 = filename.find("LastYear")
            i7 = filename.find(".kmz")
            if i7 != -1:        # looking at .kmz files only
                if i1 != -1:
                    block_id = filename[0:11].lower()
                    label = filename[i1+4:i2-1]
                    destination = "KML_grid"+label+"\\KMLs"
                    shutil.copy(root + "\\" + filename, destination)
                elif i3 != -1:
                    block_id = filename[0:11].lower()
                    label = filename[i3+8:i7]
                    destination = "KML_grid"+label+"\\AddPolygon"
                    shutil.copy(root + "\\" + filename, destination)
                elif i4 != -1:
                    label = filename[i4+11:i7]
                    destination = "KML_grid"+label+"\\RemovePolygon"
                    shutil.copy(root + "\\" + filename, destination)
                elif i5 != -1:
                    destination = "KML_Years\\"+filename[i5:]
                    shutil.copy(root + "\\" + filename, destination)
                    year_flag = year_flag*2
                elif i6 != -1:
                    destination = "KML_Years\\"+filename[i6:]
                    shutil.copy(root + "\\" + filename, destination)
                    year_flag = year_flag*2

    if (year_flag != 4):
        print('FirstYear or LastYear KML file missing!')
        sys.exit()

    # copy original image file into USGS_data folder
    copy_tree(inFolder+"USGS_data", "USGS_ref")

    if not os.path.exists(inFolder+"ESF_Ref"):
        os.system('mkdir "'+inFolder+'ESF_Ref"')
    else:
        os.system('del "'+inFolder+'ESF_Ref" /Q')

    finalResult = block_id + "_lc_ESFRef_30m"
    savePath = inFolder+"ESF_Ref\\"

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
    if not listRaster:  # if directory is empty
        print('USGS_Ref folder is empty!')
        sys.exit()
    for file in listRaster:
        if os.path.splitext(file)[1] in {'.img', '.IMG', '.tif', '.TIF'}:
            inputRaster=raster+"\\"+file
            #print inputRaster
            rasterPoints=fileFolder +"\\"+rasterDatabase+"\\"+"points"
            if not arcpy.Exists(rasterPoints):
                arcpy.RasterToPoint_conversion(inputRaster, rasterPoints, "Value")
                print "Raster to points is done."

    # Process: Project
    rasterPointsPrj=fileFolder +"\\"+rasterDatabase+"\\"+"pointsProjectWGS84"
    if not arcpy.Exists(rasterPointsPrj):
        rasterPointsProject=fileFolder +"\\"+rasterDatabase+"\\"+"pointsProjectWGS84"
        proCS=arcpy.SpatialReference(4326) #WGS1984
        arcpy.Project_management(rasterPoints, rasterPointsProject, proCS)
        print "Convert projects is done."

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
        print " - Processing "+grid
        getPerClassFunc(fileFolder,grid,codetoClass,code,rasterPointsProject,outputDatabase,verbose=False)

    #print "Per class processing is done."

    #merge perclasses to a large class
    perClasses=[]
    tempWS=arcpy.env.workspace
    arcpy.env.workspace = fileFolder +"\\"+ outputDatabase
    for fc in arcpy.ListFeatureClasses():
        perClasses.append(fileFolder +"\\"+ outputDatabase+"\\"+fc)
    mergeClass=fileFolder +"\\"+ outputDatabase+"\\mergeclass"
    arcpy.Merge_management(perClasses,mergeClass)
    #dissolveClass=fileFolder +"\\"+ outputDatabase+"\\dissolveclass"
    #arcpy.Dissolve_management(mergeClass, dissolveClass, "POINT_X;POINT_Y", [["cls_lbl", "SUM"]], "SINGLE_PART")
    #arcpy.AlterField_management(dissolveClass, "SUM_cls_lbl","cls_lbl")

    arcpy.env.workspace = tempWS
    print "Merge single classes is done."
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
    arcpy.SelectLayerByLocation_management(rasterCopy_ly, "WITHIN", mergeClass, "", "NEW_SELECTION")

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
    print "Final points shapefile is done."
    ##
    ##

    ## Points to raster
    rasterFinal=fileFolder +"\\"+rasterFinalDatabase+"\\"+finalResult

    arcpy.env.snapRaster = inputRaster
    elevRaster = arcpy.sa.Raster(inputRaster)
    arcpy.env.extent = elevRaster.extent
    arcpy.env.outputCoordinateSystem = "PROJCS['NAD_1983_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['false_easting',0.0],PARAMETER['false_northing',0.0],PARAMETER['central_meridian',-96.0],PARAMETER['standard_parallel_1',29.5],PARAMETER['standard_parallel_2',45.5],PARAMETER['latitude_of_origin',23.0],UNIT['Meter',1.0]]"
    arcpy.env.geographicTransformations = ""
    arcpy.PointToRaster_conversion(wholeClassProj, "cls_lbl", rasterFinal, "SUM", "NONE", "30")

    finalfile = arcpy.Raster(rasterFinal)
    finalfile.save(savePath+finalResult+".tif")

    print "Final raster file is created."

    ## Process first/last year files

    # Load and convert FirstYear and LastYear KML files to layers
    print " - Processing yearly KML files"
    arcpy.env.workspace = fileFolder+"\\KML_Years"
    FirstKML = fileFolder+'\\KML_Years\\FirstYear.kmz'
    arcpy.KMLToLayer_conversion(FirstKML, '', "FirstYear", "NO_GROUNDOVERLAY")  ##
    LastKML = fileFolder+'\\KML_Years\\LastYear.kmz'
    arcpy.KMLToLayer_conversion(LastKML, '', "LastYear", "NO_GROUNDOVERLAY")  ##

    # Year property is of string type when read into arcpy, so we add a new numeric field
    # and copy the string value to a integer type
    arcpy.AddField_management('FirstYear\Polygons', 'Year', 'LONG')
    arcpy.AddField_management('LastYear\Polygons', 'Year', 'LONG')
    arcpy.CalculateField_management('FirstYear\Polygons', 'YEAR', 'int(!NAME!)', "PYTHON")
    arcpy.CalculateField_management('LastYear\Polygons', 'YEAR', 'int(!NAME!)', "PYTHON")

    print " - Converting yearly polygons to point"
    # Intersect final point features (calculated previously) with first and last year polygons to absorb their value
    # as a new attribute to the point layer and save it to new feature classes (Points2 and Points3)
    #arcpy.RasterToPoint_conversion('samp01_0113_ESFRef.tif', 'Points1', 'Value')
    Points2 = fileFolder +"\\"+ outputDatabase+"\\Points2"
    Points3 = fileFolder +"\\"+ outputDatabase+"\\Points3"
    arcpy.Intersect_analysis([wholeClassProj, 'FirstYear\Polygons'], Points2)
    arcpy.Intersect_analysis([wholeClassProj, 'LastYear\Polygons'], Points3)

    # Convert Points2 and Points3 to raster, keeping their year values in conversion
    print " - Converting points to rasters and making composite"
    arcpy.PointToRaster_conversion(Points2, 'YEAR', 'Band2.tif')
    arcpy.PointToRaster_conversion(Points3, 'YEAR', 'Band3.tif')

    # combine two new rasters with the original one to create a 3-band raster
    rasterFinal_3band = rasterFinal+"_3band"
    arcpy.CompositeBands_management(rasterFinal+';Band2.tif;Band3.tif', rasterFinal_3band)
    finalfile = arcpy.Raster(rasterFinal_3band)
    finalfile.save(savePath+finalResult+"_3band.tif")

    print "Year validity data added to a new raster as additional bands."

    print "* Postprocess is complete for file " + finalResult + "."

if __name__ == "__main__":
    main()
