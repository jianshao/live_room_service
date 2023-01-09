# -*- coding:utf-8 -*-
'''
Created on 2020年12月22日

@author: zhaojiangang
'''
import random

from fqparty.domain.models.user import User
from fqparty.domain.room.room import RoomUser, RoomMic
from tomato.utils import sortedlist


userList = []


def calcRoomUserScore(roomUser, ownerUser):
    # 房主
    return (-1 if roomUser == ownerUser else 0,
            -roomUser.user.userLevel,
            -roomUser.user.isVip,
            0 if roomUser.user.userId != roomUser.user.prettyId else 1,
            0 if roomUser.mic else 1,
            roomUser.enterRoomTime)


def main():
    ownerUser = None
    for i in range(100):
        user = User()
        user.userId = i
        user.userLevel = random.randint(1, 10)
        user.isVip = random.randint(0, 2)
        user.prettyId = random.choice([user.userId, 6666])
        micId = random.choice([0,0,0,0,0,1])
        if micId == 0:
            mic = None
        else:
            mic = RoomMic(None, micId)
        roomUser = RoomUser(None, user, {})
        roomUser.mic = mic
        
        if not ownerUser:
            ownerUser = roomUser
            
        roomUser.sortScore = calcRoomUserScore(roomUser, ownerUser)
        sortedlist.insert(userList, roomUser)
        
    l = [(roomUser.user.userId, roomUser.sortScore) for roomUser in userList]
    print sortedlist.indexOf(userList, userList[0])
    print sortedlist.indexOf(userList, userList[1])
    print l
    sortedlist.remove(userList, userList[0])
    l = [(roomUser.user.userId, roomUser.sortScore) for roomUser in userList]
    print l


if __name__ == '__main__':
    main()
    
    