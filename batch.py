import os,sys, string

work_list = []
available_drives = ['%s:' % d for d in string.ascii_uppercase if not os.path.exists('%s:' % d)]
newDrive = available_drives[0]

if os.environ['COMPUTERNAME'] == 'DESKTOP-7KDG5DC':
    map_string = 'subst ' + newDrive + ' "C:\\Users\\shhey\\OneDrive - SUNY ESF\\Relabelling"'
elif os.environ['COMPUTERNAME'] == 'ESF-ERE107-1':
    map_string = 'subst ' + newDrive + ' "D:\\Shahriar\\OneDrive - SUNY ESF\\Relabelling"'
else:
    print('Unknown computer. Please add your computer name and OneDrive path to the code')
    sys.exit()

os.system(map_string)
#inFolder = "D:\\Shahriar\\LandsatSeries_blocks\\Relabelling"
regions = os.listdir(newDrive)

for region in regions:
    samples = os.listdir(newDrive+"\\"+region)
    for sample in samples:
        work_list.append(newDrive+"\\"+region+"\\"+sample+"\\")

run = open('run.bat', 'w')
run.write(map_string+"\n")
for item in work_list[0:1]:
    run.write("C:\Python27\ArcGIS10.5\python.exe Postprocess.py "+item+"\n")
run.write('subst '+newDrive+' /D')
run.close()

