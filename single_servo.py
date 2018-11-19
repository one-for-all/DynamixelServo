# This Demo Turns a Single Servo back and forth between
# 0 and 300 Degrees (max range for DX 117)
import os

# OS specifc implementation of getch()
if os.name == "nt":
    import msvcrt

    def getch():
        return msvcrt.getch().decode()
else:
    import sys
    import tty
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import *

### Connection Specific Constants
# Protocal version
PROTOCOL_VERSION            = 1.0

DXL_ID                      = 0  # Set this to the ID of the servo that we are controlling
BAUDRATE                    = 57600  # Dynamixel default baudrate
DEVICENAME                  = '/dev/ttyUSB0'  # Check which port is being used on your controller
       # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*

### Servo Specific Constants
# Control table address
ADDR_DX_TORQUE_ENABLE       = 24
ADDR_DX_GOAL_POSITION       = 30
ADDR_DX_PRESENT_POSITION    = 36

TORQUE_ENABLE                = 1  # Value for enabling the torque
TORQUE_DISABLE              = 0  # Value for disabling the torque
DXL_MINIMUM_POSITION_VALUE  = 0  # Dynamixel will rotate between this value
DXL_MAXIMUM_POSITION_VALUE  = 1023  # and this value (note that the Dynamixel would not move when the position value is out of movable range. Check e-manual about the range of the Dynamixel you use.)
DXL_MOVING_STATUS_THRESHOLD = 10  # Dynamixel moving status threshold

COMM_SUCCESS                = 0  # Communication Success result value
COMM_TX_FAIL                = -1001  # Communication Tx Failed

ESC_ASCII_VALUE             = 0x1b


def main():
    portHandler = PortHandler(DEVICENAME)

    packetHandler = PacketHandler(PROTOCOL_VERSION)

    if portHandler.openPort():
        print("Succeeded to open the port")
    else:
        print("Failed to open the port")
        print("Press any key to terminate")
        getch()
        quit()

    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
    else:
        print("Failed to change the baudrate")
        print("Press any key to terminate")
        getch()
        quit()

    # Enable Dynamixel Torque
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_DX_TORQUE_ENABLE, TORQUE_ENABLE)
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))
    else:
        print("Dynamixel has been successfully connected")

    goal_positions = [DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE]
    index = 0
    while True:
        print("Press any key to continue! (or press ESC to quit!)")
        if getch() == chr(0x1b):
            break

        goal_pos = goal_positions[index]
        # Write goal position
        dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_DX_GOAL_POSITION, goal_pos)
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % packetHandler.getRxPacketError(dxl_error))

        # Execute until error within threshold
        while True:
            # Read present position
            dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_DX_PRESENT_POSITION)
            if dxl_comm_result != COMM_SUCCESS:
                print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                print("%s" % packetHandler.getRxPacketError(dxl_error))

            print("[ID:%03d] GoalPos:%03d  PresPos:%03d" % (DXL_ID, goal_pos, dxl_present_position))

            if abs(goal_pos - dxl_present_position) < DXL_MOVING_STATUS_THRESHOLD:
                break

        index = 1 - index # Toggle index between 1 and 0

    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_DX_TORQUE_ENABLE, TORQUE_DISABLE)
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))

if __name__ == "__main__":
    main()