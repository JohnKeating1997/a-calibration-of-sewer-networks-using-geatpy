import os
import numpy as np
import pandas as pd
import time
from swmm5.swmm5tools import SWMM5Simulation
import geatpy as ea

from my_split import run_simulation1 as run_simulation1
from my_split import run_simulation2 as run_simulation2
from my_split import modify_inp as modify_inp

from my_problem import read_data as read_data
# from my_problem import read_data as read_data
from my_problem import MyProblem as MyProblem

if __name__ == "__main__":
    """
    split
    """
    con_mat = np.zeros((4,64))
    meters_pos = [13,36,57,14]  # Node14 对应 P64
    downstream_arr = [None]*4
    for i in range(1,65):
        modify_inp('case_empty.inp', i)
        if i in meters_pos:
            downstream_arr[meters_pos.index(i)] = run_simulation2('case_modified.inp')
        con_mat = run_simulation1(con_mat,'case_modified.inp',meters_pos)

    for i,v in enumerate(downstream_arr):
        con_mat[i] += v
        for inx,val in enumerate(con_mat[i]):
            if val == 2:
                con_mat[i,inx] = 0
    for i,v in enumerate(meters_pos):
        con_mat[i,v-1] = 1  #把监测点本身补上
    # print(con_mat)


    """
    define problem
    """
    res,avg = read_data('监测点数据.xlsx', 1)  # J-36 水位计

    """=================================实例化问题对象==============================="""
    problem = MyProblem(M=1,con_mat_row=con_mat[1],avg=1,gauge_index=1,ObjData=res)
    """=================================种群设置==============================="""
    Encoding = 'BG'       # 编码方式
    NIND = 120            # 种群规模

    Field = ea.crtfld(Encoding, problem.varTypes, problem.ranges, problem.borders) # 创建区域描述器
    population = ea.Population(Encoding, Field, NIND) # 实例化种群对象（此时种群还没被初始化，仅仅是完成种群对象的实例化）
    """===============================算法参数设置============================="""
    myAlgorithm = ea.soea_SEGA_templet(problem, population)  # 实例化一个算法模板对象
    myAlgorithm.MAXGEN = 100  # 最大进化代数
    """==========================调用算法模板进行种群进化======================="""
    [population, obj_trace, var_trace] = myAlgorithm.run()  # 执行算法模板
    population.save()  # 把最后一代种群的信息保存到文件中

    # 输出结果
    best_gen = np.argmin(problem.maxormins * obj_trace[:, 1]) # 记录最优种群个体是在哪一代
    best_ObjV = obj_trace[best_gen, 1]
    print('最优的目标函数值为：%s'%(best_ObjV))
    """
    保存一下最优的种群对应的inp文件
    """
    problem.modify_inp(infile='case1.inp',pattern=var_trace[best_gen],output_name='case_best.inp')

    print('最优的控制变量值为：')
    for i in range(var_trace.shape[1]):
        print(var_trace[best_gen, i])
    print('有效进化代数：%s'%(obj_trace.shape[0]))
    print('最优的一代是第 %s 代'%(best_gen + 1))
    print('评价次数：%s'%(myAlgorithm.evalsNum))
    print('时间已过 %s 秒'%(myAlgorithm.passTime))