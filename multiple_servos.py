# This Demo Turns 3 Servos back and forth independently
# Either daisy-chained or separately plugged
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

DXL_ID1                     = 0 # First Servo ID
DXL_ID2                     = 1 # Second Servo ID
DXL_ID3                     = 2 # Third Servo ID
BAUDRATE                    = 57600  # Dynamixel default baudrate
DEVICENAME                  = '/dev/ttyUSB0'  # Check which port is being used on your controller
       # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*

### Servo Specific Constants
# Control table address
ADDR_DX_TORQUE_ENABLE       = 24
ADDR_DX_GOAL_POSITION       = 30
ADDR_DX_PRESENT_POSITION    = 36

# Data Byte Length
LEN_DX_GOAL_POSITION       = 4
LEN_DX_PRESENT_POSITION    = 4

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

    # Initialize GroupSyncWrite instance
    groupSyncWrite = GroupSyncWrite(portHandler, packetHandler, ADDR_DX_GOAL_POSITION, LEN_DX_GOAL_POSITION)

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
    def enable_torque(dxl_id):
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_DX_TORQUE_ENABLE, TORQUE_ENABLE)
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
            quit()
        elif dxl_error != 0:
            print("%s" % packetHandler.getRxPacketError(dxl_error))
            quit()
        else:
            print("Dynamixel #{} has been successfully connected".format(dxl_id))

    enable_torque(DXL_ID1)
    enable_torque(DXL_ID2)
    enable_torque(DXL_ID3)

    # Add goal position value to the Syncwrite parameter storage
    def add_goal_param(dxl_id, param_goal):
        dxl_addparam_result = groupSyncWrite.addParam(dxl_id, param_goal)
        if dxl_addparam_result is not True:
            print("[ID:%03d] groupSyncWrite addparam failed" % dxl_id)
            quit()

    # Syncwrite goal position
    def sync_write_goal():
        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(dxl_comm_result))

    def clear_goal_param():
        groupSyncWrite.clearParam()

    def read_pos(dxl_id):
        dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, dxl_id, ADDR_DX_PRESENT_POSITION)
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
            return None
        elif dxl_error != 0:
            print("%s" % packetHandler.getRxPacketError(dxl_error))
            return None
        return dxl_present_position

    goal_positions = [DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE]
    index = 0
    while True:
        print("Press any key to continue! (or press ESC to quit!)")
        if getch() == chr(0x1b):
            break

        # Allocate goal position value into byte array
        goal_pos1 = goal_positions[index]
        param_goal1 = [DXL_LOBYTE(DXL_LOWORD(goal_pos1)),
                               DXL_HIBYTE(DXL_LOWORD(goal_pos1)),
                               DXL_LOBYTE(DXL_HIWORD(goal_pos1)),
                               DXL_HIBYTE(DXL_HIWORD(goal_pos1))]
        goal_pos2 = goal_positions[index]//2
        param_goal2 = [DXL_LOBYTE(DXL_LOWORD(goal_pos2)),
                               DXL_HIBYTE(DXL_LOWORD(goal_pos2)),
                               DXL_LOBYTE(DXL_HIWORD(goal_pos2)),
                               DXL_HIBYTE(DXL_HIWORD(goal_pos2))]
        goal_pos3 = goal_positions[index]//3
        param_goal3 = [DXL_LOBYTE(DXL_LOWORD(goal_pos3)),
                               DXL_HIBYTE(DXL_LOWORD(goal_pos3)),
                               DXL_LOBYTE(DXL_HIWORD(goal_pos3)),
                               DXL_HIBYTE(DXL_HIWORD(goal_pos3))]

        add_goal_param(DXL_ID1, param_goal1)
        add_goal_param(DXL_ID2, param_goal2)
        add_goal_param(DXL_ID3, param_goal3)
        sync_write_goal()
        clear_goal_param()


        # Execute until error within threshold
        while True:
            # Read present position
            dxl_present_pos1 = read_pos(DXL_ID1)
            dxl_present_pos2 = read_pos(DXL_ID2)
            dxl_present_pos3 = read_pos(DXL_ID3)

            print("[ID:%03d] GoalPos:%03d  PresPos:%03d\n\
                     [ID:%03d] GoalPos:%03d  PresPos:%03d\n\
                     [ID:%03d] GoalPos:%03d  PresPos:%03d\n\
                  "% (DXL_ID1, goal_pos1, dxl_present_pos1,
                        DXL_ID2, goal_pos2, dxl_present_pos2,
                        DXL_ID2, goal_pos3, dxl_present_pos3))

            if abs(goal_pos1 - dxl_present_pos1) < DXL_MOVING_STATUS_THRESHOLD and \
               abs(goal_pos2 - dxl_present_pos2) < DXL_MOVING_STATUS_THRESHOLD and \
               abs(goal_pos3 - dxl_present_pos3) < DXL_MOVING_STATUS_THRESHOLD:
                break

        index = 1 - index # Toggle index between 1 and 0


    # Disable Torque
    def disable_torque(dxl_id):
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_DX_TORQUE_ENABLE, TORQUE_DISABLE)
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % packetHandler.getRxPacketError(dxl_error))

    disable_torque(dxl_id1)
    disable_torque(dxl_id2)
    disable_torque(dxl_id3)

    # Close Port
    portHandler.closePort()

if __name__ == "__main__":
    main()