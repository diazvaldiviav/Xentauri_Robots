import cv2
import numpy as np
import math
import os,sys,time,json,base64
import spidev as SPI
from PIL import Image,ImageDraw,ImageFont
import xgoscreen.LCD_2inch as LCD_2inch
import RPi.GPIO as GPIO
import PID
from xgolib import XGO 


#初始化pid init pid
Px = 0.35
Ix = 0
Dx = 0.0001
X_Middle_error = 160 #图像X轴中心 #Image X-axis center
X_track_PID = PID.PositionalPID(Px, Ix, Dx) 

Py = 0.23
Iy = 0
Dy = 0.0001
Y_Middle_error = 120 #图像Y轴中心 #Image Y-axis center
Y_track_PID = PID.PositionalPID(Py, Iy, Dy)

Pa = 1
Ia = 0
Da = 0
Area_Middle_error = 20 #小球的距离 The distance of the ball
Area_track_PID = PID.PositionalPID(Pa, Ia, Da) 

dog = XGO("xgolite")
dog.reset()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class MyBall():
    def __init__(self):
        self.display = LCD_2inch.LCD_2inch()
        self.display.Init()
        self.display.clear()
        self.splash = Image.new("RGB",(320,240),"black")
        self.display.ShowImage(self.splash)
        self.cap=None
        self.key1=17
        self.key2=22
        self.key3=23
        self.key4=24
        GPIO.setup(self.key1,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key2,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key3,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key4,GPIO.IN,GPIO.PUD_UP)

    #key_value
    def xgoButton(self,button):
        if button == "a":
            last_state_a =GPIO.input(self.key1)
            time.sleep(0.02)
            return(not last_state_a)
        elif button == "b":
            last_state_b=GPIO.input(self.key2)
            time.sleep(0.02)
            return(not last_state_b)
        elif button == "c":
            last_state_c=GPIO.input(self.key3)
            time.sleep(0.02)
            return(not last_state_c)
        elif button == "d":
            last_state_d=GPIO.input(self.key4)
            time.sleep(0.02)
            return(not last_state_d)
        
    def open_camera(self):
        if self.cap==None:
            self.cap =cv2.VideoCapture(0)
            self.cap.set(3,320)
            self.cap.set(4,240)


    def filter_img(self,frame,color):
        b,g,r = cv2.split(frame)
        frame_bgr = cv2.merge((r,g,b))
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        if isinstance(color, list):
            color_lower = np.array(color[0])
            color_upper = np.array(color[1])
        else:
            color_upper, color_lower = get_color_mask(color)
        mask = cv2.inRange(hsv, color_lower, color_upper)
        img_mask = cv2.bitwise_and(frame, frame, mask=mask)
        return img_mask


    def cap_color_mask(self,position=None, scale=25, h_error=20, s_limit=[90, 255], v_limit=[90, 230]):
        if position is None:
            position = [160, 100]
        count = 0
        self.open_camera()
        while True:
            if self.xgoButton("c"):   
                self.display.clear()
                self.splash = Image.new("RGB",(320,240),"black")
                self.display.ShowImage(self.splash)
                break
            success,frame = self.cap.read()

            b,g,r = cv2.split(frame)
            frame_bgr = cv2.merge((r,g,b))

            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            color = np.mean(h[position[1]:position[1] + scale, position[0]:position[0] + scale])
            if (self.xgoButton("b") or cv2.waitKey(1) == ord('y')) and count == 0:
                count += 1
                color = np.mean(h[position[1]:position[1] + scale, position[0]:position[0] + scale])
                color_lower = [max(color - h_error, 0), s_limit[0], v_limit[0]]
                color_upper = [min(color + h_error, 255), s_limit[1], v_limit[1]]
                return [color_lower, color_upper]

            if count == 0:
                cv2.rectangle(frame, (position[0], position[1]), (position[0] + scale, position[1] + scale),
                            (255, 255, 255), 2)
                cv2.putText(frame, 'press button B', (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
                    

            
            b,g,r = cv2.split(frame)
            img = cv2.merge((r,g,b))
            imgok = Image.fromarray(img)
            self.display.ShowImage(imgok)

            r,g,b = cv2.split(img)
            imagecv = cv2.merge((b,g,r))
            cv2.imshow('frame', imagecv)



    def BallRecognition(self,color_mask,target="camera",p1=36, p2=15, minR=6, maxR=35):
        x=y=ra=0
        if target=="camera":
            self.open_camera()
            success,image = self.cap.read()
            #水平反转 Flip horizontal
            cv2.flip(image,0)

        else:
            print("please open camera!")
            return


        frame_mask=self.filter_img(image, color_mask)
        
        img = cv2.medianBlur(frame_mask, 5)
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        
        circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 20, param1=p1, param2=p2, minRadius=minR,maxRadius=maxR)


        
        b,g,r = cv2.split(image)
        image = cv2.merge((r,g,b))
        if circles is not None and len(circles[0]) == 1:
            param = circles[0][0]
            x, y, ra = int(param[0]), int(param[1]), int(param[2])
            cv2.circle(image, (x, y), ra, (255, 255, 255), 2)
            cv2.circle(image, (x, y), 2, (255, 255, 255), 2)
        imgok = Image.fromarray(image)
        self.display.ShowImage(imgok)
        
        r,g,b = cv2.split(image)
        imagecv = cv2.merge((b,g,r))
        cv2.imshow('frame', imagecv)
        cv2.waitKey(1)

        
        return x,y,ra


def limit_fun(input,min,max):
    if input < min:
        input = min
    elif input > max:
        input = max
    return input


XGO_edu = MyBall()
color=XGO_edu.cap_color_mask() #position=[145, 105],scale=35

try:
    while True:
        if XGO_edu.xgoButton("c"):   #c键按下退出循环 #Press the C key to exit the loop
            XGO_edu.display.clear()
            XGO_edu.splash = Image.new("RGB",(320,240),"black")
            XGO_edu.display.ShowImage(XGO_edu.splash)
            break


        result=XGO_edu.BallRecognition(color)  #填入获取的颜色 #Fill in the obtained color
        #print(result)  

        if result[0]==0 and result[1]==0 and result[2]==0:  #识别不到的情况 #Unrecognized situations
            continue

       
        X_track_PID.SystemOutput = result[0] #X 
        X_track_PID.SetStepSignal(X_Middle_error)
        X_track_PID.SetInertiaTime(0.01, 0.1)               
        x_real_value = int(X_track_PID.SystemOutput)
        x_real_value = limit_fun(x_real_value ,-18,18)

        
        Y_track_PID.SystemOutput = result[1] #y 
        Y_track_PID.SetStepSignal(Y_Middle_error)
        Y_track_PID.SetInertiaTime(0.01, 0.1)               
        y_real_value = int(Y_track_PID.SystemOutput)
        y_real_value = limit_fun(y_real_value + 90,75,115)

        
        Area_track_PID.SystemOutput = result[2] #area 
        Area_track_PID.SetStepSignal(Area_Middle_error)
        Area_track_PID.SetInertiaTime(0.01, 0.1)               
        area_real_value = int(Area_track_PID.SystemOutput)
        area_real_value = limit_fun(area_real_value ,-35,35)

        dog.translation(['x','y','z'],[area_real_value,x_real_value,y_real_value])
except:
    dog.reset()
    XGO_edu.display.clear()
    XGO_edu.splash = Image.new("RGB",(320,240),"black")
    XGO_edu.display.ShowImage(XGO_edu.splash)
    del dog
    del XGO_edu


    