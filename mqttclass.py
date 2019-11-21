#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Date: 2019/11/21
# @Author: Tigerots



import base64
import hashlib
import hmac
import random
import string
import time
import sys


'''
1. 登录 物联网通信控制台。您可在控制台创建产品、添加设备、并获取设备密钥。
2. 按照物联网通信约束生成 username 字段，username 字段格式如下：

    username字段的格式为： ${productid}${devicename};${sdkappid};${connid};${expiry}
        注意：${}表示变量，并非特定的拼接符号。
        
    其中各字段含义如下：
        productid：产品 ID。
        devicename： 设备名称。
        sdkappid：固定填12010126。
        connid ：一个随机字符串。
        过期时间 ：表示签名的有效期， 从1970年1月1日00:00:00 UTC 时间至今秒数的 UTF8 字符串。
        
3. 用 base64 对设备私钥进行解码得到原始密钥 raw_key。
4. 用第3步生成的 raw_key，通过 HMAC-SHA1 或者 HMAC-SHA256 算法对 username 生成一串摘要，简称 token。
5. 按照物联网通信约束生成 password 字段，password 字段格式为：
        
    password字段格式为： ${token};hmac签名方法
        其中hmac签名方法字段填写第三步用到的摘要算法，可选的值有 hmacsha256 和 hmacsha1

6. 最终将上面生成的参数填入对应的 mqtt connect 报文中。
    将 clientid 填入到 MQTT 协议的 clientid 字段。
    将 username 填入到 mqtt 的 username 字段。
    将 password 填入到 mqtt 的 password 字段，即可接入到物联云通信平台。
    
    通过 psk 方式接入端口默认为1883。若客户端支持 ca 证书，您也可以使用8883端口接入。
'''



# 生成指定长度的随机字符串
def RandomConnid(length):
    msg = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    return msg

# 生成接入物联云需要的各参数
def IotHmac_tos(productID, devicename, devicePsk):
    # 1. 生成connid为一个随机字符串,方便后台定位问题
    connid = RandomConnid(5)

    # 2. 生成过期时间,表示签名的过期时间,从纪元1970年1月1日 00:00:00 UTC 时间至今秒数的 UTF8 字符串
    expiry = int(time.time()) + 60*60

    # 3. 生成MQTT的clientid部分, 格式为${productid}${devicename}
    clientid = "{}{}".format(productID, devicename)

    # 4. 生成mqtt的username部分, 格式为${clientid};${sdkappid};${connid};${expiry}
    username = "{};12010126;{};{}".format(clientid, connid, expiry)

    # 5. 对username进行签名,生成token
    # 此处为Python3 的写法, 需要进行类型转换
    psk_b = base64.b64decode(devicePsk.encode('utf-8'))# 解码后为二进制串
    psk1 = str(psk_b,"utf-8")# 按utf8编码成字符串
    token = hmac.new( bytes(psk1, 'utf-8'), bytes(username, 'utf-8'), digestmod=hashlib.sha256).hexdigest()# 转换成utf-8的字节串
    # 此处为Python2 的写法, Python2 隐式转换了数据编码
    # token = hmac.new(devicePsk.decode("base64"), username, digestmod=hashlib.sha256).hexdigest()

    # 6. 根据物联云通信平台规则生成password字段
    password = "{};{}".format(token, "hmacsha256")
    return {
        "clientid": clientid,
        "username": username,
        "password": password
    }
    pass

import paho.mqtt.client as mqtt
# 腾讯云MQTT客户端信息结构
class TosMqttClientInfo(object):
    def __init__(self, productID, devicename, devicePsk):
        self.productID = productID
        self.devicename = devicename
        self.devicePsk = devicePsk
        self.iotsite = '{}.iotcloud.tencentdevices.com'.format(productID)

    def set_ProInfo(self, productID, devicename, devicePsk):
        self.productID = productID
        self.devicename = devicename
        self.devicePsk = devicePsk

    def psk_decode(self):
        # base64解码工具
        code_base64 = base64.b64decode(self.devicePsk.encode('utf-8'))
        # print(code_base64)
        return code_base64

    def get_IotHmac_tos(self):
        # 产生登录用信息
        IotHmac_tos_list = IotHmac_tos(self.productID, self.devicename, self.devicePsk)
        # print(IotHmac_tos_list)
        return IotHmac_tos_list



# MQTT客户端类
class MqttClient_Struct(TosMqttClientInfo):
    def __init__(self, productID, devicename, devicePsk):
        super(MqttClient_Struct,self).__init__(productID, devicename, devicePsk)
        # 密钥认证为1883, 证书认证为8883
        self.port = 1883
        # 云地址为 productID.iotcloud.tencentdevices.com
        self.host = self.iotsite
        # 生成客户端连接信息
        self.client_dict = self.get_IotHmac_tos()
        # 创建客户端
        self.client = mqtt.Client(self.client_dict['clientid'])
        # 设置用户名密码
        self.client.username_pw_set(self.client_dict.get('username'), self.client_dict.get('password'))

        # 定义回调函数
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        pass

    def connect(self):
        self.client.connect(self.host, self.port, 60)
        self.client.subscribe("HRDQBHLDHS/TaxiLed_Dev_002/data")  # 订阅
        self.client.subscribe("HRDQBHLDHS/TaxiLed_Dev_002/control")  # 订阅
        self.client.loop_forever()


    '''
    HRDQBHLDHS/TaxiLed_Dev_002/control    订阅
    HRDQBHLDHS/TaxiLed_Dev_002/data       订阅和发布
    HRDQBHLDHS/TaxiLed_Dev_002/event      发布
    '''

    # MQTT连接服务器
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))  # 打印连接状态
        pass
    # 生产环境: 报文读取,消息处理,超时请求,心跳包,重连管理
    def on_message(client, userdata, msg):
        print(msg.topic + " " + ":" + str(msg.payload))  # 打印接受的消息
        pass
    # 发布消息
    def publish(self):
        pass
    # 订阅主题
    def subscribe(self):
        pass
    # 取消订阅主题
    def unsubscribe(self):
        pass
    # 查看是否已经连接
    def isconnect(self):
        pass
    # 获取登录错误码
    def geterrcode(self):
        pass







if __name__ == '__main__':
    # 测试产品 TaxiLedV1_2   产品ID: HRDQBHLDHS
    # 设备名称:   TaxiLed_Dev_002
    # key = tigerots0123456789   base64后: dGlnZXJvdHMwMTIzNDU2Nzg5
    tos_info = MqttClient_Struct("HRDQBHLDHS", "TaxiLed_Dev_002", "dGlnZXJvdHMwMTIzNDU2Nzg5")
    tos_info.connect()






























# ==========================End============================
