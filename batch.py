import os

work_list = []
map_string = """subst K: 'D:\\Shahriar\\OneDrive - SUNY ESF\\Relabelling'"""
print map_string
os.system(map_string)
#inFolder = "D:\\Shahriar\\LandsatSeries_blocks\\Relabelling"
inFolder = "K:\\"
regions = os.listdir(inFolder)

for region in regions:
    samples = os.listdir(inFolder+"\\"+region)
    for sample in samples:
        work_list.append(inFolder+"\\"+region+"\\"+sample+"\\")

run = open('run.bat', 'w')
run.write(map_string+"\n")
for item in work_list:
    run.write("C:\Python27\ArcGIS10.5\python.exe Postprocess.py "+item+"\n")
run.close()

