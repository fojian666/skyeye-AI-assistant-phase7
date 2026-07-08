# -*-coding:utf-8-*-
import os
import sys
import arcpy
import time


def Main(lyr1, lyr2, output_lyr):
    try:
        arcpy.MakeFeatureLayer_management(lyr1, 'lyr1')
        arcpy.MakeFeatureLayer_management(lyr2, 'lyr2')

        arcpy.SelectLayerByLocation_management("lyr1", 'HAVE_THEIR_CENTER_IN', "lyr2")
        arcpy.SelectLayerByAttribute_management("lyr1", "SWITCH_SELECTION")

        matchcount = int(arcpy.GetCount_management('lyr1')[0])
        if matchcount == 0:
            print('no features matched spatial criteria')
        else:
            arcpy.CopyFeatures_management("lyr1", output_lyr)
            print('Success! The output features are {0}'.format(matchcount))
        arcpy.Delete_management('lyr1')
        arcpy.Delete_management('lyr2')
    except Exception as e:
        print(e)


def savelog(log_info, savepath):
    localtime = time.asctime(time.localtime(time.time()))
    with open(savepath, "a+") as f:
        f.write(str(localtime) + " " + log_info + "\n")


if __name__ == '__main__':
    # input_lyr1 = r'I:\Test\gaochun\building\building_label.shp'
    # input_lyr2 = r'I:\Test\gaochun\building\pre\shp\building2000_eliminate.shp'
    # output_lyr1 = r'I:\Test\gaochun\building\pre\new_function\res1.shp'
    # output_lyr2 = r'I:\Test\gaochun\building\pre\new_function\res2.shp'
    input_lyr1 = sys.argv[1]
    input_lyr2 = sys.argv[2]
    output_path= sys.argv[3]
    output_lyr1 = os.path.join(output_path, os.path.basename(input_lyr1).split(".")[0] + "_res.shp")
    output_lyr2 = os.path.join(output_path, os.path.basename(input_lyr2).split(".")[0] + "_res.shp")

    Main(input_lyr1, input_lyr2, output_lyr1)
    Main(input_lyr2, input_lyr1, output_lyr2)
    sys.exit(0)


