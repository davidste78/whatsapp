from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import ImageDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import LocationMediaMessageProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import VCardMediaMessageProtocolEntity
import urllib2
import urllib
import time
import datetime
import json
import re

class EchoLayer(YowInterfaceLayer):

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        
        if messageProtocolEntity.getType() == 'text':
            self.onTextMessage(messageProtocolEntity)

        if not messageProtocolEntity.isGroupMessage():
            if messageProtocolEntity.getType() == 'media':
                self.onMediaMessage(messageProtocolEntity)
    
    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
        self.toLower(ack)
    
    def handleDebugEcho(self,messageProtocolEntity):
        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())
        
        outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                                                                  messageProtocolEntity.getBody(),
                                                                  to = messageProtocolEntity.getFrom())
            
        print("Echoing %s to %s" % (messageProtocolEntity.getBody(), messageProtocolEntity.getFrom(False)))
        if messageProtocolEntity.isGroupMessage():
            print("%s %s "% (messageProtocolEntity.getParticipant(), messageProtocolEntity.getParticipant(False)))
                                                                  
        #send receipt otherwise we keep receiving the same message over and over
        self.toLower(receipt)
        self.toLower(outgoingMessageProtocolEntity)

    def onTextMessage(self,messageProtocolEntity):
        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())
        
        message = messageProtocolEntity.getBody()
        message = message.decode('ascii', 'ignore')

        debugEcho = False
    
        if debugEcho == True:
            self.handleDebugEcho(messageProtocolEntity)
            return
        
        if message == "":
            self.toLower(receipt)
            print("Got invalid message")
            return
        
        groupId = messageProtocolEntity.getFrom()
        
        if messageProtocolEntity.isGroupMessage():
            sender = messageProtocolEntity.getParticipant()
            senderPhone = messageProtocolEntity.getParticipant(False)
        else:
            sender = groupId
            senderPhone = groupId.split('@')[0]
        
        print "got message " + message
        print "groupId " + groupId
        print "sender " + sender
        print "sender phone " + senderPhone
        
        jsonData = { 'message':message.encode('utf8'), 'groupId':groupId, 'sender':sender, 'senderPhone':senderPhone }
        
        dataString = json.dumps(jsonData)

        print "send json" + dataString
        
        # Set the request authentication headers
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d %H:%M:%S')
        headers = {'DecibelAppID': 'My App ID','DecibelAppKey': 'app key', 'DecibelTimestamp': timestamp}

        # Send the GET request
        url = 'http://payagent.elasticbeanstalk.com/payAgentRest/imInterface/v1/' + urllib.quote(dataString)
        #url = 'http://localhost:8080/PayAgent/payAgentRest/imInterface/v1/' + urllib.quote(dataString)
        print "url:" + url
        request = urllib2.Request(url, None, headers)
        
        gotError = 0
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            gotError = 1
        except urllib2.URLError, e:
            gotError = 1
        except httplib.HTTPException, e:
            gotError = 1
        except Exception:
            gotError = 1

        if gotError == 1:
            self.toLower(receipt)
            print("Got urllib2.urlopen error")
            return


        resp = response.read()

        # Read the response
        #        if req.has_data() == True:
        #   resp = urllib2.urlopen(req).read()
        #else:
        #   print "Error on URL request"
        #   resp = "{}"
        
        print "rest json:" + resp
        
        j = json.loads(resp)
        
        restResp = ""
        if 'message' in j:
            restResp = j['message']
    
        print "rest response:" + restResp
        
        if restResp != "":
            outgoingMessageProtocolEntity = TextMessageProtocolEntity(restResp, to = messageProtocolEntity.getFrom())
            
            print("Got '%s' Response '%s' to %s name %s" % (message, restResp, messageProtocolEntity.getFrom(False), messageProtocolEntity.getParticipant()))
            #send receipt otherwise we keep receiving the same message over and over
            self.toLower(receipt)
            self.toLower(outgoingMessageProtocolEntity)
        else:
            #send receipt otherwise we keep receiving the same message over and over
            self.toLower(receipt)
            print("Got '%s' , not responding" % message)

    def onMediaMessage(self, messageProtocolEntity):
        if messageProtocolEntity.getMediaType() == "image":
            
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())

            outImage = ImageDownloadableMediaMessageProtocolEntity(
                messageProtocolEntity.getMimeType(), messageProtocolEntity.fileHash, messageProtocolEntity.url, messageProtocolEntity.ip,
                messageProtocolEntity.size, messageProtocolEntity.fileName, messageProtocolEntity.encoding, messageProtocolEntity.width, messageProtocolEntity.height,
                messageProtocolEntity.getCaption(),
                to = messageProtocolEntity.getFrom(), preview = messageProtocolEntity.getPreview())

            print("Echoing image %s to %s" % (messageProtocolEntity.url, messageProtocolEntity.getFrom(False)))

            #send receipt otherwise we keep receiving the same message over and over
            self.toLower(receipt)
            self.toLower(outImage)

        elif messageProtocolEntity.getMediaType() == "location":

            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())

            outLocation = LocationMediaMessageProtocolEntity(messageProtocolEntity.getLatitude(),
                messageProtocolEntity.getLongitude(), messageProtocolEntity.getLocationName(),
                messageProtocolEntity.getLocationURL(), messageProtocolEntity.encoding,
                to = messageProtocolEntity.getFrom(), preview=messageProtocolEntity.getPreview())

            print("Echoing location (%s, %s) to %s" % (messageProtocolEntity.getLatitude(), messageProtocolEntity.getLongitude(), messageProtocolEntity.getFrom(False)))

            #send receipt otherwise we keep receiving the same message over and over
            self.toLower(outLocation)
            self.toLower(receipt)
        elif messageProtocolEntity.getMediaType() == "vcard":
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())
            outVcard = VCardMediaMessageProtocolEntity(messageProtocolEntity.getName(),messageProtocolEntity.getCardData(),to = messageProtocolEntity.getFrom())
            print("Echoing vcard (%s, %s) to %s" % (messageProtocolEntity.getName(), messageProtocolEntity.getCardData(), messageProtocolEntity.getFrom(False)))
            #send receipt otherwise we keep receiving the same message over and over
            self.toLower(outVcard)
            self.toLower(receipt)
