#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Time: 2019/11/8
# @Author: Tigerots

import datetime
import socket
import sys
# 不生成__pyche__文件
sys.dont_write_bytecode = True
from PyQt5.QtCore import QStringListModel


# 这里引入了PyQt5.QtWidgets模块，这个模块包含了基本的组件。
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QFileDialog, QLabel, QListWidgetItem
# 窗口代码自动生成, 最后不要和应用程序放到一个文件, 方便以后更新
from MySocketProject import tcp_logic
from MySocketProject import udp_logic
from MySocketProject import signal_emit



# 主窗口类
class Form1Win(tcp_logic.TcpLogic, udp_logic.UdpLogic, signal_emit.SignalEmit):
    def __init__(self):
        super(Form1Win, self).__init__()
        # 禁止最大化, 禁止拉伸
        #self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setFixedSize(self.width(), self.height())
        # 属性
        self.client_socket_list = list()
        self.another = None
        self.link = False

        # 状态栏
        self.status = self.statusBar()
        self.status.showMessage('状态信息:')
        #self.S_Sta = QLabel("Status:")
        self.S_IP = QLabel("IP:")
        self.S_Port = QLabel("Port:")
        #self.status.addPermanentWidget(self.S_Sta, stretch=0)
        self.status.addPermanentWidget(self.S_IP, stretch=0)
        self.status.addPermanentWidget(self.S_Port, stretch=0)
        # 增加公司服务器默认IP
        TcpTypeList = ["TCP服务器", "TCP客户端", "UDP服务器", "UDP客户端", ]
        self.comboBox_TCP.addItems(TcpTypeList)
        # 使用的物联网协议类型
        IotProList = ["MQTT协议", "COAP协议", "其他协议", ]
        self.cbx_mqtt_coap.addItems(IotProList)
        self.cbx_mqtt_coap.setEnabled(False)

        # 默认发送内容
        self.textEdit_Send.setText("Hello my world...")
        # TODO Hex发送和定时发送还没写,以后用到了再写吧

        # 执行初始化函数
        self.connect()# 初始化信号-槽
        # 启动时获取本机IP放到IP列表
        self.click_get_ip()
        IpTypeList = ["222.222.19.106", ]  # 公司服务器
        self.comboBox_IP.addItems(IpTypeList)
        # 窗口重新初始化
        self.cbx_tcp_Changed()
        # 表格初始化===================================================================
        # listView
        self.str_item = "222.222.19.106:9000" # 添加数据
        self.listWidget_client.addItem(QListWidgetItem(self.str_item))# 添加数据
        # self.str_item = "192.168.1.151:9000"  # 添加数据
        # self.listWidget_client.addItem(QListWidgetItem(self.str_item))

        # table view 设置数据层次结构
        self.model = QStandardItemModel(10, 4)
        # 设置水平方向头标签文本内容
        self.model.setHorizontalHeaderLabels(['类型', '地址', '端口','时间'])
        nowTime=str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.model.setItem(0, 0, QStandardItem("TCP Client"))
        self.model.setItem(0, 1, QStandardItem("222.222.19.106"))
        self.model.setItem(0, 2, QStandardItem("9000"))
        self.model.setItem(0, 3, QStandardItem('%s' % (nowTime)))
        self.tbl_history.setModel(self.model)
        # 水平方向标签拓展剩下的窗口部分，填满表格
        # self.tbl_history.horizontalHeader().setStretchLastSection(True)
        # 水平方向，表格大小拓展到适当的尺寸
        # self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # TODO 这个表格要怎么用还没想好
    # 以下区域定义函数=================================================================

    # 绑定pushButton和comboBox信号与槽Signals & slots
    def connect(self):
        # 按键 btn
        self.Btn_OpenTcp.clicked.connect(self.btn_socket_open)
        self.Btn_Send.clicked.connect(self.Btn_TcpSendData)
        # 列表框 combobox, 这里为啥下拉列表时会自动收回呢?
        self.comboBox_TCP.currentTextChanged.connect(self.cbx_tcp_Changed)
        self.comboBox_IP.currentIndexChanged.connect(self.IpChanged)
        # 菜单栏
        self.File_Open.triggered.connect(self.openMsg)
        # 复选框 checkBox
        self.checkBox_iot.toggled.connect(self.checkBox_iot_fun)
        self.checkBox_GapTime.toggled.connect(self.cbx_GapTime)
        self.checkBox_Hex.toggled.connect(self.cbx_Hex)
        self.lineEdit_GapTime.textChanged.connect(self.edt_GapTime)
        # 清空按键
        self.cbtn_clr.clicked.connect(self.cbtn_clr_recv)
        # 信号槽
        self.signal_write_msg.connect(self.write_msg)
        self.signal_list_ip.connect(self.change_list_ip)
        pass

    # 是否使用物联网协议
    def checkBox_iot_fun(self):
        if self.checkBox_iot.isChecked():
            self.cbx_mqtt_coap.setEnabled(True)
        else:
            self.cbx_mqtt_coap.setEnabled(False)


    # 有新客户端连接, 将客户端IP缓存
    def change_list_ip(self, msg):
        for i in range(0, self.listWidget_client.count()):
            text_list = self.listWidget_client.item(i).text()
            if text_list == msg:
                return
        # 新的客户端IP显示到列表, 去除重复的
        self.listWidget_client.addItem(QListWidgetItem(msg))

    # 清除接收区
    def cbtn_clr_recv(self):
        self.textEdit_recv.clear()
        pass

    # 功能函数，向接收区写入数据的方法, 信号-槽触发
    # PyQt程序的子线程中，直接向主线程的界面传输字符是不符合安全原则的
    def write_msg(self, msg):
        self.textEdit_recv.insertPlainText(msg)
        # 滚动条移动到结尾
        self.textEdit_recv.moveCursor(QtGui.QTextCursor.End)

    # 获取本机ip
    def click_get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('114.114.114.114', 80))
            my_addr = s.getsockname()[0]
            self.comboBox_IP.addItem(str(my_addr))
        except Exception as ret:
            # 若无法连接互联网使用，会调用以下方法
            try:
                my_addr = socket.gethostbyname(socket.gethostname())
                self.comboBox_IP.addItem(str(my_addr))
            except Exception as ret_e:
                self.status.showMessage("无法获取ip，请连接网络！\n")
        finally:
            s.close()

    # 打开或关闭网络链接, 函数名要求小写, 类名第一个字母大写
    def btn_socket_open(self):
        # 网络没有连接
        if self.link is False:
            if self.comboBox_TCP.currentIndex() == 0:
                self.tcp_server_start()
            elif self.comboBox_TCP.currentIndex() == 1:
                self.tcp_client_start()
            elif self.comboBox_TCP.currentIndex() == 2:
                self.udp_server_start()
            elif self.comboBox_TCP.currentIndex() == 3:
                self.udp_client_start()
            self.Btn_OpenTcp.setText("关闭连接")
            self.S_Port.setText("Port: " + self.lineEdit_Port.text())
            self.S_IP.setText("IP: " + self.comboBox_IP.currentText())
            self.status.showMessage("成功连接到网络...")
            self.link = True
        # 网络连接时,关闭连接
        else:
            if self.comboBox_TCP.currentIndex() == 0 or self.comboBox_TCP.currentIndex() == 1:
                self.tcp_close()
            elif self.comboBox_TCP.currentIndex() == 2 or self.comboBox_TCP.currentIndex() == 3:
                self.udp_close()
            else:
                pass
            self.S_IP.setText("IP: ")
            self.S_Port.setText("Port: ")
            self.Btn_OpenTcp.setText("打开连接")
            self.status.showMessage("断开网络连接...")
            self.link = False

    def Btn_TcpSendData(self):
        if self.comboBox_TCP.currentIndex()==0 or self.comboBox_TCP.currentIndex()==1:
            self.tcp_send()
        elif self.comboBox_TCP.currentIndex()==2 or self.comboBox_TCP.currentIndex()==3:
            self.udp_send()
        else:
            pass
        self.status.showMessage("发送数据")


    def cbx_tcp_Changed(self):
        if self.comboBox_TCP.currentIndex()==0 or self.comboBox_TCP.currentIndex()==2:
            self.label_2.setText("本机地址")
            self.label_3.setText("本机端口")
            self.comboBox_IP.setCurrentIndex(0)
            self.comboBox_IP.setEnabled(False)
        elif self.comboBox_TCP.currentIndex()==1 or self.comboBox_TCP.currentIndex()==3:
            self.label_2.setText("服务器地址")
            self.label_3.setText("服务器端口")
            self.comboBox_IP.setCurrentIndex(1)
            self.comboBox_IP.setEnabled(True)
        else:
            pass


    def IpChanged(self):
        pass

    def openMsg(self):
        file, ok = QFileDialog.getOpenFileName(self, "打开", "C:/", "All Files (*);;Text Files (*.txt)")
        self.statusbar.showMessage(file)
        pass

    def cbx_GapTime(self):
        if self.checkBox_GapTime.isChecked() is True:
            self.status.showMessage("定时发送数据 "+self.lineEdit_GapTime.text()+"ms")
        else:
            self.status.showMessage("取消定时发送数据")
        pass
    def cbx_Hex(self):
        if self.checkBox_Hex.isChecked() is True:
            self.status.showMessage("HEX发送数据")
        else:
            self.status.showMessage("ASCII发送数据")
        pass

    def edt_GapTime(self):
        if int(self.lineEdit_GapTime.text())<10:
            self.lineEdit_GapTime.setText("10")
            self.status.showMessage("发送时间间隔不能小于10ms...")
        else:
            self.status.showMessage("发送时间间隔: "+self.lineEdit_GapTime.text()+"ms")
        pass



if __name__ == "__main__":
    #每个PyQt5应用都必须创建一个应用对象。sys.argv是一组命令行参数的列表。
    # Python可以在shell里运行，这个参数提供对脚本控制的功能。
    app = QApplication(sys.argv)
    MainWin = Form1Win()
    MainWin.show()
    # 最后，我们进入了应用的主循环中，事件处理器这个时候开始工作。主循环从窗口上接收事件，
    # 并把事件传入到派发到应用控件里。当调用exit()方法或直接销毁主控件时，主循环就会结束。
    # sys.exit()方法能确保主循环安全退出。外部环境能通知主控件怎么结束。
    sys.exit(app.exec_())






