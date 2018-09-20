import os
import arcpy
import shutil

def getPerClassFunc(fileFolder,grid,codetoClass,code,rasterPoints,outputDatabase,verbose):

    perClass=fileFolder+"\\"+grid
    kmls=perClass+"\\KMLs"
    addPoly=perClass+"\\AddPolygon"
    removePoly=poly=perClass+"\\RemovePolygon"

    tempKmls=perClass+"\\tempKmls"
    tempAdd=perClass+"\\tempAdd"
    tempRemove=perClass+"\\tempRemove"
    tempMerge=perClass+"\\templayermerge"
    os.makedirs(tempKmls)
    os.makedirs(tempAdd)
    os.makedirs(tempRemove)
    os.makedirs(tempMerge)

    tempDatabase="temp.gdb"
    arcpy.CreateFileGDB_management(perClass, tempDatabase) 

    
    listKmls=os.listdir(kmls)
    kmlNumber=len(listKmls)

    listAddPoly=os.listdir(addPoly)
    addNumber=len(listAddPoly)

    listRemovePoly=os.listdir(removePoly)
    removeNumber=len(listRemovePoly)


    kmlLayer=[]

    if kmlNumber>0:    
        for file in listKmls:
            sampKML=kmls+"\\"+file
            #get short name
            splitext=os.path.splitext(file)
            outputName=splitext[0]      
            # Process: KML To Layer
            arcpy.KMLToLayer_conversion(sampKML, tempKmls, outputName, "NO_GROUNDOVERLAY")##        
            kmlLayer.append(tempKmls+"\\"+outputName+".gdb\\Placemarks\\Points")##        
            #print kmlLayer
            if verbose:
                print "KML to Layer is done"


    if addNumber>0:
        for file in listAddPoly:
            sampAdd=addPoly+"\\"+file
            splitext=os.path.splitext(file)
            outputName=splitext[0]
            # Process: KML To Layer
            arcpy.KMLToLayer_conversion(sampAdd, tempAdd, outputName, "NO_GROUNDOVERLAY")
            addPolygon=tempAdd+"\\"+outputName+".gdb\\Placemarks\\Polygons"

    if removeNumber>0:
        for file in listRemovePoly:
            sampRemove=removePoly+"\\"+file
            splitext=os.path.splitext(file)
            outputName=splitext[0]
            # Process: KML To Layer
            arcpy.KMLToLayer_conversion(sampRemove, tempRemove, outputName, "NO_GROUNDOVERLAY")
            removePolygon=tempRemove+"\\"+outputName+".gdb\\Placemarks\\Polygons"
            

           
    # create merge feature class from different groups in perclass
    if kmlNumber>=1:
        # Process: Merge
        outputmerge=perClass+"\\"+tempDatabase+"\\mergelayer"
        arcpy.Merge_management(kmlLayer,outputmerge)

    

    # create feature class for remove polygons: Remove points fall in removepolygons
    if removeNumber>0 and kmlNumber>0:
        
        outputmerge_rm=tempMerge+"\\mergelayer"
        #print outputmerge,removePolygon
        # Process: Select Layer By Location
        arcpy.MakeFeatureLayer_management(outputmerge, outputmerge_rm)
        arcpy.SelectLayerByLocation_management(outputmerge_rm, "WITHIN", removePolygon, "", "NEW_SELECTION")

        # Process: Select Layer By Attribute
        arcpy.SelectLayerByAttribute_management(outputmerge_rm, "SWITCH_SELECTION", "")

        # Process: Copy Features
        outputRemove=perClass+"\\"+tempDatabase+"\\outputRemove"
        arcpy.CopyFeatures_management(outputmerge_rm, outputRemove, "", "0", "0", "0")
        if verbose:
            print "remove points is done"
        
    #create feature class for addpolygons
    if addNumber>0:
        # Process: Select Layer By Location
        rasterPointsForAdd=tempMerge+"\\rasterpoints"
        arcpy.MakeFeatureLayer_management(rasterPoints, rasterPointsForAdd)    
        arcpy.SelectLayerByLocation_management(rasterPointsForAdd, "WITHIN", addPolygon, "", "NEW_SELECTION")

        # Process: Copy Features
        outputAdd=perClass+"\\"+tempDatabase+"\\outputAdd"
        arcpy.CopyFeatures_management(rasterPointsForAdd, outputAdd, "", "0", "0", "0")
        if verbose:
            print "add points is done"
        
    isOutput=0    
    # merge if both add and remove
    if addNumber>0 and removeNumber>0:
        # merge
        outputPerClass=perClass+"\\"+tempDatabase+"\\outputPerclass"
        arcpy.Merge_management([outputRemove,outputAdd],outputPerClass)
        isOutput=1
        if verbose:
            print "merge add and remove is done"

    if addNumber>0 and  removeNumber==0 and kmlNumber==0:
        outputPerClass=outputAdd
        isOutput=1

    if addNumber==0 and  removeNumber>0:
        outputPerClass=outputRemove
        isOutput=1

    if kmlNumber>0 and  addNumber==0  and removeNumber==0:
        outputPerClass=outputmerge
        isOutput=1
        
    if kmlNumber>0 and  addNumber>0  and removeNumber==0:
        # merge
        outputPerClass=perClass+"\\"+tempDatabase+"\\outputPerclass"
        arcpy.Merge_management([outputmerge,outputAdd],outputPerClass)
        isOutput=1

    if addNumber==0 and  removeNumber==0 and kmlNumber>0:
        outputPerClass=outputmerge
        isOutput=1
        
    if isOutput >0:        
        # add field and calculate field
        # Process: Add Field
        arcpy.AddField_management(outputPerClass, "cls_lbl", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Calculate Field
        arcpy.CalculateField_management(outputPerClass, "cls_lbl", codetoClass[code], "VB", "")

        if verbose:
            print "Add and calculate field is done"

        # get output
        outputGdb=fileFolder +"\\"+ outputDatabase+"\\"+ grid
        arcpy.CopyFeatures_management(outputPerClass, outputGdb, "", "0", "0", "0")

        if verbose:
            print grid +" is done"


def makeExcelFile(WIP, inFolder, original_raster, corrected):

    arcpy.CreateFileGDB_management(WIP+"\\", "temp.gdb")
    arcpy.env.workspace = WIP+"\\temp.gdb"
    #arcpy.env.overwriteOutput = True

    Original_classes = {
        0: 'None',
        1: 'Water',
        2: 'Developed',
        3: 'Mech. Distrubed',
        4: 'Mining',
        5: 'Barren',
        6: 'Forest',
        7: 'Grass/Shrubland',
        8: 'Agriculture',
        9: 'Wetland',
        10: 'Nonmech. Disturbed',
        11: 'Ice/Snow'
    }

    New_classes = {
        0:'None',
        21:'Water',
        22:'Imprevious',
        23:'Grass/Shrubland',
        24:'Forest',
        25:'Bare',
        26:'Cultivated',
        27:'Wetland',
        28:'Ice/Snow',
        30:'Transition'
    }

    # Local variables:
    #base_path = "C:\\Users\\shhey\\test\\"
    os.chdir(inFolder)
    #corrected = base_path+"ESF_Ref\\samp01_0113_1991_2017_lc_ESFRef_30m.tif"
    original = arcpy.sa.Raster(original_raster)
    inputValid = "inputValid"
    selected = "selected"
    out_table = "output_table"
    excel_table = inFolder+"ESF_Ref\\conversion_table.xls"

    arcpy.CheckOutExtension("spatial")

    valid = arcpy.sa.ExtractByAttributes(original, 'Count > 0')
    valid.save(inputValid)
    rows = arcpy.da.SearchCursor(inputValid,["Value", "Count"])
    classes = []
    for row in rows:
        classes.append(row[0])
    #print 'Number of classes: %d' %  len(classes)

    table = arcpy.CreateTable_management(arcpy.env.workspace, out_table)
    arcpy.AddField_management(table, "Original_class", "LONG")
    arcpy.AddField_management(table, "Desc1", "TEXT")
    arcpy.AddField_management(table, "New_class", "LONG")
    arcpy.AddField_management(table, "Desc2", "TEXT")
    arcpy.AddField_management(table, "Count", "LONG")

    with arcpy.da.InsertCursor(table, ['Original_class', 'Desc1', 'New_class', 'Desc2', 'Count']) as cursor:
        for c in classes:
            layer = arcpy.sa.ExtractByAttributes(original, 'Value = '+str(c))
            sel = arcpy.sa.ExtractByMask(corrected, layer)
            sel.save(selected)
            rows = arcpy.da.SearchCursor(selected,["Value", "Count"])
            #print 'converted from class %d :' % c
            for row in rows:
                #print '   new class %d, count %d' % (row[0], row[1])
                cursor.insertRow((c, Original_classes[c], row[0], New_classes[row[0]], row[1]))

    arcpy.TableToExcel_conversion(table, excel_table)
