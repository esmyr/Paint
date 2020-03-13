"""
Made by Espen Myrset
"""

from PIL import Image as Im, ImageTk, ImageDraw, ImageGrab
from math import sqrt
import tkinter as tk
from tkinter import filedialog

""" Classes """


class PaintWindow:
    def __init__(self, directory=None):
        self.__root = tk.Tk()
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
        self.__frameStatic = tk.Frame(self.__root)  # For static tools
        self.__frameStatic.grid(column=0, row=0, sticky=tk.NSEW)
        self.__frameDynamic = tk.Frame(self.__root)  # For dynamic tools
        self.__frameDynamic.grid(column=0, row=1, sticky=tk.NSEW)
        self.__frameImage = tk.Frame(self.__root)  # For image
        self.__frameImage.grid(column=1, row=0, rowspan=2, sticky=tk.NSEW)

        self.globalProp = GlobalProperties(self)

        self.image = Image(self, self.__frameImage)
        if self.__fileName is not None:
            self.image.makeImage(Im.open(self.__directory).convert("RGB"))
        elif ImageGrab.grabclipboard() is not None:
            self.image.makeImage(ImageGrab.grabclipboard())
        else:
            self.image.makeImage(Im.new('RGB', (600, 400), (255, 255, 255)))

        self.__mouse = DragPoints()

        # Tools
        self.__toolLine = ToolLine(self.__frameDynamic, self.globalProp)
        self.__toolRec = ToolRectangle(self.__frameDynamic, self.globalProp)
        self.__toolCir = ToolCircle(self.__frameDynamic, self.globalProp)

        # Grids preset tool
        self.globalProp.toolSelected = self.__toolLine.select()

        self.__widgetStatic = WidgetStatic(self, self.__frameStatic)

        # bind actions
        self.image.canvas.bind("<Button-1>", self.mousePressHandler)  # right click
        self.image.canvas.bind("<Motion>", self.mouseMoveHandler)
        self.image.canvas.bind("<ButtonRelease>", self.mouseReleaseHandler)
        self.__root.bind("<Control-z>", self.image.undo)
        self.__root.bind("<Control-s>", self.save)

        self.image.displayImage()

        self.__root.mainloop()

    @property
    def root(self):
        return self.__root

    @property
    def imgWdh(self):
        return self.image.imgWdh

    @property
    def imgHgt(self):
        return self.image.imgHgt

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
            drawImage = self.image.makeDrawImage()

            self.__mouse.newEndPos(event.y // self.globalProp.zoom, event.x // self.globalProp.zoom)
            drawPositions = self.__mouse.copy()  # copy to be modified in drawing algorithms
            self.globalProp.toolSelected.draw(drawPositions, drawImage)
            self.image.displayImage()

    # saves changes
    def mouseReleaseHandler(self, event=None):
        self.__mouse.dragging = False
        self.image.saveChanges()

    def save(self, event=None):
        if self.__fileName is None:
            self.saveAs()
        else:
            self.image.save(self.__directory)
            self.__root.title("Paint: {}".format(self.__fileName))

    def saveAs(self):
        directory = filedialog.asksaveasfilename(filetypes=[('PNG', '.png'), ('All files', '*')])
        if directory is not "":
            directory = makeStandardDirectory(directory, end=".png")
            self.__fileName = getFileName(directory)
            self.__directory = directory
            self.save()

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
        self.__mainApp = mainApp
        self.__free = tk.BooleanVar(value=False)
        self.thickness = 5
        self.color = (255, 0, 0)
        self.zoom = 1
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

    def resizeToHalfScreen(self):
        screenwidth = self.__mainApp.root.winfo_screenwidth()
        screenheight = self.__mainApp.root.winfo_screenheight()
        self.zoom = round(max(1, min((screenheight / self.__mainApp.imgHgt) // 2,
                                     (screenwidth / self.__mainApp.imgWdh) // 2)))


# Tool (to be used with inheritance for the different tools) to represent tools with a dynamic tool frame
class Tool:
    def __init__(self, parentFrame, globalProp):
        self.__frame = tk.Frame(parentFrame)  # used for tools to grid to dynamic frame
        self.__globalProp = globalProp

    @property
    def frame(self):
        return self.__frame

    @property
    def globalProp(self):
        return self.__globalProp

    def grid(self):
        self.__frame.grid(sticky=tk.NSEW)

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
        self.__fill = tk.BooleanVar(value=False)
        self.__widgetFill = tk.Checkbutton(self.frame, text="Fill", variable=self.__fill)
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
        self.__fill = tk.BooleanVar(value=False)
        self.__widgetFill = tk.Checkbutton(self.frame, text="Fill", variable=self.__fill)
        self.__widgetFill.grid(row=0, sticky=tk.W)
        self.__propCentre = tk.BooleanVar(value=False)
        self.__widgetCentre = tk.Checkbutton(self.frame, text="Centre", variable=self.__propCentre)
        self.__widgetCentre.grid(row=1, sticky=tk.W)

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
        self.__widgetNew = tk.Button(frameStatic, text="N", command=None)  # Featured
        self.__widgetOpen = tk.Button(frameStatic, text="O", command=None)  # Featured
        self.__widgetSave = tk.Button(frameStatic, text="S", command=mainApp.save)
        self.__widgetSaveAs = tk.Button(frameStatic, text="SA", command=mainApp.saveAs)
        self.__widgetUndo = tk.Button(frameStatic, text="U", command=mainApp.image.undo)
        self.__widgetFree = tk.Checkbutton(frameStatic, text="Free hand", variable=mainApp.globalProp.freeVar)
        # Tool icons
        self.__widgetLineSelect = tk.Button(frameStatic, text="L", command=lambda: mainApp.changeTool(mainApp.toolLine))
        self.__widgetRecSelect = tk.Button(frameStatic, text="R", command=lambda: mainApp.changeTool(mainApp.toolRec))
        self.__widgetCirSelect = tk.Button(frameStatic, text="C", command=lambda: mainApp.changeTool(mainApp.toolCir))

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
                element.grid(row=rowNr, column=colMax - columnsLeft, columnspan=span, sticky=tk.NSEW)
                columnsLeft = columnsLeft - span
            lastRow += 1

        for col in range(colMax):  # Insert canvas to make even column spacing and line at end of toolbar
            tk.Canvas(frame, width=colSize, height=3, bd=0, highlightthickness=0, bg="black") \
                .grid(column=col, row=lastRow)


class Image:
    def __init__(self, mainApp, frame):
        self.__mainApp = mainApp
        self.img = None
        self.__imgPrev = None  # used for undo
        self.__imgDisplay = None  # temporary image when drawing (displayed)
        self.imgDraw = None  # draw reference that changes image object (initialized when moving mouse)
        self.__photoImg = None  # used in canvas (needs to be saved as variable)
        self.canvas = None  # creates Canvas
        self.__frame = frame

    @property
    def imgWdh(self):
        return self.img.size[0]

    @property
    def imgHgt(self):
        return self.img.size[1]

    def makeImage(self, image):
        self.img = image
        self.__imgPrev = self.img.copy()
        self.__imgDisplay = self.img.copy()
        self.__mainApp.globalProp.resizeToHalfScreen()  # determines suitable zoom ratio
        # (bd and highlightthickness avoids edge around canvas)
        self.canvas = tk.Canvas(self.__frame, height=self.imgHgt * self.__mainApp.globalProp.zoom,
                                width=self.imgWdh * self.__mainApp.globalProp.zoom, bd=0, highlightthickness=0)
        self.canvas.grid()

    # resize and display sketch image
    def displayImage(self):
        # PhotoImage used in canvas (resample=0 avoids filter when zooming/resizing)
        self.__photoImg = ImageTk.PhotoImage(self.__imgDisplay.resize((
            self.imgWdh * self.__mainApp.globalProp.zoom, self.imgHgt * self.__mainApp.globalProp.zoom), resample=0))
        self.canvas.create_image(0, 0, image=self.__photoImg, anchor=tk.NW)  # insert image in upper left corner

    def makeDrawImage(self):
        self.__imgDisplay = self.img.copy()
        self.imgDraw = ImageDraw.Draw(self.__imgDisplay)
        return self.imgDraw

    def saveChanges(self):
        self.__imgPrev = self.img.copy()
        self.img = self.__imgDisplay.copy()

    def undo(self, event=None):
        self.img, self.__imgPrev = self.__imgPrev, self.img
        self.__imgDisplay = self.img
        self.displayImage()

    def save(self, directory):
        self.img.save(directory)


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
