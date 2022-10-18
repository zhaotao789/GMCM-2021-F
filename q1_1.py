import pandas as pd
import numpy as np
import pickle
import tqdm
import swifter

f='A'
path_employees='data/Data {}-Crew.csv'.format(f)
path_flights='data/Data {}-Flight.csv'.format(f)
df_employees = pd.read_csv(path_employees).fillna(0)
df_flights = pd.read_csv(path_flights).fillna(0)

def Dptrtime(row):
    return row.DptrDate+' '+row.DptrTime
def Arrvtime(row):
    return row.ArrvDate+' '+row.ArrvTime
df_flights['Dptrtime']=df_flights.apply(Dptrtime,axis=1)
df_flights['Arrvtime']=df_flights.apply(Arrvtime,axis=1)
df_flights['index']=df_flights.index
for col in ['Dptrtime','Arrvtime']:
    df_flights[col]=pd.to_datetime(df_flights[col])
    df_flights[col+'_day'] = df_flights[col].dt.day
    df_flights[col + '_minute'] = df_flights[col].dt.minute
    df_flights[col + '_hour'] = df_flights[col].dt.hour
    df_flights[col + '_time'] = df_flights[col+'_hour']*60+df_flights[col+'_minute']
    df_flights[col+'_allTime']=(df_flights[col]-pd.to_datetime('8/11/2021 00:00:00')).map(lambda x:x.total_seconds()/60)   #距起点的时间
for col in ['Captain','FirstOfficer','Deadhead']:
    df_employees[col]=df_employees[col].apply(lambda x:True if x=='Y' else False)
df_employees['index']=df_employees.index
df_employees.columns=['number','cap_enable','fo_enable','dh_enable','base','d_cost','p_cost','index']
employees=df_employees

flights=df_flights[['Arrvtime_day','ArrvStn','Arrvtime_time','Dptrtime_day','DptrStn','Dptrtime_time','index','FltNum','Arrvtime_allTime','Dptrtime_allTime','Dptrtime','Arrvtime']]
flights.columns=['arr_date','arr_stn','arr_time','dpt_date','dpt_stn','dpt_time','index','number','Arr_all','Dpt_all','Dptrtime','Arrvtime']

min_day=flights['arr_date'].min()
min_time=flights['Dpt_all'].min()+24*60*(min_day-1)

C_dic=dict(zip(employees['index'].values,employees['number'].values))   #员工


#模型需要的参数
C=employees['index'].values.tolist()
C1=employees.loc[(employees.cap_enable==True)&(employees.fo_enable==False) ,'index'].values.tolist()
C2=employees.loc[(employees.cap_enable==True)&(employees.fo_enable==True) ,'index'].values.tolist()
C3=employees.loc[(employees.cap_enable==False)&(employees.fo_enable==True) ,'index'].values.tolist()

AP_dic=list(set(np.append(flights['arr_stn'].unique(),flights['dpt_stn'].unique())) ) #总共有多少个站点
AP_dic=dict(list(enumerate(AP_dic)))
AP=list(AP_dic.keys())
AP_f_dpt_dic =dict(flights.groupby('dpt_stn')['index'].apply(list))
AP_f_arr_dic = dict(flights.groupby('arr_stn')['index'].apply(list))
for k in AP_dic:     #修改AP_f_dpt_dic的key
    AP_f_dpt_dic.update({k:AP_f_dpt_dic.pop('{}'.format(AP_dic[k]))})
    AP_f_arr_dic.update({k: AP_f_arr_dic.pop('{}'.format(AP_dic[k]))})
AP_dic_new=dict(zip(AP_dic.values(), AP_dic.keys()))
flights['arr_stn_index']=flights['arr_stn'].map(AP_dic_new)
flights['dpt_stn_index']=flights['dpt_stn'].map(AP_dic_new)

Base = employees['base'].unique().tolist()  # 值
Base_dic_key=[]  # 键
for k in Base:
    Base_dic_key.append(employees.loc[employees['base']==k,'index'].min())
Base_dic = dict(zip(Base_dic_key, Base))  # 起点

C1_base = []
C2_base = []
C3_base = []
for key in Base_dic:
    list_=employees.loc[employees['base']==Base_dic[key],'index'].values.tolist()    #所有的人
    C1_base.append(list(set(C1).intersection(set(list_))))
    C2_base.append(list(set(C2).intersection(set(list_))))
    C3_base.append(list(set(C3).intersection(set(list_))))

F_dic=dict(zip(flights['index'].values,flights['number'].values))   #飞机
F=flights['index'].values
F_ap_dpt_dic = dict(zip(flights['index'].values,flights['dpt_stn_index'].values))
F_ap_arr_dic =dict(zip(flights['index'].values,flights['arr_stn_index'].values))
F_leave_base = []
F_arrive_base=[]
for key in Base_dic_key:
    b=employees.loc[key,'base']
    key=[k for k, v in AP_dic.items() if v == b][0] #有一层映射关系
    F_arrive_base.append(AP_f_arr_dic[key])
    F_leave_base.append(AP_f_dpt_dic[key])
nonF_leave_base = []
nonF_arrive_base = []
for i in range(len(Base_dic_key)):
    nonF_leave_base.append(list(set(F) - set(F_leave_base[i])))
    nonF_arrive_base.append(list(set(F) - set(F_arrive_base[i])))

def transp(index,F,l):
    l = list(set(F) - set(l))
    l = [[index] * len(l), l]  # 不满足条件的
    l = list(map(tuple, zip(*l)))  # 转置
    return l

def FF(flights,minCT,MinRest,Base,F):   #判断不满足条件的组合
    Index1=[]    #执勤
    Index2 = []  #
    Index3=[]
    for index1,row1 in tqdm.tqdm(flights.iterrows()):  #到达
        l=flights.loc[(flights['dpt_stn']==row1.arr_stn) & (flights['Dpt_all']-row1.Arr_all>=minCT )]['index'].tolist()
        Index1=Index1+transp(index1,F,l)
        l = flights.loc[(flights['dpt_stn'] == row1.arr_stn) & (flights['Dpt_all'] - row1.Arr_all > MinRest) & (flights['dpt_date']>row1.dpt_date)]['index'].tolist()
        Index2=Index2+transp(index1, F, l)
        l = flights.loc[(flights['dpt_stn'] == row1.arr_stn) & (flights['dpt_date'] -row1.dpt_date>2) &(row1.arr_stn in Base)]['index'].tolist()
        Index3=Index3+transp(index1, F, l)
    return Index1,Index2,Index3

minCT=40    #最小时间为40分组
MinRest=660

FF,FF1,FF2 =FF(flights,minCT,MinRest,Base,flights['index'].tolist())   #找到下一个站

# 按天划分，转换成多个小任务
FD=flights.groupby(['dpt_date'])['index'].apply(list).to_dict()

arrivedate=dict(zip(flights['index'].values,flights['arr_date'].values))
leavedate=dict(zip(flights['index'].values,flights['dpt_date'].values))
# leavetimestr=dict(zip(flights['index'].values,flights['Dptrtime'].values))
# arrivetimestr=dict(zip(flights['index'].values,flights['Arrvtime'].values))

Dates=flights['arr_date'].unique().tolist()

DCost=dict(zip(flights['index'].values,employees['d_cost'].values))
PCost=dict(zip(flights['index'].values,employees['p_cost'].values))


import gurobipy as gp
from gurobipy import *

m=gp.Model('m1')

z=m.addVars(F,vtype=gp.GRB.BINARY,name='z')
x_ikdh=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_dh')
x_ikfo=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_fo')
x_ikcap=m.addVars(F,C,vtype=gp.GRB.BINARY,name='x_cap')

r_iksta=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_iksta')
r_jkfin=m.addVars(F,C,vtype=gp.GRB.BINARY,name='r_jkfin')

y_ijk=m.addVars(F,F,C,vtype=gp.GRB.BINARY,name='y_ijk')


m.ModelSense=GRB.MINIMIZE

m.setObjective(-z.sum())
# m.setObjective(x_ikdh.sum())
# m.setObjective(gp.quicksum(x_ikfo[i,k] for i in data_loader_a.F for k in data_loader_a.C2))

#m.setObjectiveN(-z.sum(),index = 0,weight =0.8)
#m.setObjectiveN(x_ikdh.sum(),index=1,weight=0.2)
#m.setObjectiveN(gp.quicksum(x_ikfo[i,k] for i in data_loader_a.F for k in data_loader_a.C2),index=2,weight=0.05)

#########################################################
F = F       #航班总数
C = C        #工作人员总数
C1 = C1      #只能当正机长
C2 = C2
C3 = C3     #只能当副机长
FF = FF     #不能配对的组合
nonF_arrive_base = nonF_arrive_base    #不能作为到达的飞机
nonF_leave_base = nonF_leave_base     #不能作为出发的飞机
F_leave_base = F_leave_base          #作为到达的飞机
F_arrive_base = F_arrive_base        #作为到达的飞机
#####################################################



M=5
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
if f=='B':
    m.addConstrs(r_jkfin[j, k] == 0 for j in nonF_arrive_base[1] for k in C)
    m.addConstrs(r_iksta[i, k] == 0 for i in nonF_leave_base[1] for k in C)

m.addConstrs(gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] )<=1  for k in C)
m.addConstrs(gp.quicksum(r_jkfin[j,k] for j in F_arrive_base[0] )-gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] ) == 0 for k in C)
if f=='B':
    m.addConstrs(gp.quicksum(r_iksta[i, k] for i in F_leave_base[0]) <= 1 for k in C)
    m.addConstrs(gp.quicksum(r_jkfin[j, k] for j in F_arrive_base[0]) - gp.quicksum(r_iksta[i, k] for i in F_leave_base[0]) == 0        for k in C)

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
m.setObjective(x_ikdh.sum())
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
if f=='B':
    m.addConstrs(r_jkfin[j, k] == 0 for j in nonF_arrive_base[0] for k in C)
    m.addConstrs(r_iksta[i, k] == 0 for i in nonF_leave_base[0] for k in C)

m.addConstrs(gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] )<=1  for k in C)
m.addConstrs(gp.quicksum(r_jkfin[j,k] for j in F_arrive_base[0] )-gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] ) == 0 for k in C)
if f=='B':
    m.addConstrs(gp.quicksum(r_iksta[i, k] for i in F_leave_base[0]) <= 1 for k in C)
    m.addConstrs(
        gp.quicksum(r_jkfin[j, k] for j in F_arrive_base[0]) - gp.quicksum(r_iksta[i, k] for i in F_leave_base[0]) == 0
        for k in C)

#第一问中航班对应周期的约束
m.addConstrs(1-(y_ijk.sum(i,'*',k)+r_iksta[i,k]+r_jkfin[i,k])<=M*(1-(x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k])) for i in F for k in C)
m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k]-(y_ijk.sum('*',i,k)+r_iksta[i,k]) == 0 for i in F for k in C)

m.addConstrs(y_ijk.sum(i,'*',k)+r_jkfin[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)
m.addConstrs(y_ijk.sum('*',i,k)+r_iksta[i,k] <= x_ikcap[i,k]+x_ikfo[i,k]+x_ikdh[i,k]  for i in F for k in C)

#多目标优化
m.addConstr(z.sum()==206)
# m.addConstr(x_ikdh.sum()==8)

m.update()
m.optimize()


## 优化目标⑦


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
if f=='B':
    m.addConstrs(r_jkfin[j, k] == 0 for j in nonF_arrive_base[0] for k in C)
    m.addConstrs(r_iksta[i, k] == 0 for i in nonF_leave_base[0] for k in C)

m.addConstrs(gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] )<=1  for k in C)
m.addConstrs(gp.quicksum(r_jkfin[j,k] for j in F_arrive_base[0] )-gp.quicksum(r_iksta[i,k] for i in F_leave_base[0] ) == 0 for k in C)
if f=='B':
    m.addConstrs(gp.quicksum(r_iksta[i, k] for i in F_leave_base[0]) <= 1 for k in C)
    m.addConstrs(
        gp.quicksum(r_jkfin[j, k] for j in F_arrive_base[0]) - gp.quicksum(r_iksta[i, k] for i in F_leave_base[0]) == 0
        for k in C)

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


results_dic = {'em_no':[], 'fl_no':[], 'cls':[]}
for i in F:
    for k in C:
        if x_ikcap[i,k].x > 0.9:
            results_dic['em_no'].append(k)
            results_dic['fl_no'].append(i)
            results_dic['cls'].append(1)
        if x_ikfo[i,k].x > 0.9:
            results_dic['em_no'].append(k)
            results_dic['fl_no'].append(i)
            results_dic['cls'].append(2)
        if x_ikdh[i,k].x > 0.9:
            results_dic['em_no'].append(k)
            results_dic['fl_no'].append(i)
            results_dic['cls'].append(3)

#%%

pd.DataFrame(results_dic).to_csv('results.csv', index=0)
