import numpy as np
from swmm5.swmm5tools import SWMM5Simulation

def run_simulation1(con_mat,inpfile,meters_pos):
    """
    calculate the Connectivity Matrix
    :param con_mat:
    :param inpfile:
    :param meters_pos:
    :return: modified con_mat
    """

    st1 = SWMM5Simulation(inpfile)
    for i in range(1,65):
        # if i in meters_pos:
        #     continue
        if any(list(st1.Results('NODE', str(i), 4))):
            if any(list(st1.Results('NODE', '13', 4))):
                con_mat[0,i-1] = 1
            if any(list(st1.Results('NODE', '36', 4))):
                con_mat[1,i-1] = 1
            if any(list(st1.Results('NODE', '57', 4))):
                con_mat[2,i-1] = 1
            if any(list(st1.Results('NODE', '14', 4))):
                con_mat[3, i-1] = 1
    return con_mat

def run_simulation2(inpfile):
    """
    calculate the flow/water level meters
    :param inpfile:
    :return:
    """
    st1 = SWMM5Simulation(inpfile)
    downstream_arr = np.zeros(64)
    for i in range(1, 65):
        if any(list(st1.Results('NODE', str(i), 4))):
            downstream_arr[i-1] = 1
    return downstream_arr

def modify_inp(infile,node_index):
    """
    :param infile:
    :return:
    """
    with open(infile,'r')as inp :
        lines = inp.readlines()

        for i,v in enumerate(lines):
            if v== '[INFLOWS]\n':
                index = i+3  # swmm5 文件有一些注释，所以要跳过两行
                break
        info =str(node_index) + '   FLOW             ""               FLOW     1.0      1.0      25 \n'
        lines.insert(index,info)
    with open('case_modified.inp','w') as output:
        output.writelines(lines)

if __name__ == "__main__":
    con_mat = np.zeros((4,64))
    meters_pos = (13,14,36,57)
    downstream_arr = []
    for i in range(1,65):
        modify_inp('case_empty.inp', i)
        if i in meters_pos:
            downstream_arr.append(run_simulation2('case_modified.inp'))
        con_mat = run_simulation1(con_mat,'case_modified.inp',meters_pos)

    for i,v in enumerate(downstream_arr):
        con_mat[i] += v
        for inx,val in enumerate(con_mat[i]):
            if val == 2:
                con_mat[i,inx] = 0
    print(con_mat)
