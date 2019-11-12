#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Time: 2019/11/8
# @Author: Tigerots


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QTableWidget

import sys
sys.dont_write_bytecode = True

import socket
import threading
from MyTcpTool import stopThreading
from MyTcpTool import Form1
from MyTcpTool import signalEmit


class UdpLogic(QMainWindow, Form1.Ui_MainWindow, QTableWidget, signalEmit.SignalEmit):
    def __init__(self):
        QMainWindow.__init__(self)
        Form1.Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.udp_socket = None
        self.address = None
        self.udp_sever_th = None
        self.udp_client_th = None
        self.link = False

    # 开启UDP服务端方法
    def udp_server_start(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            port = int(self.lineEdit_Port.text())
            address = ('', port)
            self.udp_socket.bind(address)
        except Exception as ret:
            msg = '请检查端口号\n'
            self.signal_write_msg.emit(msg)
        else:
            self.udp_sever_th = threading.Thread(target=self.udp_server_concurrency)
            self.udp_sever_th.start()
            msg = 'UDP服务端正在监听端口:{}\n'.format(port)
            self.signal_write_msg.emit(msg)

    # 用于创建一个线程持续监听UDP通信
    def udp_server_concurrency(self):
        while True:
            recv_msg, recv_addr = self.udp_socket.recvfrom(1024)
            msg = recv_msg.decode('utf-8')
            msg = '来自IP:{}端口:{}:\n{}\n'.format(recv_addr[0], recv_addr[1], msg)
            self.signal_write_msg.emit(msg)
            msg = "{0}:{1}".format(recv_addr[0], recv_addr[1])
            self.signal_list_ip.emit(msg)

    # 确认UDP客户端的ip及地址
    def udp_client_start(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.address = (str(self.comboBox_IP.currentText()), int(self.lineEdit_Port.text()))
        except Exception as ret:
            msg = '请检查目标IP，目标端口\n'
            self.signal_write_msg.emit(msg)
        else:
            self.udp_socket.connect(self.address)
            self.udp_client_th = threading.Thread(target=self.udp_client_concurrency)
            self.udp_client_th.start()

            msg = 'UDP客户端已启动\n'
            self.signal_write_msg.emit(msg)

    # 用于创建一个线程持续监听UDP通信
    def udp_client_concurrency(self):
        while True:
            recv_msg, recv_addr = self.udp_socket.recvfrom(1024)
            msg = recv_msg.decode('utf-8')
            msg = '来自IP:{}端口:{}:\n{}\n'.format(recv_addr[0], recv_addr[1], msg)
            self.signal_write_msg.emit(msg)

    # 功能函数，用于UDP客户端发送消息
    def udp_send(self):
        if self.link is False:
            msg = '请选择服务，并点击连接网络\n'
            self.signal_write_msg.emit(msg)
        else:
            try:
                send_msg = (str(self.textEdit_Send.toPlainText())).encode('utf-8')
                if self.comboBox_TCP.currentIndex() == 2:
                    a, b = self.listWidget_client.currentItem().text().split(":")# 将数据发送到选中的客户端
                    self.address = (str(a), int(b))
                    self.udp_socket.sendto(send_msg, self.address)
                    msg = 'UDP客户端已发送\n'
                    self.signal_write_msg.emit(msg)
                if self.comboBox_TCP.currentIndex() == 3:
                    self.udp_socket.sendto(send_msg, self.address)
                    msg = 'UDP客户端已发送\n'
                    self.signal_write_msg.emit(msg)
            except Exception as ret:
                msg = '发送失败\n'
                self.signal_write_msg.emit(msg)

    # 功能函数，关闭网络连接的方法
    def udp_close(self):
        if self.comboBox_TCP.currentIndex() == 2:
            try:
                self.udp_socket.close()
                if self.link is True:
                    msg = '已断开网络\n'
                    self.signal_write_msg.emit(msg)
            except Exception as ret:
                pass
        if self.comboBox_TCP.currentIndex() == 3:
            try:
                self.udp_socket.close()
                if self.link is True:
                    msg = '已断开网络\n'
                    self.signal_write_msg.emit(msg)
            except Exception as ret:
                pass
        try:
            stopThreading.stop_thread(self.udp_sever_th)
        except Exception:
            pass
        try:
            stopThreading.stop_thread(self.udp_client_th)
        except Exception:
            pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = UdpLogic()
    ui.show()
    sys.exit(app.exec_())
