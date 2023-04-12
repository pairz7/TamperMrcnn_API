"""
按照6:2:2划分数据集
"""
#分割数据集 6/2/2
import os
import shutil
def move(src_root,dst_root,name):
    shutil.move(src_root+'pic/'+name+".jpg",dst_root+'pic/'+name+".jpg")
    shutil.move(src_root+'cv2_mask/' + name + ".png",dst_root+'cv2_mask/'+name+".png")
    shutil.move(src_root+"labelme_json/"+name+"_json/",dst_root+"labelme_json/"+name+"_json/")


dataset_root='cp_data/'
pic_path=dataset_root+'pic/'
mask_path=dataset_root+'cv2_mask/'
json_path=dataset_root+'labelme_json/'
val_dataset_root='val_data/'
val_pic_path=val_dataset_root+'pic/'
val_mask_path=val_dataset_root+'cv2_mask/'
val_json_path=val_dataset_root+'labelme_json/'
count=len(os.listdir(dataset_root+'pic'))
train_count=(int)(count*0.6)
val_count=(int)(count*0.2)
test_count=count-train_count-val_count
print("划分情况 train:%d val:%d test:%d"%(train_count,val_count,test_count))
cnt=0
for img in os.listdir(pic_path):
    if cnt==train_count-1:
        break
    imgName=img.split('.')[0]
    move(dataset_root,'train_data/',imgName)
    cnt+=1
cnt=0
for img in os.listdir(pic_path):
    if cnt==val_count-1:
        break
    imgName=img.split('.')[0]
    move(dataset_root,'val_data/',imgName)
    cnt+=1
cnt=0
for img in os.listdir(pic_path):
    if cnt==test_count-1:
        break
    imgName=img.split('.')[0]
    move(dataset_root,'test_data/',imgName)
    cnt+=1

print("ok!")