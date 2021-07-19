#! /usr/bin/env python

import configparser
import os,sys
import time
from GetItems import Zabbix
from SaveToExcel  import WriteExcel
import datetime

path = os.path.dirname(os.path.abspath(__file__))
sys.intern(path)


if __name__ == "__main__":
    print("start".center(60,"*"))
    print("zabbix统计机器资源使用情况".center(60))
    config = configparser.ConfigParser()
    config.read(os.path.join(os.getcwd(), 'config.ini'), encoding='utf-8')
    # 实例化一个zabbix对象
    #api调用地址
    zabbix_api='http://10.190.5.237/api_jsonrpc.php'
    zabbix_user=input("请输入您zabbix的账号：")
    zabbix_passwd=input('请输入您zabbix的密码：')
    file_name='服务器资源使用情况分析'
    zabbix =  Zabbix(
        zabbix_api,
        zabbix_user,
        zabbix_passwd
    )
    starttime = datetime.datetime.now()
    # 调用GetItemValue方法获取每台监控主机的监控数据
    zabbix_data = zabbix.GetItemValue()
    if len(zabbix_data) == 2:
        print(zabbix_data['errmsg'])
        print("end".center(60, "*"))
    else:
        date_time = time.strftime('%Y-%m-%d_%H-%M')
        #print(zabbix_data)
        file_name = os.path.join(os.getcwd(), file_name + date_time + '.xlsx')
        WriteExcel(file_name, zabbix_data)
        endtime = datetime.datetime.now()
        run_time=endtime - starttime
        print(f"程序运行：{run_time.seconds} s  生成文件：{file_name}")
        print("end".center(60, "*"))