import helper as Helper

def read_command_content_0x80(content):
    # Prompt the server important information, the content of which is an ASCII string.
    # Content: [0x00]: The length or structure of the fetch instruction is incorrect
    # Content: [0x01]: The device is powered on and restarted.
    # Content: [0x02]+[4byte recording start date]+[22byte data length]: Add a sleep report.
    # Reply: If the server does not use frame type [0x14] to read data, the device will retransmit every 1 minute. A total of 3 times will be issued.
    # Contents: [0xF0]: The device is waiting for firmware update.
    STATUS = {
        "00": "INCORRECT_DATA",
        "01": "POWERED_AND_RESTARTED",
        "02": "ADDED_SLEEP_REPORT",
        "F0": "WAITING_FIRMWARE_UPDATE"
    }
    status = content[0]
    sleep_report = None
    if status == '02':
        start_date = int(content[1], 16) + (int(content[2], 16) << 8) + (int(content[3], 16) << 16) + (int(content[4], 16) << 24)
        data_length = Helper.hex_to_ascii(content[5:])
        sleep_report = {
            "start_date": start_date,
            "data_length": data_length
        }
    data = {
        "status": STATUS.get(status, "UNKNOWN"),
        "sleep_report": sleep_report
    }
    return data


def read_command_content_0x81(content):
    """
    content: data of the past 30 seconds.
    Request to retransmit the past 120 seconds of data. The returned content package is 360 bytes, a total of 30 groups, each group is 12 bytes.
    The structure of each group is: [serial number 1byte]+[time 4byte] +[state 1byte]+[heart rate 1byte]+[respiration rate 1byte]+[SDATA 2byte]+[PDATA 2byte]
    If [time 4Byte]=0x00000000, this piece of data is invalid.
    """
    content_length = len(content)
    print(f"Content length: {content_length}")
    if content_length != 360:
        print(f"Invalid content length: {content}")
        return
    data = []
    for i in range(0, content_length, 12):
        group = content[i:i+12]
        serial_number = int(group[0], 16) # Cycle from 0 to 119
        timestamp = int(group[1], 16) + (int(group[2], 16) << 8) + (int(group[3], 16) << 16) + (int(group[4], 16) << 24)
        status = int(group[5], 16)
        heart_rate = int(group[6], 16) # The value is 0 when out of bed or when it cannot be calculated.
        respiration_rate = int(group[7], 16) / 10 # Its real value = byte value/10. The value is 0 when out of bed or when it cannot be calculated.
        sdata = int(group[8], 16) + (int(group[9], 16) << 8)
        pdata = int(group[10], 16) + (int(group[11], 16) << 8)
        obj = {
            "serial_number": serial_number,
            "timestamp": timestamp,
            "status": status,
            "heart_rate": heart_rate,
            "respiration_rate": respiration_rate,
            "sdata": sdata,
            "pdata": pdata
        }
        data.append(obj)
    return data


def read_command_content_0x82(content):
    """
    content: data for the past 30 minutes.
    content package is 450 bytes, a total of 30 groups, each group is 15 bytes.
    The structure of each group is: [serial number 1byte]+[time 4byte]+[state 1byte]+[heart rate 1byte]+[respiration rate 1byte] +[body movement 1byte]+[snoring number 1byte]+[respiratory disorder number] 1byte]+[PTHD 2byte]+[TEMP 2byte]
    If [time 4Byte]=0x00000000, this piece of data is invalid.
    """
    content_length = len(content)
    print(f"Content length: {content_length}")
    if content_length != 450:
        print(f"Invalid content length: {content}")
        return
    data = []
    for i in range(0, content_length, 15):
        group = content[i:i+15]
        serial_number = int(group[0], 16) # Cycle from 0 to 119
        timestamp = int(group[1], 16) + (int(group[2], 16) << 8) + (int(group[3], 16) << 16) + (int(group[4], 16) << 24)
        status = int(group[5], 16)
        heart_rate = int(group[6], 16) # The value is 0 when out of bed or when it cannot be calculated.
        respiration_rate = int(group[7], 16) / 10 # Its real value = byte value/10. The value is 0 when out of bed or when it cannot be calculated.
        body_motion = int(group[8], 16) # the number of body movements per minute.
        number_snore = int(group[9], 16) # the number of snores per minute.
        breathing_disorder = int(group[10], 16) # the number of respiratory disturbances per minute.
        pthd = int(group[11], 16) + (int(group[12], 16) << 8)
        temp = int(group[13], 16) + (int(group[14], 16) << 8)
        obj = {
            "serial_number": serial_number,
            "timestamp": timestamp,
            "status": status,
            "heart_rate": heart_rate,
            "respiration_rate": respiration_rate,
            "body_movement": body_motion,
            "snoring_number": number_snore,
            "respiratory_disorder": breathing_disorder,
            "pthd": pthd,
            "temp": temp
        }
        data.append(obj)
    return data


def read_command_content_0x83(content):
    """
    content: None
    Forcibly stop working in either mode, leaving the device in standby mode. The indicator light will be blinking light. The device automatically enters the 0x20 working mode after the start timer is greater than or equal to 5 minutes. The device sends a command (excluding [0x08]:
    Heartbeat Reply) to reset the internal start timer.
    """
    return True


def read_command_content_0x84(content):
    """
    content [0x20] confirmation, and starts to work
    content [0x21] has already started before
    content [0x22] The instrument fails and cannot start
    """
    STATUS = {
        "20": "CONFIRMATION_AND_START",
        "21": "ALREADY_STARTED",
        "22": "FAILED_TO_START"
    }
    status = content[0]
    data = {
        "status": STATUS.get(status, "UNKNOWN")
    }
    return data


def read_command_content_0x85(content):
    """
    sent in server monitor mode. A total of 12 bytes, sent every 1 second.
    The content is [serial number 1byte]+[time 4byte] +[status 1byte]+[heart rate 1byte]+[respiration rate 1byte]+[SDATA 2byte]+[PDATA 2byte]
    status=0x01 get out of bed in this second; =0x02 move in this second; # =0x03 sit up in this second; =0x04 sleep in this second; =0x05 wake up in this second; =0x06 heavy object in this second; =0x07 snore in this second; =0x08 weak breathing;
    """
    STATUS = {
        "01": "GET_OUT_OF_BED",
        "02": "SPLIT_MOVEMENT",
        "03": "SIT_UP",
        "04": "SLEEP",
        "05": "WAKE_UP",
        "06": "HEAVY_OBJECT",
        "07": "SNORE",
        "08": "WEAK_BREATHING"
    }
    if len(content) != 12:
        print(f"Invalid content length: {content}")
        return
    serial_number = int(content[0], 16) # Cycle from 0 to 119
    timestamp = int(content[1], 16) + (int(content[2], 16) << 8) + (int(content[3], 16) << 16) + (int(content[4], 16) << 24)
    status = content[5]
    heart_rate = int(content[6], 16) # The value is 0 when out of bed or when it cannot be calculated.
    respiration_rate = int(content[7], 16) / 10 # Its real value = byte value/10. The value is 0 when out of bed or when it cannot be calculated.
    sdata = int(content[8], 16) + (int(content[9], 16) << 8)
    pdata = int(content[10], 16) + (int(content[11], 16) << 8)
    data = {
        "serial_number": serial_number,
        "timestamp": timestamp,
        "status": STATUS.get(status, "UNKNOWN"),
        "heart_rate": heart_rate,
        "respiration_rate": respiration_rate,
        "sdata": sdata,
        "pdata": pdata
    }
    return data


def read_command_content_0x86(content):
    # sent in server monitor mode. A total of 15 bytes, sent every 1 second.
    # The content is [serial number 1byte]+[time 4byte]+[status 1byte]+[heart rate 1byte]+[respiration rate 1byte] +[body movement 1byte]+[snoring number 1byte]+[respiratory disorder 1byte] +[PTHD 2byte]+[TEMP 2byte]
    #**
    # Status per minute =0x01 for the separation bed; =0x02 for the split movement; =0x03 for the sitting up; =0x04 for the sleep; =0x05 for the awake; =0x06 for the heavy object;
    #**
    if len(content) != 15:
        print(f"Invalid content length: {content}")
        return
    serial_number = int(content[0], 16) # Cycle from 0 to 119
    timestamp = int(content[1], 16) + (int(content[2], 16) << 8) + (int(content[3], 16) << 16) + (int(content[4], 16) << 24)
    STATUS = {
        "01": "GET_OUT_OF_BED",
        "02": "SPLIT_MOVEMENT",
        "03": "SIT_UP",
        "04": "SLEEP",
        "05": "AWAKE",
        "06": "HEAVY_OBJECT"
    }
    status = STATUS.get(content[5], "UNKNOWN")
    heart_rate = int(content[6], 16) # The value is 0 when out of bed or when it cannot be calculated.
    respiration_rate = int(content[7], 16) / 10 # Its real value = byte value/10. The value is 0 when out of bed or when it cannot be calculated.
    body_motion = int(content[8], 16) # the number of body movements per minute.
    number_snore = int(content[9], 16) # the number of snores per minute.
    breathing_disorder = int(content[10], 16) # the number of respiratory disturbances per minute.
    pthd = int(content[11], 16) + (int(content[12], 16) << 8)
    temp = int(content[13], 16) + (int(content[14], 16) << 8)
    data = {
        "serial_number": serial_number,
        "timestamp": timestamp,
        "status": status,
        "heart_rate": heart_rate,
        "respiration_rate": respiration_rate,
        "body_movement": body_motion,
        "snoring_number": number_snore,
        "respiratory_disorder": breathing_disorder,
        "pthd": pthd,
        "temp": temp
    }
    return data


def read_command_content_0x87(content):
    """
    # content: [mode 1byte] + [error 1byte] + [4byte time]
    # 0x00 stands for standby mode;=0x20 stands for server monitoring mode;=0x30 stands for data debugging mode;=0x40 stands for BLE debugging mode;=0xF0 means waiting for firmware update;
    # In the standby state of 0x00, you can use frame type [0x0B]: calibrate the clock, then frame type [0x04]: work mode setting starts to work
    # In the 0x20 state, you can wait for data;
    # At 0x30, you can use the frame type [0x03] stop command to make it stand by, and then start working again;
    # In 0x40, it is recommended to wait for it to return to the 0x00 state, because in the 0x40 state, the BLE communication is at a high priority. At this
    # time, the server sends the commands, except for the [0x07] query status, [0x08] heartbeat command and [0x0C] version query command. , other
    # commands do not respond.
    # =0xF0 means waiting for firmware update; at this time, the device is in the factory state, the firmware is not loaded, and the server needs to update
    # the firmware.
    """
    MODES = {
        "00": "STANDBY",
        "20": "SERVER_MONITORING",
        "30": "DATA_DEBUGGING",
        "40": "BLE_DEBUGGING",
        "F0": "WAITING_FIRMWARE_UPDATE"
    }
    mode = MODES.get(content[0], "UNKNOWN")
    error = int(content[1], 16)
    # 0x00 means no error;=any other value means the device is faulty and needs to be returned to the factory.
    timestamp = int(content[2], 16) + (int(content[3], 16) << 8) + (int(content[4], 16) << 16) + (int(content[5], 16) << 24)
    data = {
        "mode": mode,
        "error": error,
        "timestamp": timestamp
    }
    return data


def read_command_content_0x88(content):
    """
    Heartbeat Response, no content
    Since the device cannot determine its own networking status, the server needs to send a heartbeat every 1 minute. If it does not receive it for
    more than 5 minutes, the device will restart the wifi.
    """
    return True


def read_command_content_0x89(content):
    """
    pressure calibration
    content [0x00] calibration complete, content [0x01] can not be calibrated
    """
    STATUS = {
        "00": "CALIBRATION_COMPLETE",
        "01": "CANNOT_BE_CALIBRATED"
    }
    status = STATUS.get(content[0], "UNKNOWN")
    data = {
        "status": status
    }
    return data


def read_command_content_0x8A(content):
    """
    content [0x00] indicates that the parameter has been reset
    content [0x01] + [64byte parameter]
    Among them, there are 64byte parameters, each 4 bytes is a parameter, in order from Para1 to Para16, the format is float, the low order is in the front and the high order is in the back.
    content [0x02] indicates that the parameter has been modified
    content [0x03] indicates that the number of data bits is incorrect or the parameter is wrong
    """
    STATUS = {
        "00": "PARAMETER_RESET",
        "01": "PARAMETER_READ",
        "02": "PARAMETER_MODIFIED",
        "03": "INCORRECT_DATA"
    }
    status = STATUS.get(content[0], "UNKNOWN")
    data = {
        "status": status
    }
    return data


def read_command_content_0x8B(content):
    """
    the content is no, indicating that the device has finished setting the clock
    """
    return True


def read_command_content_0x8C(content):
    """
    Used to determine the device version and firmware version of the system.
    content [multi-bit characters]
    [multi-character]: something like: "Hardware_V2_HVER100_FVER100" contains name hardware_V2, device version number 100, firmware version number 100.
    """
    version = Helper.hex_to_ascii(content)
    data = {
        "version": version
    }
    return data


def read_command_content_0x8D(content):
    """
    firmware update response
    content [0x00] means it is ready. The device needs about 3 to 5 seconds to clear the storage space, and the server needs to wait.
    content [0x01]+[0x00]+[2byte packet number] indicates correct reception,
    Content [0x01]+[0x01]+[2byte packet number] indicates a receiving error
    Content [0x01]+[0x02]+[2byte packet number] indicates device write error

    content [0x02]+[0x00] indicates that the verification is over and ready to restart,
    content [0x02]+[0x01]+[2byte package sequence number] indicates that a package cannot be restarted if it is not completed.
    """
    status = "UNKNOWN"
    code = int(content[0], 16)
    if code == 0:
        status = "READY"
    if code == 1:
        error = int(content[1], 16)
        if error == 0:
            status = "CORRECT_RECEPTION"
        if error == 1:
            status = "RECEIVING_ERROR"
        if error == 2:
            status = "DEVICE_WRITE_ERROR"
    if code == 2:
        error = int(content[1], 16)
        if error == 0:
            status = "READY_TO_RESTART"
        if error == 1:
            status = "INCOMPLETED"
    data = {
        "status": status
    }
    return data


def read_command_content_0x93(content):
    """
    device storage report query
    content [15 groups of data], a total of 390 bytes
    Each group contains [4byte start time]+[22byte conclusion data]
    [Time 4byte]: If all 4bytes are 0xFF, the record is invalid.
    [22byte conclusion data] Each 2byte group, the low order is in the front and the high order is in the back. include:
    [2byte total sleep duration]: the length of the longest sleep period in a day, in minutes. Equal to 0 or 0xFFFF, the record is invalid. All conclusions are
    set to zero.
    [2byte sleep efficiency]: expressed as a percentage, the output is 0~100. It mainly focuses on the proportion of effective sleep time to total sleep time.
    [2byte sleep quality]: The score indicates the health of sleep, and the output is 0~100.
    [2byte number of turns over]: Indicates the number of turns over in the sleep data period.
    [2byte sleep time]: Indicates the time from bedtime to sleep, in minutes.
    [2byte number of getting out of bed]: Indicates the total number of getting out of bed from the start of bed entry to the end of sleep.
    [2byte sleep rhythm phase]: Sleep health indicator.
    [2byte slop1]: Reserved indicator, not used yet.
    [Start time of 2bytes]: The starting minute of the longest sleep, the value is one of 0~1440, which means that the longest sleep starts at a certain
    minute of the total report length of 1440 minutes in the current day. The exact time needs to use the start time of the report + this value * 60 seconds.
    [2bytes of breathing disorder index]: The breathing disorder index AHI during the entire sleep period
    [2byte total snoring times]: The total snoring times during the entire sleep period.
    In the device, the report generation of the previous day starts at 9:00 by default.
    """
    content_length = len(content)
    print(f"Content length: {content_length}")
    if content_length != 390:
        print(f"Invalid content length: {content}")
        return
    data = []
    for i in range(0, content_length, 26):
        group = content[i:i+26]
        timestamp = int(group[0], 16) + (int(group[1], 16) << 8) + (int(group[2], 16) << 16) + (int(group[3], 16) << 24)
        total_sleep_duration = int(group[4], 16) + (int(group[5], 16) << 8)
        if total_sleep_duration == 0 or total_sleep_duration == 0xFFFF:
            continue
        sleep_efficiency = int(group[6], 16) + (int(group[7], 16) << 8)
        sleep_quality = int(group[8], 16) + (int(group[9], 16) << 8)
        number_turns_over = int(group[10], 16) + (int(group[11], 16) << 8)
        sleep_time = int(group[12], 16) + (int(group[13], 16) << 8)
        number_get_out_of_bed = int(group[14], 16) + (int(group[15], 16) << 8)
        sleep_rhythm_phase = int(group[16], 16) + (int(group[17], 16) << 8)
        slop1 = int(group[18], 16) + (int(group[19], 16) << 8)
        start_time = int(group[20], 16) + (int(group[21], 16) << 8)
        breathing_disorder_index = int(group[22], 16) + (int(group[23], 16) << 8)
        total_snoring_times = int(group[24], 16) + (int(group[25], 16) << 8)
        obj = {
            "timestamp": timestamp,
            "total_sleep_duration": total_sleep_duration,
            "sleep_efficiency": sleep_efficiency,
            "sleep_quality": sleep_quality,
            "number_turns_over": number_turns_over,
            "sleep_time": sleep_time,
            "number_get_out_of_bed": number_get_out_of_bed,
            "sleep_rhythm_phase": sleep_rhythm_phase,
            "slop1": slop1,
            "start_time": start_time,
            "breathing_disorder_index": breathing_disorder_index,
            "total_snoring_times": total_snoring_times
        }
        data.append(obj)
    return data


def read_command_content_0x94(content):
    """
    device storage data read
    content [4byte start time]+[1byte serial number 0~11]+[data 480byte].
    content [4byte start time]+[1byte=0xFF]. Read error. Time or serial number is wrong.
    Returns the data of a certain 2-hour period of a report. Each 4byte of data is a group representing 1 minute of data, a total of 120 minutes of data.
    4byte is:
    [1byte status]:
    =0x01 get out of bed; =0x02 move; =0x03 sit up; =0x04 sleep; =0x05 wake up; =0x06 heavy object;
    =0x11 Deep (deep sleep);=0x12 Light (light sleep);=0x13 REM;=0x14 Wake (awake);=0x15 Out out of bed;=0x16 heavy object;
    The state is composed of analytic and non-analytical periods, so multiple states need to be displayed. When it is indicated, 0x04 and 0x12 are
    displayed in the same state (light sleep), 0x05 and 0x14 are in one state; 0x01 and 0x15 are in one state; 0x06 and 0x16 are not displayed temporarily.
    The displayed states include: getting out of bed, sitting up, awake, REM, light sleep, deep sleep
    [1byte heart rate]: Heart rate is an unsigned 1-byte integer. is the final comprehensive judgment value of the minute. Its true value = byte value. The
    value is 0 when there is an exit in this minute.
    [1byte breathing rate]: The breathing rate is an unsigned 1-byte integer. is the final comprehensive judgment value of the minute. Its real value = byte
    value/10. The value is 0 when there is an exit in this minute.
    [1byte body motion]: body motion is an unsigned 1-byte integer. Represents the number of body movements per minute.
    """
    content_length = len(content)
    print(f"Content length: {content_length}")
    if content_length < 480:
        print(f"Invalid content length: {content}")
        return
    start_time = int(content[0], 16) + (int(content[1], 16) << 8) + (int(content[2], 16) << 16) + (int(content[3], 16) << 24)
    serial_number = content[4]
    if serial_number == 'FF':
        print("Read error. Time or serial number is wrong.")
        return
    data_content = content[5:]
    data = []
    STATUS = {
        "01": "GET_OUT_OF_BED",
        "02": "SPLIT_MOVEMENT",
        "03": "SIT_UP",
        "04": "SLEEP",
        "05": "AWAKE",
        "06": "HEAVY_OBJECT",
        "11": "DEEP_SLEEP",
        "12": "LIGHT_SLEEP",
        "13": "REM",
        "14": "AWAKE",
        "15": "GET_OUT_OF_BED",
        "16": "HEAVY_OBJECT"
    }
    for i in range(5, len(data_content), 4):
        group = data_content[i:i+4]
        status = STATUS.get(group[0], "UNKNOWN")
        heart_rate = int(group[1], 16)
        respiration_rate = int(group[2], 16) / 10
        body_motion = int(group[3], 16)
        obj = {
            "status": status,
            "heart_rate": heart_rate,
            "respiration_rate": respiration_rate,
            "body_motion": body_motion
        }
        data.append(obj)
    data = {
        "start_time": start_time,
        "serial_number": serial_number,
        "data": data
    }
    return data

def read_command_content_0x97(content):
    """
    clear all data
    no content. Indicates completion.
    """
    return True

def read_client_command(command):
    frame_type = command[1]
    frame_length = Helper.len_frame(command[2:4])
    id = Helper.hex_to_ascii(command[4:14])
    content = command[14:-1]
    command_handlers = {
        '80': read_command_content_0x80,
        '81': read_command_content_0x81,
        '82': read_command_content_0x82,
        '83': read_command_content_0x83,
        '84': read_command_content_0x84,
        '85': read_command_content_0x85,
        '86': read_command_content_0x86,
        '87': read_command_content_0x87,
        '88': read_command_content_0x88,
        '89': read_command_content_0x89,
        '8A': read_command_content_0x8A,
        '8B': read_command_content_0x8B,
        '8C': read_command_content_0x8C,
        '8D': read_command_content_0x8D,
        '93': read_command_content_0x93,
        '94': read_command_content_0x94,
        '97': read_command_content_0x97,
    }
    handler = command_handlers.get(frame_type)
    if handler:
        data = handler(content)
        if data:
            print(f"ID: {id}, Frame Type: {frame_type}, Data: {data}")
            # send data to server
    else:
        print(f"Unknown command: {command}")
