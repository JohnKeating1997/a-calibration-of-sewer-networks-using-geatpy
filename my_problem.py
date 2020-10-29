# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import geatpy as ea
# from geatpy.Problem import Problem
from swmm5.swmm5tools import SWMM5Simulation
import os


# 自定义问题类
def read_data(infile,gauge_index):
    gauge_dict = ('J13','J36','J57','P64')
    df1 = pd.read_excel(infile)
    res = list(df1[gauge_dict[gauge_index]])[1::]
    return (res,sum(res)/len(res))



def get_result(inpfile):
    st1 = SWMM5Simulation(inpfile)
    return st1

class MyProblem(ea.Problem):  # 继承Problem父类
    def __init__(self, M ,con_mat_row,avg,gauge_index,ObjData):
        """

        :param M:
        :param con_mat_row:
        :param avg: Baseline
        :param gauge_index:
        :param ObjData:
        """

        """
        1.解析con_mat，找出对应的连接管段
        """
        self.nodes = []
        for i, v in enumerate(con_mat_row):
            if v == 1:
                self.nodes.append(i + 1)

        """
        2.初始化问题参数
        """
        name = 'MyProblem'  # 初始化name（函数名称，可以随意设置）
        M = 1  # 初始化M（目标维数）
        maxormins = [1]  # 初始化maxormins（目标最小最大化标记列表，1：最小化该目标；-1：最大化该目标）
        Dim = int(24*len(self.nodes))  # 初始化Dim（决策变量维数）
        varTypes = [0] * Dim  # 初始化varTypes（决策变量的类型，0：实数；1：整数）
        lb = [0] * Dim  # 决策变量下界
        ub = [5] * Dim  # 决策变量上界
        lbin = [1] * Dim  # 决策变量下边界是否包含
        ubin = [1] * Dim  # 决策变量上边界是否包含
        gauge_dict = (13,36,57,64)
        gauge = gauge_dict[gauge_index]
        # 调用父类构造方法完成实例化
        ea.Problem.__init__(self, name, M, maxormins, Dim, varTypes, lb, ub, lbin, ubin)
        self.con_mat_row = con_mat_row
        self.avg= avg
        self.gauge = gauge
        self.ObjData = ObjData

    def modify_inp(self,infile,pattern,output_name='case_try.inp'):
        """
        :param infile: 空流量的inp文件
        :param pattern: 各个上游节点24小时的流量输入，数组
        :return: void，最后生成一个新inp文件"case_try.inp"
        """
        """
        修改inp文件，最后生成新的inp文件"case_try.inp"
        """
        var = []
        tmp = ""
        for inx in range(len(pattern)):
            tmp += (str(np.around(pattern[inx], decimals=3)) + "  ")
            if (inx+1) % 24 == 0 and (inx+1) != 1:
                var.append(tmp)
                tmp = ""

        with open(infile, 'r')as inp:
            lines = inp.readlines()
            inflow_index = -1
            pattern_index = -1
            """
            找到inflows 和 pattern的插入位置
            """
            for i, v in enumerate(lines):
                if v == '[INFLOWS]\n':
                    inflow_index = i + 3  # swmm5 文件有一些注释，所以要跳过两行
                if v == '[PATTERNS]\n':
                    pattern_index = i + 4
                if inflow_index != -1 and pattern_index != -1:
                    break

            for i in range(len(self.nodes)):
                flow_info = str(self.nodes[i]) + '                FLOW             ""               FLOW     1.0      1.0      ' + str(
                    self.avg) + '      Pattern' + str(self.nodes[i]) + '\n'
                lines.insert(inflow_index, flow_info)
                inflow_index += 1

                pattern_info = 'Pattern' + str(self.nodes[i]) + '         HOURLY     ' + var[i] + '\n'
                lines.insert(pattern_index, pattern_info)
                pattern_index += 1
        """
        生成新文件
        """
        if (os.path.exists(output_name)):
            os.remove(output_name)
        with open(output_name, 'w') as output:
            output.writelines(lines)

    def aimFunc(self, pop):  # 目标函数
        Vars = pop.Phen  # 得到决策变量矩阵

        f = np.zeros(shape=(len(Vars),1))
        for i,v in enumerate(Vars):
            """
            修改inp
            """
            self.modify_inp(infile='case1.inp',pattern=v)
            """
            获取结果
            """
            try:
                st = get_result(inpfile='case_try.inp')
                if self.gauge in (13,36,57):
                    res = list(st.Results('NODE',str(self.gauge),0))
                elif self.gauge in (64):
                    res = list(st.Results('LINK',str(self.gauge),0))
            except:
                res = list(np.zeros(47))   ## swmm5包有时候会出现error 303 无法读取，如果出现这个错，就全赋值0，让这个个体淘汰掉好了

            MSE = 0
            for j in range(len(self.ObjData)):
                MSE += (self.ObjData[j]-res[j])**2
            RMSE = np.sqrt(MSE/len(self.ObjData))
            f[i] = RMSE
        pop.ObjV = f  # 把求得的目标函数值赋值给种群pop的ObjV




    # def calReferObjV(self):  # 计算全局最优解
    #     uniformPoint, ans = ea.crtup(self.M, 10000)  # 生成10000个在各目标的单位维度上均匀分布的参考点
    #     globalBestObjV = uniformPoint / 2
    #     return globalBestObjV

# if __name__ == '__main__':
#     #
#     #
#     # read_data('监测点数据.xlsx',1)
#
#     get_result('case_empty.inp')
