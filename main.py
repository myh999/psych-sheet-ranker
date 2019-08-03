import pytesseract
import cv2
import numpy as np
from PIL import Image
import json
import string
import os
import logging
import re

import config

EXAMPLE_DIRECTORY = "examples"
LOG_FILE = "log/example.log"

def isInt(word):
    try:
        int(word)
        return True
    except ValueError:
        return False

def showImage(img):
    cv2.imshow('window', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def getTextLines(img):

    # Make image grayscale and invert bits
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = 255 - img

    reduced = cv2.reduce(img, 1, cv2.REDUCE_AVG).copy()

    reduced = reduced <= 0

    yCoords = []
    y = 0
    count = 0
    isSpace = False

    reducedRows, reducedCols = reduced.shape

    for i in range(reducedRows):
        if not isSpace and reduced[i]:
            isSpace = True
            count = 1
            y = i
        else:
            if not reduced[i]:
                isSpace = False
                yCoords.append(y/count)
            else:
                y += i
                count += 1

    result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    resultRows, resultCols, channels = result.shape
    for i in yCoords:
        i = int(i)
        cv2.line(result, (0, i), (resultCols, i), (0, 255, 0))

    showImage(result)

def getLines(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 500)
    for line in lines:
        for rho, theta in line:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    showImage(img)

def getText():
    directory_str = EXAMPLE_DIRECTORY
    directory = os.fsencode(directory_str)
    files = os.listdir(directory)
    files.sort()
    txt = ""
    numFiles = len(files)
    iteration = 0
    for filename in files:
        iteration += 1
        print("Parsing File " + str(iteration) + " of " + str(numFiles))
        filenameString = filename.decode("utf-8")
        img = cv2.imread(directory_str + "/" + filenameString)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 1000)

        for rho, theta in lines[0]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            half = x1
        rows, cols = img.shape[:2]
        left = img[0:rows, 0:half]
        right = img[0:rows, half:cols]
        txt += pytesseract.image_to_string(left)
        txt += pytesseract.image_to_string(right)  
    return txt

def getPoints(text):
    result = {i: 0 for i in config.teams}
    state = "NULL"
    lines = text.split("\n")
    expected = 0
    previous = 0
    translator = str.maketrans("", "", string.punctuation)
    for line in lines:
        words = line.split()
        if (words != [] and words[0] != ""):
            words[0] = words[0].translate(translator)
            if "Event" in words[0]:
                state = "NULL"
                print(line)
                previous = expected + 1
                expected = 1
            elif "NULL" is state:
                if "Team" in words[0]:
                    state = "RELAY"
                elif "Name" in words[0]:
                    state = "INDIVIDUAL"
            elif isInt(words[0][0]):
                if "RELAY" is state:
                    multiplier = 2
                    aliases = config.relayAliases
                else:
                    multiplier = 1
                    aliases = config.aliases
                
                place = int(re.search(r'\d+', words[0]).group())

                teamName = ""
                for word in words:
                    word = word.translate(translator)
                    if word in aliases:
                        teamName = aliases[word]
                if (place in config.points):
                    points = config.points[place]*multiplier
                else:
                    points = 0
                if not teamName:
                    print("Info: Could not find team name in " + line)
                else:
                    if (place != expected):
                        if (place != previous):
                            print("Warning: Unexpected Place " + str(place) + ", expected " + str(expected))
                        else:
                            previous = 0
                        expected = place
                    print(str(place) + " " + teamName + ": +" + str(points))
                    result[teamName] += points
                expected += 1
    return result

def main():
    text = getText() 
    print(text)
    result = getPoints(text)
    print(result)


if __name__ == "__main__":
    main()
