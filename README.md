# a-calibration-of-sewer-networks-using-geatpy
环境流体力学的作业，注释很详细。主要用了geatpy这个启发式算法库，以及一些常见的如numpy pandas os 等包

# 尝试一
最初拿到这个题目的时候的想法很简单，用遗传算法对每一个节点的24小时pattern进行寻优，一共64个节点，这样就有64*24=1536个待定参数，为了解决参数过于庞大的问题，又得益于排水管网是树状网且正常情况下流向单一，所以用监测点将管网进行分割。

这里写了一个脚本可以自动识别上下游管段，也就是 ```my_split.py``` 就是在某一点随意设置一个流量，看下游哪些节点有流量经过，就可以识别这个点的下游管段，通过这个方法把整个管网设成了4段。虽然这个管网比较简单，看不出优势，但是如果是一个非常复杂的管网，这样自动化的脚本可以节省非常多的精力。

![ 图一 自动识别监测点上游示意图](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/1.png)

按照监测点将管网分割成四段之后，一段一段进行优化，这样每一步大概有20个左右的节点，寻优参数减少到了20*24=480个待定参数，这样通过遗传算法是有解决的可能的。

每个节点24小时的节点流量编入染色体，适应度函数就是RMSE均方根误差：

其中：
* ——t为时间步
* ——n为时间步的个数，由于题目条件给了00:30到23:30共47个数据，因此n=47
* ——v<sub>jt</sub>为t时刻的监测值，v<sub>mt</sub>为t时刻的模拟值
为了最终结果符合工程实际，设置了一些惩罚项：

(1)当夜间（22：00-6：00）的平均流量大于白天的平均流量，这是不符合用水规律的，适应度函数后加一个惩罚值；

(2)当各节点日平均流量的方差σ与均值averge的比值超过0.5时，说明节点流量分布非常不均匀，可能会出现离监测点近的地方很大流量，远的地方几乎没有流量，这是不合符工程实际的，因为这时候也加了一个惩罚项，即：

* fitness = fitness-0.8σ                                     (2)

经过一些尝试之后，选择种群数量为120，迭代100代，最后得到的结果如图：

![ 图二 第一次尝试](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/2.png)
![ 图三 第二次尝试](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/3.png)

由于计算时间实在过长，算了J13和J36两段就没再算了。

这样求解有两个问题：
1. 前几代收敛不是特别明显，且误差巨大，在20代左右的时候收敛十分迅猛，说明前期种群的质量实在是太差了（因为是完全随机的种群），颇有点大海捞针的感觉白白浪费了很多机时；
2. 40代之后，收敛又不很明显了，甚至最优值还有波动（没有设置精英保留策略），最好的RMSE也就是实际平均值的2%左右了。

# 尝试二
针对尝试一的问题，这是因为初始条件太随意了，跟隔壁组讨论了一下之后，有一些解决方法：
1. 由于给了一个流量监测值，三个水位监测值，想要充分利用条件必须得从另外三个节点的水位推出流量，这一点可以通过无压圆管流公式得出：

![ 图四 无压圆管流公式](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/4.jpg)
![](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/formula2.JPG)

其中：
* ——θ是充满角
* —— h是水位高度
* —— d是管道直径
* —— i 是管道坡度
* —— n 是管道糙率

经过计算后，水位曲线就换算成了流量曲线，最终各监测值如下图所示：

![ 图四 修正初始条件后的结果](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/5.png)

2. 分析四个监测点的时间曲线：

把各监测点流量通过z-score标准化进行压缩：

X_normalized=(X-μ)/σ                                    (5)

下图展现了四个监测点的时间曲线对比：

![ 图五 四个监测点的时间曲线对比](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/6.png)
 
在inp文件的初始化上，依然是每一个节点一个timeseries，不同的是这次用的不是随机初始条件，而是用四个监测点的时间曲线来给每一个节点赋初值。

3. 各个节点的流量分配也不应该是随机的，这里根据比流量来进行分配：算出一个区域的总管长，然后根据管长计算比流量，再平均分给两端的节点。最终把每个节点分配到的比例当作Scale Factor输入到inp文件里，把监测点的流量序列当作Time Series输入到inp文件里。

![ 图六 EPA SWMM GUI中输入Time Series](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/7.png)

4. 由于一个区域内不可能每个节点都是一样的时间曲线，各个节点之间性质不一样（居民楼、医院、工厂等等），居民楼之间也不可能是一模一样的曲线，因此采用遗传算法，对每一个节点的time series进行一些扰动，并寻找这种“扰动”的最优组合。

目标函数同式（1），惩罚函数同式（2）。

# 结果展示
 
![ 图六 EPA SWMM GUI中输入Time Series](https://github.com/JohnKeating1997/a-calibration-of-sewer-networks-using-geatpy/blob/main/img/8.png)

最终：
J36节点处液位RMSE为0.0016，是平均监测值的0.98%；

J13 节点处液位RMSE为0.0047，是平均监测值的3.93%；

J57 节点处液位RMSE 为0.0022，是平均监测值的2.48%；

P64 管道流量RMSE为4.804，是平均监测值的4.66%；
