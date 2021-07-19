#! /usr/bin/env python
# _*_ coding: utf-8 _*_

# @Desc   :调用zabbix api接口，获取监控数据，zabbix-版本为5.0以上


import requests
import json
import re

class Zabbix(object):
    def __init__(self, ApiUrl, User, Pwd):
        self.ApiUrl = ApiUrl
        self.User = User
        self.Pwd = Pwd
        self.__Headers = {
            'Content-Type': 'application/json-rpc',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'
        }
        self.Message = {
            1001: {"errcode": "1001", "errmsg": "请求路径错误，请检查API接口路径是否正确."},
            1002: {"errcode": "1002", "errmsg": "Login name or password is incorrect."},
            1003: {"errcode": "1003", "errmsg": "未获取到监控主机，请检查server端是否监控有主机."},
            1004: {"errcode": "1004", "errmsg": "未知错误."},
        }


    def __Login(self):
        '''
        登陆zabbix，获取认证的秘钥
        Returns: 返回认证秘钥

        '''
        # 登陆zabbix,接口的请求数据
        LoginApiData = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": self.User,
                "password": self.Pwd
            },
            "id": 1
        }
        # 向登陆接口发送post请求，获取result
        LoginRet = requests.post(url=self.ApiUrl, data=json.dumps(LoginApiData), headers=self.__Headers)
        # 判断请求是否为200
        if LoginRet.status_code is not 200:
            return 1001
        else:
            # 如果是200状态，则进行数据格式化
            try:
                LoginRet = LoginRet.json()
            except:
                return 1001
            # 如果result在返回数据中，那么表示请求成功，则获取认证key
            if 'result' in LoginRet:
                Result = LoginRet['result']
                return Result
            # 否则返回用户或密码错误
            else:
                return 1002


    def __GetMonitorHost(self):
        # 调用登陆函数，获取auth，并判断是否登陆成功
        Auth = self.__Login()
        if Auth == 1001:
            return 1001
        elif Auth == 1002:
            return 1002
        else:
            HostApiData = {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": ["hostid", "host", "name"],
                    "selectInterfaces": ["interfaces", "ip"],
                },
                "auth": Auth,
                "id": 1
            }
            # 向host.get接口发起请求，获取所有监控主机
            HostRet = requests.post(url=self.ApiUrl, data=json.dumps(HostApiData), headers=self.__Headers).json()

            if 'result' in HostRet:
                if len(HostRet['result']) != 0:
                    # 循环处理每一条记录，进行结构化,最终将所有主机加入到all_host字典中
                    Allhost = {}
                    for host in HostRet['result']:
                        # host = {'hostid': '10331', 'host': '172.24.125.24', 'name': 'TBDS测试版172.24.125.24', 'interfaces': [{'ip': '172.24.125.24'}]}
                        # 进行结构化，提取需要的信息
                        HostInfo = {'host': host['host'], 'hostid': host['hostid'], 'ip': host['interfaces'][0]['ip'],
                                     'name': host['name']}
                        # host_info = {'host': '172.24.125.24', 'hostid': '10331', 'ip': '172.24.125.24', 'name': 'TBDS测试版172.24.125.24'}
                        # 加入到all_host中
                        Allhost[host['hostid']] = HostInfo
                    #print(Allhost)主机结构化列表
                    return {"Auth":Auth, "Allhost":Allhost}
                else:
                    return 1003
            else:
                return 1001


    def GetItemValue(self):
        '''
        # 调用item.get接口，获取监控项（监控项中带有每个监控项的最新监控数据） 接口说明文档：https://www.zabbix.com/documentation/4.0/zh/manual/api/reference/item/get
        Returns: 返回所有监控主机监控信息，
        '''
        # 获取所有的主机
        HostRet = self.__GetMonitorHost()
        # 判断HostRet是否有主机和认证key存在，这里如果是类型如果是字段，那边表示一定获取到的有主机信息，如果不是，则表示没有获取到值

        if type(HostRet) is dict:
            # 首先拿到认证文件和所有主机信息
            Auth, AllHost = HostRet['Auth'], HostRet['Allhost']
            # 定义一个新的allhost，存放所有主机新的信息
            NewAllHost = {}
            # 循环向每个主机发起请求，获取监控项的值
            for k in AllHost:
                ItemData = {
                    "jsonrpc": "2.0",
                    "method": "item.get",
                    "params": {
                        "output": ["extend", "name", "key_", "lastvalue"],
                        "hostids": str(k),
                        "search": {
                            "key_":
                                [
                                    "system.hostname",    # 主机名
                                    "system.uptime",      # 系统开机时长
                                    "io.usedgen[*]",        # 根目录使用率监控
                                    "disk_capacity.[disk_all_Usage]",#服务器总使用率
                                    "system.cpu.util",    # cpu使用率
                                    "system.cpu.num",     # cpu核数
                                    "system.cpu.load",    # cpu平均负载
                                    "system.cpu.util[,idle]",     # cpu空闲时间
                                    "vm.memory.utilization",      # 内存使用率
                                    "vm.memory.size[total]",      # 内存总大小
                                    "vm.memory.size[available]",  # 可用内存
                                    "net.if.in",  # 网卡每秒流入的比特(bit)数
                                    "net.if.out"  # 网卡每秒流出的比特(bit)数
                                ]
                        },
                        "searchByAny": "true",
                        "sortfield": "name"
                    },
                    "auth": Auth,
                    "id": 1
                }
                # 向每一台主机发起请求，获取监控项
                Ret = requests.post(url=self.ApiUrl, data=json.dumps(ItemData), headers=self.__Headers).json()
                #print(Ret)
                if 'result' in Ret:
                    # 判断每台主机是否有获取到监控项，如果不等于0表示获取到有监控项
                    if len(Ret['result']) != 0:
                        # 从所有主机信息中取出目前获取信息的这台主机信息存在host_info中
                        HostInfo = AllHost[k]
                        #{'host': 'Zabbix server', 'hostid': '10084', 'ip': '127.0.0.1', 'name': 'Zabbix server'}
                        # 循环处理每一台主机的所有监控项
                        #print(HostInfo)
                        for host in Ret['result']:
                            #print(str(host.values()))
                            # 匹配所有分区挂载目录使用率的正则表达式
                            DiskUtilization = re.findall(r'根目录使用率监控', str(host.values()))
                            #print(DiskUtilization)
                            if len(DiskUtilization) == 1:   #如果匹配到了分区目录，进行保存
                                HostInfo[host['name']] = host['lastvalue']

                            # 匹配网卡进出流量的正则表达式
                            NetworkBits = re.findall(r'Interface.*: Bits [a-z]{4,8}', str(host.values()))
                            #print(host.values())
                            if  len(NetworkBits) == 1:
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'System name' in host.values():      # 匹配主机名，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'System uptime' in host.values():  # 匹配系统开机运行时长，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'Number of CPUs' in host.values(): # 匹配CPU核数，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'Total memory' in host.values():   # 匹配内存总大小，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif '/: Total space' in host.values(): # 匹配根目录总量，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif '/: Used space' in host.values():  # 匹配根目录使用量，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif '/: Space utilization' in host.values():  # 匹配根目录使用量，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'Load average (1m avg)' in host.values():  # 匹配CPU平均1分钟负载，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'Load average (5m avg)' in host.values():  # 匹配CPU平均5分钟负载，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'Load average (15m avg)' in host.values():  # 匹配CPU平均15分钟负载，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'idle time' in host.values():  # 匹配CPU空闲时间，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'CPU utilization' in host.values(): # 匹配CPU使用率，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'Memory utilization' in host.values(): # 匹配内存使用率，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif 'Available memory' in host.values():   # 匹配可用内存大小，进行保存
                                HostInfo[host['name']] = host['lastvalue']
                            elif '服务器硬盘总使用率' in host.values():
                                HostInfo[host['name']] = host['lastvalue']
                        #print(HostInfo)
                        NewAllHost[HostInfo['hostid']] = HostInfo
                        #print(NewAllHost)
                else:
                    return {"errcode": "1001", "errmess": "Login name or password is incorrect."}
            return NewAllHost
            #print(NewAllHost)

        elif HostRet == 1001:
            return self.Message[1001]
        elif HostRet == 1002:
            return self.Message[1002]
        elif HostRet == 1003:
            return self.Message[1003]
        else:
            return self.Message[1004]
