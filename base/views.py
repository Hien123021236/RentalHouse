from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
import pickle
import pandas as pd
from pandas.core.frame import DataFrame
from base import data
import numpy as np
from django.core import serializers
import json

# Create your views here.

class Data():
    df = pd.DataFrame()
    mean = pd.DataFrame()
    source = pd.DataFrame()
    source_sc = pd.DataFrame()
    options_floor = []
    options_age = []
    @staticmethod
    def Init():
        houses_dict_sc = pickle.load(open('base/data/house_dict.pkl' , 'rb'))
        houses_dict = pickle.load(open('base/data/house.pkl' , 'rb'))
        houses_sc = pd.DataFrame(houses_dict_sc)
        houses = pd.DataFrame(houses_dict)
        Data.df = houses_sc.copy()
        Data.source =  houses.copy()

def recommender(data):
    mean = data.mean()
    print("mean")
    print(mean)
    std = data.std()
    print("std")
    print(std)
    array = []
    
    for i, item in data.iterrows():
        check_unit_floor = np.abs(item['unit_floor'] - mean['unit_floor']) <= std['unit_floor'] 
        check_property_age = np.abs(item['property_age'] - mean['property_age']) <= std['property_age'] 
        if (check_unit_floor) & (check_property_age):
            array.append(item)
    
    new_data = pd.DataFrame(array.copy())

    if(len(new_data.index) < 4):
        return new_data , True , None , None , None
    else:
        print("Tap muc tieu")
        print(new_data)
        r, c = new_data.shape
        print(r,c)
        unit_floor_max = mean['unit_floor']
        unit_floor_min = mean['unit_floor']
        property_age_max = mean['property_age']
        property_age_min = mean['property_age']
        
        unit_floor_max_point = None
        unit_floor_min_point = None
        property_age_max_point = None
        property_age_min_point = None
        
        
        
        for i,item in new_data.iterrows():
            item['index'] = i
            #get diem bien cua unit_floor
            if ((item['unit_floor'] - mean['unit_floor'] > 0) & (item['unit_floor'] > unit_floor_max)):
                unit_floor_max = item['unit_floor']

            if ((item['unit_floor'] - mean['unit_floor'] < 0) & (item['unit_floor'] < unit_floor_min)):
                unit_floor_min = item['unit_floor']

                    
            #get diem bien cua property_age
            if ((item['property_age'] - mean['property_age'] > 0) & (item['property_age'] > property_age_max)):
                property_age_max = item['property_age']

            if ((item['property_age'] - mean['property_age'] < 0) & (item['property_age'] < property_age_min)):
                property_age_min = item['property_age']

        unit_floor_max_dis_min = float('inf')
        unit_floor_min_dis_min = float('inf')
        property_age_max_dis_min = float('inf')
        property_age_min_dis_min = float('inf')
        
        for i,item in new_data.iterrows():
            unit_floor_max_dis = np.sqrt(np.square(item['unit_floor'] - unit_floor_max) + np.square(item['property_age'] - mean['property_age']))
            if( unit_floor_max_dis < unit_floor_max_dis_min):
                unit_floor_max_dis_min = unit_floor_max_dis
                unit_floor_max_point = new_data.loc[[i]]           
        new_data.drop(unit_floor_max_point.index[0],inplace = True)
        
                
        for i,item in new_data.iterrows():
            unit_floor_min_dis = np.sqrt(np.square(item['unit_floor'] - unit_floor_min)  + np.square(item['property_age'] - mean['property_age']))
            if( unit_floor_min_dis < unit_floor_min_dis_min):
                unit_floor_min_dis_min = unit_floor_min_dis
                unit_floor_min_point = new_data.loc[[i]]
        new_data.drop(unit_floor_min_point.index[0],inplace = True)
            
        for i,item in new_data.iterrows():
            property_age_max_dis = np.sqrt(np.square(item['property_age'] - property_age_max)  + np.square(item['unit_floor'] - mean['unit_floor']))
            if( property_age_max_dis < property_age_max_dis_min):
                property_age_max_dis_min = property_age_max_dis
                property_age_max_point = new_data.loc[[i]]
        new_data.drop(property_age_max_point.index[0],inplace = True)
            
        for i,item in new_data.iterrows():
            property_age_min_dis = np.sqrt(np.square(item['property_age'] - property_age_min)  + np.square(item['unit_floor'] - mean['unit_floor']))
            if( property_age_min_dis < property_age_min_dis_min):
                property_age_min_dis_min = property_age_min_dis
                property_age_min_point = new_data.loc[[i]]
        new_data.drop(property_age_min_point.index[0],inplace = True)   
            
        option_unit_floor = [unit_floor_max_point,unit_floor_min_point]
        option_property_age = [property_age_max_point,property_age_min_point]
            
        return data , False ,option_unit_floor ,option_property_age ,mean

def UnSelectPoint(data ,mean, unselect_unit_floor_point,unselect_property_age_point):
   
    new_data = data.copy()
    print(data)
    print(mean)
    print(unselect_unit_floor_point)
    print(unselect_property_age_point)
    
    #loai 2 diem bien
    new_data.drop(unselect_unit_floor_point.index[0],inplace = True)
    new_data.drop(unselect_property_age_point.index[0],inplace = True)
    
    p1 = unselect_unit_floor_point.iloc[0]
    p2 = unselect_property_age_point.iloc[0]

    # viet pt duong thang
    if((p1['unit_floor'] - p2['unit_floor']) != 0 ):
        a = (p1['property_age'] - p2['property_age'])/(p1['unit_floor'] - p2['unit_floor'])
        b = p1['property_age'] - a*(p1['unit_floor'])
        K = a*mean['unit_floor']+b -mean['property_age']
    
    else:
        return new_data
        
    for i,item in new_data.iterrows():
        f = a*item['unit_floor'] + b - item['property_age']
        #x duong , y am
        if(((item['unit_floor'] >= p2['unit_floor']) & (item['property_age'] <= p1['property_age'])) & (f*K <= 0)):
            new_data =  new_data.drop(i)
        #x duong ,y duong    
        elif(((item['unit_floor'] >= p2['unit_floor']) & (item['property_age'] >= p1['property_age'])) & (f*K <= 0) ):
            new_data =  new_data.drop(i)
            
        #x am , y duong
        elif(((item['unit_floor'] <= p2['unit_floor']) & (item['property_age'] >= p1['property_age'])) & (f*K <= 0) ):
            new_data =  new_data.drop(i)
        
        #x am y am
        elif(((item['unit_floor'] <= p2['unit_floor']) & (item['property_age'] <= p1['property_age'])) & (f*K <= 0)):
            new_data =  new_data.drop(i)
    
    return new_data

def ajaxrecommender(request):
    Data.df ,completed , option_unit_floor ,option_property_age ,mean = recommender(Data.df)
    Data.mean = mean
    Data.options_floor = option_unit_floor
    Data.options_age = option_property_age

    floor0 = option_unit_floor[0].copy()
    floor1 = option_unit_floor[1].copy()
    age0 = option_property_age[0].copy()
    age1 = option_property_age[1].copy()
    
    floor0.loc[(floor0[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    floor1.loc[(floor1[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    age0.loc[(age0[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    age1.loc[(age1[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]

    return JsonResponse({
        'completed' :completed,
        'floor':[
            floor0.to_json(),
            floor1.to_json()
            ],
        'age':[
            age0.to_json(), 
            age1.to_json()
            ]
    })

def ajaxunselectpoint(request):
    floor = int(request.POST['floor'])
    age = int(request.POST['age'])
    new_df = UnSelectPoint(Data.df, Data.mean, Data.options_floor[floor],  Data.options_age[age])
    Data.df = new_df
    Data.df ,completed , option_unit_floor ,option_property_age ,mean = recommender(Data.df)
    Data.mean = mean
    Data.options_floor = option_unit_floor
    Data.options_age = option_property_age
    

    floor0 = None if option_unit_floor is None else option_unit_floor[0].copy() 
    floor1 = None if option_unit_floor is None else option_unit_floor[1].copy() 
    age0 = None if option_property_age is None else option_property_age[0].copy() 
    age1 = None if option_property_age is None else option_property_age[1].copy() 

    data = pd.DataFrame(Data.df.copy())
    data.loc[(data[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    
    if floor0 is not None:
        floor0.loc[(floor0[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    if floor1 is not None:
        floor1.loc[(floor1[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    if age0 is not None:
        age0.loc[(age0[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    if age1 is not None:
        age1.loc[(age1[:].index).isin(Data.source[:].index), ['unit_floor', 'property_age']] = Data.source[['unit_floor', 'property_age']]
    
    if(completed == True):
        return JsonResponse({
            'completed' :completed,
            'data' : data.to_html()         
        })
    else:    
        return JsonResponse({
        'completed' :completed,
        'floor':[
            floor0.to_json(),
            floor1.to_json()
            ],
        'age':[
            age0.to_json(), 
            age1.to_json()
            ]
        })



def index(request):
    context = {'data':Data.df}
    return render(request,'base/index.html',context)


def init(request):
    Data.Init()
    context = {'data':Data.df}
    return render(request,'base/init.html',context)
