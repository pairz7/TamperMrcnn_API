"""
用于debug
请按照自己需求编写
"""
import multiprocessing
import os
import shutil
import time

"""SET :如果数据集是以文件名奇偶区分则设置为1 以倒数第5位区分则设置为0"""
SET=1
"""DATASET :数据集的文件夹名"""
DATASET=["train_data","test_data","val_data"]

# print("CPU_COUNT--->>>{}".format(multiprocessing.cpu_count()))
def pic_dir(dataset):
    return "./%s/pic"%(dataset)

def mask_dir(dataset):
    return "./%s/cv2_mask"%(dataset)

def json_dir(dataset):
    return "./%s/labelme_json"%(dataset)


def print_numDataset(dataset):
    print(str(len(os.listdir(pic_dir(dataset)))) + " in "+pic_dir(dataset))
    print(str(len(os.listdir(mask_dir(dataset)))) + " in "+mask_dir(dataset))
    print(str(len(os.listdir(json_dir(dataset)))) + " in "+json_dir(dataset))

    
def testDataset(dataset):
    _pic_dir=pic_dir(dataset)
    num=len(os.listdir(_pic_dir))
    Ccnt = 0
    Scnt = 0
    for img in os.listdir(_pic_dir):
        if '.jpg' not in img:
            continue 
        imgName = img.split('.')[0]
        if SET==0:
             # 文件名第5位为1代表拼接 为0代表复制粘贴
            flag = imgName[5]
            if flag =='1':
                # 拼接
                Scnt += 1
            if flag == '0':
                # 复制粘贴
                Ccnt += 1
        elif SET==1:
            # 文件名编号为偶数表示复制粘贴 为奇数表示拼接
            if int(imgName)%2!=0:
                # 拼接
                Scnt += 1
            if int(imgName)%2==0:
                # 复制粘贴
                Ccnt += 1
    return [Scnt,Ccnt,num]
   
    
startTime=time.time()
for dataset in DATASET:
    print(dataset+"数据情况:")
    print("拼接:复制:总数 = "+str(testDataset(dataset)))
    print_numDataset(dataset)
    print()
print("Completed! cost %fs"%(time.time()-startTime))
    
    
    