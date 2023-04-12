from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import time

import numpy as np
import io
import skimage.io
from mrcnn.config import Config
# Kerasfrom io import StringIO
import base64
from urllib.parse import quote
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image
import matplotlib.pyplot as plt
# Flask utils
from flask import Flask, redirect, url_for, request, render_template ,make_response,jsonify
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from mrcnn import utils
import mrcnn.model as modellib
from mrcnn import visualize
# Define a flask app
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources=r'/*')
# Model saved with Keras model.save()
MODEL_PATH = 'logs/mask_rcnn_shapes_0012.h5'
# MODEL_PATH = 'F:/2022.10.08-basicMrcnn-19w-8/shapes20221008T1601/mask_rcnn_shapes_0020.h5'
#MODEL_PATH = 'F:/实验-数据集分类/shapes20221023T2136/mask_rcnn_shapes_0020.h5'

# You can also use pretrained model from Keras
# Check https://keras.io/applications/
#from keras.applications.resnet50 import ResNet50
#model = ResNet50(weights='imagenet')
#print('Model loaded. Check http://127.0.0.1:5000/')
# Local path to trained weights file
ROOT_DIR = os.path.abspath("../")

MODEL_DIR = os.path.join(ROOT_DIR, "logs")
class InferenceConfig(Config):
    # Set batch size to 1 since we'll be running inference on
    # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    NUM_CLASSES = 1+1
    NAME = "shapes"
    DETECTION_MIN_CONFIDENCE=0.3

config = InferenceConfig()
model = modellib.MaskRCNN(mode="inference", model_dir=MODEL_DIR, config=config)

# Load weights trained on MS-COCO
model.load_weights(MODEL_PATH, by_name=True)
MODEL_DIR = os.path.join(ROOT_DIR, "logs")
class_names = ['background','tamper']
def model_predict(img_path, model,threshold=0.3):
    model.config.DETECTION_MIN_CONFIDENCE = threshold
    img1=skimage.io.imread(img_path)
    # Preprocessing the image
    results = model.detect([img1]   , verbose=1)
    # class_names = ['background','tamper']
    # Visualize results
    """Todo Verify
        可以调整score的阈值
        可以得到都有哪些篡改类型
    """
    r = results[0]
    return visualize.display_instances(img1, r['rois'], r['masks'], r['class_ids'],class_names, r['scores'],threshold=threshold),r

@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')

file_path=""

@app.route('/predict', methods=['POST'])
def upload():
    if request.method == "POST":
        fig = plt.figure()
        f = request.files['file']
        threshold = float(request.form['threshold'])
        req=request
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'static', secure_filename(f.filename))
        f.save(file_path)
        print(file_path)
        startTime = time.time()
        preds,result_info = model_predict(file_path,model,threshold)
        result_info=pickResult(result_info,threshold)
        names_list=get_class_name_list(result_info)
        cost_time=time.time()-startTime
        cost_time="%.2f"%(cost_time)
        img = io.BytesIO()
        preds.savefig(img, format='png',bbox_inches="tight")
        img.seek(0)
        data = base64.b64encode(img.getvalue()).decode()
        data_url = 'data:image/png;base64,{}'.format(quote(data))
        res={'data_url':data_url,'cost_time':cost_time,'class_names':names_list,'scores':get_scores_list(result_info)}
        return jsonify(res)
    return None


"""       
@app.route('/prediction', methods=['GET'])
def gred():
    print(request.args.get(file_path))
    return render_template("im1.html",url = 'static/new_plot.jpg',url1= str(request.args.get(file_path)))
"""    

"""
@app.after_request
def func_res(resp):     
    res = make_response(resp)
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Methods'] = 'GET,POST'
    res.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return res
"""

"""获得预测的类别"""
def get_class_name_list(result):
    class_ids=result['class_ids']
    name_list = []
    for id in class_ids:
        name_list.append(class_names[id])
    split='-'
    return split.join(name_list)

"""获得scores的列表"""
def get_scores_list(result):
    split='-'
    score_list=[]
    for score in result['scores']:
        score_list.append(str(score))
    return split.join(score_list)

def getMostList(result):
    pass

def delndarry(ndarry,del_index):
    ndarry = ndarry.tolist()
    ndarry=[i for num,i in enumerate(ndarry) if num not in del_index]
    return np.array(ndarry)

"""筛选result"""
def pickResult(result,threshold=0.7):
    delIndex=[]
    for i in range(len(result['scores'])):
        if result['scores'].tolist()[i]<threshold:
            delIndex.append(i)
    result['rois'] = delndarry(result['rois'], delIndex)
    result['class_ids'] = delndarry(result['class_ids'], delIndex)
    result['masks'] = delndarry(result['masks'], delIndex)
    result['scores'] = delndarry(result['scores'], delIndex)
    return result

if __name__ == '__main__':
    # app.run(port=5002, debug=True)

    # Serve the app with gevent
    http_server = WSGIServer(('', 8080), app)
    http_server.serve_forever()
