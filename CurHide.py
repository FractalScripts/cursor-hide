import configparser
import subprocess
import keyboard
import mouse
import sys
import os

import PyQt6.QtWidgets as qtWidgets
import PyQt6.QtCore as qtCore
import PyQt6.QtGui as qtGui

from PIL import Image, ImageOps

# CurHide
# Made by FractalScripts
# An open-source program to hide your mouse cursor with a keyboard shortcut.
# version 1.0.0

# Default configuration
withMouse = True
shortcut = ("win+alt", "right")
freeze = False
freezeShortcutEnabled = True
freezeShortcut = "x"
moveEscape = True
moveEscShortcutEnabled = True
moveEscShortcut = "z"
iconPath = "ico/icon1.ico"
iconInvert = False
trayText = "CurHide"
editor = "notepad.exe"

liveUpdate = False

# Set up variables
hidden = False
click = False
run = True
tempFreeze = False
tempMoveEsc = False
moveEscapeBuffer = (0, 0)

config = configparser.ConfigParser()

# Tools
def toggleBool(bool): # Toggle boolean value
    if bool:
        return False
    else:
        return True

def getRelativeFile(path = ""): # Get relative file path when inside bundle
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        script_dir = os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        script_dir = os.path.dirname(os.path.abspath(__file__))
    if path == "": # Get absolute path
        absPath = script_dir
    else:
        absPath = os.path.join(script_dir, path)
    return absPath

def icoInvert(icopath, savepath): # Image inversion
    with Image.open(icopath).convert('RGBA') as img:
        r, g, b, a = img.split() # Split into channels

        rgb_image = Image.merge('RGB', (r, g, b)) # Merge only colors
        inverted_rgb = ImageOps.invert(rgb_image) # Invert

        r_inv, g_inv, b_inv = inverted_rgb.split() # Split inverted image into channels

        inverted_image = Image.merge('RGBA', (r_inv, g_inv, b_inv, a)) # Merge inverted channels with original alpha channel

        inverted_image.save(savepath, format="ICO", sizes=[inverted_image.size]) # Save image
# Tools End

def setConfig(): # Load configuration from file
    global withMouse, shortcut, freeze, freezeShortcutEnabled, freezeShortcut, moveEscape, moveEscShortcutEnabled, moveEscShortcut, iconPath, iconInvert, trayText, editor
    config.read(getRelativeFile("config.ini"))
    if not config["Global"].getboolean("useDefaults"):
        withMouse = config["Global"].getboolean("withMouse")
        shortcut = tuple(config["Global"]["shortcut"].replace(" ", "").split(","))
        freeze = config["Freeze"].getboolean("freeze")
        freezeShortcutEnabled = config["Freeze"].getboolean("freezeShortcutEnabled")
        freezeShortcut = str(config["Freeze"]["freezeShortcut"])
        moveEscape = config["MoveEscape"].getboolean("moveEscape")
        moveEscShortcutEnabled = config["MoveEscape"].getboolean("moveEscShortcutEnabled")
        moveEscShortcut = str(config["MoveEscape"]["moveEscShortcut"])
        iconPath = str(config["Tray"]["iconPath"])
        iconInvert = config["Tray"].getboolean("iconInvert")
        trayText = str(config["Tray"]["trayText"])
        editor = str(config["Tray"]["editor"])

def hideCur(): # Command execution
    global hidden, tempFreeze, tempMoveEsc, moveEscapeBuffer
    exe = getRelativeFile("nomousy.exe")
    command = [exe, "h"] # Hiding command
    if tempFreeze:
        command.append("f") # Add freeze flag
    subprocess.Popen(command) # Run command
    if tempMoveEsc:
        moveEscapeBuffer = mouse.get_position() # Set moveEsc location buffer
    hidden = True

def showCur(): # Command execution
    global hidden
    subprocess.Popen([getRelativeFile("nomousy.exe")]) # Run command
    hidden = False

def eventTrigger(keyIn): # Watch for global shortcut
    if withMouse:
        if keyboard.is_pressed(keyIn[0]) and mouse.is_pressed(button=keyIn[1]): # Shortcut with mouse button
            return True
    else:
        if keyboard.is_pressed(keyIn[0]): # Shortcut without mouse button
            return True

def extraBinds(): # Freeze and moveEsc shortcut watchers
    global tempFreeze, tempMoveEsc
    if keyboard.is_pressed(freezeShortcut) and freezeShortcutEnabled: # Freeze shortcut
        tempFreeze = toggleBool(tempFreeze) # Toggle freeze
    if keyboard.is_pressed(moveEscShortcut) and moveEscShortcutEnabled: # MoveEsc shortcut
        tempMoveEsc = toggleBool(tempMoveEsc) # Toggle moveEsc

def toggleCur():
    global hidden
    if hidden: # Toggle hide/show
        showCur()
    else:
        hideCur()

def checkShortcut(): # Main shortcut watcher
    global click, shortcut, tempFreeze, tempMoveEsc
    if eventTrigger(shortcut): # Check for global shortcut
        tempFreeze = freeze # Set values to default
        tempMoveEsc = moveEscape
        extraBinds() # Toggle values if extra binds are pressed
        if not click: # As long as a click hasn't activated yet
            click = True
            toggleCur() # Toggle cursor visibility
    else: # Reset click when shortcut is not pressed
        if click:
            click = False

def quitApp(): # Exit watcher
    global run
    if hidden:
        showCur()
    run = False
    app.quit()  # Clean up Qt application
    sys.exit() # Exit program

def moveEscapeCheck(): #  MoveEsc watcher
    global moveEscapeBuffer, tempFreeze
    if hidden and mouse.get_position() != moveEscapeBuffer: # If mouse location has changed
        if not tempFreeze:
            showCur() # Show cursor if not frozen

def openConfig(): # Open configuration file
    configPath = getRelativeFile("config.ini")
    try:
        subprocess.Popen([editor, configPath]) # Open config with editor
    except Exception as e:
        print(f"Failed to open editor '{editor}'. Error: {e}") # Print error

def traySetup(): # Set up system tray icon
    global iconPath, app
    app = qtWidgets.QApplication(sys.argv)  # Create application instance
    trayFile = getRelativeFile(iconPath) # Get icon path

    if iconInvert: # Invert icon if enabled
        icoInvert(trayFile, getRelativeFile("inverted.ico"))
        icon = "inverted.ico"
    else:
        icon = trayFile
    
    icon = getRelativeFile(icon)
    trayIcon = qtWidgets.QSystemTrayIcon(qtGui.QIcon(icon), parent=app) # Set icon and tooltip
    trayIcon.setToolTip(trayText)

    # Menu setup
    trayMenu = qtWidgets.QMenu()
    hideAction = qtGui.QAction("Show/Hide Cursor", trayMenu)
    openAction = qtGui.QAction("Open Configuration File", trayMenu)
    exitAction = qtGui.QAction("Exit", trayMenu)

    # Menu actions
    trayMenu.addAction(hideAction)
    trayMenu.addSeparator()
    trayMenu.addAction(openAction)
    trayMenu.addSeparator()
    trayMenu.addAction(exitAction)

    # Set Menu
    trayIcon.setContextMenu(trayMenu)

    # Connect actions
    hideAction.triggered.connect(toggleCur)
    openAction.triggered.connect(openConfig)
    exitAction.triggered.connect(quitApp)

    # Click to Hide
    def onTrayClick(reason):
        if reason == qtWidgets.QSystemTrayIcon.ActivationReason.Trigger: # On left click
            hideCur()
    
    trayIcon.activated.connect(onTrayClick)

    # Show tray icon
    trayIcon.show()


def main(): # Main loop
    global run, hidden, tempMoveEsc
    
    # Set up timer for checking shortcuts
    timer = qtCore.QTimer()
    timer.timeout.connect(lambda: checkShortcut())
    timer.start(10)  # Check every 10ms
    
    # Set up timer for moveEsc checking
    moveEscTimer = qtCore.QTimer()
    moveEscTimer.timeout.connect(lambda: moveEscapeCheck() if tempMoveEsc and hidden else None)
    moveEscTimer.start(10)  # Check every 10ms
    
    if liveUpdate:
        watcher = qtCore.QFileSystemWatcher() # Set up file watcher
        watcher.addPath(getRelativeFile("config.ini")) # Watch config file
        watcher.fileChanged.connect(setConfig) # Live update configuration
    
    # Start Qt event loop
    app.exec()

# Program Initialization

setConfig() # Load configuration

if config["Global"].getboolean("liveUpdate"): # Live update setting
    liveUpdate = True

traySetup()  # Get QApplication instance from traySetup
main()  # Start the main event loop