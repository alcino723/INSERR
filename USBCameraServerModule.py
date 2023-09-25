import socket
import struct
import numpy as np
import cv2 as cv # pip install opencv-python
from ModuleBase import Module
from ModuleBase import ModuleManager
from pubsub import pub



class USBCameraHandler(Module):
    def __init__(self):
        super().__init__()

        self.conn = None
        self.addr = None
        self.connected = False
        self.PORT = 8080

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.bind(("", self.PORT))
        self.socket.listen()
    
    # waits for client connection
    def wait_for_client(self):
        self.conn, self.addr = self.socket.accept()
        self.connected = True
        print(f"USB Connected {self.addr}")
    
    # receives camera frame and publish it out
    def run(self):
        if self.connected:
            # try:

            # Receive the frame size from the client
            frame_size_data = self.conn.recv(struct.calcsize('<L'))
            if frame_size_data:
                frame_size = struct.unpack('<L', frame_size_data)[0]

                # Receive the frame data from the client
                frame_data = b''
                while len(frame_data) < frame_size:
                    data = self.conn.recv(frame_size - len(frame_data))
                    if not data:
                        break
                    frame_data += data

                # Decode the MJPEG data and convert it to a BGR image
                frame = cv.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv.IMREAD_COLOR)

                pub.sendMessage("ethernet.usbcam", message = {"data": frame})
            else:
                self.connected = False
                self.conn.close()
                self.socket.close()
                print(f"USB Disconnected from {self.addr}")
                pub.sendMessage("ethernet.usbcam", message = {"data": 0})
                cv.destroyAllWindows()
                self.wait_for_client()
            
            # except socket.error:
            #     self.connected = False
            #     self.socket.close()
            #     print(f"USB Disconnected from {self.addr}")
            #     self.wait_for_client()
        else:
            self.wait_for_client()

class USBCameraDisplay(Module):
    def __init__ (self):
        super().__init__()

        pub.subscribe(self.message_listener, "ethernet.usbcam")
    
    def message_listener(self, message):
        # check if message['data'] is an image or 0, if it is 0 check if there are cv windows open, destroy them
        if type(message["data"]) == np.ndarray:
            cv.imshow("USB Camera", message["data"])
            cv.waitKey(1)
        else:
            cv.destroyAllWindows()



if __name__ == "__main__":
    USBCameraHandler = USBCameraHandler()
    USBCameraDisplay = USBCameraDisplay()

    USBCameraHandler.start(80)
    USBCameraDisplay.start(1)


