import cv2
from xgolib import XGO
import xgoscreen.LCD_2inch as LCD_2inch
import HSV_Config_Two
from PIL import Image,ImageDraw,ImageFont
import PID
import time
from key import Button


button=Button()

line_speed = 10 #巡线的速度 Speed of patrol line
line_color = 'blue' #yellow  blue  green  red
line_color_step = 2 #蓝色线 blue line

#初始化pid Init pid
Px_line = 0.08 # move:0.25  trun 0.15  0.08
Ix_line = 0
Dx_line = 0.0001
X_line_Middle_error = 160 #图像X轴中心  Image X-axis center
X_line_track_PID = PID.PositionalPID(Px_line, Ix_line, Dx_line) 


g_dog = XGO(port='/dev/ttyAMA0',version="xgolite")
g_dog.translation(['z'],[75]) #最低 upplow
time.sleep(0.2)
g_dog.attitude(['p'],[15])
time.sleep(0.2)
g_dog.pace('slow') 
time.sleep(.2)



#要识别的颜色阈值 Color threshold to be recognized
color_hsv  = {"red"   : ((0, 70, 72), (7, 255, 255)),
              "green" : ((54, 109, 78), (77, 255, 255)),
              "blue"  : ((92, 100, 62), (121, 251, 255)),
              "yellow": ((26, 100, 91), (32, 255, 255))}

#屏幕清除 screen blanker
mydisplay = LCD_2inch.LCD_2inch()
mydisplay.clear()
splash = Image.new("RGB", (mydisplay.height, mydisplay.width ),"black")
mydisplay.ShowImage(splash)



image=cv2.VideoCapture(0)
image.set(3,320)
image.set(4,240)
update_hsv = HSV_Config_Two.update_hsv()


def change_line_color():
    global line_color,line_color_step
    line_color_step = (line_color_step+1)%5
    if line_color_step == 0:
        line_color = 'red'
    elif line_color_step == 1:
        line_color = 'green'
    elif line_color_step == 2:
        line_color = 'blue'
    elif line_color_step == 3:
        line_color = 'yellow'

def limit_fun(input,min,max):
    if input < min:
        input = min
    elif input > max:
        input = max
    return input

def Find_color(colors_dict,num_len):
    if num_len == 0:
        return -1 #没找到 no find
    for i in range(num_len):
        if colors_dict[i] == line_color:
            return i #找到了 find!
    return -1 #没找到 no find

def TEST():
    global color_hsv
    while True:
        ret, frame = image.read() #usb摄像头 usb camera
        frame, binary,hsvname,xylist=update_hsv.get_contours(frame,color_hsv)
        unique_colors = list(dict.fromkeys(hsvname))
        
        # 根据列表的长度来决定如何分割字符串  Determine how to split the string based on the length of the list
        num_colors = len(unique_colors)

        if line_color == 'blue':
            cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
        elif line_color == 'green':
            cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        elif line_color == 'red':
            cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        elif line_color == 'yellow':
            cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
        else:
            cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)

        #frame
        if(cv2.waitKey(1)==ord('k') or  button.press_d() ):#按键按下 key put down
            change_line_color()


        index = Find_color(unique_colors,num_colors)
        if index >= 0:
            # print(line_color,xylist[index]) 

            color_x = xylist[index][0]
            print(color_x)

            #### X的方向(控制左右) Direction of X (control left and right)
            X_line_track_PID.SystemOutput = color_x  #X 
            X_line_track_PID.SetStepSignal(X_line_Middle_error)
            X_line_track_PID.SetInertiaTime(0.01, 0.1)               
            x_line_real_value = int(X_line_track_PID.SystemOutput)

            # x_line_real_value = limit_fun(x_line_real_value ,-18,18)
            # g_dog.move('y',x_line_real_value)

            x_line_real_value = limit_fun(x_line_real_value ,-150,150)
            g_dog.turn(x_line_real_value)

            g_dog.move('x',line_speed)
            
        
        else:
            g_dog.stop() 


        # 实时传回图像数据进行显示 Real-time image data transmission for display
        cv2.imshow("color_image", frame)

        #显示在小车的lcd屏幕上  Display on the LCD screen of the car
        b,g,r = cv2.split(frame)
        img = cv2.merge((r,g,b))
        imgok = Image.fromarray(img)
        mydisplay.ShowImage(imgok)

        if button.press_b():
            g_dog.stop()
            g_dog.reset()
            break
        
try:
    while True:
        TEST()
except:
    g_dog.stop()
    g_dog.reset()