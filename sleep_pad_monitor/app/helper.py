def len_frame(frame_length):
    return int(frame_length[0], 16) + (int(frame_length[1], 16) << 8)

def hex_to_ascii(frame_id):
    return ''.join([chr(int(byte, 16)) for byte in frame_id])

def str_to_hex(string):
    return [f"{ord(char):02X}" for char in string]

def int_to_hex(integer, byte_length):
    return [f"{byte:02X}" for byte in integer.to_bytes(byte_length, byteorder='little')]

def flatten_list(nested_list):
    return [item for sublist in nested_list for item in (sublist if isinstance(sublist, list) else [sublist])]