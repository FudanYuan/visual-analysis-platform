from . import main
from .. import db
from ..models import Hello
from flask import render_template, request

from .analysis import analysis

import os
import redis
import pickle
import multiprocessing
import json as js
import pandas as pd
import numpy as np


debug = True

subprocess = multiprocessing.Process(name='empty')
r = redis.StrictRedis(host='localhost', port=6379, db=0, charset='utf-8', decode_responses=True)
r_data = redis.StrictRedis(host='localhost', db=0, port=6379)

@main.route('/init', methods=['POST'])
def init():
    print('init start')
    if subprocess.is_alive():
        subprocess.terminate()
    r.set('global', '1')
    r.delete('status')
    r.delete('data')
    print('init finish')
    tmp = {"status":0}
    return js.dumps(tmp)

@main.route('/run', methods=['POST'])
def run():
    a = request.get_data().decode('utf-8')
    a = js.loads(a)
    print(a)
    global child_process
    subprocess = multiprocessing.Process(name="analysis", target=analysis, args=(a,))
    subprocess.daemon = True
    subprocess.start()
    print('running processing')
    tmp = {"status":0}
    return js.dumps(tmp)

@main.route('/progress', methods=['POST'])
def progress():
    progress = r.hgetall('status')
    print(progress)
    status = r.get('global')
    print(status)
    if status != '0':
        status = '1'

    tmp = {
        "status":status,
        "progress":progress
    }
    return js.dumps(tmp)

@main.route('/sample', methods=['POST'])
def sample():
    finish = False
    try:
        a = request.get_data().decode('utf-8')
        a = js.loads(a)
        df = pickle.loads(r_data.hget('data', a['node_name']+'out1'))
        num = max(a['number'], 0)
        num = min(num, len(df))
        index = df.columns.tolist()
        df = df[0:num]
        df = df.round(3)
        for i in range(len(index)):
            index[i] += '\n(' + str(df[index[i]].dtype) + ')'
        df = df.fillna('NaN')
        df = np.array(df).tolist()

        ret = {}
        ret = {
            'col':len(index),
            'index':index,
            'row':num,
            'data': df
        }
        finish = True

    except AttributeError as e:
        print('Error in route : sapmle Attribute')
        print(e)
        if type(df) is "list":
            df = df[0]
        ret = {
            'col':1,
            'index':['ErrorMessage'],
            'row':1,
            'data':[[str(df[0])]]
        }
    except Exception as e:
        print('Error in route : sapmle Exception')
        print(e)
        ret = {
            'col':1,
            'index':['ErrorMessage'],
            'row':1,
            'data':[[str(e)]]
        }
    if not finish and not debug:
        ret = {
            'col':0,
            'index':[],
            'row':0,
            'data':[],
            'message':ret['data']
        }

    return js.dumps(ret).encode('utf-8')
