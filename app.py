from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import time
import pymysql
import numpy as np
import io
import skimage.io
from mrcnn.config import Config
# Kerasfrom io import StringIO
import base64
from urllib.parse import quote
import uuid
import datetime
# Flask utils
from flask import Flask, request,jsonify,send_from_directory, make_response
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
# from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
# from matplotlib.figure import Figure
from mrcnn import utils
import mrcnn.model as modellib
from mrcnn import visualize
# Define a flask app
from flask_cors import CORS

from matplotlib import pyplot as plt
import matplotlib
matplotlib.use("TkAgg")

app = Flask(__name__)
CORS(app, resources=r'/*')
# Model saved with Keras model.save()
MODEL_PATH = 'logs/mask_rcnn_shapes_0012.h5'
ROOT_DIR = os.path.abspath("../")
MODEL_DIR = os.path.join(ROOT_DIR, "logs")

# Mysql配置
host = 'notamper.cn'
port = 3306
db = 'tamperWeb'
user = ''
password = ''

# ---- 用pymysql 操作数据库
def get_connection():
    conn = pymysql.connect(host=host, port=port, db=db, user=user, password=password)
    return conn

mysql_conn = get_connection()

class InferenceConfig(Config):
    # Set batch size to 1 since we'll be running inference on
    # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    NUM_CLASSES = 1+1
    NAME = "shapes"
    DETECTION_MIN_CONFIDENCE=0.3
    IMAGE_MIN_DIM = 512

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


file_path=""

@app.route('/predict', methods=['POST'])
def upload():
    if request.method == "POST":
        """第一轮生成记录信息"""
        detectID = uuid.uuid1().hex
        serviceName = "图像篡改检测"
        detectDatetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        """接收参数"""
        f = request.files['file']
        threshold = float(request.form['threshold'])
        orderID = request.form['orderID']
        recv_key = request.form['Key']
        """
        验证API是否可用
        首先检查orderID是否存在 然后查看key是否对应 
        如果valid 判断state是否为正在运行 判断剩余次数是否大于0 如果是则通过且剩余次数-1 使用次数+1
        """
        isValid = False
        msg = '发生未知错误'
        try:
            # check out if the connect is exist
            mysql_conn.ping(reconnect=True)
            cursor = mysql_conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("select `usedTimes`,`remainTimes`,`key`,`state` from api where orderID = '%s'"%orderID)
            api = cursor.fetchall()
            api = api[0]
            if len(api)==0 or recv_key!=api['key']:
                #api验证失败
                isValid = False
                msg = 'API验证失败'
            else:
                usedTimes = int(api['usedTimes'])
                remainTimes = int(api['remainTimes'])
                state = api['state']
                if state=='正在运行':
                    if remainTimes>0:
                        remainTimes -= 1
                        usedTimes += 1
                        cursor.execute("UPDATE `api` SET `usedTimes`='%d', `remainTimes`='%d' WHERE (`orderID`='%s')"%(usedTimes, remainTimes, orderID))
                        mysql_conn.commit()
                        isValid = True
                    else:
                        cursor.execute(
                            "UPDATE `api` SET `state`='%s' WHERE (`orderID`='%s')" % (
                            '欠费停止', orderID))
                        mysql_conn.commit()
                        msg = 'API已欠费'
                        isValid = False
                else:
                    msg = 'API处于不可用状态'
                    isValid = False
            cursor.close()
        except Exception as e:
            mysql_conn.rollback()
            print(e)
            cursor.close()
            pass
        if not isValid:
            return jsonify({'msg': msg, 'code':0, 'result':None})
        """
        验证通过
        """
        basepath = os.path.dirname(__file__)
        file_suffix = f.filename.split('.')[1]
        file_name = detectID + '.' + file_suffix
        file_path = os.path.join(basepath, 'imageUpload', secure_filename(file_name))
        '''第二轮生成记录信息'''
        uploadImageUrl = 'imageUpload/' + file_name
        resultImageUrl = 'imageResult/' + detectID + '.jpg'
        callerIP = request.form['ip']
        callerUsername = request.form['username']
        f.save(file_path)
        print(file_path)
        '''生成记录 插入数据库'''
        try:
            # check out if the connect is exist
            mysql_conn.ping(reconnect=True)
            cursor = mysql_conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("INSERT INTO `imageRecord` \
            (`detectID`, `serviceName`, `detectThreshold`,`detectDatetime`, \
             `detectState`,`resultImageUrl`, `uploadImageUrl`, `callerIP`, `callerUsername`) \
            VALUES ('%s', '%s', '%.2f','%s', '%s', '%s', '%s', '%s', '%s')" % (
                detectID, serviceName, threshold, detectDatetime, "检测中",\
                resultImageUrl, uploadImageUrl, callerIP, callerUsername))
            mysql_conn.commit()
            cursor.close()
        except Exception as e:
            mysql_conn.rollback()
            print(e)
            cursor.close()
            pass
        """检测部分"""
        isExcept = False
        cost_time = 0
        tamperRegionNum = 0
        detectResult = ''
        code = 1
        res = {}
        try:
            startTime = time.time()
            preds, result_info = model_predict(file_path, model, threshold)
            result_info = pickResult(result_info, threshold)
            names_list = get_class_name_list(result_info)
            """第三轮生成记录信息"""
            tamperRegionNum = len(result_info['scores'])
            if tamperRegionNum > 0:
                detectResult = "疑似篡改"
            else:
                detectResult = "未发现篡改"
            cost_time = time.time() - startTime
            cost_time = "%.2f" % (cost_time)
            img = io.BytesIO()
            preds.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
            # preds.margins(0, 0)
            plt.margins(0, 0)
            preds.savefig(img, format='jpg', pad_inches=-1)
            preds.savefig(resultImageUrl, format='jpg',pad_inches=-1)
            img.seek(0)
            data = base64.b64encode(img.getvalue()).decode()
            data_url = 'data:image/jpeg;base64,{}'.format(quote(data))
            res = {'data_url': data_url, 'cost_time': cost_time, 'class_names': names_list,
                   'scores': get_scores_list(result_info)}
            '''修改记录 生成完整记录'''
        except:
            isExcept = True
        try:
            # check out if the connect is exist
            mysql_conn.ping(reconnect=True)
            cursor = mysql_conn.cursor(pymysql.cursors.DictCursor)
            if isExcept:
                cursor.execute(
                    "UPDATE `imageRecord` SET `detectCostTime`='%ss', `detectState`='%s' WHERE (`detectID`='%s')" % (
                        cost_time, "检测失败", detectID))
                msg = '检测失败'
                code = 0

            else:
                cursor.execute(
                    "UPDATE `imageRecord` SET `detectCostTime`='%ss', `tamperRegionNum`='%d', `detectResult`='%s', `detectState`='%s' WHERE (`detectID`='%s')" % (
                        cost_time, tamperRegionNum, detectResult, "已完成", detectID))
                msg = '检测成功'
            mysql_conn.commit()
            cursor.close()
        except Exception as e:
            mysql_conn.rollback()
            print(e)
            cursor.close()
            pass
        return jsonify({'msg':msg,'code':code,'result':res})
    return None



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
    port = 801  # 端口号
    dev = 1 #1表示是开发模式
    if dev==1:
        # app.run('', port, debug=True,  use_reloader=False)
        http_server = WSGIServer(('', port), app)
        http_server.serve_forever()
    else:
        # app.run('', port, debug=True, ssl_context=('cert/9215363_notamper.cn.pem', 'cert/9215363_notamper.cn.key'))
        # Serve the app with gevent
        print("Web Service running in http://localhost:%d/" % port)
        http_server = WSGIServer(('', port), app, keyfile='cert/9766242_service.notamper.cn.key',
                                 certfile='cert/9766242_service.notamper.cn.pem')
        http_server.serve_forever()

