import redis
import pandas as pd
import MySQLdb
import queue
from .algorithm import *
from .basic import *
from .data_process import *
from .others import *

r = redis.StrictRedis(host='localhost', port=6379, charset='utf-8', decode_responses=True)

from .api.inout import in0out1, in1out0, in1out1, in1out2, in2out1, in2out2

data = {}

# status : 0 finish 1 running 2 unvisited -1 failed

def analysis(data):
    """
    execute gragh according "all_nodes" "all_lines" "nodes_details"
    detail:
    1. delete old nodes which doesn't appear (use old nodes table)
    2. set new lines, degree setting & type check
    """
    r.set('global', '1')
    # check nodes' type

    # check degree
    in_degree = {}
    for line, pair in data['all_lines'].items():
        in_degree[pair[1]] = pair[0]
        # check input type

    r.delete('status')

    q = queue.Queue()
    while True:
        for node, t in data['all_nodes'].items():
            if r.hexists('status', node):
                continue

            dic = {'name':node,
                   'node_type':t,
                   'params':data['nodes_details'][node]
                  }

            if t in in0out1:
                r.hset('status', node, '1')
                q.put(dic)

            elif t in in1out0 or t in in1out1 or t in in1out2:
                in1 = node+'in1'
                if in1 not in in_degree:
                    r.hset('status', node, '-1')
                    continue
                if r.hget('status', in_degree[in1][:-4]) != '0':
                    continue
                r.hset('status', node, '1')
                dic.update({'in1':in_degree[in1]})
                q.put(dic)

            elif t in in2out1:
                in1 = node+'in1'
                in2 = node+'in2'
                if in1 not in in_degree or in2 not in in_degree:
                    r.hset('status', node, '-1')
                    continue
                if r.hget('status', in_degree[in1][:-4]) != '0':
                    continue
                if r.hget('status', in_degree[in2][:-4]) != '0':
                    continue
                r.hset('status', node, '1')
                dic.update({
                    'in1':in_degree[in1],
                    'in2':in_degree[in2]
                })
                q.put(dic)

            else:
                print("ERROR, unknown type found : " + t)

        if q.empty():
            break
        run(**q.get())

    r.set('global', '0')


def run(name, node_type, params, in1=None, in2=None):
    global data
    print('running', name)
    if node_type in in0out1:
        b, result = run_func(node_type, params=params)
        data[name + 'out1'] = result
    elif node_type in in1out0:
        b, tmp = run_func(node_type, in1=data[in1], params=params)
    elif node_type in in1out1:
        b, result = run_func(node_type, in1=data[in1], params=params)
        data[name + 'out1'] = result
    elif node_type in in1out2:
        b, results = run_func(node_type, in1=data[in1], params=params)
        data[name + 'out1'] = results[0]
        data[name + 'out2'] = results[1]
    elif node_type in in2out1:
        b, result = run_func(node_type, in1=data[in1], in2=data[in2], params=params)
        data[name + 'out1'] = result
    else:
        print("ERROR, unknown type found : " + node_type)

    if b:
        r.hset('status', name, '0')
    else:
        r.hset('status', name, '-1')

def run_func(node_type, params=None, in1=None, in2=None):
    s = node_type.replace('-', '_')
    return eval(s + '(in1=in1, in2=in2, **params)')


