"""
Made by Espen Myrset
"""

import numpy as np
from PIL import Image as Im, ImageTk, ImageDraw
from tkinter import *

""" Classes """
class paintWindow:
    def __init__(self, path):
        self.__root = Tk()
        self.__root.title("Paint")
        self.__root.geometry('+0+0')  # Top left position

        # Root consists of these frames
        self.__stcToolFrame = Frame(self.__root)  # For static tools
        self.__stcToolFrame.grid(column=0, row=0, sticky=(W, N, E, S))
        self.__dynToolFrame = Frame(self.__root)  # For dynamic tools
        self.__dynToolFrame.grid(column=0, row=1, sticky=(W, N, E, S))
        self.__imageFrame = Frame(self.__root)  # For image
        self.__imageFrame.grid(column=1, row=0, rowspan=2, sticky=(W, N, E, S))

        self.__path = path
        self.__img = Im.open(self.__path).convert("RGB")  # main image (PIL image object)
        self.__imgSketch = self.__img.copy()  # temporary image when drawing
        self.__imgDraw = ImageDraw.Draw(self.__imgSketch)  # draw reference that changes image object
        self.__photoImg = ImageTk.PhotoImage(self.__imgSketch)  # used in canvas (needs to be saved as variable)

        self.__imgWdh, self.__imgHgt = self.__img.size

        # Tools
        self.__zoom = None
        self.resizeToHalfScreen()
        self.__clickY = 0
        self.__clickX = 0
        self.__pressing = False
        self.__thickness = 5
        self.__color = (255, 0, 0)

        # Tool icons
        self.__TNewBtn = Button(self.__stcToolFrame, text="N", command=None)
        self.__TOpenBtn = Button(self.__stcToolFrame, text="O", command=None)
        self.__TSaveBtn = Button(self.__stcToolFrame, text="S", command=self.save)

        self.autoGrid(self.__stcToolFrame, 32, [[self.__TNewBtn, self.__TOpenBtn, self.__TSaveBtn]])

        # bd and highlightthickness avoids edge around canvas
        self.__imgCanvas = Canvas(self.__imageFrame, height=self.__imgHgt*self.__zoom,
                                  width=self.__imgWdh*self.__zoom, bd=0, highlightthickness=0)
        self.__imgCanvas.grid()
        self.updateImage()

        self.__imgCanvas.bind("<Button-1>", self.mousePressHandler)  # right click
        self.__imgCanvas.bind("<Motion>", self.mouseMoveHandler)
        self.__imgCanvas.bind("<ButtonRelease>", self.mouseReleaseHandler)

        mainloop()

    def mousePressHandler(self, event=None):
        self.__pressing = True
        self.__clickY = event.y//self.__zoom
        self.__clickX = event.x//self.__zoom

    def mouseMoveHandler(self, event=None):  # makes and displays a new image whenever mouse is moving
        if self.__pressing:
            self.__imgSketch = self.__img.copy()
            self.__imgDraw = ImageDraw.Draw(self.__imgSketch)
            self.drawLine(event.y//self.__zoom, event.x//self.__zoom)
            self.updateImage()

    def mouseReleaseHandler(self, event=None):  # saves changes
        self.__pressing = False
        self.__img = self.__imgSketch.copy()

    def updateImage(self):  # resize and display sketch image
        # PhotoImage used in canvas (resample=0 avoids filter when zooming/resizing)
        self.__photoImg = ImageTk.PhotoImage(self.__imgSketch.resize((
            self.__imgWdh*self.__zoom, self.__imgHgt*self.__zoom), resample=0))
        self.__imgCanvas.create_image(0, 0, image=self.__photoImg, anchor=NW)  # insert image in upper left corner

    def autoGrid(self, frame, colSize, gridList):
        # Determines number of columns
        colMax = 1
        for list in gridList:
            if len(list) > colMax:
                colMax = len(list)

        # Grids all columns
        lastRow = 1
        for row, list in enumerate(gridList):
            columnsLeft = colMax
            for col, element in enumerate(list):
                span = columnsLeft // (len(list) - col)
                columnsLeft = columnsLeft - span
                element.grid(row=row, column=col, columnspan=span, sticky=(W, N, E, S))
            lastRow += 1

        for col in range(colMax):  # Insert canvas to make even column spacing and line at end of toolbar
            Canvas(frame, width=colSize, height=3, bd=0, highlightthickness=0, bg="black")\
                .grid(column=col, row=lastRow)

    def save(self):
        self.__img.save("newImage.png")


    def drawLine(self, eventY, eventX):
        startY = self.__clickY
        startX = self.__clickX
        endY = min(max(eventY, 0), self.__imgHgt)
        endX = min(max(eventX, 0), self.__imgWdh)
        dY = abs(startY - eventY)
        dX = abs(startX - eventX)

        if dY >= 2*dX:  # Line: |
            self.__imgDraw.line([startX, startY, startX, endY], fill=self.__color, width=self.__thickness)
        elif dX >= 2*dY:  # Line: -
            self.__imgDraw.line([startX, startY, endX, startY], fill=self.__color, width=self.__thickness)

        else:  # Line: / or \
            length = round((dY + dX) / 2)
            backslash = False
            if (endY > startY and endX > startX) or (endY < startY and endX < startX):
                backslash = True  # Line: \ else /
                if endY < startY:  # Changes point so that the upper point is drawn first
                    startY, startX = startY - length, startX - length
            elif endY < startY:
                startY, startX = startY - length, startX + length

            endY = startY + length
            endX = startX + length if backslash else startX - length
            self.__imgDraw.line([startX, startY, endX, endY], fill=self.__color, width=self.__thickness)


    def resizeToHalfScreen(self):
        screenwidth = self.__root.winfo_screenwidth()
        screenheight = self.__root.winfo_screenheight()
        self.__zoom = round(max(1, min((screenheight / self.__imgHgt) // 2, (screenwidth / self.__imgWdh) // 2)))


""" Functions """


""" Loose code """
paintWindow("images/image1.png")

