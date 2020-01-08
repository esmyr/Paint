"""
Made by Espen Myrset
"""

import numpy as np
from PIL import Image as Im, ImageTk, ImageDraw
from tkinter import *

""" Classes """
class paintWindow:
    def __init__(self, fileName):
        self.__root = Tk()
        self.__root.title("Paint")
        self.__root.geometry('+0+0')  # Top left position

        # Root consists of 3 frames
        self.__stcToolFrame = Frame(self.__root)  # For static tools
        self.__stcToolFrame.grid(column=0, row=0, sticky=(W, N, E, S))
        self.__dynToolFrame = Frame(self.__root)  # For dynamic tools
        self.__dynToolFrame.grid(column=0, row=1, sticky=(W, N, E, S))
        self.__imageFrame = Frame(self.__root)  # For image
        self.__imageFrame.grid(column=1, row=0, rowspan=2, sticky=(W, N, E, S))

        # Frames for dynamic frame
        self.__toolLine = Tool("Line", self.__dynToolFrame)
        self.__TFreeHand = BooleanVar(value=False)
        self.__TChkFreeHand = Checkbutton(self.__toolLine.getFrame(), text="Free hand", variable=self.__TFreeHand)
        self.__TChkFreeHand.grid()

        self.__toolRec = Tool("Rectangle", self.__dynToolFrame)
        self.__TFillBox = BooleanVar(value=False)
        self.__TChkFreeHand = Checkbutton(self.__toolRec.getFrame(), text="Fill", variable=self.__TFillBox)
        self.__TChkFreeHand.grid()
        # Grids preset tool
        self.__toolSel = self.__toolRec.sel()

        # Saves path and filename
        if "/" in fileName:
            self.__path = fileName[:fileName.rfind("/")]
            fileName = fileName.replace("{}/".format(self.__path), "")
        else:
            self.__path = None
        self.__fileName = fileName

        self.__img = Im.open("{}/{}".format(self.__path, self.__fileName)).convert("RGB")  # main image (PIL image object)
        self.__imgPrev = self.__img.copy()  # used for undo
        self.__imgDisplay = self.__img.copy()  # temporary image when drawing (displayed)
        self.__imgDraw = None  # draw reference that changes image object (initialized when moving mouse)
        self.__photoImg = None  # used in canvas (needs to be saved as variable)

        self.__imgWdh, self.__imgHgt = self.__img.size

        # Tools (preset values)
        self.__zoom = None
        self.resizeToHalfScreen()  # determines suitable zoom ratio
        self.__clickY, self.__clickX = 0, 0
        self.__pressing = False
        self.__thickness = 5
        self.__color = (255, 0, 0)

        # Button icons
        self.__TBtnNew = Button(self.__stcToolFrame, text="N", command=None)  # Featured
        self.__TBtnOpen = Button(self.__stcToolFrame, text="O", command=None)  # Featured
        self.__TBtnSave = Button(self.__stcToolFrame, text="S", command=self.save)
        self.__TBtnSaveAs = Button(self.__stcToolFrame, text="SA", command=None)
        self.__TBtnUndo = Button(self.__stcToolFrame, text="U", command=self.undo)
        # Tool icons
        self.__TBtnLine = Button(self.__stcToolFrame, text="L", command=lambda: self.changeTool(self.__toolLine))
        self.__TBtnRec = Button(self.__stcToolFrame, text="R", command=lambda: self.changeTool(self.__toolRec))

        self.autoGrid(self.__stcToolFrame, 32,
                      [[self.__TBtnNew, self.__TBtnOpen, self.__TBtnSave, self.__TBtnSaveAs],
                       [self.__TBtnUndo],
                       [self.__TBtnLine, self.__TBtnRec]])

        # bd and highlightthickness avoids edge around canvas
        self.__imgCanvas = Canvas(self.__imageFrame, height=self.__imgHgt*self.__zoom,
                                  width=self.__imgWdh*self.__zoom, bd=0, highlightthickness=0)
        self.__imgCanvas.grid()
        self.updateImage()

        self.__imgCanvas.bind("<Button-1>", self.mousePressHandler)  # right click
        self.__imgCanvas.bind("<Motion>", self.mouseMoveHandler)
        self.__imgCanvas.bind("<ButtonRelease>", self.mouseReleaseHandler)

        self.__root.bind("<Control-z>", self.undo)

        mainloop()

    def mousePressHandler(self, event=None):
        self.__pressing = True
        self.__clickY = event.y//self.__zoom
        self.__clickX = event.x//self.__zoom

    def mouseMoveHandler(self, event=None):  # makes and displays a new image whenever mouse is moving
        if self.__pressing:
            self.__imgDisplay = self.__img.copy()
            self.__imgDraw = ImageDraw.Draw(self.__imgDisplay)

            eventY = event.y//self.__zoom
            eventX = event.x//self.__zoom
            if self.__toolSel == self.__toolLine:
                self.drawLine(eventY, eventX)
            elif self.__toolSel == self.__toolRec:
                self.drawRectangle(eventY, eventX)
            self.updateImage()

    def mouseReleaseHandler(self, event=None):  # saves changes
        self.__pressing = False
        self.__imgPrev = self.__img.copy()
        self.__img = self.__imgDisplay.copy()

    def updateImage(self):  # resize and display sketch image
        # PhotoImage used in canvas (resample=0 avoids filter when zooming/resizing)
        self.__photoImg = ImageTk.PhotoImage(self.__imgDisplay.resize((
            self.__imgWdh*self.__zoom, self.__imgHgt*self.__zoom), resample=0))
        self.__imgCanvas.create_image(0, 0, image=self.__photoImg, anchor=NW)  # insert image in upper left corner

    # Grids array with widgets with the same row/column as they are placed in array (calculates columnspan)
    def autoGrid(self, frame, colSize, gridList):
        # Determines number of columns
        colMax = 1
        for list in gridList:
            if len(list) > colMax:
                colMax = len(list)

        # Grids all columns
        lastRow = 1
        for rowNr, list in enumerate(gridList):
            columnsLeft = colMax
            for col, element in enumerate(list):
                span = columnsLeft // (len(list) - col)  # smallest buttons to the left
                element.grid(row=rowNr, column=colMax - columnsLeft, columnspan=span, sticky=(W, N, E, S))
                columnsLeft = columnsLeft - span
            lastRow += 1

        for col in range(colMax):  # Insert canvas to make even column spacing and line at end of toolbar
            Canvas(frame, width=colSize, height=3, bd=0, highlightthickness=0, bg="black")\
                .grid(column=col, row=lastRow)

    def save(self):
        self.__img.save("{}/New_{}".format(self.__path, self.__fileName))

    def undo(self, event=None):
        self.__img, self.__imgPrev = self.__imgPrev, self.__img
        self.__imgDisplay = self.__img
        self.updateImage()

    def changeTool(self, newTool):
        self.__toolSel.unGrid()
        self.__toolSel = newTool.sel()

    def drawLine(self, eventY, eventX):
        startY = self.__clickY
        startX = self.__clickX
        endY = min(max(eventY, 0), self.__imgHgt)
        endX = min(max(eventX, 0), self.__imgWdh)
        dY = abs(startY - eventY)
        dX = abs(startX - eventX)

        if not self.__TFreeHand.get():
            if dY >= 2*dX:  # Line: |
                endX = startX
            elif dX >= 2*dY:  # Line: -
                endY = startY

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

    def drawRectangle(self, eventY, eventX):
        if self.__TFillBox.get():
            fill = self.__color
        else:
            fill = None
        self.__imgDraw.rectangle([self.__clickX, self.__clickY, eventX, eventY], fill=fill, outline=self.__color, width=self.__thickness)

    def resizeToHalfScreen(self):
        screenwidth = self.__root.winfo_screenwidth()
        screenheight = self.__root.winfo_screenheight()
        self.__zoom = round(max(1, min((screenheight / self.__imgHgt) // 2, (screenwidth / self.__imgWdh) // 2)))

class Tool:
    def __init__(self, name, parentFrame):
        self.__name = name
        self.__frame = Frame(parentFrame)

    def getFrame(self):
        return self.__frame

    def grid(self):
        self.__frame.grid(sticky=(W, N, E, S))

    def unGrid(self):
        self.__frame.grid_remove()

    def sel(self):  # grids dynamic frame returns self when tool is selected
        self.grid()
        return self

    def __str__(self):
        return self.__name

""" Functions """


""" Loose code """
paintWindow("images/image1.png")

