  #Python 代码
# DATA_A
###########################################
NUM_D = 15
NUM_Fli = 206
NUM_P = 7
NUM_BOTH = 6 # 全都能干
NUM_CAP = 5 # 只能当几机长
NUM_FIRST = 10 # 只能当助手
LowerLimit_Combine = 40
UpperLimit_Combine = 1e5
JIDI = [1]
MaxBlk=600
MinRest =660
MaxDP =720
###########################################
769
# DATA_B
###########################################
# NUM_D = 31
# NUM_Fli = 13954
# NUM_P = 39
# NUM_BOTH = 124 # 全都能干
# NUM_CAP = 87 # 只能当几机长
# NUM_FIRST = 254 # 只能当助手
# LowerLimit_Combine = 40
# UpperLimit_Combine = 1e5
# JIDI = [1,2]
# MaxBlk=600
# MinRest =660
# MaxDP =720
###########################################

#from Parameters import *

class Flight:
    def __init__(self, id_in, t_d_in, t_a_in, p_d_in, p_a_in, d_d_in):
        self.id = id_in
        self.cap = 1
        self.fir = 1
        self.t_d = t_d_in
        self.t_a = t_a_in
        self.p_d = p_d_in
        self.p_a = p_a_in
        self.d_d = d_d_in

    def __lt__(self, other):
        return self.t_d < other.t_d

    def __eq__(self, other):
        return self.p_d == other.p_d and self.p_a == self.p_a

class Group_Flight:
    def __init__(self, f: Flight):
        self.flights = [f]
        self.t_d = f.t_d
        self.t_a = f.t_a
        self.p_d = f.p_d
        self.p_a = f.p_a
        self.cap = 1
        self.first = 1
        self.d_d = f.d_d
        self.type = -1 # 1 主机长 3 副机长 2 乘机
        self.time_fly = f.t_a - f.t_d

    def add_flight(self, f: Flight):
        self.flights.append(f)
        self.t_a = f.t_a
        self.p_a = f.p_a
        self.time_fly = self.time_fly + f.t_a - f.t_d

    def add_group(self, g):
        for f in g.flights:
            self.add_flight(f)

    def add_group_first(self, g):
        for f in reversed(g.flights):
            self.add_flight_first(f)

    def add_flight_first(self, f: Flight):
        self.flights.insert(0,f)
        self.t_d = f.t_d
        self.p_d = f.p_d
        self.time_fly = self.time_fly + f.t_a - f.t_d

    def set_type(self, t):
        self.type = t

    def __lt__(self, other):
        return self.t_d < other.t_d

    def __eq__(self, other):
        return self.p_d == other.p_d and self.p_a == self.p_a

class Pilot:
    def __init__(self, EmpNo, DutyCostPerHour, ParingCostPerHour, TYPE, jidi):
        self.EmpNo = EmpNo
        self.DutyCostPerHour = DutyCostPerHour
        self.ParingCostPerHour = ParingCostPerHour
        self.TYPE = TYPE
        self.jidi = jidi
        self.flights = []
        self.group = None
        self.groups = {}
        self.duty = [False] * (NUM_D + 1)
        self.p_a_d = [jidi] * (NUM_D + 1)
        self.p_d_d = [jidi] * (NUM_D + 1)
        self.t_a_d = [-1] * (NUM_D + 1)
        self.t_d_d = [-1] * (NUM_D + 1)
        self.zhiqinChengben = [0] * (NUM_D + 1)
        self.time_fly = [0] * (NUM_D + 1)
        self.time_duty = [0] * (NUM_D + 1)

        for d in range(1, NUM_D + 1):
            self.groups[d] = []

    def assign_group(self, g: Group_Flight):
        self.group = g
        self.groups[g.d_d].append(g)
        self.duty[g.d_d] = True
        self.p_a_d[g.d_d] = g.p_a
        self.t_a_d[g.d_d] = g.t_a
        self.p_d_d[g.d_d] = g.p_d
        self.t_d_d[g.d_d] = g.t_d
        self.zhiqinChengben[g.d_d] = self.DutyCostPerHour * (self.t_a_d[g.d_d] - self.t_d_d[g.d_d])
        self.time_duty[g.d_d] = (self.t_a_d[g.d_d] - self.t_d_d[g.d_d])
        self.time_fly[g.d_d] = g.time_fly

    def add_group(self, g: Group_Flight):
        if len(self.groups[g.d_d]) == 0:
            self.assign_group(g)
            return
        self.groups[g.d_d].append(g)
        self.p_a_d[g.d_d] = g.p_a
        self.t_a_d[g.d_d] = g.t_a
        self.time_duty[g.d_d] = (self.t_a_d[g.d_d] - self.t_d_d[g.d_d])
        self.zhiqinChengben[g.d_d] = self.DutyCostPerHour * self.time_duty[g.d_d]
        self.time_fly[g.d_d] = self.time_fly[g.d_d] + g.time_fly

    def add_group_first(self, g: Group_Flight):
        if len(self.groups[g.d_d]) == 0:
            self.assign_group(g)
            return
        self.groups[g.d_d].insert(0, g)
        self.p_d_d[g.d_d] = g.p_d
        self.t_d_d[g.d_d] = g.t_d
        self.time_duty[g.d_d] = (self.t_a_d[g.d_d] - self.t_d_d[g.d_d])
        self.zhiqinChengben[g.d_d] = self.DutyCostPerHour * self.time_duty[g.d_d]
        self.time_fly[g.d_d] = self.time_fly[g.d_d] + g.time_fly

import pandas as pd
import numpy as np 
from Flight import * 
#from Parameters import *
import copy 
import time 


class Greedy: 
    def __init__(self):
        self.data = None
        self.map_p2f = {} # 机场到航班（起飞相同）的映射
        for i in range(1, NUM_P + 1):
            self.map_p2f[i] = set()
        self.map_t2f = {}
        self.pilots = {}
        self.pilots[1] = []
        self.pilots[2] = []
        self.pilots[3] = []
        self.chengji = 0
        self.zhiqinChengben = 0
        self.read()
        self.map_t2f[0] = []
        for i in range(1, NUM_D + 1):
            self.map_t2f[i] = []
        for i, r in self.data.iterrows():
            self.map_t2f[r["DptrD"]].append(Flight(i, r["DptrT_min"], r["ArrvT_min"], r["DptrP"], r["ArrvP"], r["DptrD"]))

        self.map_t2g = None

    def read(self):
        self.data = pd.read_csv("data/Data A-Flight.csv", dtype={"ArrvD": int, "ArrvT": int,"DptrD": int, "DptrT": int, "ArrvP": int, "DptrP": int,"FlightT": int, "DptrT_min": int, "ArrvT_min": int})
        for i, r in self.data.iterrows():
            self.map_p2f[r["DptrP"]].add(i)

        self.data_pilot = pd.read_csv("Data_A_Pilot.csv", dtype={"DutyCostPerHour": int, "ParingCostPerHour": int,    "TYPE": int, "jidi": int, "EmpNo": str})
        for i, r in self.data_pilot.iterrows():
            self.pilots[r["TYPE"]].append(Pilot(r["EmpNo"], r["DutyCostPerHour"], r["ParingCostPerHour"],        r["TYPE"], r["jidi"]))

        # print(self.data)

    def run(self):
        ordered_map_p2f = {}
        for i in range(1, NUM_P + 1):
            ordered_map_p2f[i] = list()
        for i, r in self.data.iterrows():
            self.map_p2f[r["DptrP"]].add(Flight(i, r["DptrT_min"]))
        for i in range(1, NUM_P + 1):
            ordered_map_p2f[i].sort()
        num_allocated_per = 0
        while num_allocated_per < NUM_Fli:
            pass

    def make_group(self):
        map_t2f_temp = copy.deepcopy(self.map_t2f)
        map_t2g = {}
        map_t2g[0] = []
        for d in range(1, NUM_D + 1):
            map_t2g[d] = []
            flag_group = True
            map_t2f_temp[d].sort()
            while flag_group:
                flag_group = False
                temp_f1 = None
                temp_f2 = None
                for f1 in range(len(map_t2f_temp[d])):
                    if map_t2f_temp[d][f1].p_d not in JIDI:
                        continue
                    for f2 in range(f1 + 1, len(map_t2f_temp[d])):
                        if (map_t2f_temp[d][f1].p_d == map_t2f_temp[d][f2].p_a
                            and map_t2f_temp[d][f1].p_a == map_t2f_temp[d][f2].p_d
                            and (map_t2f_temp[d][f2].t_d - map_t2f_temp[d][f1].t_a) > UpperLimit_Combine):
                            print("检查 2")
                        if (map_t2f_temp[d][f1].p_d == map_t2f_temp[d][f2].p_a
                            and map_t2f_temp[d][f1].p_a == map_t2f_temp[d][f2].p_d
                            and (map_t2f_temp[d][f2].t_d - map_t2f_temp[d][f1].t_a) >= LowerLimit_Combine
                            and (map_t2f_temp[d][f2].t_d - map_t2f_temp[d][f1].t_a) <= UpperLimit_Combine):
                            g = Group_Flight(map_t2f_temp[d][f1])
                            g.add_flight(map_t2f_temp[d][f2])
                            map_t2g[d].append(g)
                            if map_t2f_temp[d][f1].p_d not in JIDI:
                                print("检查 1")
                            flag_group = True
                            temp_f1 = f1
                            temp_f2 = f2
                            break
                    if flag_group:
                        break
                if flag_group:
                    del map_t2f_temp[d][temp_f2]
                    del map_t2f_temp[d][temp_f1]

        for d in range(1, NUM_D + 1):
            for f1 in range(len(map_t2f_temp[d])):
                map_t2g[d].append(Group_Flight(map_t2f_temp[d][f1]))

        self.map_t2g = map_t2g
        return map_t2g

    def coombine_group(self):
        for d in range(1, NUM_D + 1):
            flag_com = True # 是否还有可以合并的
            self.map_t2g[d].sort()
            while flag_com:
                flag_com = False
                temp_g1 = None
                temp_g2 = None
                for g1 in range(len(self.map_t2g[d])):
                    for g2 in range(g1 + 1, len(self.map_t2g[d])):
                        if (self.map_t2g[d][g1].p_d == self.map_t2g[d][g2].p_a
                            and self.map_t2g[d][g1].p_a == self.map_t2g[d][g2].p_d
                            and (self.map_t2g[d][g2].t_d - self.map_t2g[d][g1].t_a) > UpperLimit_Combine):
                                # 由于连接时间过长而没有连接的 group
                            print("检查 3")
                        if (self.map_t2g[d][g1].p_d == self.map_t2g[d][g2].p_a
                            and self.map_t2g[d][g1].p_a == self.map_t2g[d][g2].p_d
                            and (self.map_t2g[d][g2].t_d - self.map_t2g[d][g1].t_a) >= LowerLimit_Combine
                            and (self.map_t2g[d][g2].t_d - self.map_t2g[d][g1].t_a) <= UpperLimit_Combine):
                            self.map_t2g[d][g1].add_group(self.map_t2g[d][g2])
                            temp_g2 = g2
                            flag_com = True
                            break
                    if flag_com:
                        break
                if flag_com:
                    del self.map_t2g[d][temp_g2]

            for g in range(len(self.map_t2g[d])):
                if self.map_t2g[d][g].p_a not in JIDI:
                    print("检查 4")

    def allocate_pilot_zhiqin(self):
        self.chengji = 0
        for d in range(1, NUM_D + 1):
            for g in self.map_t2g[d]:
                if (g.p_d in JIDI):
                    flag_1 = False # 正机长是否分配成功
                    flag_3 = False # 副机长是否分配成功
                    for p in self.pilots[1]:
                        if (not p.duty[d]) and (not p.duty[d - 1]):
                            p.assign_group(g)
                            flag_1 = True
                    for p in self.pilots[3]:
                        if (not p.duty[d]) and (not p.duty[d - 1]):
                            p.assign_group(g)
                            flag_3 = True
                    if not flag_1:
                        for p in self.pilots[2]:
                            if (not p.duty[d]) and (not p.duty[d - 1]):
                                p.assign_group(g)
                                flag_1 = True
                    if not flag_3:
                        for p in self.pilots[2]:
                            if (not p.duty[d]) and (not p.duty[d - 1]):
                                p.assign_group(g)
                                flag_3 = True
                    if not flag_1 or not flag_3:
                        print("分配失败")
                else:
                    for g2 in self.map_t2g[d]:
                        if (g2.p_d in JIDI and g.t_d - g2.t_a >= LowerLimit_Combine):
                            flag_1 = False # 正机长是否分配成功
                            flag_3 = False # 副机长是否分配成功
                            for p in self.pilots[1]:
                                if (not p.duty[d]) and (not p.duty[d - 1]):
                                    p.assign_group(g2)
                                    p.add_group(g)
                                    flag_1 = True
                                    self.chengji = self.chengji + 1
                            for p in self.pilots[3]:
                                if (not p.duty[d]) and (not p.duty[d - 1]):
                                    p.assign_group(g2)
                                    p.add_group(g)
                                    flag_3 = True
                                    self.chengji = self.chengji + 1

                            if not flag_1:
                                for p in self.pilots[2]:
                                    if (not p.duty[d]) and (not p.duty[d - 1]):
                                        p.assign_group(g2)
                                        p.add_group(g)
                                        flag_1 = True
                                        self.chengji = self.chengji + 1
                            if not flag_3:
                                for p in self.pilots[2]:
                                    if (not p.duty[d]) and (not p.duty[d - 1]):
                                        p.assign_group(g2)
                                        p.add_group(g)
                                        flag_3 = True
                                        self.chengji = self.chengji + 1
                            if not flag_1 or not flag_3:
                                print("分配失败")
                        if flag_1 and flag_3:
                            break

    def allocate_pilot(self):
        self.chengji = 0
        for d in range(1, NUM_D + 1):
            for g in self.map_t2g[d]:
                if (g.p_d in JIDI and g.p_a in JIDI):
                    flag_1 = False # 正机长是否分配成功
                    flag_3 = False # 副机长是否分配成功
                    for p in self.pilots[1]:
                        if not p.duty[d] and p.p_a_d[d - 1] == g.p_d:
                            p.assign_group(g)
                            p.groups[d][-1].set_type(1)
                            flag_1 = True
                            break
                    for p in self.pilots[3]:
                        if not p.duty[d] and p.p_a_d[d - 1] == g.p_d:
                            p.assign_group(g)
                            p.groups[d][-1].set_type(3)
                            flag_3 = True
                            break
                    if not flag_1:
                        for p in self.pilots[2]:
                            if not p.duty[d] and p.p_a_d[d - 1] == g.p_d:
                                p.assign_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1 = True
                                break
                    if not flag_3:
                        for p in self.pilots[2]:
                            if not p.duty[d] and p.p_a_d[d - 1] == g.p_d:
                                p.assign_group(g)
                                p.groups[d][-1].set_type(3)
                                flag_3 = True
                                break
                    if (not flag_1) or (not flag_3):
                        print(f"{d}天分配失败 3")
                    else:
                        print("分配成功 1")
                        continue
                elif g.p_d not in JIDI:
                    flag_1_wai = False
                    flag_3_wai = False
                    for p in self.pilots[1]:
                        if p.p_a_d[d - 1] == g.p_d and (not p.duty[d]):
                            p.assign_group(g)
                            p.groups[d][-1].set_type(1)
                            flag_1_wai = True
                            break
                    for p in self.pilots[3]:
                        if p.p_a_d[d - 1] == g.p_d and (not p.duty[d]):
                            p.assign_group(g)
                            p.groups[d][-1].set_type(3)
                            flag_1_wai = True
                            break
                    if not flag_1_wai:
                        for p in self.pilots[2]:
                            if p.p_a_d[d - 1] == g.p_d and (not p.duty[d]):
                                p.assign_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1_wai = True
                                break
                    if not flag_3_wai:
                        for p in self.pilots[2]:
                            if p.p_a_d[d - 1] == g.p_d and (not p.duty[d]):
                                p.assign_group(g)
                                p.groups[d][-1].set_type(3)
                                flag_1_wai = True
                                break
                    if flag_1_wai and flag_3_wai:
                        continue

                    for g2 in self.map_t2g[d]:
                        flag_1 = flag_1_wai # 正机长是否分配成功
                        flag_3 = flag_3_wai # 副机长是否分配成功
                        if (g2.p_d in JIDI and g.t_d - g2.t_a >= LowerLimit_Combine and g2.p_a == g.p_d):
                            if not flag_1:
                                for p in self.pilots[1]:
                                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                                        p.assign_group(g2)
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        self.chengji = self.chengji + 1
                                        break
                            if not flag_3:
                                for p in self.pilots[3]:
                                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                                        p.assign_group(g2)
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        self.chengji = self.chengji + 1
                                        break

                            if not flag_1:
                                for p in self.pilots[2]:
                                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                                        p.assign_group(g2)
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        self.chengji = self.chengji + 1
                                        break
                            if not flag_3:
                                for p in self.pilots[2]:
                                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                                        p.assign_group(g2)
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        self.chengji = self.chengji + 1
                                        break
                            if (not flag_1) or (not flag_3):
                                print("分配失败 2")
                            else:
                                print("分配成功 2")
                        if flag_1 and flag_3:
                            flag_1_wai = True
                            flag_3_wai = True
                            break

                    if not (flag_1_wai and flag_3_wai):
                        for g2 in self.map_t2g[d - 1]:
                            flag_1 = flag_1_wai # 正机长是否分配成功
                            flag_3 = flag_3_wai # 副机长是否分配成功
                            if (g2.p_d in JIDI and g.t_d - g2.t_a >= LowerLimit_Combine):
                                if not flag_1:
                                    for p in self.pilots[1]:
                                        if (not p.duty[d]) and (not p.duty[d - 1]) and p.p_a_d[d - 2] == g2.p_d:
                                            p.add_group(g2)
                                            p.groups[d - 1][-1].set_type(2)
                                            p.assign_group(g)
                                            p.groups[d][-1].set_type(1)
                                            flag_1 = True
                                            self.chengji = self.chengji + 1
                                            break
                                if not flag_3:
                                    for p in self.pilots[3]:
                                        if (not p.duty[d] and (not p.duty[d - 1])) and p.p_a_d[d - 2] == g2.p_d:
                                            p.add_group(g2)
                                            p.groups[d - 1][-1].set_type(2)
                                            p.assign_group(g)
                                            p.groups[d][-1].set_type(3)
                                            flag_3 = True
                                            self.chengji = self.chengji + 1
                                            break

                                if not flag_1:
                                    for p in self.pilots[2]:
                                        if (not p.duty[d]) and (not p.duty[d - 1]) and p.p_a_d[d - 1] == g2.p_d:
                                            p.add_group(g2)
                                            p.groups[d - 1][-1].set_type(2)
                                            p.assign_group(g)
                                            p.groups[d][-1].set_type(1)
                                            flag_1 = True
                                            self.chengji = self.chengji + 1
                                            break
                                if not flag_3:
                                    for p in self.pilots[2]:
                                        if (not p.duty[d] and (not p.duty[d - 1])) and p.p_a_d[d - 1] == g2.p_d:
                                            p.add_group(g2)
                                            p.groups[d - 1][-1].set_type(2)
                                            p.assign_group(g)
                                            p.groups[d][-1].set_type(3)
                                            flag_3 = True
                                            self.chengji = self.chengji + 1
                                            break
                                if not flag_1 or not flag_3:
                                    print("分配失败 1")
                                else:
                                    print("分配成功 3")
                            if flag_1 and flag_3:
                                flag_1_wai = True
                                flag_3_wai = True
                                break
                    if not (flag_1_wai and flag_3_wai): # 前面没有单独航班配对，只能找航班来配对
                        for g2 in self.map_t2g[d]:
                            self.dangtian_find_fly2_g(g, g2, flag_1_wai, flag_3_wai, d)

    def dangtian_find_fly2_g(self, g, g2, flag_1_wai, flag_3_wai, d):
        flag_1 = flag_1_wai # 正机长是否分配成功
        flag_3 = flag_3_wai # 副机长是否分配成功
        if (g2.p_d in JIDI and g.t_d - g2.t_a >= LowerLimit_Combine and g2.p_a == g.p_d):
            if not flag_1:
                for p in self.pilots[1]:
                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                        p.assign_group(g2)
                        p.groups[d][-1].set_type(2)
                        p.add_group(g)
                        p.groups[d][-1].set_type(1)
                        flag_1 = True
                        self.chengji = self.chengji + 1
                        break
            if not flag_3:
                for p in self.pilots[3]:
                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                        p.assign_group(g2)
                        p.groups[d][-1].set_type(2)
                        p.add_group(g)
                        p.groups[d][-1].set_type(3)
                        flag_3 = True
                        self.chengji = self.chengji + 1
                        break

            if not flag_1:
                for p in self.pilots[2]:
                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                        p.assign_group(g2)
                        p.groups[d][-1].set_type(2)
                        p.add_group(g)
                        p.groups[d][-1].set_type(1)
                        flag_1 = True
                        self.chengji = self.chengji + 1
                        break
            if not flag_3:
                for p in self.pilots[2]:
                    if (not p.duty[d]) and p.p_a_d[d - 1] == g2.p_d:
                        p.assign_group(g2)
                        p.groups[d][-1].set_type(2)
                        p.add_group(g)
                        p.groups[d][-1].set_type(3)
                        flag_3 = True
                        self.chengji = self.chengji + 1
                        break
            if (not flag_1) or (not flag_3):
                print("分配失败 2")
            else:
                print("分配成功 2")


    def print_result_p1(self):
        print("开始统计")
        result = pd.DataFrame(columns=('EmpNo', 'Day', 'FlightNo', 'DptrT', 'DptrP', 'ArrvT', 'ArrvP', 'Type'))
        self.zhiqinChengben = []
        self.time_fly = []
        self.time_duty = []
        self.num_tibu = [0] * NUM_BOTH
        idx = -1
        for p in self.pilots[2]:
            idx = idx + 1
            for d in range(1, NUM_D + 1):
                if p.duty[d]:
                    for g in p.groups[d]:
                        if g.type == 3:
                            self.num_tibu[idx] = self.num_tibu[idx] + 1
        print(f"替补数量: {sum(self.num_tibu)}")
        # hangshu=0
        # for p in self.pilots[1] + self.pilots[2] + self.pilots[3]:
        # self.time_fly.append(sum(p.time_fly))
        # self.zhiqinChengben.append(sum(p.zhiqinChengben))
        # self.time_duty.append(sum(p.time_duty))
        # for d in range(1, NUM_D + 1):
        # print(d)
        # if p.duty[d]:
        # for g in p.groups[d]:
        # for f in g.flights:
        # hangshu=hangshu+1
        # else:
        # hangshu = hangshu + 1
        # print(hangshu)
        hangshu = 0
        table = []
        for p in self.pilots[1] + self.pilots[2] + self.pilots[3]:
            self.time_fly.append(sum(p.time_fly))
            self.zhiqinChengben.append(sum(p.zhiqinChengben)/60.0)
            self.time_duty.append(sum(p.time_duty))

            for d in range(1, NUM_D + 1):
                if p.duty[d]:
                    for g in p.groups[d]:
                        for f in g.flights:
                            # table.append([p.EmpNo, d, f.id, f.t_d,f.p_d, f.t_a, f.p_a, g.type])
                            # print([p.EmpNo, d, f.id, f.t_d,f.p_d, f.t_a, f.p_a, g.type], hangshu)
                            hangshu = hangshu + 1
                            print(hangshu)
                            result = result.append({'EmpNo': p.EmpNo, 'Day': d, 'FlightNo': f.id, 'DptrT': f.t_d,'DptrP': f.p_d, 'ArrvT': f.t_a, 'ArrvP': f.p_a, 'Type': g.type},
                            ignore_index=True)
                else:
                    hangshu = hangshu + 1
                    print(hangshu)
                    result = result.append({'EmpNo': p.EmpNo, 'Day': d, 'Type': 0},  ignore_index=True)
        # result=pd.concat([result, pd.DataFrame(table, columns=['EmpNo', 'Day', 'FlightNo', 'DptrT',
        # 'DptrP', 'ArrvT', 'ArrvP', 'Type'])])

        print(f"执勤成本总和: {sum(self.zhiqinChengben)}")
        print(f"执勤成本最小: {min(self.zhiqinChengben) }")
        print(f"执勤成本最大: {max(self.zhiqinChengben) }")
        print(f"飞行时间总和: {sum(self.time_fly) / 60}")
        print(f"飞行时间最小: {min(self.time_fly) / 60}")
        print(f"飞行时间最大: {max(self.time_fly) / 60}")
        print(f"执勤时间总和: {sum(self.time_duty) / 60}")
        print(f"执勤时间最小: {min(self.time_duty) / 60}")
        print(f"执勤时间最大: {max(self.time_duty) / 60}")

        result.to_csv("CrewRosters_A_p1.csv", index=False)

    def print_result_p2(self):
        print("开始统计")
        result = pd.DataFrame(columns=('EmpNo', 'Day', 'FlightNo', 'DptrT', 'DptrP', 'ArrvT', 'ArrvP', 'Type'))
        self.zhiqinChengben = []
        self.time_fly = []
        self.time_duty = []
        self.zhiqintianshu=[]
        self.ziqinshichang_perduty=[]
        self.time_fly_perduty=[]
        self.num_tibu = [0] * NUM_BOTH
        idx = -1
        for p in self.pilots[2]:
            idx = idx + 1
            for d in range(1, NUM_D + 1):
                if p.duty[d]:
                    for g in p.groups[d]:
                        if g.type == 3:
                            self.num_tibu[idx] = self.num_tibu[idx] + 1
        print(f"替补数量: {sum(self.num_tibu)}")
        hangshu = 0
        for p in self.pilots[1] + self.pilots[2] + self.pilots[3]:
            self.zhiqintianshu.append(sum(p.duty))
            self.time_fly.append(sum(p.time_fly))
            self.zhiqinChengben.append(sum(p.zhiqinChengben) / 60.0)
            self.time_duty.append(sum(p.time_duty))
            for d in range(1, NUM_D + 1):
                self.ziqinshichang_perduty.append(p.t_a_d[d]-p.t_d_d[d])
                if (p.t_a_d[d]-p.t_d_d[d])/60>24:
                    print("6666666666666666666666")
                self.time_fly_perduty.append(p.time_fly[d])
                if p.duty[d]:
                    for g in p.groups[d]:
                        for f in g.flights:
                            hangshu = hangshu + 1
                            print(hangshu)
        # result = result.append({'EmpNo': p.EmpNo, 'Day': d, 'FlightNo': f.id, 'DptrT': f.t_d,
        # 'DptrP': f.p_d, 'ArrvT': f.t_a, 'ArrvP': f.p_a, 'Type': g.type},
        # ignore_index=True)
                else:
                    hangshu = hangshu + 1
                    print(hangshu)
        # result = result.append({'EmpNo': p.EmpNo, 'Day': d, 'Type': 0},ignore_index=True)
        print(f"执勤成本总和: {sum(self.zhiqinChengben)}")
        print(f"执勤成本最小: {min(self.zhiqinChengben) }")
        print(f"执勤成本最大: {max(self.zhiqinChengben) }")
        print(f"飞行时间总和: {sum(self.time_fly) / 60}")
        print(f"飞行时间最小: {min(self.time_fly) / 60}")
        print(f"飞行时间最大: {max(self.time_fly) / 60}")
        print(f"执勤时间总和: {sum(self.time_duty) / 60}")
        print(f"执勤时间最小: {min(self.time_duty) / 60}")
        print(f"执勤时间最大: {max(self.time_duty) / 60}")
        print(f"执勤天数平均: {np.mean(self.zhiqintianshu)}")
        print(f"执勤天数最小: {min(self.zhiqintianshu)}")
        print(f"执勤天数最大: {max(self.zhiqintianshu)}")
        print(f"一次执勤时长平均: {np.mean(self.ziqinshichang_perduty)/60}")
        print(f"一次执勤时长最小: {min(self.ziqinshichang_perduty)/60}")
        print(f"一次执勤时长最大: {max(self.ziqinshichang_perduty)/60}")
        print(f"一次执勤飞行时长平均: {np.mean(self.time_fly_perduty)/60}")
        print(f"一次执勤飞行时长最小: {min(self.time_fly_perduty)/60}")
        print(f"一次执勤飞行时长最大: {max(self.time_fly_perduty)/60}")
        self.total_zhiqin=sum(self.time_duty)
        result.to_csv("CrewRosters_A_p2.csv", index=False)

    def print_result_p3(self):
        print("开始统计")
        result = pd.DataFrame(columns=('EmpNo', 'Day', 'FlightNo', 'DptrT', 'DptrP', 'ArrvT', 'ArrvP', 'Type'))
        self.zhiqinChengben = []
        self.time_fly = []
        self.time_duty = []
        self.zhiqintianshu=[]
        self.ziqinshichang_perduty=[]
        self.time_fly_perduty=[]
        self.num_tibu = [0] * NUM_BOTH
        idx = -1
        for p in self.pilots[2]:
            idx = idx + 1
            for d in range(1, NUM_D + 1):
                if p.duty[d]:
                    for g in p.groups[d]:
                        if g.type == 3:
                            self.num_tibu[idx] = self.num_tibu[idx] + 1
        print(f"替补数量: {sum(self.num_tibu)}")
        hangshu = 0
        for p in self.pilots[1] + self.pilots[2] + self.pilots[3]:
            self.zhiqintianshu.append(sum(p.duty))
            self.time_fly.append(sum(p.time_fly))
            self.zhiqinChengben.append(sum(p.zhiqinChengben) / 60.0)
            self.time_duty.append(sum(p.time_duty))
            for d in range(1, NUM_D + 1):
                self.ziqinshichang_perduty.append(p.t_a_d[d]-p.t_d_d[d])
                if (p.t_a_d[d]-p.t_d_d[d])/60>24:
                    print("6666666666666666666666")
                    self.time_fly_perduty.append(p.time_fly[d])
                if p.duty[d]:
                    for g in p.groups[d]:
                        for f in g.flights:
                            hangshu = hangshu + 1
                            print(hangshu)
        # result = result.append({'EmpNo': p.EmpNo, 'Day': d, 'FlightNo': f.id, 'DptrT': f.t_d,
        # 'DptrP': f.p_d, 'ArrvT': f.t_a, 'ArrvP': f.p_a, 'Type': g.type},
        # ignore_index=True)
                else:
                    hangshu = hangshu + 1
                    print(hangshu)
        # result = result.append({'EmpNo': p.EmpNo, 'Day': d, 'Type': 0}, ignore_index=True)
        print(f"执勤成本总和: {sum(self.zhiqinChengben)}")
        print(f"执勤成本最小: {min(self.zhiqinChengben) }")
        print(f"执勤成本最大: {max(self.zhiqinChengben) }")
        print(f"飞行时间总和: {sum(self.time_fly) / 60}")
        print(f"飞行时间最小: {min(self.time_fly) / 60}")
        print(f"飞行时间最大: {max(self.time_fly) / 60}")
        print(f"执勤时间总和: {sum(self.time_duty) / 60}")
        print(f"执勤时间最小: {min(self.time_duty) / 60}")
        print(f"执勤时间最大: {max(self.time_duty) / 60}")
        print(f"执勤天数求和: {np.sum(self.zhiqintianshu)}")
        print(f"执勤天数平均: {np.mean(self.zhiqintianshu)}")
        print(f"执勤天数最小: {min(self.zhiqintianshu)}")
        print(f"执勤天数最大: {max(self.zhiqintianshu)}")
        print(f"一次执勤时长平均: {np.mean(self.ziqinshichang_perduty)/60}")
        print(f"一次执勤时长最小: {min(self.ziqinshichang_perduty)/60}")
        print(f"一次执勤时长最大: {max(self.ziqinshichang_perduty)/60}")
        print(f"一次执勤飞行时长平均: {np.mean(self.time_fly_perduty)/60}")
        print(f"一次执勤飞行时长最小: {min(self.time_fly_perduty)/60}")
        print(f"一次执勤飞行时长最大: {max(self.time_fly_perduty)/60}")
        self.total_zhiqin=sum(self.time_duty)
        result.to_csv("CrewRosters_B_p3.csv", index=False)

    def judge_rep(self, g: Group_Flight):
        if (g.flights[0].p_d == 1 and g.flights[0].p_a == 3) or \
            (g.flights[0].p_d == 1 and g.flights[0].p_a == 6) or \
            (g.flights[0].p_d == 1 and g.flights[0].p_a == 5):
            return True
        else:
            return False

    def judge_rep_1(self, g: Group_Flight):
        if (g.flights[0].p_d == 1 and g.flights[0].p_a == 3) or \
            (g.flights[0].p_d == 1 and g.flights[0].p_a == 6):
            return True
        else:
            return False

    def judge_rep_2(self, g: Group_Flight):
        if (g.flights[0].p_d == 1 and g.flights[0].p_a == 5):
            return True
        else:
            return False

    def allocate_p2(self):
        ##分配第 0 天##
        for g in self.map_t2g[1]:
            if self.judge_rep(g):
                flag_1, flag_3 = self.assign_p_to_group(g, 1)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                flag_1, flag_3 = self.assign_p_to_group_chengji(g, 1)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                continue
            elif len(g.flights) == 1:
                flag_1, flag_3 = self.assign_p_to_group_dan(g, g.d_d)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                    continue

            else:
                flag_1, flag_3 = self.assign_p_to_group(g, 1)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                    continue

        ##分配第二天##
        for g in self.map_t2g[2]:
            if self.judge_rep_2(g):
                flag_1, flag_3 = self.assign_p_to_group(g, 2)
                if (not flag_1) or (not flag_3):
                    print(f"{2}天分配失败 3")
                else:
                    print("分配成功 1")
                flag_1, flag_3 = self.assign_p_to_group_chengji(g, 2)
                if (not flag_1) or (not flag_3):
                    print(f"{2}天分配失败 3")
                else:
                    print("分配成功 1")
                    continue
            elif self.judge_rep_1(g):
                self.assign_p_to_group_zaiFeiShuangXiang(g, g.d_d)
            elif len(g.flights) == 1:
                if [g.flights[0].id == 1]:
                    print(1)
                flag_1, flag_3 = self.assign_p_to_group_dan(g, g.d_d)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                    continue
            else:
                flag_1, flag_3 = self.assign_p_to_group(g, 2)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                    continue
        ##分配第三到十四天##
        for d in range(3, NUM_D):
            for g in self.map_t2g[d]:
                if self.judge_rep(g):
                    self.assign_p_to_group_zaiFeiShuangXiang(g, g.d_d)
                elif len(g.flights) == 1:
                    flag_1, flag_3 = self.assign_p_to_group_dan(g, g.d_d)
                    if (not flag_1) or (not flag_3):
                        print(f"{1}天分配失败 3")
                    else:
                        print("分配成功 1")
                        continue
                else:
                    flag_1, flag_3 = self.assign_p_to_group(g, g.d_d)
                    if (not flag_1) or (not flag_3):
                        print(f"{1}天分配失败 3")
                    else:
                        print("分配成功 1")
                        continue
        ##分配最后一天##
        for g in self.map_t2g[15]:
            if self.judge_rep(g):
                flag_1, flag_3 = self.assign_p_to_group(g, 15)
                if (not flag_1) or (not flag_3):
                    print(f"{2}天分配失败 3")
                else:
                    print("分配成功 1")
                self.assign_p_to_group_zaiFeiShuangXiang_qian(g, 15)
            elif len(g.flights) == 1:
                flag_1, flag_3 = self.assign_p_to_group_dan(g, g.d_d)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                    continue
            else:
                flag_1, flag_3 = self.assign_p_to_group(g, g.d_d)
                if (not flag_1) or (not flag_3):
                    print(f"{1}天分配失败 3")
                else:
                    print("分配成功 1")
                    continue

    def assign_p_to_group(self, g, d):
        flag_1 = False # 正机长是否分配成功
        flag_3 = False # 副机长是否分配成功
        for p in self.pilots[1]:
            if not p.duty[d]:
                p.assign_group(g)
                p.groups[d][-1].set_type(1)
                flag_1 = True
                break
        for p in self.pilots[3]:
            if not p.duty[d]:
                p.assign_group(g)
                p.groups[d][-1].set_type(3)
                flag_3 = True
                break
        if not flag_1:
            for p in self.pilots[2]:
                if not p.duty[d]:
                    p.assign_group(g)
                    p.groups[d][-1].set_type(1)
                    flag_1 = True
                    break
        if not flag_3:
            for p in self.pilots[2]:
                if not p.duty[d]:
                    p.assign_group(g)
                    p.groups[d][-1].set_type(3)
                    flag_3 = True
                    break
        return flag_1, flag_3

    def assign_p_to_group_chengji(self, g, d):
        flag_1 = False # 正机长是否分配成功
        flag_3 = False # 副机长是否分配成功
        for p in self.pilots[1]:
            if not p.duty[d]:
                p.assign_group(Group_Flight(g.flights[0]))
                p.groups[d][-1].set_type(2)
                flag_1 = True
                break
        for p in self.pilots[3]:
            if not p.duty[d]:
                p.assign_group(Group_Flight(g.flights[0]))
                p.groups[d][-1].set_type(2)
                flag_3 = True
                break
        if not flag_1:
            for p in self.pilots[2]:
                if not p.duty[d]:
                    p.assign_group(Group_Flight(g.flights[0]))
                    p.groups[d][-1].set_type(2)
                    flag_1 = True
                    break
        if not flag_3:
            for p in self.pilots[2]:
                if not p.duty[d]:
                    p.assign_group(Group_Flight(g.flights[0]))
                    p.groups[d][-1].set_type(2)
                    flag_3 = True
                    break
        return flag_1, flag_3

    def assign_p_to_group_chengji_1(self, g, d, g_zhen):
        flag_1 = False # 正机长是否分配成功
        for p in self.pilots[1]:
            if not p.duty[d]:
                p.assign_group(Group_Flight(g.flights[0]))
                p.groups[d][-1].set_type(2)
                flag_1 = True
                p.add_group(g_zhen)
                p.groups[g_zhen.d_d][-1].set_type(1)
                break

        if not flag_1:
            for p in self.pilots[2]:
                if not p.duty[d]:
                    p.assign_group(Group_Flight(g.flights[0]))
                    p.groups[d][-1].set_type(2)
                    flag_1 = True
                    p.add_group(g_zhen)
                    p.groups[g_zhen.d_d][-1].set_type(1)
                    break
        return flag_1

    def assign_p_to_group_chengji_3(self, g, d, g_zhen):

        flag_3 = False # 副机长是否分配成功

        for p in self.pilots[3]:
            if not p.duty[d]:
                p.assign_group(Group_Flight(g.flights[0]))
                p.groups[d][-1].set_type(2)
                flag_3 = True
                p.add_group(g_zhen)
                p.groups[g_zhen.d_d][-1].set_type(3)
                break

        if not flag_3:
            for p in self.pilots[2]:
                if not p.duty[d]:
                    p.assign_group(Group_Flight(g.flights[0]))
                    p.groups[d][-1].set_type(2)
                    flag_3 = True
                    p.add_group(g_zhen)
                    p.groups[g_zhen.d_d][-1].set_type(3)
                    break
        return flag_3

    def assign_p_to_group_zaiFeiShuangXiang_1(self, g, d):
        flag_pre_1 = False # 是否分配完前面来的人
        for p in self.pilots[1]:
            if (len(p.groups[d - 1]) > 1):
                continue
            for g_pre in p.groups[d - 1]:

                for f in g_pre.flights:
                    if g.flights[-1].p_d == g_pre.flights[-1].p_a:
                        p.add_group(Group_Flight(g.flights[-1]))
                        p.groups[g.flights[-1].d_d][-1].set_type(1)
                        flag_pre_1 = True
                        break
                    if flag_pre_1:
                        break
            if flag_pre_1:
                break
        return flag_pre_1

    def assign_p_to_group_zaiFeiShuangXiang_3(self, g, d):
        flag_pre_1 = False # 是否分配完前面来的人
        for p in self.pilots[3]:
            if (len(p.groups[d - 1]) > 1):
                continue
            for g_pre in p.groups[d - 1]:

                for f in g_pre.flights:
                    if g.flights[-1].p_d == g_pre.flights[-1].p_a:
                        p.add_group(Group_Flight(g.flights[-1]))
                        p.groups[g.flights[-1].d_d][-1].set_type(3)
                        flag_pre_1 = True
                        break
                    if flag_pre_1:
                        break
            if flag_pre_1:
                break
        return flag_pre_1

    def assign_p_to_group_zaiFeiShuangXiang_2(self, g, d, ty):
        flag_pre_1 = False # 是否分配完前面来的人
        for p in self.pilots[2]:
            if (len(p.groups[d - 1]) > 1):
                continue
            for g_pre in p.groups[d - 1]:
                for f in g_pre.flights:
                    if g.flights[-1].p_d == g_pre.flights[-1].p_a:
                        p.add_group(Group_Flight(g.flights[-1]))
                        p.groups[g.flights[-1].d_d][-1].set_type(ty)
                        flag_pre_1 = True
                        break
                    if flag_pre_1:
                        break
            if flag_pre_1:
                break
        return flag_pre_1

    def assign_p_to_group_zaiFeiShuangXiang(self, g, d):
        flag_1 = self.assign_p_to_group_zaiFeiShuangXiang_1(g, d)
        flag_3 = self.assign_p_to_group_zaiFeiShuangXiang_3(g, d)
        if not flag_1:
            self.assign_p_to_group_zaiFeiShuangXiang_2(g, d, 1)
        if not flag_3:
            self.assign_p_to_group_zaiFeiShuangXiang_2(g, d, 3)
            self.assign_p_to_group(Group_Flight(g.flights[0]), g.flights[0].d_d)

    def assign_p_to_group_zaiFeiShuangXiang_qian_type(self, g, d, type):
        flag_pre = False # 是否分配完前面来的人
        for p in self.pilots[type]:
            for g_pre in p.groups[d - 1]:
                if g.flights[-1] == g_pre.flights[0]:
                    p.add_group(Group_Flight(g.flights[-1]))
                    flag_pre = True
                    break
            if flag_pre:
                break
        return flag_pre

    def assign_p_to_group_zaiFeiShuangXiang_qian(self, g, d):
        flag_pre_1 = False # 是否分配完前面来的人
        flag_pre_3 = False # 是否分配完前面来的人
        flag_pre_1 = self.assign_p_to_group_zaiFeiShuangXiang_qian_type(g, d, 1)
        flag_pre_3 = self.assign_p_to_group_zaiFeiShuangXiang_qian_type(g, d, 3)
        if not flag_pre_1:
            flag_pre_1 = self.assign_p_to_group_zaiFeiShuangXiang_qian_type(g, d, 2)
        if not flag_pre_3:
            flag_pre_3 = self.assign_p_to_group_zaiFeiShuangXiang_qian_type(g, d, 2)
        return flag_pre_1, flag_pre_3

    def assign_p_to_group_dan(self, g, d):
        flag_qian_1 = False # 是否前一天乘机过去了
        flag_qian_3 = False # 是否前一天乘机过去了
        for f in self.map_t2f[d - 1]:
            if f.p_a == g.p_a:
                flag_qian_1 = self.assign_p_to_group_chengji_1(Group_Flight(f), d - 1, g)
                flag_qian_3 = self.assign_p_to_group_chengji_3(Group_Flight(f), d - 1, g)
                if flag_qian_1 and flag_qian_3:
                    break
        if not (flag_qian_1 and flag_qian_3):
            for f in self.map_t2f[d]:
                if f.p_a == g.p_a:
                    if not flag_qian_1:
                        flag_qian_1 = self.assign_p_to_group_chengji_1(Group_Flight(f), d, g)
                    if not flag_qian_3:
                        flag_qian_3 = self.assign_p_to_group_chengji_3(Group_Flight(f), d, g)
                    if flag_qian_1 and flag_qian_3:
                        break
        return flag_qian_1, flag_qian_3

    def run_jiao_p2(self):
        self.make_group()
        self.allocate_p2()
        self.print_result_p2()

    def run_jiao_p1(self):
        self.make_group()
        self.coombine_group()
        self.allocate_pilot()
        self.print_result_p1()

    def tanlan_p1_B(self):
        ordered_flight = copy.deepcopy(self.map_t2f)
        num_un = 0
        table_un = pd.DataFrame()
        unallocated_g = []
        self.chengji = 0
        for d in range(1, NUM_D + 1):
            print(d)
            ordered_flight[d].sort()
            alled_f = []
            while len(ordered_flight[d]) - len(alled_f) > 0:
                print(len(ordered_flight[d]) - len(alled_f))
                g = Group_Flight(ordered_flight[d][0])
                f_fir = None
                for f in range(0, len(ordered_flight[d])):
                    if f not in alled_f:
                        g = Group_Flight(ordered_flight[d][f])
                        alled_f.append(f)
                        f_fir = f
                        break
                ind_del_f = [0]
                if g.p_d in JIDI:
                    for f in range(f_fir, len(ordered_flight[d])):
                        if f in alled_f:
                            continue
                        if ordered_flight[d][f].p_d == g.p_a and ordered_flight[d][f].t_d -g.t_a >= LowerLimit_Combine:
                            g.add_flight(ordered_flight[d][f])
                            alled_f.append(f)
                            ind_del_f.append(f)
                            if g.p_a in JIDI:
                                break

                # added_f = []
                # flag_xinhuilu = False
                # temp_g=copy.deepcopy(g)
                # for f in range(ind_del_f[-1], len(ordered_flight[d])):
                # if f in alled_f:
                # continue
                # if ordered_flight[d][f].p_d == temp_g.p_a and ordered_flight[d][
                # f].t_d - temp_g.t_a >= LowerLimit_Combine:
                # added_f.append(f)
                # temp_g.add_flight(ordered_flight[d][f])
                # # alled_f.append(f)
                # # ind_del_f.append(f)
                # if temp_g.p_a == g.p_a:
                # flag_xinhuilu=True
                # break
                # if flag_xinhuilu:
                # for f in added_f:
                # g.add_flight(ordered_flight[d][f])
                # alled_f.append(f)
                # ind_del_f.append(f)

                # print(ordered_flight[d][f].id)
                # for f in reversed(ind_del_f):
                # print(ordered_flight[d][f].id)
                # del ordered_flight[d][f]
                flag_1 = False
                flag_3 = False
                for p in self.pilots[1]:
                    if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine:
                        if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                            p.add_group_first(g)
                            p.groups[d][0].set_type(1)
                            flag_1 = True
                            break
                        if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine:
                            p.add_group(g)
                            p.groups[d][-1].set_type(1)
                            flag_1 = True
                            break

                        if (not p.duty[d]):
                            p.add_group(g)
                            p.groups[d][-1].set_type(1)
                            flag_1 = True
                            break
                for p in self.pilots[3]:
                    if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine:
                        if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                            p.add_group_first(g)
                            p.groups[d][0].set_type(3)
                            flag_3 = True
                            break
                        if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine:
                            p.add_group(g)
                            p.groups[d][-1].set_type(3)
                            flag_3 = True
                            break

                        if (not p.duty[d]):
                            p.add_group(g)
                            p.groups[d][-1].set_type(3)
                            flag_3 = True
                            break
                        # p.add_group(g)
                        # p.groups[d][-1].set_type(3)
                        # flag_3 = True
                        # break
                if not flag_1:
                    for p in self.pilots[2]:
                        if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine:
                            if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                                p.add_group_first(g)
                                p.groups[d][0].set_type(1)
                                flag_1 = True
                                break
                            if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine:
                                p.add_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1 = True
                                break

                            if (not p.duty[d]):
                                p.add_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1 = True
                                break
                            # p.add_group(g)
                            # p.groups[d][-1].set_type(1)
                            # flag_1 = True
                            # break
                if not flag_3:
                    for p in self.pilots[2]:
                        if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >=  LowerLimit_Combine:
                            if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                                p.add_group_first(g)
                                p.groups[d][0].set_type(3)
                                flag_3 = True
                                break
                            if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine:
                                p.add_group(g)
                                p.groups[d][-1].set_type(3)
                                flag_3 = True
                                break

                            if (not p.duty[d]):
                                p.add_group(g)
                                p.groups[d][-1].set_type(3)
                                flag_3 = True
                                break
                            # p.add_group(g)
                            # p.groups[d][-1].set_type(3)
                            # flag_3 = True
                            # break

                if not (flag_1 and flag_3):
                    for f in self.map_t2f[d - 1]:
                        if f.p_d in JIDI and g.p_d == f.p_a and g.t_d - f.t_a >= LowerLimit_Combine:
                            if not flag_1:
                                for p in self.pilots[1]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and (  not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        break
                            if not flag_3:
                                for p in self.pilots[3]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[  max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and ( not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        break
                            if not flag_1:
                                for p in self.pilots[2]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[ max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and ( not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        break
                            if not flag_3:
                                for p in self.pilots[2]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[ max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and ( not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        break
                temp_g = copy.deepcopy(g)
                if not (flag_1 and flag_3):
                    flag_qian = False
                    flag_hou = False
                    for f in self.map_t2f[d]:
                        if f.p_d in JIDI and f.p_a == g.p_d and g.t_d - f.t_a >= LowerLimit_Combine:
                            temp_g.add_flight_first(f)
                            flag_qian = True
                            break
                    if flag_qian:
                        for f in self.map_t2f[d]:
                            if f.p_a in JIDI and f.p_d == g.p_a and f.t_d - g.t_a >= LowerLimit_Combine:
                                temp_g.add_flight(f)
                                flag_hou = True

                                break
                    if flag_qian and flag_hou:
                        # flag_1 = False
                        # flag_3 = False
                        # print("99999999999999999999999999999999999999999999999999999999999999999999999999999999999")
                        for p in self.pilots[1]:
                            if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                p.add_group(Group_Flight(temp_g.flights[0]))
                                p.groups[d][-1].set_type(2)
                                p.add_group(Group_Flight(temp_g.flights[1]))
                                p.groups[d][-1].set_type(1)
                                p.add_group(Group_Flight(temp_g.flights[2]))
                                p.groups[d][-1].set_type(2)
                                self.chengji = self.chengji + 2
                                flag_1 = True
                                break
                        for p in self.pilots[3]:
                            if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                p.add_group(Group_Flight(temp_g.flights[0]))
                                p.groups[d][-1].set_type(2)
                                p.add_group(Group_Flight(temp_g.flights[1]))
                                p.groups[d][-1].set_type(3)
                                p.add_group(Group_Flight(temp_g.flights[2]))
                                p.groups[d][-1].set_type(2)
                                self.chengji = self.chengji + 2
                                flag_3 = True
                                break
                        if not flag_1:
                            for p in self.pilots[2]:
                                if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                    p.add_group(Group_Flight(temp_g.flights[0]))
                                    p.groups[d][-1].set_type(2)
                                    p.add_group(Group_Flight(temp_g.flights[1]))
                                    p.groups[d][-1].set_type(1)
                                    p.add_group(Group_Flight(temp_g.flights[2]))
                                    p.groups[d][-1].set_type(2)
                                    self.chengji = self.chengji + 2
                                    flag_1 = True
                                    break
                        if not flag_3:
                            for p in self.pilots[2]:
                                if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                    p.add_group(Group_Flight(temp_g.flights[0]))
                                    p.groups[d][-1].set_type(2)
                                    p.add_group(Group_Flight(temp_g.flights[1]))
                                    p.groups[d][-1].set_type(3)
                                    p.add_group(Group_Flight(temp_g.flights[2]))
                                    p.groups[d][-1].set_type(2)
                                    self.chengji = self.chengji + 2
                                    flag_3 = True
                                    break

                if not (flag_1 and flag_3):
                    unallocated_g.append(g)
                    num_un = num_un + 1
                    for f in g.flights:
                        table_un = table_un.append({'FltNum': f.id, 'DptrT': f.t_d, 'ArrvT': f.t_a, "DrtrD": f.d_d}, ignore_index=True)

            for p in self.pilots[1]:
                if p.p_a_d[d - 1] is not p.jidi and (not p.duty[d]):
                    for f in self.map_t2f[d]:
                        if f.p_d == p.p_a_d[d - 1] and f.p_a == p.jidi:
                            p.add_group(Group_Flight(f))
                            p.groups[d][-1].set_type(2)
                            self.chengji = self.chengji + 1
                            print("111111111111111111111111111111111111111111")
                            break
        self.print_result_p1()

        table_un.to_csv("UncoveredFlights_p1_B.csv", index=False)
        print(num_un)
        print(f"{self.chengji} 乘機次數")
        print("第一天 duty 人数:", sum([p.duty[1] for p in self.pilots[1] + self.pilots[2] + self.pilots[3]]))

    def tanlan_p2_B(self):
        ordered_flight = copy.deepcopy(self.map_t2f)
        num_un = 0
        table_un = pd.DataFrame()
        unallocated_g = []
        self.chengji = 0
        for d in range(1, NUM_D + 1):
            print(d)
            ordered_flight[d].sort()
            alled_f = []
            while len(ordered_flight[d]) - len(alled_f) > 0:
                print(len(ordered_flight[d]) - len(alled_f))
                g = Group_Flight(ordered_flight[d][0])
                f_fir = None
                for f in range(0, len(ordered_flight[d])):
                    if f not in alled_f:
                        g = Group_Flight(ordered_flight[d][f])
                        alled_f.append(f)
                        f_fir = f
                        break
                ind_del_f = [0]
                if g.p_d in JIDI:
                    for f in range(f_fir, len(ordered_flight[d])):
                        if f in alled_f:
                            continue
                        if ordered_flight[d][f].p_d == g.p_a and ordered_flight[d][f].t_d -g.t_a >= LowerLimit_Combine and ordered_flight[d][f].t_d - g.t_a <= UpperLimit_Combine:
                            if (g.time_fly + ordered_flight[d][f].t_a -ordered_flight[d][f].t_d) > MaxBlk:
                                continue
                            if (ordered_flight[d][f].t_a - g.t_d) > MaxDP:
                                continue
                            g.add_flight(ordered_flight[d][f])
                            alled_f.append(f)
                            ind_del_f.append(f)
                            if g.p_a in JIDI:
                                break

                # added_f = []
                # flag_xinhuilu = False
                # temp_g=copy.deepcopy(g)
                # for f in range(ind_del_f[-1], len(ordered_flight[d])):
                # if f in alled_f:
                # continue
                # if ordered_flight[d][f].p_d == temp_g.p_a and ordered_flight[d][
                # f].t_d - temp_g.t_a >= LowerLimit_Combine:
                # added_f.append(f)
                # temp_g.add_flight(ordered_flight[d][f])
                # # alled_f.append(f)
                # # ind_del_f.append(f)
                # if temp_g.p_a == g.p_a:
                # flag_xinhuilu=True
                # break
                # if flag_xinhuilu:
                # for f in added_f:
                # g.add_flight(ordered_flight[d][f])
                # alled_f.append(f)
                # ind_del_f.append(f)

                # print(ordered_flight[d][f].id)
                # for f in reversed(ind_del_f):
                # print(ordered_flight[d][f].id)
                # del ordered_flight[d][f]
                flag_1 = False
                flag_3 = False
                ### 先分配今天剩余没用的人 ###
                for p in self.pilots[1]:
                    if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (g.t_d - p.t_a_d[d - 1] <= UpperLimit_Combine):
                        if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine and(p.t_d_d[d] - g.t_a<=UpperLimit_Combine):
                            if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] - g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                p.add_group_first(g)
                                p.groups[d][0].set_type(1)
                                flag_1 = True
                                break
                        if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine and (p.time_fly[d]+g.time_fly<MaxBlk) and (g.t_d - p.t_a_d[d]<=UpperLimit_Combine):
                            if (g.t_a-p.t_d_d[d]<=MaxDP):
                                p.add_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1 = True
                                break

                        if (not p.duty[d]):
                            if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                p.add_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1 = True
                                break
                for p in self.pilots[3]:
                    if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (g.t_d - p.t_a_d[d - 1]<=UpperLimit_Combine):
                        if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine and (p.t_d_d[d] - g.t_a<=UpperLimit_Combine):
                            if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] - g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                p.add_group_first(g)
                                p.groups[d][0].set_type(3)
                                flag_3 = True
                                break
                            if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine and (g.t_d - p.t_a_d[d]<=UpperLimit_Combine):
                                if (g.t_a - p.t_d_d[d] <= MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                    p.add_group(g)
                                    p.groups[d][-1].set_type(3)
                                    flag_3 = True
                                    break

                            if (not p.duty[d]):
                                if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                    p.add_group(g)
                                    p.groups[d][-1].set_type(3)
                                    flag_3 = True
                                    break
                            # p.add_group(g)
                            # p.groups[d][-1].set_type(3)
                            # flag_3 = True
                            # break
                    if not flag_1:
                        for p in self.pilots[2]:
                            if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (g.t_d - p.t_a_d[d - 1]<=UpperLimit_Combine):
                                if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine and (p.t_d_d[d] - g.t_a<=UpperLimit_Combine):
                                    if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] -g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                        p.add_group_first(g)
                                        p.groups[d][0].set_type(1)
                                        flag_1 = True
                                        break
                                if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine and (g.t_d - p.t_a_d[d]<=UpperLimit_Combine):
                                    if (g.t_a - p.t_d_d[d] <= MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        break

                                if (not p.duty[d]):
                                    if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        break
                                # p.add_group(g)
                                # p.groups[d][-1].set_type(1)
                                # flag_1 = True
                                # break
                    if not flag_3:
                        for p in self.pilots[2]:
                            if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (g.t_d - p.t_a_d[d - 1])<=UpperLimit_Combine:
                                if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine and (p.t_d_d[d] - g.t_a)<=UpperLimit_Combine:
                                    if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] -g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                        p.add_group_first(g)
                                        p.groups[d][0].set_type(3)
                                        flag_3 = True
                                        break
                                if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine and (g.t_d - p.t_a_d[d]<=UpperLimit_Combine):
                                    if (g.t_a - p.t_d_d[d] <= MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        break

                                if (not p.duty[d]):
                                    if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        break
                                # p.add_group(g)
                                # p.groups[d][-1].set_type(3)
                                # flag_3 = True
                                # break
                    ### 选择前一天的航班乘机过来 ###
                    if not (flag_1 and flag_3):
                        for f in self.map_t2f[d - 1]:
                            if f.p_d in JIDI and g.p_d == f.p_a and g.t_d - f.t_a >= LowerLimit_Combine and (g.t_d - f.t_a<=UpperLimit_Combine):
                                if g.t_d - f.t_a < MinRest:
                                    continue
                                if not flag_1:
                                    for p in self.pilots[1]:
                                        if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[ max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and ( not p.duty[d]) and (f.t_d - p.t_a_d[max(d - 2, 0)]<=UpperLimit_Combine):
                                            p.add_group(Group_Flight(f))
                                            p.groups[d - 1][-1].set_type(2)
                                            self.chengji = self.chengji + 1
                                            p.add_group(g)
                                            p.groups[d][-1].set_type(1)
                                            flag_1 = True
                                            break
                                if not flag_3:
                                    for p in self.pilots[3]:
                                        if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[ max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and ( not p.duty[d]) and (f.t_d - p.t_a_d[ max(d - 2, 0)]<=UpperLimit_Combine):
                                            p.add_group(Group_Flight(f))
                                            p.groups[d - 1][-1].set_type(2)
                                            self.chengji = self.chengji + 1
                                            p.add_group(g)
                                            p.groups[d][-1].set_type(3)
                                            flag_3 = True
                                            break
                                if not flag_1:
                                    for p in self.pilots[2]:
                                        if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and (not p.duty[d]) and (f.t_d - p.t_a_d[  max(d - 2, 0)]<=UpperLimit_Combine):
                                            p.add_group(Group_Flight(f))
                                            p.groups[d - 1][-1].set_type(2)
                                            self.chengji = self.chengji + 1
                                            p.add_group(g)
                                            p.groups[d][-1].set_type(1)
                                            flag_1 = True
                                            break
                                if not flag_3:
                                    for p in self.pilots[2]:
                                        if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and (not p.duty[d]) and (f.t_d - p.t_a_d[max(d - 2, 0)] <=UpperLimit_Combine):
                                            p.add_group(Group_Flight(f))
                                            p.groups[d - 1][-1].set_type(2)
                                            self.chengji = self.chengji + 1
                                            p.add_group(g)
                                            p.groups[d][-1].set_type(3)
                                            flag_3 = True
                                            break
                        ### 在同一天找前面后面各一驾航班 乘两次机 ###
                        temp_g = copy.deepcopy(g)
                        if not (flag_1 and flag_3):
                            flag_qian = False
                            flag_hou = False
                            for f in reversed(self.map_t2f[d]):
                                if f.p_d in JIDI and f.p_a == g.p_d and g.t_d - f.t_a >= LowerLimit_Combine and (g.t_d - f.t_a<=UpperLimit_Combine):
                                    temp_g.add_flight_first(f)
                                    if temp_g.time_fly > MaxBlk:
                                        flag_qian = False
                                        break
                                    if temp_g.t_a - temp_g.t_d > MaxDP:
                                        flag_qian = False
                                        break
                                    flag_qian = True
                                    break
                            if flag_qian:
                                for f in self.map_t2f[d]:
                                    if f.p_a in JIDI and f.p_d == g.p_a and f.t_d - g.t_a >= LowerLimit_Combine and (f.t_d - g.t_a<=UpperLimit_Combine):
                                        temp_g.add_flight(f)
                                        if temp_g.time_fly > MaxBlk:
                                            flag_hou = False
                                            break
                                        if temp_g.t_a - temp_g.t_d > MaxDP:
                                            flag_qian = False
                                            break
                                        flag_hou = True

                                        break
                            if flag_qian and flag_hou:
                                # flag_1 = False
                                # flag_3 = False
                                # print("99999999999999999999999999999999999999999999999999999999999999999999999999999999999")
                                for p in self.pilots[1]:
                                    if temp_g.t_d - p.t_a_d[d - 1] < MinRest:
                                        continue
                                    if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and ( not p.duty[d]) and (temp_g.t_d - p.t_a_d[d -1]<=UpperLimit_Combine):
                                        p.add_group(Group_Flight(temp_g.flights[0]))
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(Group_Flight(temp_g.flights[1]))
                                        p.groups[d][-1].set_type(1)
                                        p.add_group(Group_Flight(temp_g.flights[2]))
                                        p.groups[d][-1].set_type(2)
                                        self.chengji = self.chengji + 2
                                        flag_1 = True
                                        break
                                for p in self.pilots[3]:
                                    if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]) and (temp_g.t_d - p.t_a_d[d -1]<=UpperLimit_Combine):
                                        p.add_group(Group_Flight(temp_g.flights[0]))
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(Group_Flight(temp_g.flights[1]))
                                        p.groups[d][-1].set_type(3)
                                        p.add_group(Group_Flight(temp_g.flights[2]))
                                        p.groups[d][-1].set_type(2)
                                        self.chengji = self.chengji + 2
                                        flag_3 = True
                                        break
                                if not flag_1:
                                    for p in self.pilots[2]:
                                        if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]) and (temp_g.t_d - p.t_a_d[d - 1]<=UpperLimit_Combine):
                                            p.add_group(Group_Flight(temp_g.flights[0]))
                                            p.groups[d][-1].set_type(2)
                                            p.add_group(Group_Flight(temp_g.flights[1]))
                                            p.groups[d][-1].set_type(1)
                                            p.add_group(Group_Flight(temp_g.flights[2]))
                                            p.groups[d][-1].set_type(2)
                                            self.chengji = self.chengji + 2
                                            flag_1 = True
                                            break
                                if not flag_3:
                                    for p in self.pilots[2]:
                                        if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]) and (temp_g.t_d - p.t_a_d[ d - 1]<=UpperLimit_Combine):
                                            p.add_group(Group_Flight(temp_g.flights[0]))
                                            p.groups[d][-1].set_type(2)
                                            p.add_group(Group_Flight(temp_g.flights[1]))
                                            p.groups[d][-1].set_type(3)
                                            p.add_group(Group_Flight(temp_g.flights[2]))
                                            p.groups[d][-1].set_type(2)
                                            self.chengji = self.chengji + 2
                                            flag_3 = True
                                            break

                        if not (flag_1 and flag_3):
                            unallocated_g.append(g)
                            num_un = num_un + 1
                            for f in g.flights:
                                table_un = table_un.append({'FltNum': f.id, 'DptrT': f.t_d, 'ArrvT': f.t_a, "DrtrD": f.d_d}, ignore_index=True)

                    for p in self.pilots[1]:
                        if p.p_a_d[d - 1] is not p.jidi and (not p.duty[d]):
                            for f in self.map_t2f[d]:
                                if f.p_d == p.p_a_d[d - 1] and f.p_a == p.jidi:
                                    p.add_group(Group_Flight(f))
                                    p.groups[d][-1].set_type(2)
                                    self.chengji = self.chengji + 1
                                    print("111111111111111111111111111111111111111111")
                                    break
        self.print_result_p2()

        table_un.to_csv("UncoveredFlights_p2_A.csv", index=False)
        print(num_un)
        print(f"{self.chengji} 乘機次數")
        print("第一天 duty 人数:", sum([p.duty[1] for p in self.pilots[1] + self.pilots[2] + self.pilots[3]]))
        total_fly = 0
        if len(table_un)>0:
            list_unall=table_un["FltNum"].to_list()

            for d in range(1,NUM_D+1):
                for f in self.map_t2f[d]:
                    if f.id not in list_unall:
                        total_fly=total_fly+(f.t_a-f.t_d)*2
        else:
            for d in range(1, NUM_D + 1):
                for f in self.map_t2f[d]:
                    total_fly = total_fly + (f.t_a - f.t_d) * 2
        print("机组总体利用率: ", total_fly/self.total_zhiqin)

    def tanlan_p3_B(self):
        ordered_flight = copy.deepcopy(self.map_t2f)
        num_un = 0
        table_un = pd.DataFrame()
        unallocated_g = []
        self.chengji = 0
        for d in range(1, NUM_D + 1):
            print(d)
            ordered_flight[d].sort()
            alled_f = []
            while len(ordered_flight[d]) - len(alled_f) > 0:
                print(len(ordered_flight[d]) - len(alled_f))
                g = Group_Flight(ordered_flight[d][0])
                f_fir = None
                for f in range(0, len(ordered_flight[d])):
                    if f not in alled_f:
                        g = Group_Flight(ordered_flight[d][f])
                        alled_f.append(f)
                        f_fir = f
                        break
                ind_del_f = [0]
                if g.p_d in JIDI:
                    for f in range(f_fir, len(ordered_flight[d])):
                        if f in alled_f:
                            continue
                        if ordered_flight[d][f].p_d == g.p_a and ordered_flight[d][f].t_d -g.t_a >= LowerLimit_Combine:
                            if (g.time_fly + ordered_flight[d][f].t_a -ordered_flight[d][f].t_d) > MaxBlk:
                                continue
                            if (ordered_flight[d][f].t_a - g.t_d) > MaxDP:
                                continue
                            g.add_flight(ordered_flight[d][f])
                            alled_f.append(f)
                            ind_del_f.append(f)
                            if g.p_a in JIDI:
                                break

                # added_f = []
                # flag_xinhuilu = False
                # temp_g=copy.deepcopy(g)
                # for f in range(ind_del_f[-1], len(ordered_flight[d])):
                # if f in alled_f:
                # continue
                # if ordered_flight[d][f].p_d == temp_g.p_a and ordered_flight[d][
                # f].t_d - temp_g.t_a >= LowerLimit_Combine:
                # added_f.append(f)
                # temp_g.add_flight(ordered_flight[d][f])
                # # alled_f.append(f)
                # # ind_del_f.append(f)
                # if temp_g.p_a == g.p_a:
                # flag_xinhuilu=True
                # break
                # if flag_xinhuilu:
                # for f in added_f:
                # g.add_flight(ordered_flight[d][f])
                # alled_f.append(f)
                # ind_del_f.append(f)

                # print(ordered_flight[d][f].id)
                # for f in reversed(ind_del_f):
                # print(ordered_flight[d][f].id)
                # del ordered_flight[d][f]
                flag_1 = False
                flag_3 = False
                ### 先分配今天剩余没用的人 ###
                for p in self.pilots[1]:
                    if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine:
                        if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                            if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] - g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                p.add_group_first(g)
                                p.groups[d][0].set_type(1)
                                flag_1 = True
                                break
                        if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine and (p.time_fly[d]+g.time_fly<MaxBlk):
                            if (g.t_a-p.t_d_d[d]<=MaxDP):
                                p.add_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1 = True
                                break

                        if (not p.duty[d]):
                            if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                p.add_group(g)
                                p.groups[d][-1].set_type(1)
                                flag_1 = True
                                break
                for p in self.pilots[3]:
                    if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine:
                        if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                            if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] - g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                p.add_group_first(g)
                                p.groups[d][0].set_type(3)
                                flag_3 = True
                                break
                        if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine:
                            if (g.t_a - p.t_d_d[d] <= MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                p.add_group(g)
                                p.groups[d][-1].set_type(3)
                                flag_3 = True
                                break

                        if (not p.duty[d]):
                            if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                p.add_group(g)
                                p.groups[d][-1].set_type(3)
                                flag_3 = True
                                break
                        # p.add_group(g)
                        # p.groups[d][-1].set_type(3)
                        # flag_3 = True
                        # break
                if not flag_1:
                    for p in self.pilots[2]:
                        if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine:
                            if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                                if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] -g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                    p.add_group_first(g)
                                    p.groups[d][0].set_type(1)
                                    flag_1 = True
                                    break
                            if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine:
                                if (g.t_a - p.t_d_d[d] <= MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                    p.add_group(g)
                                    p.groups[d][-1].set_type(1)
                                    flag_1 = True
                                    break

                            if (not p.duty[d]):
                                if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                    p.add_group(g)
                                    p.groups[d][-1].set_type(1)
                                    flag_1 = True
                                    break
                            # p.add_group(g)
                            # p.groups[d][-1].set_type(1)
                            # flag_1 = True
                            # break
                if not flag_3:
                    for p in self.pilots[2]:
                        if p.p_a_d[d - 1] == g.p_d and g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine:
                            if p.p_a_d[d] == g.p_d and p.t_d_d[d] - g.t_a >= LowerLimit_Combine:
                                if g.t_d - p.t_a_d[d - 1] >= MinRest and (p.t_d_a[d] -g.t_d<=MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                    p.add_group_first(g)
                                    p.groups[d][0].set_type(3)
                                    flag_3 = True
                                    break
                            if p.p_d_d[d] == g.p_a and g.t_d - p.t_a_d[d] >= LowerLimit_Combine:
                                if (g.t_a - p.t_d_d[d] <= MaxDP) and (p.time_fly[d]+g.time_fly<MaxBlk):
                                    p.add_group(g)
                                    p.groups[d][-1].set_type(3)
                                    flag_3 = True
                                    break

                            if (not p.duty[d]):
                                if g.t_d - p.t_a_d[d - 1] >= MinRest:
                                    p.add_group(g)
                                    p.groups[d][-1].set_type(3)
                                    flag_3 = True
                                    break
                            # p.add_group(g)
                            # p.groups[d][-1].set_type(3)
                            # flag_3 = True
                            # break
                ### 选择前一天的航班乘机过来 ###
                if not (flag_1 and flag_3):
                    for f in self.map_t2f[d - 1]:
                        if f.p_d in JIDI and g.p_d == f.p_a and g.t_d - f.t_a >= LowerLimit_Combine:
                            if g.t_d - f.t_a < MinRest:
                                continue
                            if not flag_1:
                                for p in self.pilots[1]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and (not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        break
                            if not flag_3:
                                for p in self.pilots[3]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and (not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        break
                            if not flag_1:
                                for p in self.pilots[2]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and (not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(1)
                                        flag_1 = True
                                        break
                            if not flag_3:
                                for p in self.pilots[2]:
                                    if p.p_a_d[max(d - 2, 0)] == f.p_d and f.t_d - p.t_a_d[max(d - 2, 0)] >= LowerLimit_Combine and (not p.duty[d - 1]) and (not p.duty[d]):
                                        p.add_group(Group_Flight(f))
                                        p.groups[d - 1][-1].set_type(2)
                                        self.chengji = self.chengji + 1
                                        p.add_group(g)
                                        p.groups[d][-1].set_type(3)
                                        flag_3 = True
                                        break
                    ### 在同一天找前面后面各一驾航班 乘两次机 ###
                    temp_g = copy.deepcopy(g)
                    if not (flag_1 and flag_3):
                        flag_qian = False
                        flag_hou = False
                        for f in reversed(self.map_t2f[d]):
                            if f.p_d in JIDI and f.p_a == g.p_d and g.t_d - f.t_a >= LowerLimit_Combine:
                                temp_g.add_flight_first(f)
                                if temp_g.time_fly > MaxBlk:
                                    flag_qian = False
                                    break
                                if temp_g.t_a - temp_g.t_d > MaxDP:
                                    flag_qian = False
                                    break
                                flag_qian = True
                                break
                        if flag_qian:
                            for f in self.map_t2f[d]:
                                if f.p_a in JIDI and f.p_d == g.p_a and f.t_d - g.t_a >= LowerLimit_Combine:
                                    temp_g.add_flight(f)
                                    if temp_g.time_fly > MaxBlk:
                                        flag_hou = False
                                        break
                                    if temp_g.t_a - temp_g.t_d > MaxDP:
                                        flag_qian = False
                                        break
                                    flag_hou = True

                                    break
                        if flag_qian and flag_hou:
                            # flag_1 = False
                            # flag_3 = False
                            # print("99999999999999999999999999999999999999999999999999999999999999999999999999999999999")
                            for p in self.pilots[1]:
                                if temp_g.t_d - p.t_a_d[d - 1] < MinRest:
                                    continue
                                if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                    p.add_group(Group_Flight(temp_g.flights[0]))
                                    p.groups[d][-1].set_type(2)
                                    p.add_group(Group_Flight(temp_g.flights[1]))
                                    p.groups[d][-1].set_type(1)
                                    p.add_group(Group_Flight(temp_g.flights[2]))
                                    p.groups[d][-1].set_type(2)
                                    self.chengji = self.chengji + 2
                                    flag_1 = True
                                    break
                            for p in self.pilots[3]:
                                if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                    p.add_group(Group_Flight(temp_g.flights[0]))
                                    p.groups[d][-1].set_type(2)
                                    p.add_group(Group_Flight(temp_g.flights[1]))
                                    p.groups[d][-1].set_type(3)
                                    p.add_group(Group_Flight(temp_g.flights[2]))
                                    p.groups[d][-1].set_type(2)
                                    self.chengji = self.chengji + 2
                                    flag_3 = True
                                    break
                            if not flag_1:
                                for p in self.pilots[2]:
                                    if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                        p.add_group(Group_Flight(temp_g.flights[0]))
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(Group_Flight(temp_g.flights[1]))
                                        p.groups[d][-1].set_type(1)
                                        p.add_group(Group_Flight(temp_g.flights[2]))
                                        p.groups[d][-1].set_type(2)
                                        self.chengji = self.chengji + 2
                                        flag_1 = True
                                        break
                            if not flag_3:
                                for p in self.pilots[2]:
                                    if p.p_a_d[d - 1] == temp_g.p_d and temp_g.t_d - p.t_a_d[d - 1] >= LowerLimit_Combine and (not p.duty[d]):
                                        p.add_group(Group_Flight(temp_g.flights[0]))
                                        p.groups[d][-1].set_type(2)
                                        p.add_group(Group_Flight(temp_g.flights[1]))
                                        p.groups[d][-1].set_type(3)
                                        p.add_group(Group_Flight(temp_g.flights[2]))
                                        p.groups[d][-1].set_type(2)
                                        self.chengji = self.chengji + 2
                                        flag_3 = True
                                        break

                    if not (flag_1 and flag_3):
                        unallocated_g.append(g)
                        num_un = num_un + 1
                        for f in g.flights:
                            table_un = table_un.append({'FltNum': f.id, 'DptrT': f.t_d, 'ArrvT': f.t_a, "DrtrD": f.d_d},ignore_index=True)

                for p in self.pilots[1]:
                    if p.p_a_d[d - 1] is not p.jidi and (not p.duty[d]):
                        for f in self.map_t2f[d]:
                            if f.p_d == p.p_a_d[d - 1] and f.p_a == p.jidi:
                                p.add_group(Group_Flight(f))
                                p.groups[d][-1].set_type(2)
                                self.chengji = self.chengji + 1
                                print("111111111111111111111111111111111111111111")
                                break
        self.print_result_p3()

        table_un.to_csv("UncoveredFlights_p3_B.csv", index=False)
        print(num_un)
        print(f"{self.chengji} 乘機次數")
        print("第一天 duty 人数:", sum([p.duty[1] for p in self.pilots[1] + self.pilots[2] + self.pilots[3]]))
        list_unall=table_un["FltNum"].to_list()
        total_fly=0
        for d in range(1,NUM_D+1):
            for f in self.map_t2f[d]:
                if f.id not in list_unall:
                    total_fly=total_fly+(f.t_a-f.t_d)*2
        print("机组总体利用率: ", total_fly/self.total_zhiqin)

if __name__ == "__main__":
    start = time.time()
    # long running
    # do something other

    g = Greedy()
    g.tanlan_p2_B()
    end = time.time()
    print(end - start)
