from cv2 import *
import numpy as np
import sys
import math
import speech_recognition as sr
import time
import pyaudio




def main(argv):
    global lastSpeech
    lastSpeech=""
    #the code cycles theorygh the colors in multicolors when multicolor is true
    multiColor=False
    multiColors=[(0,100,0),(100,0,0),(0,0,100)]
    colorcounter=0
    #this sets up the webcam
    cam = VideoCapture(0)   # 0 -> index of camera
    s,img=cam.read()  #just to find the correct size
    #load our images
    imgWolfy=imread("C:\Users\John\Desktop\wolfie.jpg")
    imgPanpipes=imread("C:\Users\John\Desktop\panpipes.jpg")

    imgLines=np.zeros((600,600,3),np.uint8)
    #need to initialize the position variables
    posX=0
    posY=0
    #this is used to detect when the wand stops moving
    counter=0
    movAvgX=[0,0,0,0,0,0,0,0,0,0]
    movAvgY=[0,0,0,0,0,0,0,0,0,0]
    stopCount=0
    lineCol=(255,0,0)
    thickness=1
    #currstroke collects data about the wnad movement since the ast reset
    currStroke=[]

    #set up speech recogntion
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source) # calibrate for amient

    stop_speechRecog=recognizer.listen_in_background(mic,speechCallback) #this starts the listener and creates returns
    #the stop function


    #this is used keep the loop looping until it is made false, by saying stop
    running=True
    #this is used to check if anything new has been said
    oldSpeech=lastSpeech
    while running:
      if oldSpeech!=lastSpeech:
          oldSpeech=lastSpeech
          rectangle(imgLines,(0,0),(600,100),(0,0,0))
          putText(imgLines,lastSpeech,(0,50),FONT_HERSHEY_SCRIPT_COMPLEX,1,(0,255,0))

      s, img = cam.read()
      if s:    # frame captured without any errors
        counter =(counter+1)%len(movAvgX)
        img=np.fliplr(img)  #mirror the image, for front facing webcam
        imgHSV=cvtColor(img,COLOR_BGR2HSV)
        #this bit picks a ball and then finds it in the image from the camera
        red=[[170,100,50],[180,255,200]]
        yellow=[[20,100,100],[40,255,255]]
        imgThresh=inRange(imgHSV,np.array(red[0]),np.array(red[1]))
        kernel=np.ones((5,5),np.uint8)
        imgNew=erode(imgThresh,  getStructuringElement(MORPH_ELLIPSE, (5,5) ))
        imgNew=dilate( imgNew, getStructuringElement(MORPH_ELLIPSE, (5, 5)) )

        #morphological closing (fill small holes in the foreground)
        imgNew=dilate( imgNew, getStructuringElement(MORPH_ELLIPSE, (5, 5)) )
        imgNew=erode(imgNew, getStructuringElement(MORPH_ELLIPSE, (5, 5)) )
        #this bit finds where the ball is in the image
        imgMoments=moments(imgNew)
        M01=imgMoments["m01"]
        M10=imgMoments["m10"]
        targetArea=imgMoments["m00"]
        if targetArea>100:  #if we can see a  decent sized balll do nothin
            newY=int(M01/targetArea)
            newX=int(M10/targetArea)
            movAvgX[counter]=newX
            movAvgY[counter]=newY
            #print ("{0},{1}".format(),np.mean(movAvgY)))
            speed=int(((newX-np.mean(movAvgX))**2+(newX-np.mean(movAvgX))**2)/1000)
            if newX<100 and newY<100:
                imgLines=np.zeros((600,600,3),np.uint8)
            if speed>0 and speed<20:
                thickness=21-speed

            if abs(newX-np.mean(movAvgX))<10 and abs(newX-np.mean(movAvgX))<10: #check if the new position is close to the old
                stopCount+=1
                #thickness=stopCount
            else:
                stopCount=0
            if stopCount>10: # if we have been stationary for 10 cycles
                imgLines=np.zeros((600,600,3),np.uint8)  #refreash the image
                if checkStroke(currStroke): #this is the end of  strokne,  need code to see what it was
                    print currStroke
                currStroke=[]
                lineCol=(0,255,0)
            line(imgLines,(posX,posY),(newX,newY),lineCol,thickness)
            posX=newX
            posY=newY
            currStroke.append([posX,posY]) # te current position to our stroke
            if multiColor:  #turn the colors around if multicolor is trye
                lineCol=multiColors[colorcounter]
                colorcounter=(colorcounter+1)%len(multiColors)




        namedWindow("colors",WINDOW_AUTOSIZE)
        #namedWindow("Orig",WINDOW_AUTOSIZE)
        #namedWindow("cam-test",WINDOW_AUTOSIZE)
        #imshow("cam-test",imgThresh)
        #imshow("Orig",img)
        imshow("colors",imgLines)
        waitKey(100)


        #this bit chatches what was last said and if it finds a match does something

        if lastSpeech.lower()=="stop":
            running=False
        if lastSpeech.lower()=="avada kedavra":
            #sets the colors (Blue,Grreen,Red)
            lineCol=(0,125,255)
            multiColor=False
        if lastSpeech.lower()=="red":
            lineCol=(0,0,255)
            multiColor=False
        if lastSpeech.lower()=="i don't believe in god":
            multiColor=True
        if lastSpeech.lower()=="wolfie":
            #displays image wolfie by replacing the relevnat bits of imgLines
            imgLines[100:100+imgWolfy.shape[0], 100:100+imgWolfy.shape[1]] = imgWolfy
        if lastSpeech.lower()=="panpipes of doom":
            imgLines[100:100+imgPanpipes.shape[0], 100:100+imgPanpipes.shape[1]] = imgPanpipes

    stop_speechRecog()

def speechCallback(recognizer,audio):
    # received audio data, now we'll recognize it using Google Speech Recognition
    global lastSpeech
    try:
        lastSpeech=recognizer.recognize_google(audio)
        print("Google Speech Recognition thinks you said " + lastSpeech)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))




def checkStroke(stroke=[]):
    if len(stroke)<20:
        return False
    else:
        #ok, now need to figure how t break up the stroke into lines and arcs.
        #first calculate speed and direction
        vel=[]
        direction=0
        currStroke=[]
        currDir=[]
        for i in range(len(stroke)-1):
            speed=math.sqrt((stroke[i][0]-stroke[i+1][0])**2+(stroke[i][1]-stroke[i+1][1])**2)
            if speed>0:
                direction=math.asin((stroke[i][0]-stroke[i+1][0])/speed)

            if len(currDir)>3:
                avgDir=np.mean(np.array(currDir))
                if abs(direction-avgDir)>.25:
                    print("Change {0}".format(avgDir))
                    currDir=[]
            currDir.append(direction)
            vel.append([speed,direction])
        print vel

        return True







if __name__ == '__main__':
    sys.exit(main(sys.argv))