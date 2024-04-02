import re  
import numpy,random,enum,uuid 
from typing import List,Union,Dict,Callable

class SDP:
    class SDPPARAMS:
        def __init__(self) -> None:
            pass
        def addSSRC(self,id,cname):
            pass
            
        def __repr__(self) -> str:
            return f"SDPPARAMS({self.__dict__})"
    defaultInnerOrder = ["i", "c", "b", "a"]
    defaultOuterOrder = ["v", "o", "s", "i", "u", "e", "p", "c", "b", "t", "r", "z", "a"]

    grammar = {
        "v": [{"name": "version", "reg": "^(\d*)$"}],
        "o": [
            {
                # o=- 20518 0 IN IP4 203.0.113.1
                # NB: sessionId will be a String in most cases because it is huge
                "name": "origin",
                "reg": "^(\S*) (\d*) (\d*) (\S*) IP(\d) (\S*)",
                "names": [
                    "username",
                    "sessionId", 
                    "sessionVersion",
                    "netType",
                    "ipVer",
                    "address",
                ],
                "format": "%s %s %d %s IP%d %s",
            }
        ],
        # default parsing of these only (though some of these feel outdated)
        "s": [{"name": "name"}],
        "i": [{"name": "description"}],
        "u": [{"name": "uri"}],
        "e": [{"name": "email"}],
        "p": [{"name": "phone"}],
        # TODO: this one can actually be parsed properly...
        "z": [{"name": "timezones"}],
        "r": [{"name": "repeats"}],  # TODO: this one can also be parsed properly
        # k: [{}], # outdated thing ignored
        "t": [
            {
                # t=0 0
                "name": "timing",
                "reg": "^(\d*) (\d*)",
                "names": ["start", "stop"],
                "format": "%d %d",
            }
        ],
        "c": [
            {
                # c=IN IP4 10.47.197.26
                "name": "connection",
                "reg": "^IN IP(\d) (\S*)",
                "names": ["version", "ip"],
                "format": "IN IP%d %s",
            }
        ],
        "b": [
            {
                # b=AS:4000
                "push": "bandwidth",
                "reg": "^(TIAS|AS|CT|RR|RS):(\d*)",
                "names": ["type", "limit"],
                "format": "%s:%s",
            }
        ],
        "m": [
            {
                # m=video 51744 RTP/AVP 126 97 98 34 31
                # NB: special - pushes to session
                # TODO: rtp/fmtp should be filtered by the payloads found here?
                "reg": "^(\w*) (\d*) ([\w/]*)(?: (.*))?",
                "names": ["type", "port", "protocol", "payloads"],
                "format": "%s %d %s %s",
            }
        ],
        "a": [
            {
                # a=rtpmap:110 opus/48000/2
                "push": "rtp",
                "reg": "^rtpmap:(\d*) ([\w\-.]*)(?:\s*\/(\d*)(?:\s*\/(\S*))?)?",
                "names": ["payload", "codec", "rate", "encoding"],
                "format": lambda o: "rtpmap:%d %s/%s/%s"
                if o.get("encoding") != None
                else ("rtpmap:%d %s/%s" if o.get("rate") != None else "rtpmap:%d %s"),
            },
            {
                # a=fmtp:108 profile-level-id=24;object=23;bitrate=64000
                # a=fmtp:111 minptime=10; useinbandfec=1
                "push": "fmtp",
                "reg": "^fmtp:(\d*) ([\S| ]*)",
                "names": ["payload", "config"],
                "format": "fmtp:%d %s",
            },
            {
                # a=control:streamid=0
                "name": "control",
                "reg": "^control:(.*)",
                "format": "control:%s",
            },
            {
                # a=rtcp:65179 IN IP4 193.84.77.194
                "name": "rtcp",
                "reg": "^rtcp:(\d*)(?: (\S*) IP(\d) (\S*))?",
                "names": ["port", "netType", "ipVer", "address"],
                "format": lambda o: "rtcp:%d %s IP%d %s"
                if o.get("address") != None
                else "rtcp:%d",
            },
            {
                # a=rtcp-fb:98 trr-int 100
                "push": "rtcpFbTrrInt",
                "reg": "^rtcp-fb:(\*|\d*) trr-int (\d*)",
                "names": ["payload", "value"],
                "format": "rtcp-fb:%s trr-int %d",
            },
            {
                # a=rtcp-fb:98 nack rpsi
                "push": "rtcpFb",
                "reg": "^rtcp-fb:(\*|\d*) ([\w\-_]*)(?: ([\w\-_]*))?",
                "names": ["payload", "type", "subtype"],
                "format": lambda o: "rtcp-fb:%s %s %s"
                if o.get("subtype") != None
                else "rtcp-fb:%s %s",
            },
            {
                # a=extmap:2 urn:ietf:params:rtp-hdrext:toffset
                # a=extmap:1/recvonly URI-gps-string
                # a=extmap:3 urn:ietf:params:rtp-hdrext:encrypt urn:ietf:params:rtp-hdrext:smpte-tc 25@600/24
                "push": "ext",
                "reg": "^extmap:(\d+)(?:\/(\w+))?(?: (urn:ietf:params:rtp-hdrext:encrypt))? (\S*)(?: (\S*))?",
                "names": ["value", "direction", "encrypt-uri", "uri", "config"],
                "format": lambda o: "extmap:%d"
                + ("/%s" if o.get("direction") != None else "")
                + (" %s" if o.get("encrypt-uri") != None else "")
                + " %s"
                + (" %s" if o.get("config") != None else ""),
            },
            {
                # a=extmap-allow-mixed
                "name": "extmapAllowMixed",
                "reg": "^(extmap-allow-mixed)",
            },
            {
                # a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:PS1uQCVeeCFCanVmcjkpPywjNWhcYD0mXXtxaVBR|2^20|1:32
                "push": "crypto",
                "reg": "^crypto:(\d*) ([\w_]*) (\S*)(?: (\S*))?",
                "names": ["id", "suite", "config", "sessionConfig"],
                "format": lambda o: "crypto:%d %s %s %s"
                if o.get("sessionConfig") != None
                else "crypto:%d %s %s",
            },
            {
                # a=setup:actpass
                "name": "setup",
                "reg": "^setup:(\w*)",
                "format": "setup:%s",
            },
            {
                # a=connection:new
                "name": "connectionType",
                "reg": "^connection:(new|existing)",
                "format": "connection:%s",
            },
            {
                # a=msid:0c8b064d-d807-43b4-b434-f92a889d8587 98178685-d409-46e0-8e16-7ef0db0db64a
                "name": "msid",
                "reg": "^msid:(.*)",
                "format": "msid:%s",
            },
            {
                # a=ptime:20
                "name": "ptime",
                "reg": "^ptime:(\d*(?:\.\d*)*)",
                "format": lambda o: "ptime:%d" if isinstance(o, int) else "ptime:%g",
            },
            {
                # a=maxptime:60
                "name": "maxptime",
                "reg": "^maxptime:(\d*(?:\.\d*)*)",
                "format": "maxptime:%d",
            },
            {
                # a=sendrecv
                "name": "direction",
                "reg": "^(sendrecv|recvonly|sendonly|inactive)",
            },
            {
                # a=ice-lite
                "name": "icelite",
                "reg": "^(ice-lite)",
            },
            {
                # a=ice-ufrag:F7gI
                "name": "iceUfrag",
                "reg": "^ice-ufrag:(\S*)",
                "format": "ice-ufrag:%s",
            },
            {
                # a=ice-pwd:x9cml/YzichV2+XlhiMu8g
                "name": "icePwd",
                "reg": "^ice-pwd:(\S*)",
                "format": "ice-pwd:%s",
            },
            {
                # a=fingerprint:SHA-1 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33
                "name": "fingerprint",
                "reg": "^fingerprint:(\S*) (\S*)",
                "names": ["type", "hash"],
                "format": "fingerprint:%s %s",
            },
            {
                # a=candidate:0 1 UDP 2113667327 203.0.113.1 54400 typ host
                # a=candidate:1162875081 1 udp 2113937151 192.168.34.75 60017 typ host generation 0 network-id 3 network-cost 10
                # a=candidate:3289912957 2 udp 1845501695 193.84.77.194 60017 typ srflx raddr 192.168.34.75 rport 60017 generation 0 network-id 3 network-cost 10
                # a=candidate:229815620 1 tcp 1518280447 192.168.150.19 60017 typ host tcpfield active generation 0 network-id 3 network-cost 10
                # a=candidate:3289912957 2 tcp 1845501695 193.84.77.194 60017 typ srflx raddr 192.168.34.75 rport 60017 tcpfield passive generation 0 network-id 3 network-cost 10
                "push": "candidates",
                "reg": "^candidate:(\S*) (\d*) (\S*) (\d*) (\S*) (\d*) typ (\S*)(?: raddr (\S*) rport (\d*))?(?: tcpfield (\S*))?(?: generation (\d*))?(?: network-id (\d*))?(?: network-cost (\d*))?",
                "names": [
                    "foundation",
                    "component",
                    "protocol",
                    "priority",
                    "ip",
                    "port",
                    "type",
                    "raddr",
                    "rport",
                    "tcptype",
                    "generation",
                    "network-id",
                    "network-cost",
                ],
                "format": lambda o: "candidate:%s %d %s %d %s %d typ %s"
                + (" raddr %s rport %d" if o.get("raddr") != None else "")
                + (" tcpfield %s" if o.get("tcptype") != None else "")
                + (" generation %d" if o.get("generation") != None else "")
                + (" network-id %d" if o.get("network-id") != None else "")
                + (" network-cost %d" if o.get("network-cost") != None else ""),
            },
            {
                # a=end-of-candidates (keep after the candidates line for readability)
                "name": "endOfCandidates",
                "reg": "^(end-of-candidates)",
            },
            {
                # a=remote-candidates:1 203.0.113.1 54400 2 203.0.113.1 54401 ...
                "name": "remoteCandidates",
                "reg": "^remote-candidates:(.*)",
                "format": "remote-candidates:%s",
            },
            {
                # a=ice-options:google-ice
                "name": "iceOptions",
                "reg": "^ice-options:(\S*)",
                "format": "ice-options:%s",
            },
            {
                # a=ssrc:2566107569 c'name':t9YU8M1UxTF8Y1A1
                "push": "ssrcs",
                "reg": "^ssrc:(\d*) ([\w_-]*)(?::(.*))?",
                "names": ["id", "attribute", "value"],
                "format": lambda o: "ssrc:%d"
                + (" %s" if o.get("attribute") != None else "")
                + (":%s" if o.get("value") != None else ""),
            },
            {
                # a=ssrc-group:FEC 1 2
                # a=ssrc-group:FEC-FR 3004364195 1080772241
                "push": "ssrcGroups",
                # token-char = %x21 / %x23-27 / %x2A-2B / %x2D-2E / %x30-39 / %x41-5A / %x5E-7E
                "reg": "^ssrc-group:([\x21\x23\x24\x25\x26\x27\x2A\x2B\x2D\x2E\w]*) (.*)",
                "names": ["semantics", "ssrcs"],
                "format": "ssrc-group:%s %s",
            },
            {
                # a=msid-semantic: WMS Jvlam5X3SX1OP6pn20zWogvaKJz5Hjf9OnlV
                "name": "msidSemantic",
                "reg": "^msid-semantic:\s?(\w*) (\S*)",
                "names": ["semantic", "token"],
                "format": "msid-semantic: %s %s",  # space after ':' is not accidental
            },
            {
                # a=group:BUNDLE audio video
                "push": "groups",
                "reg": "^group:(\w*) (.*)",
                "names": ["type", "mids"],
                "format": "group:%s %s",
            },
            {
                # a=rtcp-mux
                "name": "rtcpMux",
                "reg": "^(rtcp-mux)",
            },
            {
                # a=rtcp-rsize
                "name": "rtcpRsize",
                "reg": "^(rtcp-rsize)",
            },
            {
                # a=sctpmap:5000 webrtc-datachannel 1024
                "name": "sctpmap",
                "reg": "^sctpmap:([\w_/]*) (\S*)(?: (\S*))?",
                "names": ["sctpmapNumber", "app", "maxMessageSize"],
                "format": lambda o: "sctpmap:%s %s %s"
                if o.get("maxMessageSize") != None
                else "sctpmap:%s %s",
            },
            {
                # a=x-google-flag:conference
                "name": "xGoogleFlag",
                "reg": "^x-google-flag:([^\s]*)",
                "format": "x-google-flag:%s",
            },
            {
                # a=rid:1 send max-width=1280;max-height=720;max-fps=30;depend=0
                "push": "rids",
                "reg": "^rid:([\d\w]+) (\w+)(?: ([\S| ]*))?",
                "names": ["id", "direction", "params"],
                "format": lambda o: "rid:%s %s %s"
                if o.get("params") != None
                else "rid:%s %s",
            },
            {
                # a=imageattr:97 send [x=800,y=640,sar=1.1,q=0.6] [x=480,y=320] recv [x=330,y=250]
                # a=imageattr:* send [x=800,y=640] recv *
                # a=imageattr:100 recv [x=320,y=240]
                "push": "imageattrs",
                "reg": re.compile(
                    # a=imageattr:97
                    "^imageattr:(\\d+|\\*)"
                    +
                    # send [x=800,y=640,sar=1.1,q=0.6] [x=480,y=320]
                    "[\\s\\t]+(send|recv)[\\s\\t]+(\\*|\\[\\S+\\](?:[\\s\\t]+\\[\\S+\\])*)"
                    +
                    # recv [x=330,y=250]
                    "(?:[\\s\\t]+(recv|send)[\\s\\t]+(\\*|\\[\\S+\\](?:[\\s\\t]+\\[\\S+\\])*))?"
                ),
                "names": ["pt", "dir1", "attrs1", "dir2", "attrs2"],
                "format": lambda o: "imageattr:%s %s %s"
                + (" %s %s" if o.get("dir2") != None else ""),
            },
            {
                # a=simulcast:send 1,2,3;~4,~5 recv 6;~7,~8
                # a=simulcast:recv 1;4,5 send 6;7
                "name": "simulcast",
                "reg": re.compile(
                    # a=simulcast:
                    "^simulcast:"
                    +
                    # send 1,2,3;~4,~5
                    "(send|recv) ([a-zA-Z0-9\\-_~;,]+)"
                    +
                    # space + recv 6;~7,~8
                    "(?:\\s?(send|recv) ([a-zA-Z0-9\\-_~;,]+))?"
                    +
                    # end
                    "$"
                ),
                "names": ["dir1", "list1", "dir2", "list2"],
                "format": lambda o: "simulcast:%s %s"
                + (" %s %s" if o.get("dir2") != None else ""),
            },
            {
                # old simulcast draft 03 (implemented by Firefox)
                #   https://tools.ietf.org/html/draft-ietf-mmusic-sdp-simulcast-03
                # a=simulcast: recv pt=97;98 send pt=97
                # a=simulcast: send rid=5;6;7 paused=6,7
                "name": "simulcast_03",
                "reg": "^simulcast:[\s\t]+([\S+\s\t]+)$",
                "names": ["value"],
                "format": "simulcast: %s",
            },
            {
                # a=framerate:25
                # a=framerate:29.97
                "name": "framerate",
                "reg": "^framerate:(\d+(?:$|\.\d+))",
                "format": "framerate:%s",
            },
            {
                # RFC4570
                # a=source-filter: incl IN IP4 239.5.2.31 10.1.15.5
                "name": "sourceFilter",
                "reg": "^source-filter: *(excl|incl) (\S*) (IP4|IP6|\*) (\S*) (.*)",
                "names": [
                    "filterMode",
                    "netType",
                    "addressTypes",
                    "destAddress",
                    "srcList",
                ],
                "format": "source-filter: %s %s %s %s %s",
            },
            {
                # a=bundle-only
                "name": "bundleOnly",
                "reg": "^(bundle-only)",
            },
            {
                # a=label:1
                "name": "label",
                "reg": "^label:(.+)",
                "format": "label:%s",
            },
            {
                # RFC version 26 for SCTP over DTLS
                # https://tools.ietf.org/html/draft-ietf-mmusic-sctp-sdp-26#section-5
                "name": "sctpPort",
                "reg": "^sctp-port:(\d+)$",
                "format": "sctp-port:%s",
            },
            {
                # RFC version 26 for SCTP over DTLS
                # https://tools.ietf.org/html/draft-ietf-mmusic-sctp-sdp-26#section-6
                "name": "maxMessageSize",
                "reg": "^max-message-size:(\d+)$",
                "format": "max-message-size:%s",
            },
            {
                # RFC7273
                # a=ts-refclk:ptp=IEEE1588-2008:39-A7-94-FF-FE-07-CB-D0:37
                "push": "tsRefClocks",
                "reg": "^ts-refclk:([^\s=]*)(?:=(\S*))?",
                "names": ["clksrc", "clksrcExt"],
                "format": lambda o: "ts-refclk:%s"
                + ("=%s" if o.get("clksrcExt") != None else ""),
            },
            {
                # RFC7273
                # a=mediaclk:direct=963214424
                "name": "mediaClk",
                "reg": "^mediaclk:(?:id=(\S*))? *([^\s=]*)(?:=(\S*))?(?: *rate=(\d+)\/(\d+))?",
                "names": [
                    "id",
                    "mediaClockName",
                    "mediaClockValue",
                    "rateNumerator",
                    "rateDenominator",
                ],
                "format": lambda o: "mediaclk:"
                + ("id=%s %s" if o.get("id") != None else "%s")
                + ("=%s" if o.get("mediaClockValue") != None else "")
                + (" rate=%s" if o.get("rateNumerator") != None else "")
                + ("/%s" if o.get("rateDenominator") != None else ""),
            },
            {
                # a=keywds:keywords
                "name": "keywords",
                "reg": "^keywds:(.+)$",
                "format": "keywds:%s",
            },
            {
                # a=content:main
                "name": "content",
                "reg": "^content:(.+)",
                "format": "content:%s",
            },
            # BFCP https://tools.ietf.org/html/rfc4583
            {
                # a=floorctrl:c-s
                "name": "bfcpFloorCtrl",
                "reg": "^floorctrl:(c-only|s-only|c-s)",
                "format": "floorctrl:%s",
            },
            {
                # a=confid:1
                "name": "bfcpConfId",
                "reg": "^confid:(\d+)",
                "format": "confid:%s",
            },
            {
                # a=userid:1
                "name": "bfcpUserId",
                "reg": "^userid:(\d+)",
                "format": "userid:%s",
            },
            {
                # a=floorid:1
                "name": "bfcpFloorId",
                "reg": "^floorid:(.+) (?:m-stream|mstrm):(.+)",
                "names": ["id", "mStream"],
                "format": "floorid:%s mstrm:%s",
            },
            {
                # a=mid:1
                "name": "mid",
                "reg": "^mid:([^\s]*)",
                "format": "mid:%s",
            },
            {
                # any a= that we don't understand is kept verbatim on media.invalid
                "push": "invalid",
                "names": ["value"],
            },
        ],
    }
    for key in grammar.keys():
        objs = grammar[key]
        for obj in objs:
            if not obj.get("reg"):
                obj["reg"] = r"(.*)"
            if not obj.get("format"):
                obj["format"] = "%s" 

    @classmethod
    def makeLine(cls,field, obj, location):
        string = (
            field
            + "="
            + (
                obj["format"]((location if obj.get("push") else location[obj.get("name")]))
                if callable(obj["format"])
                else obj["format"]
            )
        )
        args = []
        if obj.get("names"):
            for name in obj.get("names"):
                if obj.get("name"):
                    if location[obj.get("name")].get(name) != None:
                        args.append(location[obj.get("name")][name])
                else:
                    if location.get(name) != None:
                        args.append(location[name])
        else:
            args.append(location[obj.get("name")])

        return string % tuple(args)

    @classmethod
    def toIntIfInt(cls,v):
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except:
                return v

    @classmethod
    def attachProperties(cls,match, location, names=None, rawName=None):
        if rawName and not names:
            location[rawName] = cls.toIntIfInt(match[1])
        else:
            i = 0
            while i < len(names):
                if match[i + 1] != None:
                    location[names[i]] = cls.toIntIfInt(match[i + 1])
                i += 1
        return


    @classmethod
    def parseReg(cls,obj, location, content):
        needsBlank = obj.get("name") and obj.get("names")
        if obj.get("push"):
            if not location.get(obj.get("push")):
                location[obj.get("push")] = []

        elif needsBlank:
            if not location.get(obj.get("name")):
                location[obj.get("name")] = {}
        keyLocation = (
            {}
            if obj.get("push")
            else (location.get(obj.get("name")) if needsBlank else location)
        )

        cls.attachProperties(
            re.match(obj["reg"], content), keyLocation, obj.get("names"), obj.get("name")
        )

        if obj.get("push"):
            location[obj.get("push")].append(keyLocation)
    @classmethod
    def getNetType(cls,IpAddr:str):
        return 4 if len(IpAddr.split("."))==4 else 6 
    
    
    
    
    
    
    @classmethod
    def parse(cls,sdp: str) -> dict: 
        session = {}
        media = []
        location = session
        lines = [line for line in sdp.splitlines() if re.match(r"^([a-z])=(.*)", line)]
        for l in lines:
            field = l[0]
            content = l[2:]

            if field == "m":
                media.append({"rtp": [], "fmtp": []})
                location = media[-1]

            for obj in cls.grammar.get(field, []):
                if re.match(obj["reg"], content):
                    cls.parseReg(obj, location, content)
                    break

        session["media"] = media
        
        parobj=cls.SDPPARAMS()
        parobj.__dict__=session
        return parobj
    @classmethod
    def write(cls,session: dict,outerOrder: list = defaultOuterOrder,innerOrder: list = defaultInnerOrder,): 
        if session.get("version") == None:
            session["version"] = 0  # 'v=0' must be there (only defined version atm)
        if session.get("name") == None:
            session["name"] = " "  # 's= ' must be there if no meaningful name set
        for media in session.get("media", []):
            if media.get("payloads") == None:
                media["payloads"] = ""
        sdp = []
        # loop through outerOrder for matching properties on session
        for field in outerOrder:
            for obj in cls.grammar[field]:
                if obj.get("name"):
                    if obj["name"] in session.keys():
                        if session.get(obj["name"]) != None:
                            sdp.append(cls.makeLine(field, obj, session))
                elif obj.get("push"):
                    if obj["push"] in session.keys():
                        if session.get(obj["push"]) != None:
                            for el in session.get(obj["push"]):
                                sdp.append(cls.makeLine(field, obj, el))
        # then for each media line, follow the innerOrder
        for mLine in session.get("media", []):
            sdp.append(cls.makeLine("m", cls.grammar["m"][0], mLine))
            for field in innerOrder:
                for obj in cls.grammar[field]:
                    if obj.get("name"):
                        if obj["name"] in mLine.keys():
                            if mLine.get(obj["name"]) != None:
                                sdp.append(cls.makeLine(field, obj, mLine))
                    elif obj.get("push"):
                        if obj["push"] in mLine.keys():
                            if mLine.get(obj["push"]) != None:
                                for el in mLine.get(obj["push"]):
                                    sdp.append(cls.makeLine(field, obj, el))
        return "\r\n".join([*sdp, ""])
    @classmethod
    def createSDP(cls,username,rtpIp="",sessionId:int=None,sessionVersion:int=None,mediaList:List[Callable]=[]) -> SDPPARAMS: 
        parobj=cls.SDPPARAMS()
        parobj.version=0
        parobj.name="PYSANMEDIA"
        parobj.timing={"start":0,"stop":0}
        parobj.origin={'username': username,'sessionId': sessionId,'sessionVersion': sessionVersion,'netType': 'IN','ipVer': cls.getNetType(rtpIp),'address': rtpIp}

        parobj.media=mediaList
        return parobj
        




"""
from audio import AudioMediaManager
SDPMANAGER=SDP()
test=SDPMANAGER.createSDP(
    username="ersansrcck0145",
    rtpaddr="192.168.1.34:4000",
    rtcpaddr="192.168.1.34:4001",
    sessionId=3894262903,
    sessionVersion=3894262903,
    AudioObject=AudioMediaManager()      
).__dict__

SDPMANAGER.parse(SDPMANAGER.write(test)).__dict__"""













class TAGSETTINGS(enum.Enum):
    @staticmethod
    def createobjkwargs(**kwargs):
        defaults={"INDEX":None,"REQUESTNAME":None,"RESPONSENAME":None,"DEFAULTVALUE":None,"SPLITESCHARS":";"} | kwargs
        defaults["RESPONSENAME"]=defaults["RESPONSENAME"] or defaults["REQUESTNAME"]
        return defaults | kwargs
    

    
    VIA=createobjkwargs(INDEX=10,REQUESTNAME="Via")
    FROM=createobjkwargs(INDEX=30,REQUESTNAME="From")
    CONTACT=createobjkwargs(INDEX=70,REQUESTNAME="Contact")

    ALLOW=createobjkwargs(INDEX=90,REQUESTNAME="Allow",SPLITESCHARS=", ")
    SUPPORTED=createobjkwargs(INDEX=140,REQUESTNAME="Supported",SPLITESCHARS=", ")
    WWW_AUTH=createobjkwargs(INDEX=110,REQUESTNAME="Authorization",RESPONSENAME="WWW-Authenticate",SPLITESCHARS=", ")
    PROXY_AUTH=createobjkwargs(INDEX=120,REQUESTNAME="Proxy-Authorization",RESPONSENAME="Proxy-Authenticate",SPLITESCHARS=", ")
    ROUTE=createobjkwargs(INDEX=130,REQUESTNAME="Route",RESPONSENAME="Record-Route",SPLITESCHARS=", ")

    MAX_FORWARDS=createobjkwargs(INDEX=20,REQUESTNAME="Max-Forwards",DEFAULTVALUE="70")
    CALL_ID=createobjkwargs(INDEX=45,REQUESTNAME="Call-ID")
    CSEQ=createobjkwargs(INDEX=50,REQUESTNAME="CSeq")
    USER_AGENT=createobjkwargs(INDEX=60,REQUESTNAME="User-Agent")
    EXPIRES=createobjkwargs(INDEX=80,REQUESTNAME="Expires",DEFAULTVALUE="300")
    SERVER=createobjkwargs(INDEX=100,REQUESTNAME="Server")
    SESSION_EXPRES=createobjkwargs(INDEX=150,REQUESTNAME="Session-Expires",DEFAULTVALUE="1800")
    MIN_E=createobjkwargs(INDEX=160,REQUESTNAME="Min-SE",DEFAULTVALUE="90")
    MAX_SE=createobjkwargs(INDEX=170,REQUESTNAME="Max-SE",DEFAULTVALUE="300")
    CONTENT_TYPE=createobjkwargs(INDEX=180,REQUESTNAME="Content-Type")
    CONTENT_LENGHT=createobjkwargs(INDEX=190,REQUESTNAME="Content-Length")
    TO=createobjkwargs(INDEX=40,REQUESTNAME="To")
    
    
    


class TEXT_CLEAR:
    STARTCARACTERS=lambda self=None: {
        "()":{"finds":numpy.zeros((1, 2),dtype=int)[1:],"(":list(),")":list()},
        "[]":{"finds":numpy.zeros((1, 2),dtype=int)[1:],"[":list(),"]":list()},
        "{}":{"finds":numpy.zeros((1, 2),dtype=int)[1:],"{":list(),"}":list()},
        "<>":{"finds":numpy.zeros((1, 2),dtype=int)[1:],"<":list(),">":list()},
        "''":{"finds":numpy.zeros((1, 2),dtype=int)[1:],"'":list(),"'":list()},
        '""':{"finds":numpy.zeros((1, 2),dtype=int)[1:],'"':list(),'"':list()},
    }
    _splites:any=[";",", "]
    replaces_metin="REPLTOKENIXERREPL"
    setsescapes=[re.escape(key) for dicts in STARTCARACTERS().values() for key in dicts.keys() if key!="finds"]
    
    
    def FindCharIndex(self,stringvector) -> list[dict[dict],]:
        findcharskey=[]
        _charctersets=self.STARTCARACTERS()
        for re_char in re.finditer("|".join(self.setsescapes),stringvector):
            _char,_index=re_char.group(),re_char.start()
            dicts_key=None
            for keyname in _charctersets.keys():
                if _char in keyname:
                    if keyname not in findcharskey:
                        findcharskey.append(keyname)
                    dicts_key=keyname
                    break
            _charctersets[dicts_key][_char].append(_index)
        return [_charctersets[keys] for keys in findcharskey]
    
    
    def QueteCharClear(self,stringVector)-> numpy.ndarray:
        """
            QueteCharClear('Digest realm="sip.deneaefa.com", nonce="123123123123", algorithm=MD5, test="123:'de=,neme'"')
            >>>>["sip.deneaefa.com",    "123123123123",     "123:'de=neme,'"]
        """
        _starts_finish_numpy_arrs=numpy.zeros((1, 2),dtype=int)[1:]
        #index find 
        for chardict in self.FindCharIndex(stringVector): 
            keys=list(chardict.keys()) 
            start_indexs,ends_indexs=numpy.array([chardict[keys[1]],chardict[keys[-1]]])
            if numpy.array_equal(start_indexs,ends_indexs):
                chardict["finds"]=numpy.concatenate((chardict["finds"],ends_indexs.reshape(-1,2)),axis=0)
            else:    
                # 5 saniye  
                for indexends in ends_indexs:
                    indexstarts=start_indexs[start_indexs<indexends].max()
                    start_indexs=start_indexs[start_indexs!=indexstarts] 
                    chardict["finds"]=numpy.vstack((chardict["finds"],[[indexstarts,indexends]]))
            _starts_finish_numpy_arrs=numpy.vstack((_starts_finish_numpy_arrs,chardict["finds"]))
        startendmesafe=numpy.abs(_starts_finish_numpy_arrs[:,0]-_starts_finish_numpy_arrs[:,1]).reshape(-1,1)
        _starts_finish_numpy_arrs=numpy.hstack((_starts_finish_numpy_arrs,startendmesafe))
        byukdenkuck=numpy.argsort(_starts_finish_numpy_arrs[:, -1])[::-1]
        _starts_finish_numpy_arrs=_starts_finish_numpy_arrs[byukdenkuck][:,[0,1]]
        _replacesall=[stringVector[starts:finisg+1]  for starts,finisg in _starts_finish_numpy_arrs] 
        return _replacesall
    
    
class TagInValueNameSpace:
    def __init__(self,key=None,value=None,startSep=None,endSep=None) -> None:
        self.key=key
        self.value=value
        self.startSep=startSep
        self.endSep=endSep 
    def __str__(self) -> str:
        return str(f"TagInValueNameSpace(key={self.key},value={self.value},startSep={self.startSep},endSep={self.endSep})")
    def __repr__(self) -> str:
        return str(f"TagInValueNameSpace(key={self.key},value={self.value},startSep={self.startSep},endSep={self.endSep})")
    @property
    def toString(self):
        if self.key.startswith("ARGS_"):
            return f"{self.startSep}{self.value}{self.endSep}"
        else:
            return f"{self.startSep}{self.key}={self.value}{self.endSep}"
    @classmethod
    def ToTagIn(cls,allkwargs,stringvector):
        start_new_kwargs={}
        for key,value in allkwargs.items(): 
            if key.startswith("ARGS_"):
                start=stringvector.split(value,1)[0] 
                stringvector=stringvector.replace(start+value,"")
                start_new_kwargs[key]=TagInValueNameSpace(key=key,value=value,startSep=start,endSep="")
            else:
                start=stringvector.split(key,1)[0]
                stringvector=stringvector.replace(start+key,"").split(value,1)[-1]
                start_new_kwargs[key]=TagInValueNameSpace(key=key,value=value,startSep=start,endSep="")
        return start_new_kwargs
    
    
    
class TEXT_TO_DICT(TEXT_CLEAR): 
    def KeyToValue(self,stringVector):
        for keys,value in self._replacesall.items():
            if keys in stringVector:
                return stringVector.replace(keys,value)
        return stringVector
    def ValueToKey(self,stringVector):
        for keyname,value in self._replacesall.items():
            stringVector=stringVector.replace(value,keyname)
        return stringVector
    def CreateRandKey(self,splvectors:str=""):
        id=len(self._replacesall.keys())
        return f"{self.replaces_metin}_{splvectors}_{id}"
     
     
    def findSplitChar(self,allkwargs,stringvector) -> str:
        counts={key:0 for key in self._splites}
        for spchar in counts.keys():
            for _key,value in allkwargs.items(): 
                counts[spchar]+=len(list(filter(lambda x:x.startswith(spchar),stringvector.split(value))))
        return [key for key,value in counts.items() if value==max(counts.values())][0]
    
    
    
    @classmethod
    def tokenizeText(cls,stringVector,splites:str=None) -> dict: 
        """
            parseTEXT('Digest realm="sip.browsercalls.com"asdasd, nonce="2162392220", algorithm=MD5')
            >>>>{'ARGS_0': 'Digest', 'realm': '"sip.browsercalls.com"asdasd,', 'nonce': '"2162392220",', 'algorithm': 'MD5'}
        
        """
        self=TEXT_TO_DICT()
        self._replacesall={} 
        allkwargs={}  
        splits_text="|".join(self._splites)
        countscheck=len(re.split(splits_text,stringVector))
        
        if len(stringVector)==0:
            return {},""
        
        if countscheck==1: 
            allkwargs[f"ARGS_{len(allkwargs.keys())}"]=self.KeyToValue(stringVector) 
        else:
            replace_values=self.QueteCharClear(stringVector) 
            for repl_val in replace_values:
                self._replacesall[self.CreateRandKey("kwargs")]=repl_val  
            clear_string=self.ValueToKey(stringVector) 
            for param_vals in re.split(splits_text,clear_string):
                if "=" in param_vals:
                    for vals in param_vals.split(): 
                        if "=" not in vals: 
                            start_index=stringVector.find(vals)
                            end_index=start_index+len(vals)
                            keynames,values=f"ARGS_{len(allkwargs.keys())}",self.KeyToValue(param_vals[start_index:end_index+1])#"'Digest'>'Digest '"
                        else:
                            keys,values=vals.split("=",1)
                            keynames,values=self.KeyToValue(keys),self.KeyToValue(values)
                        allkwargs[keynames]=values
                else:#''rport
                    for vals in param_vals.split():
                        keynames,values=f"ARGS_{len(allkwargs.keys())}",self.KeyToValue(vals)
                        allkwargs[keynames]=values 
        return allkwargs,self.findSplitChar(allkwargs,stringVector)


class TAGS(TEXT_TO_DICT):
    def __init__(self,INDEX=None,REQUESTNAME=None,RESPONSENAME=None,DEFAULTVALUE="",SPLITESCHARS=";") -> None:
        self.TAG_UUID=f"{uuid.uuid4()}-{uuid.uuid4()}"
        self.INDEX:int=INDEX
        self.REQUESTNAME:str=REQUESTNAME
        self.RESPONSENAME:str=RESPONSENAME or REQUESTNAME
        self.SPLITESCHARS=SPLITESCHARS 
        self._KWARGS=TagInValueNameSpace.ToTagIn(self.tokenizeText(DEFAULTVALUE)[0],DEFAULTVALUE)

    def replaceMainValue(self,value):#user-agent,content-lenght
        self._KWARGS[list(self._KWARGS.keys())[0]].value=value
    def replaceKwargValue(self,name,value): #tag,branch
        self._KWARGS[name].value=value
    def KwargToArgs(self,name):
        if self._KWARGS.get("rport"):
            self._KWARGS[name].key=f"ARGS_{list(self._KWARGS.keys()).index(name)}"
            self._KWARGS[name].value=name
    
    
    def createTag(self,TagName,value): 
        tags=self._getToTagEnum(TagName)
        if len(tags)>0:
            self.__dict__=self.__dict__ |  tags[0].value
            if not value:
                value=self.DEFAULTVALUE 
            allkwargs,self.SPLITESCHARS=self.tokenizeText(value)
            self._KWARGS=TagInValueNameSpace.ToTagIn(allkwargs,value)
                
        else:
            print(TagName) 
            self.RESPONSENAME=TagName
            self.REQUESTNAME=TagName 
            allkwargs,self.SPLITESCHARS=self.tokenizeText(value)
            self._KWARGS=TagInValueNameSpace.ToTagIn(allkwargs,value)

        return self
    def getParse(self,stringvector):
        tagName,tagValue=stringvector.split(":",1)
        tagValue=tagValue.strip()
        findTagObj=self._getToTagEnum(tagName)
        if len(findTagObj)>0:
            self.__dict__=self.__dict__ |  findTagObj[0].value
        else:
            self.RESPONSENAME=tagName
            self.REQUESTNAME=tagName 
            print(tagName)
        allkwargs,self.SPLITESCHARS=self.tokenizeText(tagValue)
        self._KWARGS=TagInValueNameSpace.ToTagIn(allkwargs,tagValue)
        return self

    @property
    def getKwargsDict(self):
        return {name:self.stripValChar(value.value) for name,value in self._KWARGS.items() if not name.startswith("ARGS_")}
    @property
    def getArgsDict(self):
        return [self.stripValChar(value.value) for name,value in self._KWARGS.items() if name.startswith("ARGS_")]
    @property
    def getValue(self):
        metins=""
        for keys,TagInValueNameSpaceval in self._KWARGS.items(): 
            metins+=TagInValueNameSpaceval.toString 
        return metins
    @getValue.setter
    def getValue(self,value):
        allkwargs,self.SPLITESCHARS=self.tokenizeText(value)
        self._KWARGS=TagInValueNameSpace.ToTagIn(allkwargs,value)
        
    @property
    def getMainValue(self):
        metins=""
        for keys,TagInValueNameSpaceval in self._KWARGS.items(): 
            if keys.startswith("ARGS_"):
                metins+=TagInValueNameSpaceval.toString 
            else:
                break
        if metins!="":
            return metins
        else:
            return None
    @property
    def tagNames(self):
        return list(set([self.REQUESTNAME,self.RESPONSENAME]))
    @property
    def toString(self):
        return f"{self.REQUESTNAME}: "+self.getValue.strip(self.SPLITESCHARS)
    def stripValChar(self,values):
        return values.strip("'").strip('"').strip("<").strip(">")
    def _getToTagEnum(self,tagname):
        tags=[]
        for DEFNAME,DEFDICT in TAGSETTINGS._member_map_.items():
            if tagname.lower() in ";".join([DEFDICT.value["REQUESTNAME"],DEFDICT.value["RESPONSENAME"]]).lower():
                tags.append(DEFDICT)
        return tags
    def __repr__(self) -> str:
        return str(f"TAGS(INDEX={self.INDEX},REQUESTNAME={self.REQUESTNAME},RESPONSENAME={self.RESPONSENAME},SPLITESCHARS={self.SPLITESCHARS},_KWARGS=[TagInValueNameSpace(),TagInValueNameSpace()......])")








class HEADER:
    def __init__(self) -> None: 
        self.TAGCONTENTS={} 
    def replaceKwargsValue(self,TagName,Kwargs,Value):
        self.getFirstTag(TagName).replaceKwargValue(Kwargs,Value)
    def replaceMainValue(self,TagName,Value):
        self.getFirstTag(TagName).replaceMainValue(Value)
    @classmethod
    def getParse(cls,stringvector):
        self=HEADER()
        
        HEADER_ROWS=stringvector.split("\n")
        for row in HEADER_ROWS:
            TAGv=TAGS().getParse(row)
            self.TAGCONTENTS[TAGv.TAG_UUID]=TAGv
        return self
    
    def addTag(self,TagName=None,value=None):
        TAGv=TAGS().createTag(TagName,value)
        self.TAGCONTENTS[TAGv.TAG_UUID]=TAGv
        return self

    def getTagUid(self,tagName) -> dict:
        tags={} 
        for tagid,TAGv in self.TAGCONTENTS.items(): 
            if tagName.lower() in ";".join([TAGv.RESPONSENAME,TAGv.REQUESTNAME]).lower(): 
                tags[tagid]=TAGv 
        return tags
    def getFirstTag(self,tagName) -> TAGS:
        for tagid,TAGv in self.TAGCONTENTS.items(): 
            if tagName in ";".join([TAGv.RESPONSENAME,TAGv.REQUESTNAME]): 
                return TAGv 
    def delTags(self,*taguuids):
        for tagid in taguuids:
            del self.TAGCONTENTS[tagid]
            
    @property
    def getTagRequestNames(self):
        return [TAGv.REQUESTNAME for TAGv in self.TAGCONTENTS.values()]
    def __repr__(self):
        vals=list(self.TAGCONTENTS.values()) 
        return f"[\n\t{vals[0]},\n\t.......\n\t{vals[-1]}\n]"
    
