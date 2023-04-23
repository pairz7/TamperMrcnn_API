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
import base64
from urllib.parse import quote
import uuid
import datetime
# Flask utils
from flask import Flask, request,jsonify,make_response
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
# Define a flask app
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources=r'/*')
# Model saved with Keras model.save()
MODEL_PATH = 'logs/mask_rcnn_shapes_0012.h5'
ROOT_DIR = os.path.abspath("../")
MODEL_DIR = os.path.join(ROOT_DIR, "logs")

# Mysql配置
# mysql配置
host = 'notamper.cn'
port = 3306
db = 'tamperWeb'
user = 'web_user'
password = '123456'

# ---- 用pymysql 操作数据库
def get_connection():
    conn = pymysql.connect(host=host, port=port, db=db, user=user, password=password)
    return conn

mysql_conn = get_connection()

@app.route("/imageResult/<img_path>")
def get_filename(img_path):
    image_data = open('imageResult/' + img_path, 'rb').read()
    res = make_response(image_data)
    res.headers['Content-Type'] = 'image/png'
    return res  

@app.route('/imageUpload/<img_path>')
def read_img(img_path):
    image_data = open('imageUpload/' + img_path, 'rb').read()
    res = make_response(image_data)
    res.headers['Content-Type'] = 'image/png'
    return res    


if __name__ == '__main__':
    port = 2333  # 端口号
    dev = 1 #1表示是开发模式
    if dev==1:
        # app.run('', port, debug=True,  use_reloader=False)
        http_server = WSGIServer(('', port), app)
        http_server.serve_forever()
    else:
        app.run('', port, debug=True, ssl_context=('cert/9215363_notamper.cn.pem', 'cert/9215363_notamper.cn.key'))
        # Serve the app with gevent
        print("Web Service running in http://localhost:%d/" % port)
        http_server = WSGIServer(('', port), app, keyfile='cert/9766242_service.notamper.cn.key',
                                 certfile='cert/9766242_service.notamper.cn.pem')
        http_server.serve_forever()

