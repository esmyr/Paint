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
        self.__frameStatic = Frame(self.__root)  # For static tools
        self.__frameStatic.grid(column=0, row=0, sticky=(W, N, E, S))
        self.__frameDynamic = Frame(self.__root)  # For dynamic tools
        self.__frameDynamic.grid(column=0, row=1, sticky=(W, N, E, S))
        self.__frameImage = Frame(self.__root)  # For image
        self.__frameImage.grid(column=1, row=0, rowspan=2, sticky=(W, N, E, S))

        # Tools and widgets for dynamic frame
        self.__toolLine = Tool("Line", self.__frameDynamic)
        self.__propLineFree = BooleanVar(value=False)
        self.__widgetLineFree = Checkbutton(self.__toolLine.getFrame(), text="Free hand", variable=self.__propLineFree)
        self.__widgetLineFree.grid()

        self.__toolRec = Tool("Rectangle", self.__frameDynamic)
        self.__propRecFill = BooleanVar(value=False)
        self.__widgetRecFill = Checkbutton(self.__toolRec.getFrame(), text="Fill", variable=self.__propRecFill)
        self.__widgetRecFill.grid()

        # Grids preset tool
        self.__toolSelected = self.__toolRec.select()

        # Saves path and filename
        if "/" in fileName:
            self.__path = fileName[:fileName.rfind("/")]
            fileName = fileName.replace("{}/".format(self.__path), "")
        else:
            self.__path = None
        self.__fileName = fileName

        self.__img = Im.open("{}/{}".format(self.__path, self.__fileName)).convert(
            "RGB")  # main image (PIL image object)
        self.__imgPrev = self.__img.copy()  # used for undo
        self.__imgDisplay = self.__img.copy()  # temporary image when drawing (displayed)
        self.__imgDraw = None  # draw reference that changes image object (initialized when moving mouse)
        self.__photoImg = None  # used in canvas (needs to be saved as variable)

        self.__imgWdh, self.__imgHgt = self.__img.size
        self.__clickY, self.__clickX = 0, 0
        self.__pressing = False

        # Button icons
        self.__widgetNew = Button(self.__frameStatic, text="N", command=None)  # Featured
        self.__widgetOpen = Button(self.__frameStatic, text="O", command=None)  # Featured
        self.__widgetSave = Button(self.__frameStatic, text="S", command=self.save)
        self.__widgetSaveAs = Button(self.__frameStatic, text="SA", command=None)
        self.__widgetUndo = Button(self.__frameStatic, text="U", command=self.undo)
        # Tool icons
        self.__widgetLineSelect = Button(self.__frameStatic, text="L", command=lambda: self.changeTool(self.__toolLine))
        self.__widgetRecSelect = Button(self.__frameStatic, text="R", command=lambda: self.changeTool(self.__toolRec))
        # Properties (preset values)
        self.__propThickness = 5
        self.__propColor = (255, 0, 0)
        self.__propZoom = None
        self.resizeToHalfScreen()  # determines suitable zoom ratio

        self.autoGrid(self.__frameStatic, 32,
                      [[self.__widgetNew, self.__widgetOpen, self.__widgetSave, self.__widgetSaveAs],
                       [self.__widgetUndo],
                       [self.__widgetLineSelect, self.__widgetRecSelect]])

        # creates Canvas (bd and highlightthickness avoids edge around canvas)
        self.__imgCanvas = Canvas(self.__frameImage, height=self.__imgHgt * self.__propZoom,
                                  width=self.__imgWdh * self.__propZoom, bd=0, highlightthickness=0)
        self.__imgCanvas.grid()
        self.updateImage()

        # bind actions
        self.__imgCanvas.bind("<Button-1>", self.mousePressHandler)  # right click
        self.__imgCanvas.bind("<Motion>", self.mouseMoveHandler)
        self.__imgCanvas.bind("<ButtonRelease>", self.mouseReleaseHandler)
        self.__root.bind("<Control-z>", self.undo)

        self.__root.mainloop()

    def mousePressHandler(self, event=None):
        self.__pressing = True
        self.__clickY = event.y // self.__propZoom
        self.__clickX = event.x // self.__propZoom

    # makes and displays a new image whenever mouse is moving
    def mouseMoveHandler(self, event=None):
        if self.__pressing:
            self.__imgDisplay = self.__img.copy()
            self.__imgDraw = ImageDraw.Draw(self.__imgDisplay)

            eventY = event.y // self.__propZoom
            eventX = event.x // self.__propZoom
            if self.__toolSelected == self.__toolLine:
                self.drawLine(eventY, eventX)
            elif self.__toolSelected == self.__toolRec:
                self.drawRectangle(eventY, eventX)
            self.updateImage()

    # saves changes
    def mouseReleaseHandler(self, event=None):
        self.__pressing = False
        self.__imgPrev = self.__img.copy()
        self.__img = self.__imgDisplay.copy()

    # resize and display sketch image
    def updateImage(self):
        # PhotoImage used in canvas (resample=0 avoids filter when zooming/resizing)
        self.__photoImg = ImageTk.PhotoImage(self.__imgDisplay.resize((
            self.__imgWdh * self.__propZoom, self.__imgHgt * self.__propZoom), resample=0))
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
            Canvas(frame, width=colSize, height=3, bd=0, highlightthickness=0, bg="black") \
                .grid(column=col, row=lastRow)

    def save(self):
        self.__img.save("{}/New_{}".format(self.__path, self.__fileName))

    def undo(self, event=None):
        self.__img, self.__imgPrev = self.__imgPrev, self.__img
        self.__imgDisplay = self.__img
        self.updateImage()

    def changeTool(self, newTool):
        self.__toolSelected.unGrid()
        self.__toolSelected = newTool.select()

    def drawLine(self, eventY, eventX):
        startY = self.__clickY
        startX = self.__clickX
        endY = min(max(eventY, 0), self.__imgHgt)
        endX = min(max(eventX, 0), self.__imgWdh)
        dY = abs(startY - eventY)
        dX = abs(startX - eventX)

        if not self.__propLineFree.get():
            if dY >= 2 * dX:  # Line: |
                endX = startX
            elif dX >= 2 * dY:  # Line: -
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

        self.__imgDraw.line([startX, startY, endX, endY], fill=self.__propColor, width=self.__propThickness)

    def drawRectangle(self, eventY, eventX):
        startX = min(self.__clickX, eventX)
        endX = max(self.__clickX, eventX)
        startY = min(self.__clickY, eventY)
        endY = max(self.__clickY, eventY)
        if self.__propRecFill.get():
            fill = self.__propColor
        else:
            fill = None
        self.__imgDraw.rectangle([startX, startY, endX, endY], fill=fill, outline=self.__propColor,
                                 width=self.__propThickness)

    def resizeToHalfScreen(self):
        screenwidth = self.__root.winfo_screenwidth()
        screenheight = self.__root.winfo_screenheight()
        self.__propZoom = round(max(1, min((screenheight / self.__imgHgt) // 2, (screenwidth / self.__imgWdh) // 2)))


class Tool:
    def __init__(self, name, parentFrame):
        self.__name = name
        self.__frame = Frame(parentFrame)  # used for tools to grid to dynamic frame

    def getFrame(self):
        return self.__frame

    def grid(self):
        self.__frame.grid(sticky=(W, N, E, S))

    def unGrid(self):
        self.__frame.grid_remove()

    # grids dynamic frame returns self when tool is selected
    def select(self):
        self.grid()
        return self

    def __str__(self):
        return self.__name


""" Functions """

""" Loose code """
if __name__ == "__main__":
    paintWindow("images/image1.png")
