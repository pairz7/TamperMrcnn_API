"""
用于合并数据集
将SP与CM合并为1类(tamper)
Written By DoubleZ
"""

import os
import shutil
import time

"""SET :如果数据集是以文件名奇偶区分则设置为1 以倒数第5位区分则设置为0"""
SET=1
"""DATASET :数据集的文件夹名"""
DATASET=["train_data","test_data","val_data"]

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

"""merge SP与CM 偶数是CM 奇数是Sp"""
def shuffleDataset(dataset):
    cntSp=1
    cntCm=2
    for img in os.listdir(pic_dir(dataset)):
        imgName= img.split('.')[0]
        if SET==0:
             # 文件名第5位为1代表拼接 为0代表复制粘贴
            flag = imgName[5]
            if flag =='1':
                # 拼接
                renameData(dataset,imgName,cntSp)
                editFile(dataset + '/labelme_json/' + imgName + "_json/info.yaml", "splicing","tamper")
                cntSp += 2
            if flag == '0':
                # 复制粘贴
                renameData(dataset,imgName,cntCm)
                editFile(dataset + '/labelme_json/' + imgName + "_json/info.yaml", "copymove","tamper")
                cntCm += 2
        elif SET==1:
            # 文件名编号为偶数表示复制粘贴 为奇数表示拼接
            if int(imgName)%2!=0:
                # 拼接
                renameData(dataset,imgName,cntSp)
                editFile(dataset + '/labelme_json/' + imgName + "_json/info.yaml", "splicing","tamper")
                cntSp += 2
            if int(imgName)%2==0:
                # 复制粘贴
                renameData(dataset,imgName,cntCm)
                editFile(dataset + '/labelme_json/' + imgName + "_json/info.yaml", "copymove","tamper")
                cntCm += 2


for dataset in DATASET:
    startTime=time.time()
    print("start!")
    shuffleDataset(dataset)
    print("Completed! cost %fs"%(time.time()-startTime))
