"""
squeeze_dataset
按照比例缩小数据集大小
Written by DoubleZ
"""
import os
import shutil
import time

"""DEL_RATIO参数为数据集缩小比率 数据集将缩小到原来的DEL_RATIO倍 """
DEL_RATIO=0.6 #数据集缩小比率
"""DATASET为要操作的数据集文件名"""
DATASET=["train_data","test_data","val_data"]
"""SET :如果数据集是以文件名奇偶区分则设置为1 以倒数第5位区分则设置为0"""
SET=1

def pic_dir(dataset):
    return "./%s/pic/"%(dataset)

def mask_dir(dataset):
    return "./%s/cv2_mask/"%(dataset)

def json_dir(dataset):
    return "./%s/labelme_json/"%(dataset)

def remove(dataset,name):
    os.remove(pic_dir(dataset)+name+".jpg")
    os.remove(mask_dir(dataset) + name + ".png")
    shutil.rmtree(json_dir(dataset)+name+"_json")

def squeezeDataset(dataset):
    num=len(os.listdir(pic_dir(dataset)))
    DELNUM = num*(1-DEL_RATIO)
    print("原数据集数量:{},删除的数据量:{}".format(num,DELNUM))
    Ccnt = 0
    Scnt = 0
    for img in os.listdir(pic_dir(dataset)):
        imgName = img.split('.')[0]
        if SET==0:
             # 文件名第5位为1代表拼接 为0代表复制粘贴
            flag = imgName[5]
            if flag =='1' and Scnt<DELNUM/2:
                # 拼接
                remove(dataset,imgName)
                Ccnt += 1
            if flag == '0' and Ccnt<DELNUM/2:
                # 复制粘贴
                remove(dataset,imgName)
                Ccnt += 1
        elif SET==1:
            # 文件名编号为偶数表示复制粘贴 为奇数表示拼接
            if int(imgName)%2!=0 and Scnt<DELNUM/2:
                # 拼接
                remove(dataset,imgName)
                Scnt += 1
            if int(imgName)%2==0 and Ccnt<DELNUM/2:
                # 复制粘贴
                remove(dataset,imgName)
                Ccnt += 1
    print("ok,has deleted for "+dataset+":" + str(Ccnt+Scnt))
    print("there still " + str(len(os.listdir(pic_dir(dataset)))) + " in "+pic_dir(dataset))
    print("there still " + str(len(os.listdir(mask_dir(dataset)))) + " in "+mask_dir(dataset))
    print("there still " + str(len(os.listdir(json_dir(dataset)))) + " in "+json_dir(dataset))


    
startTime=time.time()
for dataset in DATASET:    
    print(dataset+":")
    squeezeDataset(dataset)
print("Completed! cost %fs"%(time.time()-startTime))

