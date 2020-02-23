"""
Made by Espen Myrset
"""

import numpy as np
from PIL import Image as Im, ImageTk, ImageDraw, ImageGrab
from tkinter import *
from tkinter import filedialog

""" Classes """


class paintWindow:
    def __init__(self, directory=None):
        self.__root = Tk()
        self.__root.geometry('+0+0')  # Top left position

        # Saves directory and filename
        self.__fileName = None
        if directory is not None:
            directory = makeStandardDirectory(directory, end=".png")
            self.__fileName = getFileName(directory)
            self.__root.title("Paint: {}".format(self.__fileName))
        else:
            self.__root.title("Paint: (untitled)")
        self.__directory = directory

        # Root consists of 3 frames
        self.__frameStatic = Frame(self.__root)  # For static tools
        self.__frameStatic.grid(column=0, row=0, sticky=(W, N, E, S))
        self.__frameDynamic = Frame(self.__root)  # For dynamic tools
        self.__frameDynamic.grid(column=0, row=1, sticky=(W, N, E, S))
        self.__frameImage = Frame(self.__root)  # For image
        self.__frameImage.grid(column=1, row=0, rowspan=2, sticky=(W, N, E, S))

        # Tools (and toolwidgets for dynamic frame)
        self.__toolLine = Tool("Line", self.__frameDynamic)

        self.__toolRec = Tool("Rectangle", self.__frameDynamic)
        self.__propRecFill = BooleanVar(value=False)
        self.__widgetRecFill = Checkbutton(self.__toolRec.getFrame(), text="Fill", variable=self.__propRecFill)
        self.__widgetRecFill.grid()

        self.__toolCir = Tool("Circle", self.__frameDynamic)
        self.__propCirFill = BooleanVar(value=False)
        self.__widgetCirFill = Checkbutton(self.__toolCir.getFrame(), text="Fill", variable=self.__propCirFill)
        self.__widgetCirFill.grid(row=0, sticky=W)
        self.__propCirCentre = BooleanVar(value=False)
        self.__widgetCirCentre = Checkbutton(self.__toolCir.getFrame(), text="Centre", variable=self.__propCirCentre)
        self.__widgetCirCentre.grid(row=1, sticky=W)

        # Grids preset tool
        self.__toolSelected = self.__toolLine.select()

        # main image (PIL image object)
        if self.__fileName is not None:
            self.__img = Im.open(self.__directory).convert("RGB")
        elif ImageGrab.grabclipboard() is not None:
            self.__img = ImageGrab.grabclipboard()
        else:
            self.__img = Im.new('RGB', (600, 400), (255, 255, 255))
        self.__imgPrev = self.__img.copy()  # used for undo
        self.__imgDisplay = self.__img.copy()  # temporary image when drawing (displayed)
        self.__imgDraw = None  # draw reference that changes image object (initialized when moving mouse)
        self.__photoImg = None  # used in canvas (needs to be saved as variable)

        self.__imgWdh, self.__imgHgt = self.__img.size
        self.__clickY, self.__clickX = 0, 0
        self.__pressing = False

        # Properties (preset values)
        self.__propFree = BooleanVar(value=False)
        self.__propThickness = 5
        self.__propColor = (255, 0, 0)
        self.__propZoom = None
        self.resizeToHalfScreen()  # determines suitable zoom ratio
        # Button icons
        self.__widgetNew = Button(self.__frameStatic, text="N", command=None)  # Featured
        self.__widgetOpen = Button(self.__frameStatic, text="O", command=None)  # Featured
        self.__widgetSave = Button(self.__frameStatic, text="S", command=self.save)
        self.__widgetSaveAs = Button(self.__frameStatic, text="SA", command=self.saveAs)
        self.__widgetUndo = Button(self.__frameStatic, text="U", command=self.undo)
        self.__widgetFree = Checkbutton(self.__frameStatic, text="Free hand", variable=self.__propFree)
        # Tool icons
        self.__widgetLineSelect = Button(self.__frameStatic, text="L", command=lambda: self.changeTool(self.__toolLine))
        self.__widgetRecSelect = Button(self.__frameStatic, text="R", command=lambda: self.changeTool(self.__toolRec))
        self.__widgetCirSelect = Button(self.__frameStatic, text="C", command=lambda: self.changeTool(self.__toolCir))

        self.autoGrid(self.__frameStatic, 32,
                      [[self.__widgetNew, self.__widgetOpen, self.__widgetSave, self.__widgetSaveAs],
                       [self.__widgetUndo],
                       [self.__widgetLineSelect, self.__widgetRecSelect, self.__widgetCirSelect],
                       [self.__widgetFree]])

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
        self.__root.bind("<Control-s>", self.save)

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
            elif self.__toolSelected == self.__toolCir:
                self.drawCircle(eventY, eventX)
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

    def save(self, event=None):
        if self.__directory is None:
            self.saveAs()
        else:
            self.__img.save(self.__directory)
            self.__root.title("Paint: {}".format(self.__fileName))

    def saveAs(self):
        directory = filedialog.asksaveasfilename(filetypes=[('PNG', '.png'), ('All files', '*')])
        if directory is not None:
            directory = makeStandardDirectory(directory, end=".png")
            self.__fileName = getFileName(directory)
            self.__directory = directory
            self.save()

    def undo(self, event=None):
        self.__img, self.__imgPrev = self.__imgPrev, self.__img
        self.__imgDisplay = self.__img
        self.updateImage()

    def changeTool(self, newTool):
        self.__toolSelected.unGrid()
        self.__toolSelected = newTool.select()

    def upLftToDwnRigCoordinates(self, startY, startX, endY, endX):
        Y = [startY, endY]
        X = [startX, endX]
        return min(Y), min(X), max(Y), max(X)

    def straightCoordinates(self, startY, startX, endY, endX, onlyDiagonal=False):
        # returns start and stop coordinates for straight drawing
        dY, dX = getCoordinateDifference(startY, startX, endY, endX)

        if not onlyDiagonal:
            if dY >= 2 * dX:  # Line: |
                endX = startX
                return startY, startX, endY, endX
            elif dX >= 2 * dY:  # Line: -
                endY = startY
                return startY, startX, endY, endX

        # Diagonal lines: / or \
        length = round((dY + dX) / 2)
        # determines Y first and makes sure the upper point is drawn first
        backslash = False
        if (endY >= startY and endX >= startX) or (endY < startY and endX <= startX):  # Line: \
            backslash = True
            if endY < startY:
                startY, startX = startY - length, startX - length  # switch if upward \
        elif endY < startY:  # Line: /
            startY, startX = startY - length, startX + length  # switch if upward /
        endY = startY + length
        # then determines X
        if backslash:
            endX = startX + length
        else:
            endX = startX - length
        return startY, startX, endY, endX

    def drawLine(self, eventY, eventX):
        if self.__propFree.get():
            startY, startX, endY, endX = self.__clickY, self.__clickX, eventY, eventX
        else:
            startY, startX, endY, endX = self.straightCoordinates(self.__clickY, self.__clickX, eventY, eventX)

        self.__imgDraw.line([startX, startY, endX, endY], fill=self.__propColor, width=self.__propThickness)

    def drawRectangle(self, eventY, eventX):
        startY, startX, endY, endX = self.__clickY, self.__clickX, eventY, eventX
        if not self.__propFree.get():
            startY, startX, endY, endX = self.straightCoordinates(startY, startX, endY, endX, True)
        startY, startX, endY, endX = self.upLftToDwnRigCoordinates(startY, startX, endY, endX)

        thickness = min(self.__propThickness, max(abs(self.__clickY - eventY), abs(self.__clickX - eventX)))
        if self.__propRecFill.get():
            fill = self.__propColor
        else:
            fill = None

        self.__imgDraw.rectangle([startX, startY, endX, endY], fill=fill, outline=self.__propColor, width=thickness)

    def drawCircle(self, eventY, eventX):
        startY, startX, endY, endX = self.__clickY, self.__clickX, eventY, eventX
        if self.__propCirCentre.get():
            dY, dX = getCoordinateDifference(startY, startX, endY, endX)
            if self.__propFree.get():
                startY, startX, endY, endX = startY - dY, startX - dX, startY + dY, startX + dX
            else:
                r = round((dY + dX) / 2)
                startY, startX, endY, endX = startY - r, startX - r, startY + r, startX + r
        else:
            if not self.__propFree.get():
                startY, startX, endY, endX = self.straightCoordinates(startY, startX, endY, endX, True)
            startY, startX, endY, endX = self.upLftToDwnRigCoordinates(startY, startX, endY, endX)

        thickness = min(self.__propThickness, max(abs(self.__clickY - eventY), abs(self.__clickX - eventX)))
        if self.__propCirFill.get():
            fill = self.__propColor
        else:
            fill = None

        self.__imgDraw.ellipse([startX, startY, endX, endY], fill=fill, outline=self.__propColor, width=thickness)

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


def getFileName(directory):
    if "\\" in directory:
        return directory[directory.rfind("\\") + 1:]
    else:
        return directory


def makeStandardDirectory(directory, end=""):
    directory = directory.replace("/", "\\", directory.count("/"))
    if len(end) > 0:
        if directory[-len(end):] != end:
            directory += end
    return directory


def getCoordinateDifference(Y1, X1, Y2, X2):
    return abs(Y1 - Y2), abs(X1 - X2)


""" Loose code """
if __name__ == "__main__":
    #paintWindow("images\\image1.png")
    paintWindow()
