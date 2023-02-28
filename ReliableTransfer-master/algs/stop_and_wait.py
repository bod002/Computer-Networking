import logging
import socket
import math
import os.path
import os
from algs.utils import load_file
from algs.udp_wrapper import UdpWrapper
from algs.texcept import TransferFailed
import time


from datetime import datetime, timedelta

log = logging.getLogger(__name__)

class StopAndWait:
    # see https://en.wikipedia.org/wiki/Stop-and-wait_ARQ
    def __init__(self, retries=5):
        self.retries = retries
        self.timeout = timedelta(seconds=5)

    def run_server(self, outdir, addr, mtu):
        "run the server on the given addr/port/mtu, files are stored in outdir"
        
        #extra 6 spaces for the header
        mtu = mtu + 6
        
        # make sure directory exists
        os.makedirs(outdir, exist_ok=True)

        # create the socket to listen on
        sock = UdpWrapper(addr)

        # use blocking on the server.
        sock.setblocking(True)

        # bind the socket to the (address, port)
        sock.bind(addr)
        in_xfr = False
        outfile = None
        last = datetime.now() - self.timeout

        oldChecksumInBytes = 0

        log.info("Server started on {}".format(addr))
        while True:
            # wait for some data to arrive
            data,remote_addr = sock.recvfrom(mtu)

            if in_xfr and datetime.now() - last > self.timeout:
                # we got something but it's been too long, abort
                log.info("Abort transfer due to timeout.".format())
                in_xfr = False
                if outfile:
                    outfile.close()
                    outfile = None

            if in_xfr:
                # we are in a transfer, check for end of file
                if data[:9] == B"///END\\\\\\":#maby change for header
                    log.info("Done receiving file from {}.".format(
                        filepath, remote_addr))
                    in_xfr = False
                    outfile.close()
                    outfile = None
                    # let the client know we are done (ack the END message)
                    sock.sendto(B"OKEND", remote_addr)
                else:
                    # else we got a chunk of data
                    log.debug("Got a chunk!")
                    
                    #gets the checksum in bytes stong form
                    checksum = self.SumOfBits(data[6:])
                    checksumInBytes = bytes(str(checksum),'utf-8')

                    #makes checksum 5 digits
                    while len(str(checksumInBytes))<8:
                        Zero2front = bytes(str(0),'utf-8')
                        checksumInBytes = Zero2front+ checksumInBytes
                    log.info("{}".format(checksumInBytes)) #####

                    #gathers header from the UDP paylaod
                    recivedSequence = data[0:1]
                    recivedChecksum = data[1:6]
                    #get sequence in int
                    cint=int.from_bytes(recivedSequence,byteorder="big")
                    
                    log.info("{}{}{}{}".format(cint,tint,recivedChecksum,checksumInBytes)) #####

                    #sequence down
                    if data == B'sequenceDown':
                        tint=int.from_bytes(expectedSequence,byteorder="big")
                        tint=tint-1
                        expectedSequence = tint.to_bytes(1,byteorder="big")                        
                    #sequence up
                    if data == B'sequenceUp':
                        tint=int.from_bytes(expectedSequence,byteorder="big")
                        tint=tint+1
                        if tint == 253: #so counter dosen't exeed one byte
                            tint = 5
                        expectedSequence = tint.to_bytes(1,byteorder="big")
                    #if message recived proporly (duplicate will fail this anyway)
                    elif recivedSequence == expectedSequence and recivedChecksum[1:5] == checksumInBytes[1:5]:
                        # just write the data...
                        outfile.write(data[6:])
                        log.info("propor recive {}".format(data))
                    
                        # and send an ack with header of checksum and sequence
                        sock.sendto(expectedSequence + checksumInBytes + B'ACK', remote_addr)
                    
                        #iterate the sequence as if the client has done so as well
                        tint=int.from_bytes(expectedSequence,byteorder="big")
                        tint=tint+1
                        if tint == 253: #so counter dosen't exeed one byte
                           tint = 5
                        expectedSequence = tint.to_bytes(1,byteorder="big")
                    #else message not recived proporly
                    else:

                        #duplicate case or repeat message becuase of droped ACK
                        #if recivedChecksum[0:1] != b'0':
                        if cint < tint:
                            if recivedChecksum[0:1] != b'0':
                                temp = int.from_bytes(expectedSequence,byteorder="big")
                                temp=temp-1
                                tempSequence = temp.to_bytes(1,byteorder="big")
                                sock.sendto(tempSequence + checksumInBytes + B'ACK', remote_addr)
                            else:
                                nothingcode = 78
                                log.info("server drops duplicate sent")
                                #sock.sendto(expectedSequence + B'duped_or_dropped', remote_addr)
                                #log.info("duplicate case drop: {}".format(recivedChecksum))
                        elif cint > tint:
                            sock.sendto(expectedSequence + checksumInBytes + B'NAKS123', remote_addr)
                        else:
                            sock.sendto(B'NAK', remote_addr)

                oldChecksumInBytes = checksumInBytes

            else:
                # we are not in a transfer, check for begin
                if data[:5] == B'BEGIN':
                    #create sequence for server
                    tint = 0
                    expectedSequence = tint.to_bytes(1,byteorder="big")
                    # parse the message to get mtu and filename
                    smsg = data.decode('utf-8').split('\n')
                    beginmsg = smsg[0]
                    filename = smsg[1]
                    filepath = os.path.join(outdir, filename)

                    # check mtu
                    remote_mtu= int(beginmsg.split("/")[1])
                    if remote_mtu > mtu:
                        log.error("Cannot receive {} from {}, MTU({}) is too large.".format(
                            filepath, remote_addr, remote_mtu))
                        # send an error to the client
                        sock.sentdo(B'ERROR_MTU', remote_addr)
                    else:
                        log.info("Begin receiving file {} from {}.".format(
                            filepath, remote_addr))
                        outfile = open(filepath, 'wb')
                        in_xfr = True
                        # ack the begin message to the client
                        sock.sendto(B'OKBEGIN', remote_addr)
                else:
                    # we got something unexpected, ignore it.
                    log.info("Ignoreing junk, not in xfer.")
            last = datetime.now()

    def begin_xfr(self, dest, filename, mtu):
        # create a socket to the destination (addr, port)
        sock = UdpWrapper(dest)

        #strip any path chars from filename for security
        filename = os.path.basename(filename)

        # timeout on recv after 1 second.
        sock.settimeout(1)
        tries = 0

        # retry until we get a response or run out of retries.
        while tries < self.retries:
            # construct the BEGIN message with MTU and filename
            msg = "BEGIN/{}\n{}".format(mtu, filename).encode('utf-8')

            # send the message
            sock.sendto(msg, dest)
            try:
                # wait for a response
                data, addr = sock.recvfrom(mtu)
            except socket.timeout:
                log.info("No response to BEGIN message, RETRY")
                tries += 1
                continue
            break
        # if we ran out of retries, raise an exception.
        if (tries >= self.retries):
            raise TransferFailed("No response to BEGIN message.")

        # if we got a response, make sure it's the right one.
        if data != B"OKBEGIN":
            raise TransferFailed("Bad BEGIN response from server, got {}".format(
                data
            ))

        # return the socket so we can use it for the rest of the transfer.
        return sock

    def end_xfr(self, sock, dest, mtu):
        # send the END message
        tries = 0
        while tries < self.retries:
            # send the message
            sock.sendto(B"///END\\\\\\", dest)
            try:
                # wait for a response
                data, addr = sock.recvfrom(mtu)
            except socket.timeout:
                log.info("No response to END message, RETRY")
                tries += 1
                continue
            break
        if (tries >= self.retries):
            raise TransferFailed("No response to END message.")
        # if we got a response, make sure it's the right one.
        if data != B"OKEND":
            raise TransferFailed("Bad END response from server, got {}".format(
                data
            ))

    def xfr(self, sock, payload, dest, mtu):
        newint = 0
        sequence = newint.to_bytes(1,byteorder="big")
        prevClientChecksumInBytes = 0
        # send each chunk, waiting for an ACK
        for i,chunk in enumerate(payload):
            tries = 0
            log.info("Send chunk {} of {}".format(i, len(payload)-1))
            time.sleep(.1)
            #gets the checksum in bytes stong form
            checksum = self.SumOfBits(chunk)
            clientChecksumInBytes = bytes(str(checksum),'utf-8')
            log.info("{}".format(clientChecksumInBytes)) #####

            #makes checksum 5 digits
            while len(str(clientChecksumInBytes))<8:
                Zero2front = bytes(str(0),'utf-8')
                clientChecksumInBytes = Zero2front+ clientChecksumInBytes
            
            log.info("{}".format(clientChecksumInBytes)) #####

            newChunk = sequence + clientChecksumInBytes + chunk 
            impissed = 0

            while tries < self.retries:
                # send the chunk that will be distingished if duplicate rater than a resend
                if tries > 0:
                    newChunk = sequence + bytes(str(tries),'utf-8') + clientChecksumInBytes[1:5] + chunk
                    sock.sendto(newChunk, dest)
                else:
                    sock.sendto(newChunk, dest)

                try:
                    # wait for an ACK
                    data, addr = sock.recvfrom(mtu)

                    #gets the checksum in bytes sting form from the response
                    responsChecksumInBytes = data[1:6]

                except socket.timeout:
                    log.info("No response to CHUNK message, RETRY")
                    tries += 1
                    continue
                
                #gets inteteger sequence number of the server
                serverSequenceInt = int.from_bytes(data[0:1],byteorder="big")

                # if we got an ACK, break out of the loop (chucnk was received)
                if data[6:] == B"ACK" and serverSequenceInt == newint:
                    log.info("good ACK recived {}".format(data))
                    #change sequence
                    newint=int.from_bytes(sequence,byteorder="big")
                    newint=newint+1
                    if newint == 253:
                        newint = 5
                    sequence = newint.to_bytes(1,byteorder="big")
                    break
                else:
                    log.info("Bad response from server, got {} instead of ACK, RETRY".format(
                        data))
                    log.info("{} {} {}".format(responsChecksumInBytes,clientChecksumInBytes,prevClientChecksumInBytes))
                    #duplicated ACK
                    if data[6:] == B'ACK' and serverSequenceInt < newint:
                        log.info("fake ACK")
                        #sock.sendto(B'sequenceDown',dest)
                    if data[1:] == B'duped_or_dropped':
                        #previous ack was dropped
                        if serverSequenceInt != newint:
                            #sock.sendto(B'sequenceUp',dest)
                            newint=int.from_bytes(sequence,byteorder="big")
                            newint=newint+1
                            if newint == 253: #so counter dosen't exeed one byte
                                newint = 5
                            sequence = newint.to_bytes(1,byteorder="big")
                            break
                        #dup message case
                        else:
                            sock.sendto(B'sequenceDown',dest)
                            break
                    #duplicate agnolagment message case
                    elif serverSequenceInt == newint and responsChecksumInBytes == prevClientChecksumInBytes:
                        break
                    #nak after droped agnolagment (ACK) message case
                    if data[6:] == B'NAKS' and responsChecksumInBytes == clientChecksumInBytes:
                        newint=int.from_bytes(sequence,byteorder="big")
                        newint=newint+1
                        if newint == 253: #so counter dosn't exeed one byte
                            newint = 5
                        sequence = newint.to_bytes(1,byteorder="big")
                        break

                    #if data[6:] == B'NAK' and responsChecksumInBytes == clientChecksumInBytes:
                        #nak after droped agnolagment (ACK) message case
                    #    if sequence == b"1":
                    #        sequence = b"0"
                    #    else:
                    #        sequence = b"1"
                    #    break
                    #droped message nak recived as a ack case 
                    #if data == B'NAK_lastTwo':
                    #    sock.sendto(prevChunk, dest)
                    #    sock.sendto(newChunk, dest)
            if (tries >= self.retries):
                raise TransferFailed("No response to CHUNK message.")

            prevChunk = newChunk
            prevClientChecksumInBytes = clientChecksumInBytes

    def chunk(self, payload, mtu):
        "break a payload into mtu sized chunks"
        # simple chunking by MTU
        chunks = math.ceil(len(payload) / mtu)
        return [payload[i*mtu:(i+1)*mtu] for i in range(chunks)], len(payload)

    def send_file(self, filename, dest, mtu):
        "Entrypoint for stop and wait sending"
        st = datetime.now()
        log.info("Sending with stop-and-wait {} --> {}:{} [MTU={}].".format(
            filename, dest[0], dest[1], mtu))

        # break the file into mtu sized pieces
        payload, total_bytes = self.chunk(load_file(filename), mtu)

        # begin the transfer
        s = self.begin_xfr(dest, filename, mtu)

        # send the chunks
        #mtuPlusHeader
        self.xfr(s, payload, dest, mtu)

        time.sleep(3)

        # end the transfer
        self.end_xfr(s, dest, mtu)

        # print stats
        et = datetime.now()
        seconds = (et-st).total_seconds()
        log.info("Sent with stop-and-wait {} in {} seconds = {:.0f} bps.".format(
            filename, seconds,
            total_bytes / seconds))

        return True
    
    def SumOfBits(self, listofBits):
        "adds up all the bits in a list of bits for the checksum"
        temp = 0
        for i in listofBits:
            temp = temp + i
        return temp

# singleton
sw = StopAndWait()