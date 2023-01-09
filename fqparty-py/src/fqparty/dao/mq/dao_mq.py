# -*- coding:utf-8 -*-
import pika
from tomato.utils import strutil, ttlog


class DaoMq(object):
    def __init__(self, channelConf):
        self.host = channelConf.get('host')
        self.queue = channelConf.get('queue')
        self.channel = None
        self.conn = None

    def connect(self):
        self.conn = pika.BlockingConnection(pika.ConnectionParameters(self.host, heartbeat=0))
        channel = self.conn.channel()
        channel.queue_declare(self.queue, durable=True)
        self.channel = channel

    def publish(self, exchange, router, data):
        if not self.channel or not self.conn.is_open:
            self.connect()

        if not isinstance(data, str):
            data = strutil.jsonDumps(data)
        try:
            self.channel.basic_publish(exchange=exchange, routing_key=router, body=data)
            ttlog.info('DaoMq.publish',
                       'exchange=', exchange,
                       'router=', router,
                       'data=', data)
        except:
            ttlog.warn('DaoMq.publish Bad',
                       'queue=', self.queue,
                       'exchange=', exchange,
                       'router=', router,
                       'data=', data)
