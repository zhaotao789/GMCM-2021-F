from utils.preprocessing import DataLoader
from matplotlib import pyplot as plt
import gc
import pickle
data_loader_a = DataLoader('data/Data A-Crew.csv', 'data/Data A-Flight.csv')
data_loader_a.dump_data()

# #读取对象
# data_loader_a =None
# with open("data_loader_a.pkl",'rb') as file:
#    data_loader_a  = pickle.loads(file.read())

F=data_loader_a.F
C=data_loader_a.C
C1=data_loader_a.C1
C2=data_loader_a.C2
C3=data_loader_a.C3
FF=data_loader_a.FF
nonF_arrive_base=data_loader_a.nonF_arrive_base
nonF_leave_base=data_loader_a.nonF_leave_base
F_leave_base=data_loader_a.F_leave_base
F_arrive_base=data_loader_a.F_arrive_base

# #保存对象
# output = open("data_loader_a.pkl", 'wb')
# str = pickle.dumps(data_loader_a)
# output.write(str)
# output.close()


#模型建立与求解
import gurobipy as gp
from gurobipy import *

## 优化目标①

m=gp.Model('m1')

z=m.addVars(F,vtype=gp.GRB.BINARY,name='z')   #航班是否起飞
x_ikdh=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_dh')    #人员k是否执行航段i乘机任务
x_ikfo=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_fo')   #人员k是否作为副机长执行航段i
x_ikcap=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_cap')   #人员k是否作为正机长执行航段i

r_iksta=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_iksta')   #人员k是否将航段i作为起点
r_jkfin=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_jkfin')   #人员k是否将航段i作为终点

y_ijk=m.addVars(F,F,C,vtype=gp.GRB.BINARY,name='y_ijk')   #两航段之间是否连接   ，和人员有关


m.ModelSense=GRB.MINIMIZE

m.setObjective(-z.sum())
# m.setObjective(x_ikdh.sum())
# m.setObjective(gp.quicksum(x_ikfo[i,k] for i in data_loader_a.F for k in data_loader_a.C2))

#m.setObjectiveN(-z.sum(),index = 0,weight =0.8)
#m.setObjectiveN(x_ikdh.sum(),index=1,weight=0.2)
#m.setObjectiveN(gp.quicksum(x_ikfo[i,k] for i in data_loader_a.F for k in data_loader_a.C2),index=2,weight=0.05)

#gurobipy的约束条件为bool约束条件
M=10000      #二分类是在0-1之间搜索
#对X的约束
m.addConstrs(x_ikfo[i,k]==0 for i in F for k in C1 )    #副机长无法执行正机长的任务
m.addConstrs(x_ikcap[i,k]==0 for i in F for k in C3 )   ##正机长无法执行副机长的任务
m.addConstrs(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]<=1 for i in F for k in C)    #正机长、副机长和乘机任务，只能执行一个

#对Z的约束
m.addConstrs(gp.quicksum(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for k in C)<=M*(z[i]) for i in F)     #此处有问题######    一架飞机最多坐5个
m.addConstrs(x_ikcap.sum(i,'*')== z[i] for i in F )   #每一架飞机最多有一个正机长
m.addConstrs(x_ikfo.sum(i,'*')== z[i] for i in F )    #每一架飞机最多有一个副机长
#m.addConstrs(M*z[j]>=gp.quicksum(x_ikcap[j,k]+x_ikfo[j,k]+x_ikdh[j,k] for k in C) for j in F)

#对Y的约束
m.addConstrs(y_ijk[i,j,k]==0 for i,j in FF for k in C)    #两段是否连通
#m.addConstrs(gp.quicksum(y_ijk[i,j,k] for j in F)<=x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for i in F for k in C)
#m.addConstrs(gp.quicksum(y_ijk[j,i,k] for j in F)<=x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for i in F for k in C)

#对roaster周期的约束
m.addConstrs(r_jkfin[j,k]== 0 for j in nonF_arrive_base[0] for k in C)   #非终点航班
m.addConstrs(r_iksta[i,k]== 0 for i in nonF_leave_base[0] for k in C)
#x_ikcap.sum(i,'*')== z[i] for i in F    即：针对矩阵x_ikcap，对每一个i，求和其C维     *表示所有
#等价于gp.quicksum(x_ikcap[i,j] for j in C)

#quicksum为gurobi推荐的sum方法
m.addConstrs(gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] )<=1  for k in C)   #只能有一个起点
m.addConstrs(gp.quicksum(r_jkfin[j,k] for j in F_arrive_base[0] )-gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] ) == 0 for k in C)    #起点和终点数相同

#第一问中航班对应周期的约束
m.addConstrs(1-(y_ijk.sum(i,'*',k)+r_iksta[i,k]+r_jkfin[i,k])<=M*(1-(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k])) for i in F for k in C)
m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k]-(y_ijk.sum('*',i,k)+r_iksta[i,k]) == 0 for i in F for k in C)

m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)
m.addConstrs(y_ijk.sum('*',i,k)+r_iksta[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)

#多目标优化
# m.addConstr(z.sum()==206)
# m.addConstr(x_ikdh.sum()==8)

m.update()
m.optimize()


## 优化目标④


m=gp.Model('m1')

z=m.addVars(F,vtype=gp.GRB.BINARY,name='z')
x_ikdh=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_dh')
x_ikfo=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_fo')
x_ikcap=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_cap')

r_iksta=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_iksta')
r_jkfin=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_jkfin')

y_ijk=m.addVars(F,F,C,vtype=gp.GRB.BINARY,name='y_ijk')


m.ModelSense=GRB.MINIMIZE

# m.setObjective(-z.sum())
m.setObjective(x_ikdh.sum())    #尽可能少的总体乘机次数
# m.setObjective(gp.quicksum(x_ikfo[i,k] for i in data_loader_a.F for k in data_loader_a.C2))

#m.setObjectiveN(-z.sum(),index = 0,weight =0.8)
#m.setObjectiveN(x_ikdh.sum(),index=1,weight=0.2)
#m.setObjectiveN(gp.quicksum(x_ikfo[i,k] for i in data_loader_a.F for k in data_loader_a.C2),index=2,weight=0.05)


M=10000
#对X的约束
m.addConstrs(x_ikfo[i,k]==0 for i in F for k in C1 )
m.addConstrs(x_ikcap[i,k]==0 for i in F for k in C3 )
m.addConstrs(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]<=1 for i in F for k in C)

#对Z的约束
m.addConstrs(gp.quicksum(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for k in C)<=M*(z[i]) for i in F)
m.addConstrs(x_ikcap.sum(i,'*')== z[i] for i in F )
m.addConstrs(x_ikfo.sum(i,'*')== z[i] for i in F )
m.addConstrs(M*z[j]>=gp.quicksum(x_ikcap[j,k]+x_ikfo[j,k]+x_ikdh[j,k] for k in C) for j in F)

#对Y的约束
m.addConstrs(y_ijk[i,j,k]==0 for i,j in FF for k in C)
#m.addConstrs(gp.quicksum(y_ijk[i,j,k] for j in F)<=x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for i in F for k in C)
#m.addConstrs(gp.quicksum(y_ijk[j,i,k] for j in F)<=x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for i in F for k in C)

#对roaster周期的约束
m.addConstrs(r_jkfin[j,k]== 0 for j in nonF_arrive_base[0] for k in C)
m.addConstrs(r_iksta[i,k]== 0 for i in nonF_leave_base[0] for k in C)

m.addConstrs(gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] )<=1  for k in C)
m.addConstrs(gp.quicksum(r_jkfin[j,k] for j in F_arrive_base[0] )-gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] ) == 0 for k in C)

#第一问中航班对应周期的约束
m.addConstrs(1-(y_ijk.sum(i,'*',k)+r_iksta[i,k]+r_jkfin[i,k])<=M*(1-(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k])) for i in F for k in C)
m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k]-(y_ijk.sum('*',i,k)+r_iksta[i,k]) == 0 for i in F for k in C)

m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)
m.addConstrs(y_ijk.sum('*',i,k)+r_iksta[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)

#多目标优化
m.addConstr(z.sum()==206)     #将上一步的目标变为约束
# m.addConstr(x_ikdh.sum()==8)

m.update()
m.optimize()


# 优化目标⑦


m=gp.Model('m1')

z=m.addVars(F,vtype=gp.GRB.BINARY,name='z')
x_ikdh=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_dh')
x_ikfo=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_fo')
x_ikcap=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_cap')

r_iksta=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_iksta')
r_jkfin=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_jkfin')

y_ijk=m.addVars(F,F,C,vtype=gp.GRB.BINARY,name='y_ijk')


m.ModelSense=GRB.MINIMIZE

# m.setObjective(-z.sum())
# m.setObjective(x_ikdh.sum())
m.setObjective(gp.quicksum(x_ikfo[i,k] for i in F for k in C2))

#m.setObjectiveN(-z.sum(),index = 0,weight =0.8)
#m.setObjectiveN(x_ikdh.sum(),index=1,weight=0.2)
#m.setObjectiveN(gp.quicksum(x_ikfo[i,k] for i in data_loader_a.F for k in data_loader_a.C2),index=2,weight=0.05)


M=10000
#对X的约束
m.addConstrs(x_ikfo[i,k]==0 for i in F for k in C1 )
m.addConstrs(x_ikcap[i,k]==0 for i in F for k in C3 )
m.addConstrs(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]<=1 for i in F for k in C)

#对Z的约束
m.addConstrs(gp.quicksum(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for k in C)<=M*(z[i]) for i in F)
m.addConstrs(x_ikcap.sum(i,'*')== z[i] for i in F )
m.addConstrs(x_ikfo.sum(i,'*')== z[i] for i in F )
m.addConstrs(M*z[j]>=gp.quicksum(x_ikcap[j,k]+x_ikfo[j,k]+x_ikdh[j,k] for k in C) for j in F)

#对Y的约束
m.addConstrs(y_ijk[i,j,k]==0 for i,j in FF for k in C)
#m.addConstrs(gp.quicksum(y_ijk[i,j,k] for j in F)<=x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for i in F for k in C)
#m.addConstrs(gp.quicksum(y_ijk[j,i,k] for j in F)<=x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k] for i in F for k in C)

#对roaster周期的约束
m.addConstrs(r_jkfin[j,k]== 0 for j in nonF_arrive_base[0] for k in C)
m.addConstrs(r_iksta[i,k]== 0 for i in nonF_leave_base[0] for k in C)

m.addConstrs(gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] )<=1  for k in C)
m.addConstrs(gp.quicksum(r_jkfin[j,k] for j in F_arrive_base[0] )-gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] ) == 0 for k in C)

#第一问中航班对应周期的约束
m.addConstrs(1-(y_ijk.sum(i,'*',k)+r_iksta[i,k]+r_jkfin[i,k])<=M*(1-(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k])) for i in F for k in C)
m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k]-(y_ijk.sum('*',i,k)+r_iksta[i,k]) == 0 for i in F for k in C)

m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)
m.addConstrs(y_ijk.sum('*',i,k)+r_iksta[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)

#多目标优化
m.addConstr(z.sum()==206)
m.addConstr(x_ikdh.sum()==8)

m.update()
m.optimize()


# 结果展示与导出

import pandas as pd

results_dic = {'em_no':[], 'fl_no':[], 'cls':[]}
for i in F:
    for k in C:
        if x_ikcap[i,k].x > 0.9:   #正机长矩阵
            results_dic['em_no'].append(k)
            results_dic['fl_no'].append(i)
            results_dic['cls'].append(1)
        if x_ikfo[i,k].x > 0.9:   #副机长矩阵
            results_dic['em_no'].append(k)
            results_dic['fl_no'].append(i)
            results_dic['cls'].append(2)
        if x_ikdh[i,k].x > 0.9:   #乘机矩阵
            results_dic['em_no'].append(k)
            results_dic['fl_no'].append(i)
            results_dic['cls'].append(3)

#%%

df = pd.DataFrame(results_dic)
df

#%%

from ResultViewer import RViewer

#%%

rv = RViewer(data_loader_a, data_cls='a')
rv.load_results_from_df(df)

#%%

rv.draw_ef_gantt(save="results/q1_a.png")

#%%

df_a = rv.get_results_df_a()

#%%

df_a

#%%

df_a.to_csv('results/q1_a_UnconveredFlights.csv', index=0)

#%%

df_b = rv.get_results_df_b()
df_b

#%%

df_b.to_csv('results/q1_a_CrewRosters.csv', index=0)
