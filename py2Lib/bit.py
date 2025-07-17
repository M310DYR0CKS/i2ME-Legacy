import socket
import sys
import os
import struct
import math
import time
import logging
import coloredlogs

# Logging setup
log = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", logger=log)

# Multicast settings
MCAST_GRP = '224.1.1.77'
MCAST_IF = '127.0.0.1'
BUF_SIZE = 1396
MULTICAST_TTL = 2
TEST_MESSAGE = b"This is a test"

# UDP socket setup
conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
conn.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(MCAST_GRP) + socket.inet_aton(MCAST_IF))

def get_next_msg_id():
    with open('./.temp/msgId.txt', "r") as f:
        msg_id = int(f.read().strip())
    with open('./.temp/msgId.txt', "w") as f:
        f.write(str(msg_id + 1))
    return msg_id

def send_test_block(msg_num, seg_num, mcast_port):
    for _ in range(3):
        p3 = struct.pack(">BHHHIIBBBBBBBI", 18, 1, 1, 8, msg_num, 0, seg_num,
                         0, 0, 8, 0, 0, 0, 67108864)
        p4 = struct.pack(">BHHHIIBBB", 18, 1, 1, 14, msg_num, 1, seg_num, 0, 0) + TEST_MESSAGE
        conn.sendto(p3, (MCAST_GRP, mcast_port))
        conn.sendto(p4, (MCAST_GRP, mcast_port))
        seg_num += 1
    return seg_num

def send_file(files, commands, num_segments, priority):
    mcast_port = 7787 if priority == 0 else 7788 if priority == 1 else None
    if mcast_port is None:
        log.critical("Invalid Priority: 0 = Routine, 1 = High Priority")
        sys.exit(1)

    msg_num = get_next_msg_id()
    seg_num = 0
    log.info(f"Sending {'High Priority' if priority else 'Routine'} Msg-{msg_num} to {MCAST_GRP}:{mcast_port}")

    for file_path, command in zip(files, commands):
        command_bytes = bytes(command + 'I2MSG', 'utf-8')
        command_len_bytes = len(command).to_bytes(4, byteorder='little')
        with open(file_path, 'ab') as f:
            f.write(command_bytes + command_len_bytes)

        packet_count = 1
        rounded_packets = math.ceil(os.path.getsize(file_path) / 1405) + 1
        segment_total = num_segments + 3
        start_flag = False
        rate_limit_counter = 0

        with open(file_path, "rb") as f:
            while (chunk := f.read(BUF_SIZE)):
                if not start_flag:
                    p1 = struct.pack(">BHHHIIBBBBBBBIBIBBB", 18, 1, 0, 16, msg_num, 0, seg_num, 0, 0, 8,
                                     segment_total, 3, 0, 0, 8, rounded_packets, 0, 0, 0)
                    conn.sendto(p1, (MCAST_GRP, mcast_port))
                    start_flag = True

                packet_hdr = struct.pack(">BHHHIIBBB", 18, 1, 0, 1405, msg_num, packet_count, 0, 0, 0)
                fec_hdr = struct.pack("<IBI", packet_count, 0, os.path.getsize(file_path))

                if len(chunk) < BUF_SIZE:
                    null_padding = bytes(BUF_SIZE - len(chunk))
                    conn.sendto(packet_hdr + fec_hdr + chunk + null_padding, (MCAST_GRP, mcast_port))
                else:
                    conn.sendto(packet_hdr + fec_hdr + chunk, (MCAST_GRP, mcast_port))

                log.debug(f"Sent packet #{packet_count}")
                packet_count += 1
                rate_limit_counter += 1

                if rate_limit_counter >= 1000:
                    time.sleep(2)
                    rate_limit_counter = 0

        seg_num += 1

    seg_num = send_test_block(msg_num, seg_num, mcast_port)

def send_command(commands, priority, msg_id=None):
    mcast_port = 7787 if priority == 0 else 7788 if priority == 1 else None
    if mcast_port is None:
        log.critical("Invalid Priority: 0 = Routine, 1 = High Priority")
        sys.exit(1)

    msg_num = msg_id if msg_id is not None else get_next_msg_id()
    seg_num = 0
    log.info(f"Sending {'High Priority' if priority else 'Routine'} Msg-{msg_num} to {MCAST_GRP}:{mcast_port}")

    for cmd in commands:
        cmd_bytes = cmd.encode('utf-8')
        cmd_path = './.temp/command'
        with open(cmd_path, 'wb') as f:
            f.write(cmd_bytes)

        cmd_size = os.path.getsize(cmd_path)
        command_tail = b'I2MSG' + cmd_size.to_bytes(4, 'little')
        with open(cmd_path, 'ab') as f:
            f.write(command_tail)

        packet_count = 1
        rounded_packets = math.ceil(os.path.getsize(cmd_path) / 1405) + 1
        start_flag = False
        rate_limit_counter = 0

        with open(cmd_path, "rb") as f:
            while (chunk := f.read(BUF_SIZE)):
                if not start_flag:
                    p1 = struct.pack(">BHHHIIBBBBBBBIBIBBB", 18, 1, 0, 16, msg_num, 0, seg_num, 0, 0, 8,
                                     4, 3, 0, 0, 8, rounded_packets, 0, 0, 0)
                    conn.sendto(p1, (MCAST_GRP, mcast_port))
                    start_flag = True

                packet_hdr = struct.pack(">BHHHIIBBB", 18, 1, 0, 1405, msg_num, packet_count, 0, 0, 0)
                fec_hdr = struct.pack("<IBI", packet_count, 0, os.path.getsize(cmd_path))

                if len(chunk) < BUF_SIZE:
                    chunk += bytes(BUF_SIZE - len(chunk))
                conn.sendto(packet_hdr + fec_hdr + chunk, (MCAST_GRP, mcast_port))

                log.debug(f"Sent packet #{packet_count}")
                packet_count += 1
                rate_limit_counter += 1

                if rate_limit_counter >= 1000:
                    time.sleep(10)
                    rate_limit_counter = 0

        seg_num += 1

    seg_num = send_test_block(msg_num, seg_num, mcast_port)
