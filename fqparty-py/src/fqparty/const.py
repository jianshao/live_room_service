# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''

class ServerTypes(object):
    CONN = 'conn'
    USER = 'user'
    ROOM = 'room'
    HTTP = 'http'
    MIC = 'mic'


class MicIds(object):
    OWNER = 999
    RANDOM = 100
    micIDs = [OWNER, 1, 2, 3, 4, 5, 6, 7, 8]
    pkHost = 100
    pkRedIDs = [1, 2, 3, 4]
    pkBlueIDs = [5, 6, 7, 8]
    pkIDs = [pkHost, 1, 2, 3, 4, 5, 6, 7, 8]

   
class AdminTypes(object):
    USER = 0
    ADMIN = 1
    OWNER = 2
    OFFICAL = 3
    SUPER = 4


class MsgTypes(object):
    TEXT = 1
    MIC_EMIOC = 2


class HttpResponseCode(object):
    SUCCESS = 0


class UserLeaveMicReason(object):
    USER_ACTIVE = 0
    USER_INVITE = 1
    MIC_LOCKED = 2
    ROOM_DATA_CHANGED = 3
    TIMEOUT = 4


class UserLeaveRoomReason(object):
    CONN_LOST = 1
    CONN_TIMEOUT = 2
    KICKOUT = 3
    USER_ACTIVE = 4
    ROOM_HEART_TIMEOUT = 5
    BAN_ROOM = 6


class Timeouts(object):
    USER_WEAKNET = 60
    USER_OFFLINE = 30


class SyncRoomDataTypes(object):
    MODE = 'mode'
    MANAGER = 'manager'
    BASEDATA = 'baseData'
    GUILD = 'guild'


class MsgRoutes(object):
    USER_BIND = '/user/bind'
    USER_KICKOUT = '/user/kickout'
    USER_BIND_AND_ENTER_ROOM = '/user/bindAndEnterRoom'
    USER_HEARTBEAT = '/user/heartbeat'
    USER_PUSH_MSG = '/user/pushUserMsg'
    USER_INFO_UPDATE = '/user/userInfoUpdate'
    ROOM_USER_ENTER = '/room/userEnter'
    ROOM_USER_LEAVE = '/room/userLeave'
    ROOM_USER_ON_MIC = '/room/userOnMic'
    ROOM_USER_LEAVE_MIC = '/room/userLeaveMic'
    ROOM_USER_LIST = '/room/userList'
    ROOM_USER_LIST_THREE = '/room/userListThree'
    ROOM_USER_WEAK_NET = '/room/userWeakNet'
    ROOM_KICKOUT_USER = '/room/kickoutUser'
    ROOM_MIC_LOCK = '/room/lockMic'
    ROOM_MIC_DISABLE = '/room/disableMic'
    ROOM_MIC_INVITE = '/room/inviteMic'
    ROOM_MIC_COUNTDOWN = '/room/countdownMic'
    ROOM_MIC_GET = '/room/getMic'
    ROOM_LOCK = '/room/lock'
    ROOM_DISABLE_MSG = '/room/disableMsg'
    ROOM_SEND_MSG_TO_ROOM = '/room/sendMsgToRoom'
    ROOM_ROOM_INFO = '/room/roomInfo'
    ROOM_USER_INFO = '/room/userInfo'
    ROOM_SYNC_MUSIC = '/room/syncMusic'
    ROOM_USER_INFO_UPDATE = '/room/userInfoUpdate'
    ROOM_DISABLE_USER_MSG = '/room/disableUserMsg'
    ROOM_BROADCAST_MSG_TO_USER = '/room/broadcastMsgToUser'
    ROOM_BROADCAST_MSG_TO_ROOM = '/room/broadcastMsgToRoom'
    ROOM_HEATUPDATE = '/room/heatUpdate'
    ROOM_SYNC_ROOM_INFO = '/room/syncRoomInfo'
    ROOM_PK_START = '/room/startPK'
    ROOM_PK_END = '/room/endPK'
    ROOM_PK_ADD_COUNTDOWN = '/room/addPKCountdown'
    ROOM_CREATE_ACORSS_PK = '/room/createAcorssPK'
    ROOM_ACORSS_PK_LIST = '/room/acorssPKList'
    ROOM_SPONSORE_ACORSS_PK = '/room/sponsoreAcrossPK'
    ROOM_REPLY_ACORSS_PK = '/room/replyAcrossPK'
    ROOM_INVITE_PK_LIST = '/room/invitePKList'
    ROOM_ACORSS_PK_START = '/room/startAcorssPK'
    ROOM_ACORSS_PK_END = '/room/endAcorssPK'
    ROOM_ACORSS_PKING_INFO = '/room/acorssPKingInfo'
    ROOM_SEARCH_ROOM = '/room/searchRoom'


class ErrorCode(object):
    OP_FAILED = 1
    ENTER_ROOM_LOCK = 2
    ENTER_ROOM_FORBBIDEN = 3
    ENTER_ROOM_ERR_PASSWORD = 4
    
    BAD_PARAMS = 6
    
    NO_IDLE_MIC = 502
    ALREADY_ON_MIC = 503
    UNKNOWN_MIC = 504
    ROOM_NOT_EXISTS = 505
    
    NOT_ADMIN_OP_MIC = 506
    USER_NOT_IN_ROOM = 507
    ROOM_NOT_ACTIVE = 508
    MIC_NOT_IDLE = 509
    USER_NOT_LOGIN = 510
    AUTH_TOKEN_FAILED = 5000
    
    MIC_ON_OWNER = 512
    MIC_ON_NOT_OWNER = 513
    MIC_LOCKED = 514
    NOT_ADMIN_OP_MUSIC = 515
    NOT_ON_MIC_OP_MUSIC = 516
    
    NOT_ADMIN_OP_ROOM = 517
    ACORSS_ROOM_EXISTS = 518







