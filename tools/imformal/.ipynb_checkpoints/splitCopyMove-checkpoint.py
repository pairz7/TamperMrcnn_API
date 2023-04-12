"""
将复制粘贴类单独移走
"""
import os
import shutil

dataset_root='train_data/'

def move(src_root,dst_root,name):
    shutil.move(src_root+'pic/'+name+".jpg",dst_root+'pic/'+name+".jpg")
    shutil.move(src_root+'cv2_mask/' + name + ".png",dst_root+'cv2_mask/'+name+".png")
    shutil.move(src_root+"labelme_json/"+name+"_json/",dst_root+"labelme_json/"+name+"_json/")


for img in os.listdir(dataset_root+'pic'):
    imgName=img.split('.')[0]
    flag=imgName[5]
    if flag=='0':
        #复制粘贴
        move(dataset_root,'cp_data/',imgName)

print("ok,done")
print("there still "+str(len(os.listdir("train_data/pic")))+" in train_data/pic/")
print("there still "+str(len(os.listdir("train_data/cv2_mask")))+" in train_data/cv2_mask/")
print("there still "+str(len(os.listdir("train_data/labelme_json")))+" in train_data/labelme_json/")
print("there still "+str(len(os.listdir("cp_data/pic")))+" in cp_data/pic/")
print("there still "+str(len(os.listdir("cp_data/cv2_mask")))+" in cp_data/cv2_mask/")
print("there still "+str(len(os.listdir("cp_data/labelme_json")))+" in cp_data/labelme_json/")