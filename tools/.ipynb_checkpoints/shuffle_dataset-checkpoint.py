"""
shuffle_dataset
清洗数据集 使两种类型平均分布
分布方法：以文件名奇偶区分 文件名为奇数则为拼接 文件名为偶数则为奇数
用于平均分布数据集
Written By Doublez
"""

import os
import shutil
import time

DATASET=["train_data","val_data","test_data"]

def pic_dir(dataset):
    return "./%s/pic/"%(dataset)

def mask_dir(dataset):
    return "./%s/cv2_mask/"%(dataset)

def json_dir(dataset):
    return "./%s/labelme_json/"%(dataset)

def generateName(cnt):
    return str(cnt).zfill(10)

def editFile(file_path,src,dst):
    edit_file=""
    with open(file_path,'r',encoding="utf-8") as f:
        for line in f:
            if src in line:
                line=line.replace(src,dst)
            edit_file+=line
    with open(file_path,'w',encoding="utf-8") as f:
        f.write(edit_file)

def renameData(dataset,old_filename,cnt):
    new_filename=generateName(cnt)
    os.rename(pic_dir(dataset)+old_filename+".jpg",pic_dir(dataset)+new_filename+".jpg")
    os.rename(mask_dir(dataset)+old_filename+".png",mask_dir(dataset)+new_filename+".png")
    os.rename(json_dir(dataset)+old_filename+"_json",json_dir(dataset)+new_filename+"_json")

"""shuffle SP与CM 偶数是CM 奇数是Sp"""
def shuffleDataset(dataset):
    cntSp=1
    cntCm=2
    for img in os.listdir(pic_dir(dataset)):
        imgName= img.split('.')[0]
        flag=imgName[5]
        if flag=='1':
            #splicing
            renameData(dataset,imgName,cntSp)
            cntSp+=2
        else:
            renameData(dataset,imgName,cntCm)
            cntCm+=2


for dataset in DATASET:
    startTime=time.time()
    print("start!")
    shuffleDataset(dataset)
    print("Completed! cost %fs"%(time.time()-startTime))
