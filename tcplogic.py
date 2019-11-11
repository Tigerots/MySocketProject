#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Time: 2019/11/8
# @Author: Tigerots


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QTableWidget

import sys
import time
import socket
import threading
from MyTcpTool import stopThreading
from MyTcpTool import Form1


class TcpLogic(QMainWindow, Form1.Ui_MainWindow, QTableWidget):
    def __init__(self):
        QMainWindow.__init__(self)
        Form1.Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.tcp_socket = None
        self.sever_th = None
        self.client_th = None
        self.client_socket_list = list()

        self.link = False  # 用于标记是否开启了连接

# 功能块儿分隔符:=========================================================================
    # 开启TCP服务器
    def tcp_server_start(self):
        # 设定IPv4, 流控
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 取消主动断开连接四次握手后的TIME_WAIT状态
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 设定套接字为非阻塞式
        self.tcp_socket.setblocking(False)
        try:
            port = int(self.lineEdit_Port.text())
            self.tcp_socket.bind(('', port))
        except Exception as ret:
            msg = '请检查端口号\n'
            self.signal_write_msg.emit(msg)
        else:
            self.tcp_socket.listen()
            self.sever_th = threading.Thread(target=self.tcp_server_concurrency)
            self.sever_th.start()
            msg = 'TCP服务端正在监听端口:%s\n' % str(port)
            self.signal_write_msg.emit(msg)

    def tcp_server_concurrency(self):
        """
        功能函数，供创建线程的方法；
        使用子线程用于监听并创建连接，使主线程可以继续运行，以免无响应
        使用非阻塞式并发用于接收客户端消息，减少系统资源浪费，使软件轻量化
        :return:None
        """
        while True:
            try:
                client_socket, client_address = self.tcp_socket.accept()
            except Exception as ret:
                time.sleep(0.001)
            else:
                client_socket.setblocking(False)
                # 将创建的客户端套接字存入列表,client_address为ip和端口的元组
                self.client_socket_list.append((client_socket, client_address))
                msg = 'TCP服务端已连接IP:%s端口:%s\n'%(client_address[0],client_address[1])
                self.signal_write_msg.emit(msg)
                print(client_address)
            # 轮询客户端套接字列表，接收数据
            for client, address in self.client_socket_list:
                try:
                    recv_msg = client.recv(1024)
                except Exception as ret:
                    pass
                else:
                    if recv_msg:
                        msg = recv_msg.decode('utf-8')
                        msg = '来自IP:{}端口:{}:\n{}\n'.format(address[0], address[1], msg)
                        self.signal_write_msg.emit(msg)
                    else:
                        client.close()
                        self.client_socket_list.remove((client, address))

    def tcp_close(self):
        pass
        """
        功能函数，关闭网络连接的方法
        :return:
        """
        if self.comboBox_TCP.currentIndex() == 0:
            try:
                for client, address in self.client_socket_list:
                    client.close()
                self.tcp_socket.close()
                if self.link is True:
                    msg = '已断开网络\n'
                    self.signal_write_msg.emit(msg)
            except Exception as ret:
                pass
        if self.comboBox_TCP.currentIndex() == 1:
            try:
                self.tcp_socket.close()
                if self.link is True:
                    msg = '已断开网络\n'
                    self.signal_write_msg.emit(msg)
            except Exception as ret:
                pass
        try:
            stopThreading.stop_thread(self.sever_th)
        except Exception:
            pass
        try:
            stopThreading.stop_thread(self.client_th)
        except Exception:
            pass

# 功能块儿分隔符:=========================================================================

    # 功能函数，TCP客户端连接其他服务端的方法
    def tcp_client_start(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            address = (str(self.comboBox_IP.currentText()), int(self.lineEdit_Port.text()))
        except Exception as ret:
            msg = '请检查目标IP，目标端口\n'
            self.signal_write_msg.emit(msg)
        else:
            try:
                msg = '正在连接目标服务器\n'
                self.signal_write_msg.emit(msg)
                self.tcp_socket.connect(address)
            except Exception as ret:
                msg = '无法连接目标服务器\n'
                self.signal_write_msg.emit(msg)
            else:
                self.client_th = threading.Thread(target=self.tcp_client_concurrency, args=(address,))
                self.client_th.start()
                msg = 'TCP客户端已连接IP:%s端口:%s\n' % address
                self.signal_write_msg.emit(msg)

    # 功能函数，用于TCP客户端创建子线程的方法，阻塞式接收
    def tcp_client_concurrency(self, address):
        while True:
            recv_msg = self.tcp_socket.recv(1024)
            if recv_msg:
                msg = recv_msg.decode('utf-8')
                msg = '来自IP:{}端口:{}:\n{}\n'.format(address[0], address[1], msg)
                self.signal_write_msg.emit(msg)
            else:
                self.tcp_socket.close()
                self.reset()
                msg = '从服务器断开连接\n'
                self.signal_write_msg.emit(msg)
                break

    # 功能函数，用于TCP服务端和TCP客户端发送消息
    def tcp_send(self):
        if self.link is False:
            msg = '请选择服务，并点击连接网络\n'
            self.signal_write_msg.emit(msg)
        else:
            try:
                send_msg = (str(self.textEdit_Send.toPlainText())).encode('utf-8')
                if self.comboBox_TCP.currentIndex() == 0:
                    # 向所有连接的客户端发送消息
                    for client, address in self.client_socket_list:
                        client.send(send_msg)
                    msg = 'TCP服务端已发送\n'
                    self.signal_write_msg.emit(msg)
                if self.comboBox_TCP.currentIndex() == 1:
                    self.tcp_socket.send(send_msg)
                    msg = 'TCP客户端已发送\n'
                    self.signal_write_msg.emit(msg)
            except Exception as ret:
                msg = '发送失败\n'
                self.signal_write_msg.emit(msg)



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = TcpLogic()
    ui.show()
    sys.exit(app.exec_())
