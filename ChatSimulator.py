import random
import time

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from functools import partial

import threading
import socket

from pathlib import Path
import os

import pickle

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, width, height, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = Canvas(self, width=width, height=height)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.scrollable_frame.bind('<Enter>', self._bound_to_mousewheel)
        self.scrollable_frame.bind('<Leave>', self._unbound_to_mousewheel)
    
    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)   

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>") 

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


def getFloatFromString(str):
    try:
        return float(str)
    except:
        return 0.0

def getIntFromString(str):
    try:
        return int(str)
    except:
        return 1

# Need to separate values from the entries for multithreading
# Values are for the thread generating chat, entries are for the GUI thread
class ChatOutputValues:
    __slots__ = ['message', 'probability']
    def __init__(self, message, probability):
        self.message = message
        self.probability = probability

class ChatOutputEntries:
    __slots__ = ['messageEntry', 'probabilityEntry']
    def __init__(self, messageEntry, probabilityEntry):
        self.messageEntry = messageEntry
        self.probabilityEntry = probabilityEntry

    def setMessageEntry(self, messageEntry):
        self.messageEntry = messageEntry

    def setProbabilityEntry(self, probabilityEntry):
        self.probabilityEntry = probabilityEntry

    def getChatOutputValues(self):
        message = self.messageEntry.get()
        probability = getFloatFromString(self.probabilityEntry.get())
        return ChatOutputValues(message, probability)


class ChatStateValues:
    __slots__ = ['outputs', 'duration']
    def __init__(self, outputs, duration):
        self.outputs = outputs
        self.duration = duration

class ChatStateEntries:
    __slots__ = ['outputs', 'durationEntry']
    def __init__(self, outputs, durationEntry):
        self.outputs = outputs
        self.durationEntry = durationEntry

    def setDurationEntry(self, durationEntry):
        self.durationEntry = durationEntry

    def getChatStateValues(self):
        chatOutputValues = []
        for output in self.outputs:
            chatOutputValues.append(output.getChatOutputValues())

        duration = getFloatFromString(self.durationEntry.get())
        return ChatStateValues(chatOutputValues, duration)

DEFAULT_STATE_DURATION = 0.0
DEFAULT_OUTPUT_MESSAGE = ''
DEFAULT_OUTPUT_PROBABILITY = 1.0

def createDefaultChatOutput():
    return ChatOutputValues(DEFAULT_OUTPUT_MESSAGE, DEFAULT_OUTPUT_PROBABILITY)

def createDefaultChatState():
    return ChatStateValues([createDefaultChatOutput()], DEFAULT_STATE_DURATION)

DEFAULT_NUMBER_OF_CHATTERS = 50
DEFAULT_MIN_TIME_BETWEEN_MESSAGES = 0.02
DEFAULT_MAX_TIME_BETWEEN_MESSAGES = 0.2
DEFAULT_TRANSITION_DURATION = 2.0

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 10000

cwd = os.getcwd()
DEFAULT_FILE_LOCATION = cwd + "\ChatOutput.log"
DEFAULT_MAX_FILE_SIZE = 500

myPurple="#f7e3ff"
myRed="#ff8080"
myGreen="#8cff93"
myLightBlack="#212121"

root = Tk()
root.title("Chat Simulator")
try:
    root.iconbitmap("chatsimulatoricon.ico")
except:
    pass

frame_settingsParent = LabelFrame(root, padx=10, pady=10, bd=0)
frame_chatParent = LabelFrame(root, padx=10, pady=10)

frame_settingsParent.grid(row=0, column=0)
frame_chatParent.grid(row=0, column=1)

frame_globalSettings = LabelFrame(frame_settingsParent, bd=0)
frame_actions = LabelFrame(frame_settingsParent, bd=0)

frame_globalSettings.grid(row=0, column=0, sticky=W)
frame_actions.grid(row=2, column=0)

######## Right Chat GUI ########

def onClickSendChat():
    outputString = entry_username.get() + ": " + entry_chatMessage.get()
    if outputTypeValue == "TCP":
        clientSocket.sendall(outputString.encode('utf-8'))
    elif outputTypeValue == "File":
        chatFile = open(fileLocation.value, "a")
        chatFile.write(outputString + "\n")
        chatFile.close()

    completeMessage = addToMessageList(outputString)
    message_chat.config(text=completeMessage)

frame_chatAdultOffspring = LabelFrame(frame_chatParent, bd=0)
frame_chatAdultOffspring.grid(row=0, column=0, columnspan=2)

chatWidth = 306
frame_chat = LabelFrame(frame_chatAdultOffspring, height=600, width=chatWidth, bd=0, bg=myLightBlack)
frame_chat.pack()
frame_chat.pack_propagate(0)

message_chat = Message(frame_chat, text="", \
    width=chatWidth, bg=myLightBlack, fg="white", font=("Arial", 10, "bold"), anchor=S, justify=LEFT)
message_chat.pack(side=BOTTOM, anchor=SW)

entry_username = Entry(frame_chatParent, width=14)
entry_username.grid(row=1, column=0, pady=4)
entry_username.insert(0, "username")

entry_chatMessage = Entry(frame_chatParent, width=36)
entry_chatMessage.grid(row=1, column=1)
entry_chatMessage.insert(0, "message")

button_sendChat = Button(frame_chatParent, text="Send", command=onClickSendChat, state=DISABLED)
button_sendChat.grid(row=2, column=1, sticky=E)

######## Validation ########

def positiveIntValidation(text, labelText):
    try:
        intVal = int(text)
        if intVal > 0:
            return True
        else:
            messagebox.showwarning("Warning", labelText + " must be an integer greater than 0.")
            return False
    except:
        messagebox.showwarning("Warning", labelText + " must be an integer greater than 0.")
        return False

def positiveNumberValidation(text, labelText):
    try:
        floatVal = float(text)
        if floatVal > 0.0:
            return True
        else:
            messagebox.showwarning("Warning", labelText + " must be a number greater than 0.")
            return False
    except:
        messagebox.showwarning("Warning", labelText + " must be a number greater than 0.")
        return False

def geqZeroNumberValidation(text, labelText):
    try:
        floatVal = float(text)
        if (floatVal >= 0.0):
            return True
        else:
            messagebox.showwarning("Warning", labelText + " must be a number greater than or equal to 0.")
            return False
    except:
        messagebox.showwarning("Warning", labelText + " must be a number greater than or equal to 0.")
        return False

def isMaxTimeBetweenGeqMin():
    if (getFloatFromString(maxTimeBetweenMessages.entry.get()) >= getFloatFromString(minTimeBetweenMessages.entry.get())):
        return True
    else:
        messagebox.showwarning("Warning", "Max Time Between Messages must be greater than or equal to Min Time Between Messages")
        return False

def doesAllValidationPass():
    if not positiveIntValidation(numberOfChatters.entry.get(), "Number of Chat Users"):
        return False
    if not positiveNumberValidation(minTimeBetweenMessages.entry.get(), "Min Time Between Messages"):
        return False
    if not positiveNumberValidation(maxTimeBetweenMessages.entry.get(), "Max Time Between Messages"):
        return False
    if not geqZeroNumberValidation(transitionDuration.entry.get(), "Fade Between States Duration"):
        return False
    if not positiveIntValidation(tcpPort.entry.get(), "TCP Port"):
        return False
    if not positiveIntValidation(fileMaxSize.entry.get(), "Max File Size (KB)"):
        return False

    if not isMaxTimeBetweenGeqMin():
        return False

    for state in chatStatesEntries:
        stateIndex = str(chatStatesEntries.index(state) + 1)
        if not geqZeroNumberValidation(state.durationEntry.get(), "Chat state " + stateIndex):
            return False

        for output in state.outputs:
            outputIndex = str(state.outputs.index(output) + 1)
            if not geqZeroNumberValidation(output.probabilityEntry.get(), "Probability for chat state " + stateIndex + " message " + outputIndex):
                return False

    return True

positiveIntValidationReg = root.register(positiveIntValidation)
positiveNumberValidationReg = root.register(positiveNumberValidation)
geqZeroNumberValidationReg = root.register(geqZeroNumberValidation)

######## Global Settings ########

def createChatStatesScrollableFrame():
    return ScrollableFrame(frame_settingsParent, 524, 530)

frame_chatStates = createChatStatesScrollableFrame()
frame_chatStates.grid(row=1, column=0, pady=10)

def replaceChatStatesFrame(newFrame):
    global frame_chatStates
    frame_chatStates.destroy()
    frame_chatStates = newFrame
    frame_chatStates.grid(row=1, column=0, pady=10)


class GlobalEntrySetting:
    __slots__ = ['value', 'label', 'entry', 'formatFunction']
    def __init__(self, labelText, value, row, formatFunction, validateCommand):
        self.label = Label(frame_globalSettings, text=labelText, anchor=E)
        self.label.grid(row=row, column=0, sticky=E)
        
        self.entry = Entry(frame_globalSettings)
        if validateCommand is not None:
            self.entry.config(validate="focusout", validatecommand=(validateCommand, '%P', labelText[0:len(labelText)-1]))
            
        self.entry.grid(row=row, column=1, sticky=W)
        self.entry.insert(0, value)

        self.value = value
        self.formatFunction = formatFunction

    def updateAllEntryValues(self):
        if self.formatFunction is not None:
            self.value = self.formatFunction(self.entry.get())
        else:
            self.value = self.entry.get()

    def hide(self):
        self.label.grid_remove()
        self.entry.grid_remove()

    def show(self):
        self.label.grid()
        self.entry.grid()

def setTcpGui():
    fileLocation.hide()
    fileMaxSize.hide()
    fileLocationButton.grid_remove()
    tcpHost.show()
    tcpPort.show()

def setFileGui():
    tcpHost.hide()
    tcpPort.hide()
    fileLocation.show()
    fileMaxSize.show()
    fileLocationButton.grid()

def hideOutputTypeGui():
    tcpHost.hide()
    tcpPort.hide()
    fileLocation.hide()
    fileMaxSize.hide()
    fileLocationButton.grid_remove()

def browseOutputFileLocation():
    path = filedialog.asksaveasfilename(initialdir=cwd, title="Set Output File Name", initialfile="ChatOutput", defaultextension="*.", filetypes=[("Log File", "*.log"),("Text File", "*.txt"),("Any Extension", "*.")])
    if (path is not None and path != ""):
        fileLocation.entry.delete(0, 'end')
        fileLocation.entry.insert(0, path)


numberOfChatters = GlobalEntrySetting("Number Of Chat Users:", DEFAULT_NUMBER_OF_CHATTERS, 0, getIntFromString, positiveIntValidationReg)
minTimeBetweenMessages = GlobalEntrySetting("Min Time Between Messages:", DEFAULT_MIN_TIME_BETWEEN_MESSAGES, 1, getFloatFromString, positiveNumberValidationReg)
maxTimeBetweenMessages = GlobalEntrySetting("Max Time Between Messages:", DEFAULT_MAX_TIME_BETWEEN_MESSAGES, 2, getFloatFromString, positiveNumberValidationReg)
transitionDuration = GlobalEntrySetting("Fade Between States Duration:", DEFAULT_TRANSITION_DURATION, 3, getFloatFromString, geqZeroNumberValidationReg)

la = Label(frame_globalSettings, text="Output Type:", anchor=E)
la.grid(row=4, column=0, sticky=E)

outputType = StringVar()
outputType.set("TCP")
frame_radioButtons = LabelFrame(frame_globalSettings, bd=0)
frame_radioButtons.grid(row=4, column=1, sticky=W)
Radiobutton(frame_radioButtons, text="TCP Server", variable=outputType, value="TCP", command=setTcpGui).grid(row=0, column=0, sticky=W)
Radiobutton(frame_radioButtons, text="File", variable=outputType, value="File", command=setFileGui).grid(row=0, column=1, sticky=W)
Radiobutton(frame_radioButtons, text="None (UI Only)", variable=outputType, value="None", command=hideOutputTypeGui).grid(row=0, column=2, sticky=W)

tcpHost = GlobalEntrySetting("TCP Host:", DEFAULT_HOST, 5, None, None)
tcpPort = GlobalEntrySetting("TCP Port:", DEFAULT_PORT, 6, getIntFromString, positiveIntValidationReg)
fileLocation = GlobalEntrySetting("File Location:", DEFAULT_FILE_LOCATION, 5, None, None)
fileLocation.entry.config(width=50)
fileLocationButton = Button(frame_globalSettings, text="Browse", command=browseOutputFileLocation)
fileLocationButton.grid(row=5, column=2, padx=4)
fileMaxSize = GlobalEntrySetting("Max File Size (KB):", DEFAULT_MAX_FILE_SIZE, 6, getIntFromString, positiveIntValidationReg)

setTcpGui()

chatStatesValues = [createDefaultChatState()]
chatStatesEntries = []

# For use in the chat generation thread
outputTypeValue = ""

def setAllEntryValues():
    numberOfChatters.updateAllEntryValues()
    minTimeBetweenMessages.updateAllEntryValues()
    maxTimeBetweenMessages.updateAllEntryValues()
    transitionDuration.updateAllEntryValues()

    global outputTypeValue
    outputTypeValue = outputType.get()

    tcpHost.updateAllEntryValues()
    tcpPort.updateAllEntryValues()
    fileLocation.updateAllEntryValues()
    fileMaxSize.updateAllEntryValues()

    global chatStatesValues
    chatStatesValues = []
    for state in chatStatesEntries:
        chatStatesValues.append(state.getChatStateValues())

######## Draw Chat States Helper Functions ########

def onClickDeleteMessage(stateIndex):
    chatStatesEntries[stateIndex].outputs.pop()
    redrawChatStates()

def onClickAddMessage(stateIndex):
    chatStatesEntries[stateIndex].outputs.append(ChatOutputEntries(None, None))
    redrawChatStates()

def onClickDeleteState(stateIndex):
    chatStatesEntries.remove(chatStatesEntries[stateIndex])
    redrawChatStates()

def onClickAddState(stateIndex):
    chatStatesEntries.insert(stateIndex+1, ChatStateEntries([ChatOutputEntries(None, None)], None))
    redrawChatStates()

def createChatStateFrame(frame_chatStates, chatStateIndex):
    fr = LabelFrame(frame_chatStates.scrollable_frame, bg=myPurple, bd=0)
    # These frames appear on all the even rows, the Add State buttons on the odd rows
    fr.grid(row=chatStateIndex*2, column=0)
    return fr

def createDurationEntry(parentFrame):
    label_duration = Label(parentFrame, text="Duration:", anchor=E, bg=myPurple)
    entry_duration = Entry(parentFrame, validate="focusout", validatecommand=(geqZeroNumberValidationReg, '%P', "Duration"))

    label_duration.grid(row=0, column=0)
    entry_duration.grid(row=0, column=1, sticky=W)
    return entry_duration

def createDeleteStateButton(parentFrame, chatStateIndex):
    button_deleteState = Button(parentFrame, text="Delete State", bg=myRed, command=partial(onClickDeleteState, chatStateIndex))
    button_deleteState.grid(row=0, column=2, columnspan=2, sticky=E, padx=4, pady=4)

def createMessageEntry(parentFrame, chatOutputindex):
    label_message = Label(parentFrame, text="Message:", anchor=E, bg=myPurple)
    entry_message = Entry(parentFrame, width=58)

    # duration is in first row
    label_message.grid(row=chatOutputindex+1, column=0)
    entry_message.grid(row=chatOutputindex+1, column=1)
    return entry_message

def createProbabilityEntry(parentFrame, chatOutputindex):
    label_probability = Label(parentFrame, text="Probability:", anchor=E, bg=myPurple)
    entry_probability = Entry(parentFrame, width=6, validate="focusout", validatecommand=(geqZeroNumberValidationReg, '%P', "Probability"))

    # duration is in first row
    label_probability.grid(row=chatOutputindex+1, column=2, padx=0)
    entry_probability.grid(row=chatOutputindex+1, column=3, padx=4)
    return entry_probability

def createChatStateBottomButtons(parentFrame, frame_chatStates, chatStateIndex, numberOfOutputs):
    frame_addDeleteMessage = LabelFrame(parentFrame, bd=0, bg=myPurple)
    frame_addDeleteMessage.grid(row=numberOfOutputs+1, column=1, sticky=W)

    button_addMessage = Button(frame_addDeleteMessage, text="+", bg=myGreen, width=2, command=partial(onClickAddMessage, chatStateIndex))
    button_addMessage.grid(row=0, column=0, sticky=W, pady=4)

    if numberOfOutputs > 1:
        button_deleteMessage = Button(frame_addDeleteMessage, text="-", bg=myRed, width=2, command=partial(onClickDeleteMessage, chatStateIndex))
        button_deleteMessage.grid(row=0, column=1, sticky=W, padx=4)

    frame_addState = LabelFrame(frame_chatStates.scrollable_frame, bd=0)
    frame_addState.grid(row=chatStateIndex*2+1, column=0, pady=4)

    button_addState = Button(frame_addState, text="Add State", bg=myGreen, command=partial(onClickAddState, chatStateIndex))
    button_addState.pack()

######## Draw Chat States ########

def drawInitialChatStates():
    for i in range(len(chatStatesValues)):
        fr = createChatStateFrame(frame_chatStates, i)

        entry_duration = createDurationEntry(fr)
        entry_duration.insert(0, chatStatesValues[i].duration)

        if len(chatStatesValues) > 1:
            createDeleteStateButton(fr, i)

        outputEntries = []
        for j in range(len(chatStatesValues[i].outputs)):
            entry_message = createMessageEntry(fr, j)
            entry_probability = createProbabilityEntry(fr, j)

            entry_message.insert(0, chatStatesValues[i].outputs[j].message)
            entry_probability.insert(0, chatStatesValues[i].outputs[j].probability)

            outputEntries.append(ChatOutputEntries(entry_message, entry_probability))

        chatStatesEntries.append(ChatStateEntries(outputEntries, entry_duration))
        createChatStateBottomButtons(fr, frame_chatStates, i, len(chatStatesValues[i].outputs))

# Need to replace all widgets because they may have new indexes after add/delete buttons were clicked
def redrawChatStates():
    frame_chatStates = createChatStatesScrollableFrame()
    for i in range(len(chatStatesEntries)):
        fr = createChatStateFrame(frame_chatStates, i)

        entry_duration = createDurationEntry(fr)
        duration = DEFAULT_STATE_DURATION if chatStatesEntries[i].durationEntry is None \
                else getFloatFromString(chatStatesEntries[i].durationEntry.get())
        entry_duration.insert(0, duration)

        chatStatesEntries[i].setDurationEntry(entry_duration)

        if len(chatStatesEntries) > 1:
            createDeleteStateButton(fr, i)

        for j in range(len(chatStatesEntries[i].outputs)):
            entry_message = createMessageEntry(fr, j)
            entry_probability = createProbabilityEntry(fr, j)

            message = DEFAULT_OUTPUT_MESSAGE if chatStatesEntries[i].outputs[j].messageEntry is None \
                    else chatStatesEntries[i].outputs[j].messageEntry.get()
            probability = DEFAULT_OUTPUT_PROBABILITY if chatStatesEntries[i].outputs[j].probabilityEntry is None \
                    else getFloatFromString(chatStatesEntries[i].outputs[j].probabilityEntry.get())

            entry_message.insert(0, message)
            entry_probability.insert(0, probability)

            chatStatesEntries[i].outputs[j].setMessageEntry(entry_message)
            chatStatesEntries[i].outputs[j].setProbabilityEntry(entry_probability)

        createChatStateBottomButtons(fr, frame_chatStates, i, len(chatStatesEntries[i].outputs))

    replaceChatStatesFrame(frame_chatStates)

######## On Click Global Action Buttons ########

stopChatOutputThread = False
serverSocket = None
clientSocket = None

internalMessageIndex = -1
maxInternalMessageCount = 38
internalMessageList = ['']*maxInternalMessageCount

def internalMessageListToString():
    output = ""
    for i in range(len(internalMessageList)):
        index = (internalMessageIndex + i + 1) % len(internalMessageList)
        output += internalMessageList[index] + ("\n" if i != len(internalMessageList)-1 else "")

    return output

def addToMessageList(message):
    global internalMessageIndex
    if internalMessageIndex < maxInternalMessageCount-1:
        internalMessageIndex += 1
    else:
        internalMessageIndex = 0

    internalMessageList[internalMessageIndex] = message
    return internalMessageListToString()

waitingOnTcpConnection = False

def setUpTcpConnection():
    global serverSocket
    global clientSocket
    global waitingOnTcpConnection

    message_chat.config(text="Waiting for TCP client at " + tcpHost.value + ":" + str(tcpPort.value) + "...")
    waitingOnTcpConnection = True

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((tcpHost.value, tcpPort.value))
    serverSocket.listen()
    clientSocket, addr = serverSocket.accept()

    waitingOnTcpConnection = False

def closeTcpConnection():
    global serverSocket
    global clientSocket

    if (clientSocket is not None):
        clientSocket.close()

    if (serverSocket is not None):
        serverSocket.close()

def refreshTcpConnection():
    closeTcpConnection()
    setUpTcpConnection()

def generateChat():
    global stopChatOutputThread
    global waitingOnTcpConnection
    stopChatOutputThread = False
    setAllEntryValues()

    if outputTypeValue == "TCP":
        try:
            refreshTcpConnection()
        except:
            messagebox.showwarning("Warning", "Unable to create TCP server at " + str(tcpHost.value) + ":" + str(tcpPort.value) + ". Try another host or port.")
            waitingOnTcpConnection = False
            stopChatOutputThread = True

    def printOutputForState(i, probabilities):
        global stopChatOutputThread
        randomForOutput = random.random()

        chatIndex = 0
        while (randomForOutput > probabilities[chatIndex] and chatIndex < len(probabilities)-1):
            chatIndex += 1

        chatter = random.randrange(0, numberOfChatters.value)
        outputString = "ChatUser" + str(chatter+1) + ": " + str(chatStatesValues[i].outputs[chatIndex].message)

        if outputTypeValue == "TCP":
            try:
                clientSocket.sendall(outputString.encode('utf-8'))
            except:
                messagebox.showwarning("Warning", "Unable to send TCP message to " + str(tcpHost.value) + ":" + str(tcpPort.value))
                stopChatOutputThread = True
                return
        elif outputTypeValue == "File":
            try:
                chatFile = open(fileLocation.value, "a")
                chatFile.write(outputString + "\n")
                chatFile.close()
            except:
                messagebox.showwarning("Warning", "Unable to write to file " + str(fileLocation.value))
                stopChatOutputThread = True
                return

            if Path(fileLocation.value).stat().st_size / 1000 >= fileMaxSize.value:
                messagebox.showwarning("Warning", "File size limit " + str(fileMaxSize.value) + "KB reached. Increase max file size or save to a new file.")
                stopChatOutputThread = True
                return

        completeMessage = addToMessageList(outputString)
        message_chat.config(text=completeMessage)

        waitTime = random.uniform(minTimeBetweenMessages.value, maxTimeBetweenMessages.value)

        # sleep in 0.5 second intervals to allow thread to be stopped while waiting
        timeRemaining = waitTime
        waitInterval = 0.5
        while timeRemaining > 0:
            if stopChatOutputThread:
                break
            timeToSleep = waitInterval if timeRemaining > waitInterval else timeRemaining
            time.sleep(timeToSleep)
            timeRemaining -= waitInterval

    def getProbabilitiesForState(index):
        probabilities = []
        totalProb = 0

        for chatOutput in chatStatesValues[index].outputs:
            totalProb += chatOutput.probability

        previousProb = 0
        for chatOutput in chatStatesValues[index].outputs:
            thisProb = chatOutput.probability / totalProb
            probabilities.append(previousProb + thisProb)
            previousProb += thisProb

        return probabilities

    for i in range(len(chatStatesValues)):
        probabilities = getProbabilitiesForState(i)
        nextStateStartTime = time.time() + chatStatesValues[i].duration

        if i > 0 and transitionDuration.value > 0:
            calculatedTransitionDuration = transitionDuration.value if \
                transitionDuration.value < chatStatesValues[i].duration or i == len(chatStatesValues)-1 else chatStatesValues[i].duration
            transitionEndTime = time.time() + calculatedTransitionDuration
            transitionStartTime = time.time()

            previousProbabilities = getProbabilitiesForState(i-1)

            while (time.time() < transitionEndTime and not stopChatOutputThread):
                transitionPercentage = (time.time() - transitionStartTime) / calculatedTransitionDuration
                randomForChatState = random.random()
                if randomForChatState < transitionPercentage:
                    printOutputForState(i, probabilities)
                else:
                    printOutputForState(i-1, previousProbabilities)

        while ((i == len(chatStatesValues)-1 or time.time() < nextStateStartTime) and not stopChatOutputThread):
            printOutputForState(i, probabilities)

        if (stopChatOutputThread):
            closeTcpConnection()
            stopChatOutputThread = False
            break


chatGenerationThread = None
def stopChatGenerationThread():
    global stopChatOutputThread
    global chatGenerationThread
    global serverSocket

    if chatGenerationThread is not None and chatGenerationThread.is_alive():
        stopChatOutputThread = True

        # If a previous thread is stuck waiting for a TCP client to connect, create a dummy connection to unlock the thread
        if waitingOnTcpConnection:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((tcpHost.value, tcpPort.value))
            closeTcpConnection()

        while stopChatOutputThread and chatGenerationThread.is_alive():
            time.sleep(0.5)

        button_stop.config(state=DISABLED)
        button_sendChat.config(state=DISABLED)

        # Get rid of connection to TCP message if there
        message_chat.config(text=internalMessageListToString())

def startChatGenerationThread():
    if not doesAllValidationPass():
        return

    global chatGenerationThread

    stopChatGenerationThread()

    chatGenerationThread = threading.Thread(target=generateChat, daemon=True)
    chatGenerationThread.start()

    button_sendChat.config(state=ACTIVE)
    button_stop.config(state=ACTIVE)

def onClickSaveSettings():
    if not doesAllValidationPass():
        return

    # Tried stopping thread after selecting file but weird behavior where thread was still alive but wasn't reaching new code
    stopChatGenerationThread()
    try:
        f = filedialog.asksaveasfile(mode="wb", initialdir=cwd, title="Save as", initialfile="ChatSimulatorSettings", defaultextension="*.", filetypes=[("Pickle File", "*.pkl"),("Any Extension", "*.*")])
        if (f is not None):
            setAllEntryValues()
            allSettings = [numberOfChatters.value, minTimeBetweenMessages.value, maxTimeBetweenMessages.value,
            transitionDuration.value, outputTypeValue, tcpHost.value, tcpPort.value, fileLocation.value,
            fileMaxSize.value, chatStatesValues]
            pickle.dump(allSettings, f)
    except:
        messagebox.showwarning("Save Failed", "Error saving settings")

def clearAllEntryFields():
    numberOfChatters.entry.delete(0, 'end')
    minTimeBetweenMessages.entry.delete(0, 'end')
    maxTimeBetweenMessages.entry.delete(0, 'end')
    transitionDuration.entry.delete(0, 'end')
    tcpHost.entry.delete(0, 'end')
    tcpPort.entry.delete(0, 'end')
    fileLocation.entry.delete(0, 'end')
    fileMaxSize.entry.delete(0, 'end')

def onClickLoadSettings():
    stopChatGenerationThread()
    try:
        f = filedialog.askopenfile(mode="rb", initialdir=cwd, title="Load Settings", filetypes=[("Pickle File", "*.pkl"),("Any File", "*.*")])
        if (f is not None):
            allSettings = pickle.load(f)

            clearAllEntryFields()
            numberOfChatters.entry.insert(0, allSettings[0])
            minTimeBetweenMessages.entry.insert(0, allSettings[1])
            maxTimeBetweenMessages.entry.insert(0, allSettings[2])
            transitionDuration.entry.insert(0, allSettings[3])
            outputType.set(allSettings[4])
            tcpHost.entry.insert(0, allSettings[5])
            tcpPort.entry.insert(0, allSettings[6])
            fileLocation.entry.insert(0, allSettings[7])
            fileMaxSize.entry.insert(0, allSettings[8])

            if allSettings[4] == "TCP":
                setTcpGui()
            elif allSettings[4] == "File":
                setFileGui()
            else:
                hideOutputTypeGui()

            global chatStatesValues
            global chatStatesEntries
            chatStatesValues = allSettings[9]
            chatStatesEntries = []

            drawInitialChatStates()
            redrawChatStates()
    except:
        messagebox.showwarning("Load Failed", "Error loading settings")

######## Global Action Buttons ########

button_save = Button(frame_actions, text="Save Settings", width=36, command=onClickSaveSettings)
button_load = Button(frame_actions, text="Load Settings", width=36, command=onClickLoadSettings)
button_stop = Button(frame_actions, text="STOP", command=stopChatGenerationThread, state=DISABLED)
button_start = Button(frame_actions, text="START", command=startChatGenerationThread, height=2)

button_save.grid(row=0, column=0, padx=2, pady=2)
button_load.grid(row=0, column=1, padx=2, pady=2)
button_stop.grid(row=1, column=0, columnspan=2, sticky=W+E, padx=2, pady=2)
button_start.grid(row=2, column=0, columnspan=2, sticky=W+E, padx=2, pady=2)

drawInitialChatStates()
root.mainloop()