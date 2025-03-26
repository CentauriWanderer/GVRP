from operator import itemgetter
from itertools import combinations
from copy import deepcopy

class MCWS(object):
    
    def __init__(self):
        self.__V = []
        self.__D = []
        self.__C = []
        self.__R = []
        self.__distances = {}
        self.__times = {}
        self.__service_times = {}
        self.__Speed = -1
        self.__Rate = -1
        self.__Level = -1
        self.__Tmax = -1
        self.__tours = []
        self.__tours_infis = []
        self.__spl = []
        self.__operation_count = 0
        self.__log = [[self.__operation_count, 'Class MCWS initialized']]
        
    def get_log(self):
        _str = ''
        for i in range(0, len(self.__log)):
            _str = _str + '# {a1}\n'.format(a1 = i)
            _str = _str + self.__log[i][1]
            _str = _str + '\n'
        return _str
    
    def add_log(self, _str):
        self.__operation_count = self.__operation_count + 1
        self.__log.append([self.__operation_count, _str])
    
    def set_vertices(self, v, labels, distances, time_s):
        assert len(v) == len(labels), 'List of vertices and labels must have same length!'
        for i in range(0, len(labels)):
            if labels[i] == 'd':
                self.__D.append(v[i])
            elif labels[i] == 'c':
                self.__C.append(v[i])
            elif labels[i] == 'r':
                self.__R.append(v[i])
        self.__V = v 
        self.__service_times = time_s
        self.__distances = distances
        self.__tours = [[0, i, 0] for i in self.__C]
            
        _str = 'Depot:\n{a1}\n'.format(a1 = self.__D)\
             + 'Customers:\n{a1}\n'.format(a1 = self.__C)\
             + 'Recharging stations:\n{a1}\n'.format(a1 = self.__R)\
             + 'Dictionary of distances:\n{a1}\n'.format(a1 = self.__distances)\
             + 'Dictionary of service times:\n{a1}\n'.format(a1 = self.__service_times)\
             + 'Initial tours generated:\n{a1}'.format(a1 = self.__tours)
        self.add_log(_str)
            
    def get_tours(self):
        return self.__tours
    
    def get_infeasible_tours(self):
        return self.__tours_infis
                
    def set_parameters(self, v, r, l, t):       
        self.__Speed = v
        self.__Rate = r
        self.__Level = l
        self.__Tmax = t
        self.__times = {i: (self.__distances[i] / v) for i in self.__distances.keys()}
        
        _str = 'Speed:\n{a1}\n'.format(a1 = self.__Speed)\
               + 'Battery consumption rate:\n{a1}\n'.format(a1 = self.__Rate)\
               + 'Battery full level:\n{a1}\n'.format(a1 = self.__Level)\
               + 'Maximum time:\n{a1}\n'.format(a1 = self.__Tmax)\
               + 'Dictionary of times:\n{a1}'.format(a1 = self.__times)
        self.add_log(_str)
        
    def get_tour_distance(self, tour):
        _distance = 0
        for i in range(0, len(tour) - 1):
            _distance = _distance + self.__distances[tuple(tour[i: i + 2])]
        return _distance
    
    def get_tour_time(self, tour):
        _time = 0
        for i in range(0, len(tour) - 1):
            _time = _time + self.__times[tuple(tour[i: i + 2])]
        for i in range(0, len(tour)):
            if tour[i] in self.__C or tour[i] in self.__R:
                _time = _time + self.__service_times[tour[i]]
        return _time
    
    def select_RS(self, p1, p2):
        if len(self.__R) == 0:
            return -1
        _costs = [self.__distances[(p1, r)] + self.__distances[(r, p2)] for r in self.__R]
        _r_min = self.__R[_costs.index(min(_costs))]
        return _r_min
    
    def spl_update(self):
        if len(self.__tours) == 1:       
            self.spl = []
        _adjvs = []
        for i in self.__tours:
            if len(i) == 3:
                _adjvs.append([i[1]])
            else:
                _adjvs.append([i[1], i[-2]])
        _savings = []
        for i in range(0, len(_adjvs)):
            for j in range(0, len(_adjvs)):
                if i != j:
                    for m in range(0, len(_adjvs[i])):
                        for n in range(0, len(_adjvs[j])):
                            _saving = self.__distances[(0, _adjvs[i][m])] + self.__distances[(0, _adjvs[j][n])]\
                                      - self.__distances[(_adjvs[i][m], _adjvs[j][n])]
                            if _saving > 0:
                                _savings.append([i, int(-3 * m + 1), j, int(-3 * n + 1), _saving]) # 0->1 1->-2
        for i in _savings:
            for j in _savings:
                if (i[0: 2], i[2: 4]) == (j[2: 4], j[0: 2]):
                    _savings.remove(j)
        _savings = sorted(_savings, key = itemgetter(4), reverse = True)
        self.__spl = _savings
    
    def get_spl(self):
        return self.__spl
    
    def validate_tour(self, tour):  
        _list_rs = [i for i in tour if i in self.__R]
        _flag = True
        _l = self.__Level
        for i in range(0, len(tour) - 1):
            _l = _l - self.__Rate * self.__distances[(tour[i], tour[i + 1])]
            if _l < 0:
                _flag = False
                break
            if tour[i + 1] in self.__R:
                _l = self.__Level
        return _flag
    
    def remove_redundant_RS(self, tour):
        _tour_best = tour
        _list_irs = [] 
        for i in range(0, len(tour)):
            if tour[i] in self.__R:
                _list_irs.append(i)
        if len(_list_irs) > 1:
            _dist_min = 9999999
            for i in range(1, len(_list_irs) + 1):
                for j in combinations(_list_irs, i): 
                    _tour_temp = []
                    for k in range(0, len(tour)):
                        if k not in j:
                            _tour_temp.append(tour[k])
                    if self.validate_tour(_tour_temp):
                        _dist_new = self.get_tour_distance(_tour_temp)
                        if _dist_new < _dist_min:
                            _dist_min = _dist_new
                            _tour_best = _tour_temp
        return _tour_best
    
    def merge_tours(self, sp):
        _index_tour1 = sp[0]
        _index_tour2 = sp[2]
        _index_p1 = sp[1]
        _index_p2 = sp[3]
        _tour1 = self.__tours[_index_tour1]
        _tour2 = self.__tours[_index_tour2]
        if _index_p1 == 1:
            _tour1.reverse()
        if _index_p2 == -2:
            _tour2.reverse()
        _tour_new = [0] + _tour1[1: -1] + _tour2[1: -1] + [0]
        _index_merge = len(_tour1) - 1
        return (_tour_new, _index_merge)
    
    def check_initial_tours(self):
        _str = '************** Checking initial tours for feasibility **************'
        _feasible_tours = []
        for i in self.__tours:
            if self.get_tour_time(i) > self.__Tmax:
                self.__tours_infis.append(i)
                _str = _str + '\nTour {a1} infeasible in time\n-'.format(a1 = i)
            elif self.validate_tour(i) == False:
                _str = _str + '\nTour {a1} infeasible in battery-level, trying RS insertion:\n'.format(a1 = i)
                _rs = self.select_RS(0, i[1])
                if _rs == -1:
                    self.__tours_infis.append(i)
                    _str = _str + 'No RS for insertion, tour infeasible\n-'
                else:
                    _tour_new = [i[0]] + [_rs] + [i[1]] + [_rs] + [i[2]]
                    _tour_new = self.remove_redundant_RS(_tour_new)
                    if self.get_tour_time(_tour_new) > self.__Tmax:
                        self.__tours_infis.append(i)
                        _str = _str + 'RS insertion not possible in time, tour infeasible\n-'
                    else:
                        if self.validate_tour(_tour_new):
                            _feasible_tours.append(_tour_new)
                            _str = _str + '{a1} --> {a2}\n-'.format(a1 = i, a2 = _tour_new)
                        else:
                            self.__tours_infis.append(i)
                            _str = _str + 'Tour still infeasible after trying RS insertion\n-'
            else:
                _feasible_tours.append(i)
        self.__tours = _feasible_tours
        _str = _str + '\nFeasible tours:\n{a1}\nInfeasible tours:\n{a2}'.format(a1 = self.__tours, a2 = self.__tours_infis)
        self.add_log(_str)
    
    def itve(self):
        _list_excs = []
        for i in range(0, len(self.__tours)):
            for j in range(0, len(self.__tours)):
                if i != j:
                    for m in range(1, len(self.__tours[i]) - 1):
                        for n in range(1, len(self.__tours[j]) - 1):
                            _list_excs.append([(i, m), (j, n)])
        for i in _list_excs:
            for j in _list_excs:
                if (i[0], i[1]) == (j[1], j[0]):
                    _list_excs.remove(j)
        _dist_min = 0
        for i in range(0, len(self.__tours)):
            _dist_min = _dist_min + self.get_tour_distance(self.__tours[i])
        _tours_best = deepcopy(self.__tours)
        for i in _list_excs:
            _tours_new = deepcopy(self.__tours)
            _temp = _tours_new[i[0][0]][i[0][1]]
            _tours_new[i[0][0]][i[0][1]] = _tours_new[i[1][0]][i[1][1]]
            _tours_new[i[1][0]][i[1][1]] = _temp
            _tours_new[i[0][0]] = self.remove_redundant_RS(_tours_new[i[0][0]])
            _tours_new[i[1][0]] = self.remove_redundant_RS(_tours_new[i[1][0]])
            _dist_new = 0
            for l in range(0, len(_tours_new)):
                if self.validate_tour(_tours_new[l]):
                    _dist_new = _dist_new + self.get_tour_distance(_tours_new[l])
                else:
                    _dist_new = _dist_new + 9999999                  
            if _dist_new < _dist_min:
                _str = 'Exchange applied: {a1}\n'.format(a1 = j)
                _str = _str + 'Total travel distance reduced from {a1} to {a2}\n-'.format(a1 = _dist_min, a2 = _dist_new)
                self.add_log(_str)
                _dist_min = _dist_new
                _tours_best = _tours_new    
        self.__tours = _tours_best
        
    def wtvir(self):
        for i in self.__tours:
            _tour_old = deepcopy(i)
            _tour_best = deepcopy(i)
            for j in range(1, len(i) - 1):
                for k in range(1, len(i) - 1):
                    if j != k:
                        _tour_new = deepcopy(i)
                        _temp = _tour_new[j]
                        _tour_new[j] = _tour_new[k]
                        _tour_new[k] = _temp
                        _tour_new = self.remove_redundant_RS(_tour_new)
                        if self.validate_tour(_tour_new):
                            if self.get_tour_distance(_tour_new) < self.get_tour_distance(_tour_best):
                                _tour_best = _tour_new
            if self.get_tour_distance(_tour_best) < self.get_tour_distance(_tour_old):
                self.__tours.remove(_tour_old)
                self.__tours.append(_tour_best)
                _str = 'Vertex interchange {a1} --> {a2}\n'.format(a1 = _tour_old, a2 = _tour_best)
                _str = _str + 'Tour distance reduced from {a1} to {a2}\n-'.format(a1 = self.get_tour_distance(_tour_old), a2 = self.get_tour_distance(_tour_best))
                self.add_log(_str)
    
    def get_total_distance(self):
        _distance = 0
        for i in self.__tours:
            _distance = _distance + self.get_tour_distance(i)
        return _distance
    
    def get_total_time(self):
        _time = 0
        for i in self.__tours:
            _time = _time + self.get_tour_time(i)
        return _time
    
    def run(self):
        
        self.check_initial_tours()
        self.spl_update()

        _index_SPL = 0
        self.add_log('************** Main part starts **************')
        while len(self.__spl) != 0 and _index_SPL != len(self.__spl):
            _sp = self.__spl[_index_SPL]
            _tour_old1 = self.__tours[_sp[0]]
            _tour_old2 = self.__tours[_sp[2]]
            _str = 'Trying to apply SP:\n{a1} in {a2}, {a3} in {a4}:\n'.format(\
                a1 = _tour_old1[_sp[1]], a2 = _tour_old1, a3 = _tour_old2[_sp[3]], a4 = _tour_old2)
            (_tour_new, _index_merge) = self.merge_tours(_sp)
            _tour_new = self.remove_redundant_RS(_tour_new)
            if self.get_tour_time(_tour_new) > self.__Tmax:
                _index_SPL = _index_SPL + 1
                _str = _str + 'Maximum duration exceeded!\n-'
                self.add_log(_str)
                continue
            if self.validate_tour(_tour_new) == False:
                _str = _str + 'Battery-level constraint violated, trying RS insertion in: {a1}\n'.format(a1 = _tour_new)
                _rs = self.select_RS(_tour_old1[_sp[1]], _tour_old2[_sp[3]])
                if _rs == -1:
                    _index_SPL = _index_SPL + 1
                    _str = _str + 'No RS for insertion!\n-'
                    self.add_log(_str)
                    continue
                _tour_new.insert(_index_merge, _rs)
                _tour_new = self.remove_redundant_RS(_tour_new)
                if self.validate_tour(_tour_new) == False:
                    _index_SPL = _index_SPL + 1
                    _str = _str + 'RS insertion not possible!\n-'
                    self.add_log(_str)
                    continue
                if self.get_tour_time(_tour_new) > self.__Tmax:
                    _index_SPL = _index_SPL + 1
                    _str = _str + 'RS insertion not possible in time!\n-'
                    self.add_log(_str)
                    continue
                '''
                if self.get_tour_time(_tour_new) >= self.get_tour_time(_tour_old1) + self.get_tour_time(_tour_old2):
                    _index_SPL = _index_SPL + 1
                    _str = _str + 'Tour merging not worthy in time after RS insertion!\n-'
                    self.add_log(_str)
                    continue
                '''
                if self.get_tour_distance(_tour_new) >= self.get_tour_distance(_tour_old1) + self.get_tour_distance(_tour_old2):
                    _index_SPL = _index_SPL + 1
                    _str = _str + 'Tour merging not worthy in distance after RS insertion!\n-'
                    self.add_log(_str)
                    continue
            self.__tours.remove(_tour_old1)
            self.__tours.remove(_tour_old2)
            self.__tours.append(_tour_new)
            _str = _str + '{a1} + {a2} = {a3}\n-'.format(a1 = _tour_old1, a2 = _tour_old2, a3 = _tour_new)
            self.add_log(_str)
            self.spl_update()
            _index_SPL = 0
        self.add_log('************** Main part ends **************\nTours:\n{a1}'.format(a1 = self.__tours))
        
        self.add_log('************** Improvement heuristics start **************')
        self.itve()
        self.itve()
        self.itve()
        self.itve()
        self.itve()
        self.itve()
        _str = '************** Tours after itve **************\n{a1}'.format(a1 = self.__tours)
        self.add_log(_str)
        
        self.wtvir()
        self.wtvir()
        self.wtvir()
        self.wtvir()
        self.wtvir()
        self.wtvir()
        _str = '************** Tours after wtvir **************\n{a1}'.format(a1 = self.__tours)
        self.add_log(_str)
        _str = '************** Program ends **************'
        self.add_log(_str)