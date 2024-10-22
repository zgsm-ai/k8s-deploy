#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socketio
from aiohttp import web

# 创建一个 Socket.IO 服务器
sio = socketio.AsyncServer(cors_allowed_origins='*')

# 创建一个 aiohttp 应用
app = web.Application()
sio.attach(app)

# 处理连接事件
@sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')

# 处理断开连接事件
@sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')

# 处理自定义事件
@sio.event
async def message(sid, data):
    print(f'Message from {sid}: {data}')
    await sio.send(sid, f'Server received: {data}')

# 启动服务器
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8765)
    