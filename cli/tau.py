import datetime
import sys
import threading
import time
import re

import RPi.GPIO as GPIO
import pymysql
from termcolor import colored

import credentials
from tau_num import tau

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
for pin in range(2, 13):
    GPIO.setup(pin, GPIO.OUT)

GPIO.output(2, 1)

monitor = True
lights = False
tauing = False
half = False
zigzag = 0
clock = False
stopwatch = False
stopped = False
web = True


def p_web():
    while web:
        db = pymysql.connect("localhost", credentials.mysql_user, credentials.mysql_password, "db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM `stuff` WHERE `key` = 'lastlog'")
        lastlog = cursor.fetchall()[0][2]
        cursor.execute("SELECT * FROM `stuff` WHERE `key` = 'lights'")
        value = cursor.fetchall()[0][2]
        for i in range(10):
            GPIO.output(i + 3, int(value[i]))
        cursor.execute("SELECT * FROM `lightlog` WHERE `id` > '" + str(lastlog) + "'")
        rows = cursor.fetchall()
        for i in range(len(rows)):
            row = rows[i]
            print(row[1] + "> " +
                  colored(row[2], "magenta" if row[3] == "red" else "red" if row[3] == "orange" else "yellow" if
                  row[3] == "yellow" else "green" if row[3] == "green" else "blue" if row[3] == "blue" else "white") +
                  ((" from " + row[5]) if row[5] != "" else ""))
        if len(rows) > 0:
            cursor.execute("UPDATE `stuff` SET `value` = '" + str(rows[len(rows) - 1][0]) + "' WHERE `key` = 'lastlog'")
            db.commit()
        for i in range(10):
            GPIO.output(i + 3, int(value[i]))
        db.close()
        time.sleep(1)
    for o in range(10):
        GPIO.output(o + 3, 0)


t_web = threading.Thread(target=p_web)
t_web.daemon = True
t_web.start()


def p_tauing():
    i = 0
    while tauing:
        if re.match("[0-9]", tau[i]):
            number = format(int(tau[i]), '010b')
            for o in range(10):
                GPIO.output(o + 3, int(number[o]))
            time.sleep(0.1)
        i += 1
    for o in range(10):
        GPIO.output(o + 3, 0)


def p_zigzag():
    t0 = time.time()
    out = "1000000000"
    for o in range(10):
        GPIO.output(o + 3, int(out[o]))
    drift = 1
    while zigzag > 0:
        t = time.time()
        if t - t0 >= .15:
            t0 = t
            _out = ""
            if out == "0000000001":
                if zigzag == 1:
                    _out = "1000000000"
                else:
                    drift = -drift
                    _out = "0100000000"
            else:
                for o in range(len(out) - 1):
                    if out[o] == "1":
                        _out += "01"
                    else:
                        _out += "0"
            out = _out
            if drift < 0:
                for o in range(len(out)):
                    GPIO.output(o + 3, int(out[len(out) - o - 1]))
            else:
                for o in range(10):
                    GPIO.output(o + 3, int(out[o]))
    for o in range(10):
        GPIO.output(o + 3, 0)


def p_clock():
    while clock:
        _hour = 0
        _time = datetime.datetime.now().time()
        for o in range(12):
            if _time.hour == o or _time.hour == o + 12:
                _hour = o
        _min = _time.minute
        binhour = format(_hour, '04b')
        binmin = format(_min, '06b')
        bintime = binhour + binmin
        for o in range(10):
            GPIO.output(o + 3, int(bintime[o]))
    for o in range(10):
        GPIO.output(o + 3, 0)


def p_stopwatch():
    start = time.time()
    while stopwatch and not stopped:
        a = format(time.time() - start, '.12f')
        if float(a) < 60:
            bintime = format(int(float(a)), '06b') + format(int((float(a) - int(float(a))) * 16), '04b')
        elif float(a) < 60 * 16:
            bintime = format(int(float(a) // 60), '04b') + format(int(float(a) - float(a) // 60 * 60), '06b')
        elif float(a) < 60 * 60 * 16:
            bintime = format(int(float(a) // 60 // 60), '04b') + format(
                int((float(a) - float(a) // 60 // 60 * 60 * 60) // 60), '06b')
        else:
            bintime = format(int(float(a) // 60 // 60), '010b')
        for o in range(10):
            GPIO.output(o + 3, int(bintime[o]))


while True:
    cmd = input()
    if cmd == "m":
        monitor = not monitor
        print(colored("Turning monitor " + ("on." if monitor else "off."), "cyan"))
        GPIO.output(2, monitor)
    elif cmd == "w":
        lights = False
        tauing = False
        half = False
        zigzag = 0
        clock = False
        stopwatch = False
        web = not web
        for i in range(10):
            GPIO.output(i + 3, 0)
        if web:
            t_web = threading.Thread(target=p_web)
            t_web.daemon = True
            t_web.start()
        print(colored(("Start" if web else "Stopp") + "ing server control.", "cyan"))
    elif cmd == "l":
        web = False
        tauing = False
        half = False
        zigzag = 0
        clock = False
        stopwatch = False
        lights = not lights
        print(colored("Turning lights " + ("on." if lights else "off."), "cyan"))
        for i in range(10):
            GPIO.output(i + 3, lights)
    elif cmd == "t":
        web = False
        lights = False
        half = False
        zigzag = 0
        stopwatch = False
        tauing = not tauing
        if tauing:
            t_tauing = threading.Thread(target=p_tauing)
            t_tauing.daemon = True
            t_tauing.start()
        print(colored(("A" if tauing else "Dea") + "ctivating tauing.", "cyan"))
    elif cmd == "h":
        web = False
        lights = False
        tauing = False
        zigzag = 0
        clock = False
        stopwatch = False
        half = not half
        print(colored("Turning half the lights " + ("on." if half else "off."), "cyan"))
        sequence = "1010101010"
        for i in range(10):
            GPIO.output(i + 3, int(sequence[i]) if half else 0)
    elif cmd == "z":
        web = False
        lights = False
        tauing = False
        half = False
        clock = False
        stopwatch = False
        zigzag = 1 if zigzag == 0 else 2 if zigzag == 1 else 0
        if zigzag == 1:
            t_zigzag = threading.Thread(target=p_zigzag)
            t_zigzag.daemon = True
            t_zigzag.start()
        print(colored("Running!" if zigzag == 1 else "Zig-Zagging!" if zigzag == 2 else "Stopping Zig-Zag.", "cyan"))
    elif cmd == "c":
        web = False
        lights = False
        tauing = False
        half = False
        zigzag = 0
        stopwatch = False
        clock = not clock
        if clock:
            t_clock = threading.Thread(target=p_clock)
            t_clock.daemon = True
            t_clock.start()
        print(colored(("A" if clock else "Dea") + "ctivating clock.", "cyan"))
    elif cmd == "s":
        web = False
        lights = False
        tauing = False
        half = False
        zigzag = 0
        clock = False
        if not stopwatch:
            stopped = False
        _sw = stopwatch
        _st = stopped
        stopwatch = not (stopwatch and stopped)
        stopped = stopwatch and not stopped and _sw == stopwatch
        if stopwatch and not stopped:
            t_stopwatch = threading.Thread(target=p_stopwatch)
            t_stopwatch.daemon = True
            t_stopwatch.start()
        elif not stopwatch:
            for i in range(10):
                GPIO.output(i + 3, 0)
        if _sw != stopwatch:
            print(colored(("Activating and star" if stopwatch else "Deactiva") + "ting stopwatch.", "cyan"))
        elif _st != stopped:
            print(colored("Stopping stopwatch.", "cyan"))
    elif cmd == "exit":
        sys.exit(0)
