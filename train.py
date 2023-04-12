"""
train.py
训练
Modified by DoubleZ, based on Matterport Ballon demo
"""
# -*- coding: utf-8 -*-
import os
import sys
import random
import math
import re
import time
import keras
from keras.models import Sequential
from keras.layers import Dense
import numpy as np
import cv2
import matplotlib
import matplotlib.pyplot as plt
import tensorflow as tf
from mrcnn.config import Config
# import utils
from mrcnn import model as modellib, utils
from mrcnn import visualize
import yaml
from mrcnn.model import log
from PIL import Image
import warnings
from mrcnn.log import Log


warnings.filterwarnings("ignore")
# os.environ["CUDA_VISIBLE_DEVICES"] = "0" #使用CPU训练
# Root directory of the project 项目根目录
ROOT_DIR = os.getcwd()

# Directory to save logs and trained model 保存训练结果与日志的位置
MODEL_DIR = os.path.join(ROOT_DIR, "logs")
iter_num = 0

# Local path to trained weights file 预训练模型位置
COCO_MODEL_PATH = os.path.join(ROOT_DIR, "mask_rcnn_coco.h5")
    
# Which weights to start with? last为从上次训练的位置继续训练 
init_with = "coco"  # imagenet, coco, or last

class ShapesConfig(Config):
    """
    训练Config   Override Config类
    """
    # Give the configuration a recognizable name
    NAME = "shapes"
    BACKBONE = "resnet101"
    # Train on 1 GPU and 8 images per GPU. We can put multiple images on each
    # GPU because the images are small. Batch size is 8 (GPUs * images/GPU).
    GPU_COUNT = 1
    IMAGES_PER_GPU = 8
    
    #训练的类别 2022/10/29修改 修改训练类别只需要修改CLASS内容
    CLASS=['splicing','copymove']
    
    #是否使用预训练模型
    USE_PRETRAINED_MODEL = True

    # Number of classes (including background)
    NUM_CLASSES = 1 + len(CLASS)  # background + n shapes

    # Use small images for faster training. Set the limits of the small side
    # the large side, and that determines the image shape.
    IMAGE_MIN_DIM = 640
    IMAGE_MAX_DIM = 640

    LEARNING_RATE = 0.001


config = ShapesConfig()
config.display()

class DrugDataset(utils.Dataset):
    # 得到该图中有多少个实例（物体）
    def get_obj_index(self, image):
        n = np.max(image)
        return n

    # 解析labelme中得到的yaml文件，从而得到mask每一层对应的实例标签
    def from_yaml_get_class(self, image_id):
        info = self.image_info[image_id]
        with open(info['yaml_path']) as f:
            temp = yaml.load(f.read(), Loader=yaml.FullLoader)
            labels = temp['label_names']
            del labels[0]
        return labels

    # 重新写draw_mask
    def draw_mask(self, num_obj, mask, image, image_id):
        # print("draw_mask-->",image_id)
        # print("self.image_info",self.image_info)
        info = self.image_info[image_id]
        # print("info-->",info)
        # print("info[width]----->",info['width'],"-info[height]--->",info['height'])
        for index in range(num_obj):
            for i in range(info['width']):
                for j in range(info['height']):
                    # print("image_id-->",image_id,"-i--->",i,"-j--->",j)
                    # print("info[width]----->",info['width'],"-info[height]--->",info['height'])
                    at_pixel = image.getpixel((i, j))
                    if at_pixel == index + 1:
                        mask[j, i, index] = 1
        return mask

    # 重新写load_shapes，里面包含自己的类别,可以任意添加
    # 并在self.image_info信息中添加了path、mask_path 、yaml_path
    # yaml_pathdataset_root_path = "/tongue_dateset/"
    # img_floder = dataset_root_path + "rgb"
    # mask_floder = dataset_root_path + "mask"
    # dataset_root_path = "/tongue_dateset/"
    def load_shapes(self, count, img_floder, mask_floder, imglist, dataset_root_path):
        """Generate the requested number of synthetic images.
        count: number of images to generate.
        height, width: the size of the generated images.
        """
        # Add classes,可通过这种方式扩展多个物体
        # self.add_class("shapes", 1, "splicing")
        # self.add_class("shapes", 2, "copymove")
        for i in range(len(config.CLASS)):
            self.add_class(config.NAME,i+1,config.CLASS[i])
        for i in range(count):
            # 获取图片宽和高

            filestr = imglist[i].split(".")[0]
            # print(imglist[i],"-->",cv_img.shape[1],"--->",cv_img.shape[0])
            # print("id-->", i, " imglist[", i, "]-->", imglist[i],"filestr-->",filestr)
            # filestr = filestr.split("_")[1]
            mask_path = mask_floder + "/" + filestr + ".png"
            yaml_path = dataset_root_path + "labelme_json/" + filestr + "_json/info.yaml"
            # print(dataset_root_path + "mask_cv2/" + filestr + "_json/img.jpg")
            # cv_img = cv2.imread(dataset_root_path + "labelme_json/" + filestr + "_json/img.png")
            cv_img = cv2.imread(dataset_root_path + "pic/" + filestr + ".jpg")
            self.add_image(config.NAME, image_id=i, path=img_floder + "/" + imglist[i],
                           width=cv_img.shape[1], height=cv_img.shape[0], mask_path=mask_path, yaml_path=yaml_path)



    # 重写load_mask
    def load_mask(self, image_id):
        """Generate instance masks for shapes of the given image ID.
        """
        global iter_num
        print("image_id", image_id)
#         print(image_id,end='')
        info = self.image_info[image_id]
        count = 1  # number of object
        img = Image.open(info['mask_path'])
        num_obj = self.get_obj_index(img)
        mask = np.zeros([info['height'], info['width'], num_obj], dtype=np.uint8)
        mask = self.draw_mask(num_obj, mask, img, image_id)
        occlusion = np.logical_not(mask[:, :, -1]).astype(np.uint8)
        for i in range(count - 2, -1, -1):
            mask[:, :, i] = mask[:, :, i] * occlusion

            occlusion = np.logical_and(occlusion, np.logical_not(mask[:, :, i]))
        labels = []
        labels = self.from_yaml_get_class(image_id)
        labels_form = []
        for i in range(len(labels)):
            for label in config.CLASS:
                if labels[i].find(label) != -1:
                    labels_form.append(label)
        class_ids = np.array([self.class_names.index(s) for s in labels_form])
        return mask, class_ids.astype(np.int32)


def get_ax(rows=1, cols=1, size=8):
    """Return a Matplotlib Axes array to be used in
    all visualizations in the notebook. Provide a
    central point to control graph sizes.
    Change the default size attribute to control the size
    of rendered images
    """
    _, ax = plt.subplots(rows, cols, figsize=(size * cols, size * rows))
    return ax

#loss可视化
def loss_visualize(epoch, tra_loss, val_loss):
    plt.style.use("ggplot")
    plt.figure()
    plt.subplot(1, 1, 1)
    plt.title("Epoch_Loss")
    plt.plot(epoch, tra_loss, label='train_loss', color='r', linestyle='-', marker='o')
    plt.plot(epoch, val_loss, label='val_loss', linestyle='-', color='b', marker='^')
    plt.legend()
    plt.xlabel('epoch')
    plt.ylabel('loss')
    plt.savefig('loss.jpg')
    plt.show()



# 基础设置 数据集路径设置
dataset_root_path = "train_data/"
img_floder = dataset_root_path + "pic"
mask_floder = dataset_root_path + "cv2_mask"
val_dataset_root_path="val_data/"
val_img_floder = val_dataset_root_path + "pic"
val_mask_floder = val_dataset_root_path + "cv2_mask"
# yaml_floder = dataset_root_path
imglist = os.listdir(img_floder)
count = len(imglist)
val_imglist=os.listdir(val_img_floder)
val_count=len(val_imglist)


# train与val数据集准备
print("正在加载训练集....")
startTime=time.time()
dataset_train = DrugDataset()
dataset_train.load_shapes(count, img_floder, mask_floder, imglist, dataset_root_path)
dataset_train.prepare()
costTime = time.time() - startTime
print("训练集->共加载%d张数据,耗时%fs" % (count,costTime))

print("正在加载验证集....")
startTime=time.time()
dataset_val = DrugDataset()
dataset_val.load_shapes(val_count, val_img_floder, val_mask_floder, val_imglist, val_dataset_root_path)
dataset_val.prepare()
val_costTime = time.time() - startTime
print("验证集->共加载%d张数据,耗时%fs" % (val_count,val_costTime))
# Load and display random samples
# image_ids = np.random.choice(dataset_train.image_ids, 4)
# for image_id in image_ids:
#    image = dataset_train.load_image(image_id)
#    mask, class_ids = dataset_train.load_mask(image_id)
#    visualize.display_top_masks(image, mask, class_ids, dataset_train.class_names)

# Create model in training mode
model = modellib.MaskRCNN(mode="training", config=config,
                          model_dir=MODEL_DIR)

if init_with == "last":
    # Load the last model you trained and continue training
    model.load_weights(model.find_last(), by_name=True)
else:
    if config.USE_PRETRAINED_MODEL:
        if not os.path.exists(COCO_MODEL_PATH):
            raise ImportError('`COCO_MODEL_PATH` not found')
        if init_with == "imagenet":
            model.load_weights(model.get_imagenet_weights(), by_name=True)
        elif init_with == "coco":
            # Load weights trained on MS COCO, but skip layers that
            # are different due to the different number of classes
            # See README for instructions to download the COCO weights
            model.load_weights(COCO_MODEL_PATH, by_name=True,exclude=["mrcnn_class_logits", "mrcnn_bbox_fc","mrcnn_bbox", "mrcnn_mask"])
    


print(model.log_dir)
config.save(model.log_dir)
logs=Log(model.log_dir)
logs.logDataset(config,costTime,val_costTime)
# Train the head branches
# Passing layers="heads" freezes all layers except the head
# layers. You can also pass a regular expression to select
# which layers to train by name pattern.
logs.beginTrain()


#layers可以设置为heads 即为只训练heads部分 设置为all则训练整个网络 学习率在这里设置
model.train(dataset_train, dataset_val,
            learning_rate=config.LEARNING_RATE,
            epochs=30,
            layers='all',
            logs=logs)

# Fine tune all layers
# Passing layers="all" trains all layers. You can also
# pass a regular expression to select which layers to
# train by name pattern.
model.train(dataset_train, dataset_val,
            learning_rate=config.LEARNING_RATE / 10,
            epochs=60,
            layers="all",
            logs=logs)
model.train(dataset_train, dataset_val,
            learning_rate=config.LEARNING_RATE / 100,
            epochs=100,
            layers="heads",
            logs=logs)

logs.endTrain()
# x_epoch, y_tra_loss, y_val_loss = modellib.call_back()
# loss_visualize(x_epoch, y_tra_loss, y_val_loss)
