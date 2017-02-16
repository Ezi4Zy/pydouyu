# -*- coding: utf-8 -*-
# @Auth:    fear
# @Mail:    fear@1201.us
# @File:    room.py
# @Date:    2017-02-15
import network.client
import thread
import time
import logging

RAW_BUFF_SIZE = 4096
KEEP_ALIVE_INTERVAL_SECONDS = 45


# Keep-Alive thread func
def keep_alive(client, delay, stop):
    while not stop:
        current_ts = int(time.time())
        client.send({
            'type': 'keeplive',
            'tick': current_ts
        })
        time.sleep(delay)


class ChatRoom:

    channel_id = -9999  # Convention

    def __init__(self, room_id):
        self.client = None
        self.stop = False
        self.room_id = room_id
        self.callbacks = {}

    def on(self, event_name, callback):
        callback_list = None
        try:
            callback_list = self.callbacks[event_name]
        except KeyError as e:
            callback_list = []
            self.callbacks[event_name] = callback_list
        callback_list.append(callback)

    def trigger_callbacks(self, event_name, message):
        callback_list = None
        try:
            callback_list = self.callbacks[event_name]
        except KeyError as e:
            logging.info('Message of type "%s" is not handled' % event_name)
            return

        if callback_list is None or len(callback_list) <= 0:
            return

        for callback in callback_list:
            callback(message)

    # Start running
    def knock(self):
        self.client = network.client.Client()
        # Send AUTH request
        self.client.send({'type': 'loginreq', 'roomid': self.room_id})

        # Start a thread to send KEEPALIVE messages separately
        thread.start_new_thread(keep_alive, (self.client, KEEP_ALIVE_INTERVAL_SECONDS, self.stop))

        # Handle messages
        for message in self.client.receive():

            # stop receive message by flag
            if self.stop:
                self.client.send({'type': 'logout'})
                break

            if not message:
                continue

            # print json.dumps(message.body)
            msg_type = message.attr('type')

            # Send JOIN_GROUP request
            if msg_type == 'loginres':
                self.client.send({'type': 'joingroup', 'rid': self.room_id, 'gid': self.channel_id})

            self.trigger_callbacks(msg_type, message)
        self.client.s.close()

