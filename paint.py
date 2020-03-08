"""
Made by Espen Myrset
"""

import numpy as np
from PIL import Image as Im, ImageTk, ImageDraw, ImageGrab
from math import sqrt
from tkinter import *
from tkinter import filedialog

""" Classes """


class PaintWindow:
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

        self.__mouse = DragPoints()

        self.globalProp = GlobalProperties(self)

        # Tools
        self.__toolLine = ToolLine(self.__frameDynamic, self.globalProp)
        self.__toolRec = ToolRectangle(self.__frameDynamic, self.globalProp)
        self.__toolCir = ToolCircle(self.__frameDynamic, self.globalProp)

        # Grids preset tool
        self.globalProp.toolSelected = self.__toolLine.select()

        self.__widgetStatic = WidgetStatic(self, self.__frameStatic)

        # creates Canvas (bd and highlightthickness avoids edge around canvas)
        self.__imgCanvas = Canvas(self.__frameImage, height=self.imgHgt * self.globalProp.zoom,
                                  width=self.imgWdh * self.globalProp.zoom, bd=0, highlightthickness=0)
        self.__imgCanvas.grid()
        self.updateImage()

        # bind actions
        self.__imgCanvas.bind("<Button-1>", self.mousePressHandler)  # right click
        self.__imgCanvas.bind("<Motion>", self.mouseMoveHandler)
        self.__imgCanvas.bind("<ButtonRelease>", self.mouseReleaseHandler)
        self.__root.bind("<Control-z>", self.undo)
        self.__root.bind("<Control-s>", self.save)

        self.__root.mainloop()

    @property
    def root(self):
        return self.__root

    @property
    def imgWdh(self):
        return self.__img.size[0]

    @property
    def imgHgt(self):
        return self.__img.size[1]

    @property
    def toolLine(self):
        return self.__toolLine

    @property
    def toolRec(self):
        return self.__toolRec

    @property
    def toolCir(self):
        return self.__toolCir

    def mousePressHandler(self, event=None):
        self.__mouse.newDrag(event.y // self.globalProp.zoom, event.x // self.globalProp.zoom)

    # makes and displays a new image whenever mouse is moving
    def mouseMoveHandler(self, event=None):
        if self.__mouse.dragging:
            self.__imgDisplay = self.__img.copy()
            self.__imgDraw = ImageDraw.Draw(self.__imgDisplay)

            self.__mouse.newEndPos(event.y // self.globalProp.zoom, event.x // self.globalProp.zoom)
            drawPositions = self.__mouse.copy()  # copy to be modified in drawing algorithms
            self.globalProp.toolSelected.draw(drawPositions, self.__imgDraw)
            self.updateImage()

    # saves changes
    def mouseReleaseHandler(self, event=None):
        self.__mouse.dragging = False
        self.__imgPrev = self.__img.copy()
        self.__img = self.__imgDisplay.copy()

    # resize and display sketch image
    def updateImage(self):
        # PhotoImage used in canvas (resample=0 avoids filter when zooming/resizing)
        self.__photoImg = ImageTk.PhotoImage(self.__imgDisplay.resize((
            self.imgWdh * self.globalProp.zoom, self.imgHgt * self.globalProp.zoom), resample=0))
        self.__imgCanvas.create_image(0, 0, image=self.__photoImg, anchor=NW)  # insert image in upper left corner

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
        self.globalProp.toolSelected.unGrid()
        self.globalProp.toolSelected = newTool.select()


class Point:
    def __init__(self, y=0, x=0):
        self.y = y
        self.x = x

    def moveToPosition(self, y, x):
        self.y = y
        self.x = x

    def moveToPoint(self, point):
        self.y = point.y
        self.x = point.x

    def copy(self):
        return Point(self.y, self.x)

    def __str__(self):
        return f"Y: {self.y}, X: {self.x}"


# Represents the mouse action by 2 points
class DragPoints:
    def __init__(self, startPoint=Point(0, 0), endPoint=Point(0, 0)):
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.dragging = False

    @property
    def startPoint(self):
        return self.__startPoint

    @startPoint.setter
    def startPoint(self, newPoint):
        self.__startPoint = newPoint

    @property
    def endPoint(self):
        return self.__endPoint

    @endPoint.setter
    def endPoint(self, newPoint):
        self.__endPoint = newPoint

    def newStartPos(self, y_cor, x_cor):
        self.__startPoint.moveToPosition(y_cor, x_cor)

    def newEndPos(self, y_cor, x_cor):
        self.__endPoint.moveToPosition(y_cor, x_cor)

    def newDrag(self, y_cor, x_cor):
        self.__startPoint.moveToPosition(y_cor, x_cor)
        self.dragging = True

    @property
    def coordinateDifference(self):
        return abs(self.startPoint.y - self.endPoint.y), abs(self.startPoint.x - self.endPoint.x)

    def upLftToDwnRigCoordinates(self):
        y = [self.startPoint.y, self.endPoint.y]
        x = [self.startPoint.x, self.endPoint.x]
        self.newStartPos(min(y), min(x))
        self.newEndPos(max(y), max(x))

    def straightCoordinates(self, onlyDiagonal=False):
        p1 = self.startPoint
        p2 = self.endPoint
        # returns start and stop coordinates for straight drawing
        dY, dX = self.coordinateDifference

        if not onlyDiagonal:
            if dY >= 2 * dX:  # Line: |
                p2.x = p1.x
                return
            elif dX >= 2 * dY:  # Line: -
                p2.y = p1.y
                return

        # Diagonal lines: / or \
        length = round((dY + dX) / 2)
        # determines Y first and makes sure the upper point is drawn first
        backslash = False
        if (p2.y >= p1.y and p2.x >= p1.x) or (p2.y < p1.y and p2.x <= p1.x):  # Line: \
            backslash = True
            if p2.y < p1.y:
                p1.y, p1.x = p1.y - length, p1.x - length  # switch if upward \
        elif p2.y < p1.y:  # Line: /
            p1.y, p1.x = p1.y - length, p1.x + length  # switch if upward /
        p2.y = p1.y + length
        # then determines X
        if backslash:
            p2.x = p1.x + length
        else:
            p2.x = p1.x - length

    def centre(self, free=False):
        dY, dX = self.coordinateDifference
        p1 = self.startPoint
        p2 = self.endPoint

        if free:
            p1.y, p1.x, p2.y, p2.x = p1.y - dY, p1.x - dX, p1.y + dY, p1.x + dX
        else:
            r = round(sqrt(dY**2 + dX**2))
            p1.y, p1.x, p2.y, p2.x = p1.y - r, p1.x - r, p1.y + r, p1.x + r

    def makeDrawList(self):
        return [self.startPoint.x, self.startPoint.y, self.endPoint.x, self.endPoint.y]

    def copy(self):
        return DragPoints(self.startPoint.copy(), self.endPoint.copy())

    def __str__(self):
        return f"Startpoint - {self.startPoint},   endPoint - {self.endPoint}"

# Global properties that can be changed and yields for multiple tools (with preset values)
class GlobalProperties:
    def __init__(self, mainApp):
        self.__free = BooleanVar(value=False)
        self.thickness = 5
        self.color = (255, 0, 0)
        self.zoom = None
        self.resizeToHalfScreen(mainApp)  # determines suitable zoom ratio
        self.toolSelected = None

    @property
    def freeVar(self):
        return self.__free

    @property
    def free(self):
        return self.__free.get()

    @free.setter
    def free(self, value=False):
        self.__free.set(value)

    def resizeToHalfScreen(self, mainApp):
        screenwidth = mainApp.root.winfo_screenwidth()
        screenheight = mainApp.root.winfo_screenheight()
        self.zoom = round(max(1, min((screenheight / mainApp.imgHgt) // 2, (screenwidth / mainApp.imgWdh) // 2)))


# Tool (to be used with inheritance for the different tools) to represent tools with a dynamic tool frame
class Tool:
    def __init__(self, parentFrame, globalProp):
        self.__frame = Frame(parentFrame)  # used for tools to grid to dynamic frame
        self.__globalProp = globalProp

    @property
    def frame(self):
        return self.__frame

    @property
    def globalProp(self):
        return self.__globalProp

    def grid(self):
        self.__frame.grid(sticky=(W, N, E, S))

    def unGrid(self):
        self.__frame.grid_remove()

    # grids dynamic frame returns self when tool is selected
    def select(self):
        self.grid()
        return self


class ToolLine(Tool):
    def __init__(self, parentFrame, globalProp):
        super().__init__(parentFrame, globalProp)

    def draw(self, drawPositions, drawRef):
        if not self.globalProp.free:
            drawPositions.straightCoordinates()

        drawRef.line(drawPositions.makeDrawList(), fill=self.globalProp.color, width=self.globalProp.thickness)


class ToolRectangle(Tool):
    def __init__(self, parentFrame, globalProp):
        super().__init__(parentFrame, globalProp)
        self.__fill = BooleanVar(value=False)
        self.__widgetFill = Checkbutton(self.frame, text="Fill", variable=self.__fill)
        self.__widgetFill.grid()

    def draw(self, drawPositions, drawRef):
        if not self.globalProp.free:
            drawPositions.straightCoordinates(True)
        drawPositions.upLftToDwnRigCoordinates()

        thickness = min(self.globalProp.thickness, min(drawPositions.coordinateDifference))
        if self.__fill.get():
            fill = self.globalProp.color
        else:
            fill = None

        drawRef.rectangle(drawPositions.makeDrawList(), fill=fill, outline=self.globalProp.color, width=thickness)


class ToolCircle(Tool):
    def __init__(self, parentFrame, globalProp):
        super().__init__(parentFrame, globalProp)
        self.__fill = BooleanVar(value=False)
        self.__widgetFill = Checkbutton(self.frame, text="Fill", variable=self.__fill)
        self.__widgetFill.grid(row=0, sticky=W)
        self.__propCentre = BooleanVar(value=False)
        self.__widgetCentre = Checkbutton(self.frame, text="Centre", variable=self.__propCentre)
        self.__widgetCentre.grid(row=1, sticky=W)

    def draw(self, drawPositions, drawRef):
        if self.__propCentre.get():
            drawPositions.centre(free=self.globalProp.free)
        else:
            if not self.globalProp.free:
                drawPositions.straightCoordinates(True)
            drawPositions.upLftToDwnRigCoordinates()

        thickness = min(self.globalProp.thickness, max(drawPositions.coordinateDifference))
        if self.__fill.get():
            fill = self.globalProp.color
        else:
            fill = None

        drawRef.ellipse(drawPositions.makeDrawList(), fill=fill, outline=self.globalProp.color, width=thickness)


# Contains all the static widgets
class WidgetStatic:
    def __init__(self, mainApp, frameStatic):
        # Button icons
        self.__widgetNew = Button(frameStatic, text="N", command=None)  # Featured
        self.__widgetOpen = Button(frameStatic, text="O", command=None)  # Featured
        self.__widgetSave = Button(frameStatic, text="S", command=mainApp.save)
        self.__widgetSaveAs = Button(frameStatic, text="SA", command=mainApp.saveAs)
        self.__widgetUndo = Button(frameStatic, text="U", command=mainApp.undo)
        self.__widgetFree = Checkbutton(frameStatic, text="Free hand", variable=mainApp.globalProp.freeVar)
        # Tool icons
        self.__widgetLineSelect = Button(frameStatic, text="L", command=lambda: mainApp.changeTool(mainApp.toolLine))
        self.__widgetRecSelect = Button(frameStatic, text="R", command=lambda: mainApp.changeTool(mainApp.toolRec))
        self.__widgetCirSelect = Button(frameStatic, text="C", command=lambda: mainApp.changeTool(mainApp.toolCir))

        self.autoGrid(frameStatic, 32,
                      [[self.__widgetNew, self.__widgetOpen, self.__widgetSave, self.__widgetSaveAs],
                       [self.__widgetUndo],
                       [self.__widgetLineSelect, self.__widgetRecSelect, self.__widgetCirSelect],
                       [self.__widgetFree]])

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


""" Loose code """
if __name__ == "__main__":
    PaintWindow("images\\image1.png")
    #PaintWindow()
