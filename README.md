# zabbix-api
zabbix调用api查询机器资源利用率，导出execl表格



![](F:\GitHub\zabbix-api\images\1626699560279.png)

最后面添加是否低负载机器

判断条件：CPU平均负载/15min >= 10 or CPU使用率 >=20

```python
if host['Number of CPUs'] == "0":
	HostItemValues.append("已停用")
if  float(host['Load average (15m avg)']) >= 10 or  float(round(float(host['CPU utilization']), 2)) >= 20 :
	HostItemValues.append("否")
else:
	HostItemValues.append("是")
```





## Zabbix-api_v1

Zabbix-api_v1版本是初级版本，需要Python环境下操作



## Zabbix-api_v2

Zabbix-api_v2版本可以打包成exe程序，可以方便执行，不需要依赖













