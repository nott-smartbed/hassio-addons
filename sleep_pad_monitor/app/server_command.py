import time
import helper as Helper

def retransmission_30s():
    """
    Command: No
    """
    frame_type = '01'
    content = None
    return [frame_type, content]


def retransmission_30min():
    """
    Command: No
    """
    frame_type = '02'
    content = None
    return [frame_type, content]


def force_device_stop():
    """
    Command: No
    """
    frame_type = '03'
    content = None
    return [frame_type, content]


def set_working_mode(mode=None):
    """
    Command: [1byte data in hexadecimal]
    0x20 to enter server monitoring mode.
    0x30 to enter the data debugging mode.
    """
    frame_type = '04'
    MODE = {
        'SERVER_MONITORING': '20',
        'DATA_DEBUGGING': '30'
    }
    content = MODE['SERVER_MONITORING']
    if mode == 'DATA_DEBUGGING':
        content = MODE['DATA_DEBUGGING']
    return [frame_type, content]


def get_device_status():
    """
    Command: No
    """
    frame_type = '07'
    content = None
    return [frame_type, content]


def heart_beat_response():
    """
    Command: No
    """
    frame_type = '08'
    content = None
    return [frame_type, content]


def pressure_calibration():
    """
    Command: No
    """
    frame_type = '09'
    content = None
    return [frame_type, content]


def get_or_update_settings(mode, parameters=None):
    """
    Command: [0x00] means reset parameter
    Command: [0x01] means read parameter
    Command: [0x02]+[64byte parameter] means setting parameter
    """
    frame_type = '0A'
    MODE = {
        'RESET': '00',
        'READ': '01',
        'SET': '02'
    }
    content = MODE['READ']
    if mode == MODE['RESET']:
        content = MODE['RESET']
    return [frame_type, content]


def clock_calibration(timestamp=None):
    """
    Command: [0x0B] + [4byte time]
    """
    frame_type = '0B'
    ts = timestamp or int(time.time())
    print(f"ts: {ts}")
    content = Helper.int_to_hex(ts, 4)
    print(f"content: {content}")
    return [frame_type, content]


def get_device_firmware_version():
    """
    Command: no
    """
    frame_type = '0C'
    content = None
    return [frame_type, content]


def firmware_update():
    """
    Command: [0x00] +[2byte package number] means start updating, 2byte package number=bin file byte number divided by 512, low order in front and high order in back
    Command: [0x01] +[2byte package serial number]+[512byte content package] means to update a certain package
    Command: [0x02] Indicates that the update is complete and requires restarting the device
    """
    frame_type = '0D'
    content = None
    return [frame_type, content]


def device_storage_report_query():
    """
    Command: no
    """
    frame_type = '13'
    content = None
    return [frame_type, content]


def device_storage_data_read(start_time, serial_number=0):
    """
    Command: [4byte start time]+[1byte serial number 0~11]. The start time of 4byte is obtained from frame type [0x13].
    Serial numbers 0~11 represent: a total of 24 hours of data, read in 12 times.
    """
    frame_type = '14'
    ts = start_time or int(time.time())
    start_time_hex = Helper.int_to_hex(ts, 4)
    serial_number_hex = f"{serial_number:02X}"
    content = start_time_hex.append(serial_number_hex)
    return [frame_type, content]


def clear_all_data():
    frame_type = '17'
    content = None
    return [frame_type, content]

