"""
Made by Espen Myrset
"""

import numpy as np
from PIL import Image as Im, ImageTk
from tkinter import *
from math import sqrt

""" Classes """
class paintWindow:
    def __init__(self, path):
        self.__root = Tk()
        self.__root.title("Paint")
        self.__root.geometry('+0+0')  # Top left position

        self.__toolFrame = Frame(self.__root)
        self.__toolFrame.grid(column=0, row=0)
        self.__imageFrame = Frame(self.__root)
        self.__imageFrame.grid(column=1, row=0)

        Canvas(self.__toolFrame, width=96, bd=0, highlightthickness=0).grid()  # Span for tool frame

        self.__path = path
        self.__img = Im.open(self.__path).convert("RGB")  # PIL image object that is used for np and canvas
        self.__imgAr = np.array(self.__img)  # makes RGB array from image [row][col][R, G, B (pixels)]
        self.__imgArSketch = self.__imgAr  # temporary image when drawing
        self.__photoImg = ImageTk.PhotoImage(self.__img)  # used in canvas (needs to be saved as variable)

        self.__imgHgt = len(self.__imgAr)
        self.__imgWdh = len(self.__imgAr[0])

        # Tools
        self.__zoom = 1
        self.resizeToHalfScreen()
        self.__click = [0, 0]  # [y, x]
        self.__pressing = False
        self.__thickness = 5
        self.__color = [255, 0, 0]

        # Tool frame
        iconsize = 32
        self.__TNewBtn = Button(self.__toolFrame, text="N", command=None)
        self.__TOpenBtn = Button(self.__toolFrame, text="O", command=None)
        self.__TSaveBtn = Button(self.__toolFrame, text="S", command=None)

        self.autoGrid([[self.__TNewBtn, self.__TOpenBtn, self.__TSaveBtn]])

        # bd and highlightthickness avoids edge around canvas
        self.__canvas = Canvas(self.__imageFrame, height=self.__imgHgt*self.__zoom,
                               width=self.__imgWdh*self.__zoom, bd=0, highlightthickness=0)
        self.__canvas.grid()
        self.updateImage()

        self.__canvas.bind("<Button-1>", self.mousePressHandler)  # right click
        self.__canvas.bind("<Motion>", self.mouseMoveHandler)
        self.__canvas.bind("<ButtonRelease>", self.mouseReleaseHandler)

        mainloop()

    def mousePressHandler(self, event=None):
        self.__pressing = True
        self.__click = [event.y//self.__zoom, event.x//self.__zoom]

    def mouseMoveHandler(self, event=None):
        if self.__pressing:
            self.__imgArSketch = self.__imgAr.copy()
            self.drawLine(event.y//self.__zoom, event.x//self.__zoom)
            self.updateImage()

    def mouseReleaseHandler(self, event=None):
        self.__pressing = False
        self.__imgAr = self.__imgArSketch  # saves changes

    def updateImage(self):  # transfers array to image that is used in canvas
        self.__img = Im.fromarray(self.__imgArSketch, 'RGB')
        # Resample=0 avoids filter when zooming
        self.__img = self.__img.resize((self.__imgWdh*self.__zoom, self.__imgHgt*self.__zoom), resample=0)
        self.__photoImg = ImageTk.PhotoImage(self.__img)  # used in canvas
        self.__canvas.create_image(0, 0, image=self.__photoImg, anchor=NW)  # insert image in upper left corner

    def autoGrid(self, gridList):
        columns = 1
        for list in gridList:
            if len(list) > columns:
                columns = len(list)

        for row, list in enumerate(gridList):
            columnsLeft = columns
            for col, element in enumerate(list):
                span = columnsLeft // (len(list) - col)
                columnsLeft = columnsLeft - span
                element.grid(row=row, column=col, columnspan=span, sticky=(W, N, E, S))

    def save(self):
        self.__img.save("{}_new".format(self.__path))


    def drawLine(self, eventY, eventX):
        startY = self.__click[0]
        startX = self.__click[1]
        endY = min(max(eventY, 0), self.__imgHgt)
        endX = min(max(eventX, 0), self.__imgWdh)
        dY = abs(startY - eventY)
        dX = abs(startX - eventX)

        if dY >= 2*dX:  # Line: |
            endPoints = [startY, endY]
            for y in range(min(endPoints) - self.__thickness//2, max(endPoints) + self.__thickness//2 + 1):
                for x in range(startX - self.__thickness//2, startX + self.__thickness//2 + 1):
                    if 0 <= x < self.__imgWdh:
                        if (y >= 0) & (y < self.__imgHgt):
                            self.__imgArSketch[y][x] = self.__color
        elif dX >= 2*dY:  # Line: -
            endPoints = [startX, endX]
            for x in range(min(endPoints) - self.__thickness//2, max(endPoints) + self.__thickness//2 + 1):
                for y in range(startY - self.__thickness//2, startY + self.__thickness//2 + 1):
                    if 0 <= y < self.__imgHgt:
                        if (x >= 0) & (x < self.__imgWdh):
                            self.__imgArSketch[y][x] = self.__color

        else:  # Line: / or \
            length = round((dY + dX) / 2)
            rToSkin = self.__thickness//2 + 1
            backslash = False
            if (endY > startY and endX > startX) or (endY < startY and endX < startX):
                backslash = True  # Line: \ else /
                if endY < startY:  # Changes point so that the upper point is drawn first
                    startY, startX = startY - length, startX - length
            elif endY < startY:
                startY, startX = startY - length, startX + length

            for i in range(rToSkin):  # Draws: ^
                y = startY - rToSkin + i
                if 0 <= y < self.__imgHgt:
                    for x in range(startX - i, startX + i + 1):
                        if 0 <= x < self.__imgWdh:
                            self.__imgArSketch[y][x] = self.__color

            for i in range(length + 1):  # Draws: \\
                y = startY + i
                if 0 <= y < self.__imgHgt:
                    diff = i if backslash else -i
                    for x in range(startX - rToSkin + diff, startX + rToSkin + diff + 1):
                        if 0 <= x < self.__imgWdh:
                            self.__imgArSketch[y][x] = self.__color

            for i in range(rToSkin):  # Draws: v
                y = startY + length + rToSkin - i
                if 0 <= y < self.__imgHgt:
                    diff = length if backslash else -length
                    for x in range(startX + diff - i, startX + diff + i + 1):
                        if 0 <= x < self.__imgWdh:
                            self.__imgArSketch[y][x] = self.__color

    def resizeToHalfScreen(self):
        screenwidth = self.__root.winfo_screenwidth()
        screenheight = self.__root.winfo_screenheight()
        self.__zoom = round(max(1, min((screenheight / self.__imgHgt) // 2, (screenwidth / self.__imgWdh) // 2)))


""" Functions """


""" Loose code """
paintWindow("images/image1.png")

