# -*- coding:utf-8 -*-
# Copyright (c) 2011 Oregon State University Open Source Lab
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
#    NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
"""
Blind reimplementation of WebSockets as a standalone wrapper for Twisted
protocols.
"""

from __future__ import division
import socket
import array
from base64 import b64encode, b64decode
from hashlib import md5, sha1
from string import digits
from struct import pack, unpack

import six
from twisted.internet import protocol
from twisted.internet.interfaces import ISSLTransport
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import _PauseableMixin
from twisted.python import log
from twisted.web.http import datetimeToString

from tomato.utils import ttlog


__version__ = "0.7.1"





class WSException(Exception):
    """
    Something stupid happened here.

    If this class escapes txWS, then something stupid happened in multiple
    places.
    """

# Flavors of WS supported here.
# HYBI00  - Hixie-76, HyBi-00. Challenge/response after headers, very minimal
#           framing. Tricky to start up, but very smooth sailing afterwards.
# HYBI07  - HyBi-07. Modern "standard" handshake. Bizarre masked frames, lots
#           of binary data packing.
# HYBI10  - HyBi-10. Just like HyBi-07. No, seriously. *Exactly* the same,
#           except for the protocol number.
# RFC6455 - RFC 6455. The official WebSocket protocol standard. The protocol
#           number is 13, but otherwise it is identical to HyBi-07.

HYBI00, HYBI07, HYBI10, RFC6455 = range(4)

# States of the state machine. Because there are no reliable byte counts for
# any of this, we don't use StatefulProtocol; instead, we use custom state
# enumerations. Yay!

REQUEST, NEGOTIATING, CHALLENGE, FRAMES = range(4)

# Control frame specifiers. Some versions of WS have control signals sent
# in-band. Adorable, right?

NORMAL, CLOSE, PING, PONG = range(4)

opcode_types = {
    0x0: NORMAL,
    0x1: NORMAL,
    0x2: NORMAL,
    0x8: CLOSE,
    0x9: PING,
    0xa: PONG,
}

encoders = {
    "base64": b64encode,
}

decoders = {
    "base64": b64decode,
}

# Fake HTTP stuff, and a couple convenience methods for examining fake HTTP
# headers.

def http_headers(s):
    """
    Create a dictionary of data from raw HTTP headers.
    """

    d = {}

    for line in s.split("\r\n"):
        try:
            key, value = [i.strip() for i in line.split(":", 1)]
            d[key] = value
        except ValueError:
            pass

    ttlog.info('http_headers:', d)
    return d

def to_lower_headers(headers):
    return {k.lower():v for k, v in headers.iteritems()}

def is_websocket(headers):
    """
    Determine whether a given set of headers is asking for WebSockets.
    """
    return ("upgrade" in headers.get("connection", "").lower()
            and headers.get("upgrade").lower() == "websocket")

def is_hybi00(headers):
    """
    Determine whether a given set of headers is HyBi-00-compliant.

    Hixie-76 and HyBi-00 use a pair of keys in the headers to handshake with
    servers.
    """

    return "sec-websocket-key1" in headers and "sec-websocket-key2" in headers

# Authentication for WS.

def complete_hybi00(headers, challenge):
    """
    Generate the response for a HyBi-00 challenge.
    """

    key1 = headers["sec-webwocket-key1"]
    key2 = headers["sec-webwocket-key2"]

    first = int("".join(i for i in key1 if i in digits)) // key1.count(" ")
    second = int("".join(i for i in key2 if i in digits)) // key2.count(" ")

    nonce = pack(">II8s", first, second, six.b(challenge))

    return md5(nonce).digest()

def make_accept(key):
    """
    Create an "accept" response for a given key.

    This dance is expected to somehow magically make WebSockets secure.
    """

    guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    accept = "%s%s" % (key, guid)
    hashed_bytes = sha1(accept.encode('utf-8')).digest()

    return b64encode(hashed_bytes).strip().decode('utf-8')

# Frame helpers.
# Separated out to make unit testing a lot easier.
# Frames are bonghits in newer WS versions, so helpers are appreciated.

def make_hybi00_frame(buf, opcode=None):
    """
    Make a HyBi-00 frame from some data.

    This function does exactly zero checks to make sure that the data is safe
    and valid text without any 0xff bytes.
    """

    if isinstance(buf, six.text_type):
        buf = buf.encode('utf-8')

    return six.b("\x00") + buf + six.b("\xff")

def parse_hybi00_frames(buf):
    """
    Parse HyBi-00 frames, returning unwrapped frames and any unmatched data.

    This function does not care about garbage data on the wire between frames,
    and will actively ignore it.
    """

    start = buf.find(six.b("\x00"))
    tail = 0
    frames = []

    while start != -1:
        end = buf.find(six.b("\xff"), start + 1)
        if end == -1:
            # Incomplete frame, try again later.
            break
        else:
            # Found a frame, put it in the list.
            frame = buf[start + 1:end]
            frames.append((NORMAL, frame))
            tail = end + 1
        start = buf.find(six.b("\x00"), end + 1)

    # Adjust the buffer and return.
    buf = buf[tail:]
    return frames, buf

def mask(buf, key):
    """
    Mask or unmask a buffer of bytes with a masking key.

    The key must be exactly four bytes long.
    """

    # This is super-duper-secure, I promise~
    key = array.array("B", key)
    buf = array.array("B", buf)
    for i in range(len(buf)):
        buf[i] ^= key[i % 4]
    return buf.tostring()

def make_hybi07_frame(buf, opcode=0x1):
    """
    Make a HyBi-07 frame.

    This function always creates unmasked frames, and attempts to use the
    smallest possible lengths.
    """

    if len(buf) > 0xffff:
        length = "\x7f%s" % pack(">Q", len(buf))
    elif len(buf) > 0x7d:
        length = "\x7e%s" % pack(">H", len(buf))
    else:
        length = chr(len(buf))

    if isinstance(buf, six.text_type):
        buf = buf.encode('utf-8')

    opcode = 0x1 if opcode is None else opcode
    # Always make a normal packet.
    header = chr(0x80 | opcode)
    return six.b(header + length) + buf

def make_hybi07_frame_dwim(buf, opcode=None):
    """
    Make a HyBi-07 frame with binary or text data according to the type of buf.
    """

    # TODO: eliminate magic numbers.
    if isinstance(buf, six.binary_type):
        opcode = 0x02 if opcode is None else opcode
        return make_hybi07_frame(buf, opcode)
    elif isinstance(buf, six.text_type):
        opcode = 0x01 if opcode is None else opcode
        return make_hybi07_frame(buf.encode("utf-8"), opcode=0x1)
    else:
        raise TypeError("In binary support mode, frame data must be either str or unicode")

def parse_hybi07_frames(buf):
    """
    Parse HyBi-07 frames in a highly compliant manner.
    """

    start = 0
    frames = []

    while True:
        # If there's not at least two bytes in the buffer, bail.
        if len(buf) - start < 2:
            break

        # Grab the header. This single byte holds some flags nobody cares
        # about, and an opcode which nobody cares about.
        header = buf[start]

        if six.PY2:
            header = ord(header)

        if header & 0x70:
            # At least one of the reserved flags is set. Pork chop sandwiches!
            raise WSException("Reserved flag in HyBi-07 frame (%d)" % header)
            frames.append(("", CLOSE))
            return frames, buf

        # Get the opcode, and translate it to a local enum which we actually
        # care about.
        opcode = header & 0xf
        try:
            opcode = opcode_types[opcode]
        except KeyError:
            raise WSException("Unknown opcode %d in HyBi-07 frame" % opcode)

        # Get the payload length and determine whether we need to look for an
        # extra length.
        length = buf[start + 1]

        if six.PY2:
            length = ord(length)

        masked = length & 0x80
        length &= 0x7f

        # The offset we're gonna be using to walk through the frame. We use
        # this because the offset is variable depending on the length and
        # mask.
        offset = 2

        # Extra length fields.
        if length == 0x7e:
            if len(buf) - start < 4:
                break

            length = buf[start + 2:start + 4]
            length = unpack(">H", length)[0]
            offset += 2
        elif length == 0x7f:
            if len(buf) - start < 10:
                break

            # Protocol bug: The top bit of this long long *must* be cleared;
            # that is, it is expected to be interpreted as signed. That's
            # fucking stupid, if you don't mind me saying so, and so we're
            # interpreting it as unsigned anyway. If you wanna send exabytes
            # of data down the wire, then go ahead!
            length = buf[start + 2:start + 10]
            length = unpack(">Q", length)[0]
            offset += 8

        if masked:
            if len(buf) - (start + offset) < 4:
                break

            key = buf[start + offset:start + offset + 4]
            offset += 4

        if len(buf) - (start + offset) < length:
            break

        data = buf[start + offset:start + offset + length]

        if masked:
            data = mask(data, key)

        if opcode == CLOSE:
            if len(data) >= 2:
                # Gotta unpack the opcode and return usable data here.
                data = unpack(">H", data[:2])[0], data[2:]
            else:
                # No reason given; use generic data.
                data = 1000, six.b("No reason given")

        frames.append((opcode, data))
        start += offset + length

    return frames, buf[start:]

class WebSocketProtocol(protocol.Protocol, _PauseableMixin):
    """
    Protocol which wraps another protocol to provide a WebSockets transport
    layer.
    """

    buf = six.b("")
    codec = None
    location = "/"
    host = "example.com"
    origin = "http://example.com"
    state = REQUEST
    flavor = None
    do_binary_frames = False
    composer = None
    userData = None
    
    def __init__(self):
        self.callOpen = False
        self.headers = {}
        self.lower_headers = {}
        self.pending_frames = []
        self.clientIp = None

    def abort(self):
        if hasattr(self.transport, 'abortConnection'):
            self.transport.abortConnection()
        else:
            self.loseConnection()

    def close(self):
        ttlog.info('WebSocketProtocol.close',
                   'peer=', self.getPeer(),
                   'clientIp=', self.getClientIp())
        # self.transport.loseConnection()
        self.closeWithReason()
        
    def send(self, data):
        self.sendRaw(self.composer.compose(data))
    
    def sendRaw(self, data):
        self.write(data)
    
    def getPeer(self):
        return self.transport.getPeer()
    
    def getHost(self):
        return self.transport.getHost()

    def getClientIp(self):
        if not self.callOpen:
            return None
        if not self.clientIp:
            if self.lower_headers:
                self.clientIp = self.lower_headers.get('kk-real-ip')
            if not self.clientIp:
                self.clientIp = self.lower_headers.get('x-forwarded-for')
            if not self.clientIp:
                self.clientIp = self.getPeer().host
        
        if ttlog.isDebugEnabled():
            ttlog.debug('WebSocketProtocol.getClientIp',
                        'headers=', self.lower_headers,
                        'clientIp=', self.clientIp)
        return self.clientIp
    
    def setBinaryMode(self, mode):
        """
        If True, send str as binary and unicode as text.

        Defaults to false for backwards compatibility.
        """
        self.do_binary_frames = bool(mode)

    def isSecure(self):
        """
        Borrowed technique for determining whether this connection is over
        SSL/TLS.
        """
        return ISSLTransport(self.transport, None) is not None

    def writeEncoded(self, data):
        if isinstance(data, six.text_type):
            data = data.encode('utf-8')
        
        if ttlog.isDebugEnabled():
            ttlog.debug('WebSocketProtocol.writeEncoded',
                        'dataLen=', len(data),
                        'clientIp=', self.clientIp)
        self.transport.write(data)

    def writeEncodedSequence(self, sequence):
        if ttlog.isDebugEnabled():
            ttlog.debug('WebSocketProtocol.writeEncoded',
                        'sequenceLen=', len(sequence),
                        'clientIp=', self.clientIp)
        self.transport.writeSequence([ele.encode('utf-8') for ele in sequence])

    def sendCommonPreamble(self):
        """
        Send the preamble common to all WebSockets connections.

        This might go away in the future if WebSockets continue to diverge.
        """

        self.writeEncodedSequence([
            "HTTP/1.1 101 FYI I am not a webserver\r\n",
            "Server: TwistedWebSocketWrapper/1.0\r\n",
            "Date: %s\r\n" % datetimeToString(),
            "Upgrade: WebSocket\r\n",
            "Connection: Upgrade\r\n",
        ])

    def sendHyBi00Preamble(self):
        """
        Send a HyBi-00 preamble.
        """

        protocol = "wss" if self.isSecure() else "ws"

        self.sendCommonPreamble()

        self.writeEncodedSequence([
            "Sec-WebSocket-Origin: %s\r\n" % self.origin,
            "Sec-WebSocket-Location: %s://%s%s\r\n" % (protocol, self.host,
                                                       self.location),
            "WebSocket-Protocol: %s\r\n" % self.codec,
            "Sec-WebSocket-Protocol: %s\r\n" % self.codec,
            "\r\n",
        ])

    def sendHyBi07Preamble(self):
        """
        Send a HyBi-07 preamble.
        """

        self.sendCommonPreamble()

        if self.codec:
            self.writeEncoded("Sec-WebSocket-Protocol: %s\r\n" % self.codec)

        challenge = self.lower_headers.get('sec-websocket-key', '')
        response = make_accept(challenge)

        self.writeEncoded("Sec-WebSocket-Accept: %s\r\n\r\n" % response)

    def parseFrames(self):
        """
        Find frames in incoming data and pass them to the underlying protocol.
        """

        if self.flavor == HYBI00:
            parser = parse_hybi00_frames
        elif self.flavor in (HYBI07, HYBI10, RFC6455):
            parser = parse_hybi07_frames
        else:
            raise WSException("Unknown flavor %r" % self.flavor)

        try:
            frames, self.buf = parser(self.buf)
        except WSException as wse:
            # Couldn't parse all the frames, something went wrong, let's bail.
            self.close(wse.args[0])
            ttlog.warn('WebSocketProtocol.parseFrames EX',
                       'peer=', self.getPeer(),
                       'clientIp=', self.getClientIp(),
                       'ex=', wse)
            return

        for frame in frames:
            opcode, data = frame
            if opcode == NORMAL:
                # Business as usual. Decode the frame, if we have a decoder.
                if self.codec:
                    data = decoders[self.codec](data)
                # Pass the frame to the underlying protocol.
                try:
                    if ttlog.isDebugEnabled():
                        ttlog.debug('WebSocketProtocol.parseFrames',
                                    'dataLen=', len(data),
                                    'clientIp=', self.clientIp,
                                    'data=', self.printBytes(data))
                    for pkg in self.composer.feed(data):
                        if not self.transport.disconnecting:
                            self.factory.onConnectionDataReceived(self, pkg)
                except:
                    self.abort()
            elif opcode == CLOSE:
                # The other side wants us to close. I wonder why?
                reason, text = data
                log.msg("Closing connection: %r (%d)" % (text, reason))
                ttlog.warn('WebSocketProtocol.parseFrames CLOSE',
                       'peer=', self.getPeer(),
                       'clientIp=', self.getClientIp(),
                       'reason=', reason,
                       'text=', text)
                # Close the connection.
                self.close()
            elif opcode == PING:
                if self.codec:
                    data = decoders[self.codec](data)
                self.factory.onConnectionPingReceived(self, data)
            elif opcode == PONG:
                if self.codec:
                    data = decoders[self.codec](data)
                self.factory.onConnectionPongReceived(self, data)

    def sendFrames(self):
        """
        Send all pending frames.
        """

        if self.state != FRAMES:
            return

        if self.flavor == HYBI00:
            maker = make_hybi00_frame
        elif self.flavor in (HYBI07, HYBI10, RFC6455):
            if self.do_binary_frames:
                maker = make_hybi07_frame_dwim
            else:
                maker = make_hybi07_frame
        else:
            raise WSException("Unknown flavor %r" % self.flavor)

        for frame in self.pending_frames:
            # Encode the frame before sending it.
            opcode = None
            if isinstance(frame, tuple):
                opcode = frame[0]
                frame = frame[1]
            if self.codec:
                frame = encoders[self.codec](frame)
            packet = maker(frame, opcode)
            self.writeEncoded(packet)
        self.pending_frames = []

    def validateHeaders(self):
        """
        Check received headers for sanity and correctness, and stash any data
        from them which will be required later.
        """

        # Obvious but necessary.
        if not is_websocket(self.lower_headers):
            log.msg("Not handling non-WS request")
            return False

        # Stash host and origin for those browsers that care about it.
        self.host = self.lower_headers.get('host', self.host)
        self.origin = self.lower_headers.get('origin', self.origin)

        # Check whether a codec is needed. WS calls this a "protocol" for
        # reasons I cannot fathom. Newer versions of noVNC (0.4+) sets
        # multiple comma-separated codecs, handle this by chosing first one
        # we can encode/decode.
        protocols = None
        if "websocket-protocol" in self.lower_headers:
            protocols = self.lower_headers["websocket-protocol"]
        elif "sec-websocket-protocol" in self.lower_headers:
            protocols = self.lower_headers["sec-websocket-protocol"]

        if isinstance(protocols, six.string_types):
            protocols = [p.strip() for p in protocols.split(',')]

            for protocol in protocols:
                if protocol in encoders or protocol in decoders:
                    log.msg("Using WS protocol %s!" % protocol)
                    self.codec = protocol
                    break

                log.msg("Couldn't handle WS protocol %s!" % protocol)

            if not self.codec:
                return False

        # Start the next phase of the handshake for HyBi-00.
        if is_hybi00(self.lower_headers):
            log.msg("Starting HyBi-00/Hixie-76 handshake")
            self.flavor = HYBI00
            self.state = CHALLENGE

        # Start the next phase of the handshake for HyBi-07+.
        if "sec-websocket-version" in self.lower_headers:
            version = self.lower_headers["sec-websocket-version"]
            if version == "7":
                log.msg("Starting HyBi-07 conversation")
                self.sendHyBi07Preamble()
                self.flavor = HYBI07
                self.state = FRAMES
            elif version == "8":
                log.msg("Starting HyBi-10 conversation")
                self.sendHyBi07Preamble()
                self.flavor = HYBI10
                self.state = FRAMES
            elif version == "13":
                log.msg("Starting RFC 6455 conversation")
                self.sendHyBi07Preamble()
                self.flavor = RFC6455
                self.state = FRAMES
            else:
                log.msg("Can't support protocol version %s!" % version)
                return False

        return True

    def printBytes(self, bts):
        ret = []
        for b in bts:
            ret.append('%d' % (ord(b)))
        return ret

    def dataReceived(self, data):
        self.buf += data

        if ttlog.isDebugEnabled():
            ttlog.debug('WebSocketProtocol.dataReceived',
                        'dataLen=', len(data),
                        'clientIp=', self.clientIp)

        oldstate = None

        while oldstate != self.state:
            oldstate = self.state

            # Handle initial requests. These look very much like HTTP
            # requests, but aren't. We need to capture the request path for
            # those browsers which want us to echo it back to them (Chrome,
            # mainly.)
            # These lines look like:
            # GET /some/path/to/a/websocket/resource HTTP/1.1
            if self.state == REQUEST:
                separator = six.b("\r\n")
                if separator in self.buf:
                    request, _chaff, self.buf = self.buf.partition(separator)
                    request = request.decode('utf-8')

                    try:
                        _verb, self.location, _version = request.split(" ")
                    except ValueError:
                        self.loseConnection()
                    else:
                        self.state = NEGOTIATING

            elif self.state == NEGOTIATING:
                # Check to see if we've got a complete set of headers yet.
                separator = six.b("\r\n\r\n")
                if separator in self.buf:
                    head, _chaff, self.buf = self.buf.partition(separator)
                    head = head.decode('utf-8')

                    self.headers = http_headers(head)
                    self.lower_headers = to_lower_headers(self.headers)
                    # Validate headers. This will cause a state change.
                    if not self.validateHeaders():
                        self.loseConnection()

            elif self.state == CHALLENGE:
                # Handle the challenge. This is completely exclusive to
                # HyBi-00/Hixie-76.
                if len(self.buf) >= 8:
                    challenge, self.buf = self.buf[:8], self.buf[8:]
                    challenge = challenge.decode('utf-8')

                    response = complete_hybi00(self.lower_headers, challenge)
                    self.sendHyBi00Preamble()
                    self.writeEncoded(response)
                    log.msg("Completed HyBi-00/Hixie-76 handshake")
                    # We're all finished here; start sending frames.
                    self.state = FRAMES

            elif self.state == FRAMES:
                if not self.callOpen:
                    self.callOpen = True
                    try:
                        self.composer = self.factory.composer()
                        self.factory.onConnectionOpen(self)
                    except:
                        self.abort()
                self.parseFrames()

        # Kick any pending frames. This is needed because frames might have
        # started piling up early; we can get write()s from our protocol above
        # when they makeConnection() immediately, before our browser client
        # actually sends any data. In those cases, we need to manually kick
        # pending frames.
        if self.pending_frames:
            self.sendFrames()

    def write(self, data):
        """
        Write to the transport.

        This method will only be called by the underlying protocol.
        """

        self.pending_frames.append(data)
        self.sendFrames()

    def writePing(self, data):
        self.pending_frames.append((0x9, data))
        self.sendFrames()
        
    def writePong(self, data):
        self.pending_frames.append((0xa, data))
        self.sendFrames()

    def writeSequence(self, data):
        """
        Write a sequence of data to the transport.

        This method will only be called by the underlying protocol.
        """

        self.pending_frames.extend(data)
        self.sendFrames()

    def closeWithReason(self, reason=""):
        """
        Close the connection.

        This includes telling the other side we're closing the connection.

        If the other side didn't signal that the connection is being closed,
        then we might not see their last message, but since their last message
        should, according to the spec, be a simple acknowledgement, it
        shouldn't be a problem.
        """

        # Send a closing frame. It's only polite. (And might keep the browser
        # from hanging.)
        if self.flavor in (HYBI07, HYBI10, RFC6455):
            frame = make_hybi07_frame(reason, opcode=0x8)
            self.writeEncoded(frame)

        self.loseConnection()

    def loseConnection(self):
        self.transport.loseConnection()

    def connectionMade(self):
        ttlog.info('WebSocketProtocol.connectionMade',
                   'peer=', self.getPeer())
        self.transport.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connectionLost(self, reason=connectionDone):
        try:
            self.factory.onConnectionLost(self, reason)
        except:
            ttlog.error('WebSocketProtocol.connectionLost',
                        'peer=', self.getPeer())
        

