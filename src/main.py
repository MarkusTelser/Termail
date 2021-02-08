import curses
import math
import threading
from curses import textpad
import time
import imaplib
import email
from email.header import decode_header
import pyfiglet
import subprocess
import concurrent.futures
import psutil
import credentials_real as cred


class TerMail:
    def __init__(self):
        curses.wrapper(self.__main__)

    def __main__(self, win):
        self.win = win
        curses.curs_set(0)

        # create all sub win, color pairs
        y, x = self.win.getmaxyx()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        self.win_title = self.win.subwin(8, int(x / 3), 2, 2)
        self.win_version = self.win.subwin(8, int(x / 6) - 1, 2, int(x / 3) + 2)
        self.win_day = self.win.subwin(8, int(x / 2) - 2, 10, 2)
        self.win_time = self.win.subwin(8, int(x / 6), 18, 2)
        self.win_date = self.win.subwin(7, int(x / 6), 24, 2)
        self.win_battery = self.win.subwin(10, int(x / 10) - 4, 19, int(x / 6) + 3)
        self.win_notes = self.win.subwin(10, int(x / 4) - 4, 19, int(x / 4) + 4)
        self.win_cmd = self.win.subwin(1, int(x / 2) - 2, y - 3, 2)
        self.win_mail = self.win.subwin(y - 4, int(x / 2) - 2, 2, int(x / 2) + 2)
        self.win_info = self.win.subwin(int(y / 2) - 7, int(x / 2) - 2, int(y / 2) + 2, 2)

        # variables
        self.notes_finished = [None] * self.win_notes.getmaxyx()[0]
        self.bar = '█'  # an extended ASCII 'fill' character
        self.IMAP_SERVER = cred.IMAPSERVER
        self.USER = cred.USER
        self.PASSWORD = cred.PASSWORD
        self.unread_count = [] * 10
        self.subject = [] * len(self.IMAP_SERVER) * 5
        self.from_ = [] * len(self.IMAP_SERVER) * 5
        self.notes = [None]

        self.win_title.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
        self.win_version.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
        self.win_cmd.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)

        self.drawBoxes()
        self.drawInfoBox()
        self.drawHelpBox()
        self.refreshAll()

        tr = threading.Thread(target=self.cmdinput)
        tr.start()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i in range(0, len(self.IMAP_SERVER)):
                executor.submit(self.getMail, self.IMAP_SERVER[i], i)
        executor.shutdown(wait=True)

        self.printEmail()
        self.refreshAll()

        tr.join()

    def getMail(self, IMAPSERVER, i):
        try:
            mail = imaplib.IMAP4_SSL(IMAPSERVER)
            mail.login(self.USER[i], self.PASSWORD[i])
            status, m = mail.select("INBOX")  # connect to inbox.
            status, v = mail.search(None, '(UNSEEN)')
            self.unread_count.append(len(v[0].split()))
            messages = int(m[0])
            N = 7
            k = 0
            for i in range(messages, messages - N, -1):
                # fetch the email message by ID
                res, msg = mail.fetch(str(i), "(RFC822)")
                for resp in msg:
                    if isinstance(resp, tuple):
                        # parse a bytes email into a message object
                        msg = email.message_from_bytes(resp[1])
                        # decode the email subject and from
                        sub = decode_header(msg["Subject"])[0][0]
                        fr = msg.get("From")
                        if isinstance(sub, bytes):
                            try:
                                sub = sub.decode('utf-8')
                            except Exception:
                                sub = sub.decode('latin-1')
                        self.from_.append(fr)
                        self.subject.append(sub)
                        k = k + 1
            # for num in range(messages, messages - len(v[0].split()), -1):
            #    mail.uid('STORE', num, '-FLAGS', '\SEEN')
            return True
        except Exception as e:
            self.cmd = e
            return False

    def drawBoxes(self):
        h, w = self.win.getmaxyx()
        textpad.rectangle(self.win, 1, 1, int(h / 2), int(w / 2))
        textpad.rectangle(self.win, int(h / 2) + 1, 1, h - 2, int(w / 2))
        textpad.rectangle(self.win, 1, int(w / 2) + 1, h - 2, w - 1)
        textpad.rectangle(self.win, h - 4, 1, h - 5, int(w / 2))
        textpad.rectangle(self.win, 18, int(w / 6) + 2, 29, int(w / 6) - 1 + int(w / 10))
        textpad.rectangle(self.win, 18, int(w / 6) + int(w / 10), 29, int(w / 2) - 1)

    def drawHelpBox(self):
        h, w = self.win.getmaxyx()
        self.win_info.addstr(0, 1, "TerMail - Options:", curses.A_STANDOUT)
        self.win_info.addstr(2, 1, "--Notes--", curses.A_BOLD)
        self.win_info.addstr(3, 1, ":a [note]              add note [note] to window")
        self.win_info.addstr(4, 1, ":d [pos]               delete note on [pos] on window")
        self.win_info.addstr(5, 1, ":d                     deletes last note on window")
        self.win_info.addstr(6, 1, ":dd                    deletes all notes on window")
        self.win_info.addstr(7, 1, ":f [pos]               set finished flag on specified pos of notes")
        self.win_info.addstr(8, 1, ":u [pos]               set unfinished flag on specified pos of notes")
        self.win_info.addstr(10, 1, "--EMails--", curses.A_BOLD)
        self.win_info.addstr(11, 1,
                             ":ur [pos1][pos2]       set unread flag on specified pos1 of mails to specified pos2 mail")
        self.win_info.addstr(12, 1,
                             ":r [pos1][pos2]        set read flag on specified pos1 of mails to specified pos2 mail")
        self.win_info.addstr(13, 1, ":urall                 set unread flag on all unread mails")
        self.win_info.addstr(14, 1, ":rall                  set read flag on all unread mails")
        self.win_info.addstr(15, 1, ":o                     open mail service")
        self.win_info.addstr(16, 1, ":c                     close mail service")
        self.win_info.addstr(18, 1, ":q                     close Program")
        self.win_info.addstr(19, 1, "[] = must, {} = optional")

    def drawInfoBox(self):
        self.win_title.addstr(0, 0, pyfiglet.figlet_format("TerMail", font="starwars"))
        self.win_version.addstr(0, 0, pyfiglet.figlet_format("v1", font="starwars"))
        self.win_day.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%A"), font="starwars"), curses.A_BOLD)
        self.win_time.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%H:%M"), font="starwars"), curses.A_BOLD)
        self.win_date.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%d.%m.%g")), curses.A_BOLD)
        self.win_battery.addstr(0, 2, "Battery:", curses.A_BOLD)
        self.win_battery.addstr(1, 2, "-percentage")
        self.win_battery.addstr(2, 2, "  " + str(round(psutil.sensors_battery().percent, 2)) + "%")
        self.win_battery.addstr(3, 2, "- hours left:")
        self.win_battery.addstr(4, 2, "  " + str(math.floor(psutil.sensors_battery().secsleft / 3600)) + "h " + str(
            psutil.sensors_battery().secsleft % 60) + "min")
        self.win_battery.addstr(5, 2, "-plugged in")
        self.win_battery.addstr(6, 2, "  " + str(psutil.sensors_battery().power_plugged))

        self.win_battery.addstr(8, 2, "Terminal: ", curses.A_BOLD)
        self.win_battery.addstr(9, 2, "  " + str(psutil.users()[0].terminal))

        # notes
        self.win_notes.clear()
        self.win_notes.addstr(0, 0, "Notes/TODO:", curses.A_BOLD)
        for i in range(1, self.win_notes.getmaxyx()[0]):
            if self.notes_finished[i] is None:
                self.win_notes.addstr(i, 0, "- " + str(i) + ". " + str(self.notes[i]) if i < len(self.notes) else "")
            elif self.notes_finished[i]:
                self.win_notes.addstr(i, 0, "- " + str(i) + ". " + str(self.notes[i]) if i < len(self.notes) else "",
                                      curses.color_pair(1))
            elif not self.notes_finished[i]:
                self.win_notes.addstr(i, 0, "- " + str(i) + ". " + str(self.notes[i]) if i < len(self.notes) else "",
                                      curses.color_pair(2))
        self.refreshAll()

    def printEmail(self):
        abstand = 5
        h, w = self.win.getmaxyx()
        for i in range(0, len(self.IMAP_SERVER)):
            unread = int(len(self.subject) / len(self.IMAP_SERVER))
            self.win_mail.addstr(1 + (i * unread * 2) + (i * abstand), 1,
                                 str(self.USER[i])[0:int(w / 2) - 3],
                                 curses.color_pair(1))
            self.win_mail.addstr(2 + (i * unread * 2) + (i * abstand), 1,
                                 "Unread E-Mails: " + str(self.unread_count[i]), curses.A_BOLD)
            for j in range(0, unread):
                if j < self.unread_count[i]:
                    self.win_mail.addstr(3 + (j * 2) + (i * unread * 2) + (i * abstand), 1,
                                         "Subject: " + str(self.subject[j + (i * unread)][0:int(w / 2) - 15]),
                                         curses.color_pair(2))
                    self.win_mail.addstr(4 + (j * 2) + (i * unread * 2) + (i * abstand), 1,
                                         "From: " + str(self.from_[j + (i * unread)][0:int(w / 2) - 15]),
                                         curses.color_pair(2))
                else:
                    self.win_mail.addstr(3 + (j * 2) + (i * unread * 2) + (i * abstand), 1,
                                         "Subject: " + str(self.subject[j + (i * unread)][0:int(w / 2) - 15]))
                    self.win_mail.addstr(4 + (j * 2) + (i * unread * 2) + (i * abstand), 1,
                                         "From: " + str(self.from_[j + (i * unread)][0:int(w / 2) - 15]))

    def cmdinput(self):
        # print instruction for cmd
        self.cmd = "this is your command line!"
        self.win_cmd.addstr(0, 0, self.cmd)
        self.win_cmd.refresh()

        # read input and catch control c
        while True:
            try:
                c = self.win.getch()
            except KeyboardInterrupt:
                return False
            # catch nothing typed in time
            if c == curses.ERR or c == curses.KEY_RESIZE:
                pass
            elif c == 10:  # Enter
                if self.commands():
                    return False
            elif self.cmd == "this is your command line!":
                self.cmd = chr(c)
            elif c == 27:
                self.cmd = "this is your command line!"
            elif c == 127:
                self.cmd = self.cmd[:-1]
            else:
                self.cmd += chr(c)

            # draw to window and refresh
            self.win_cmd.clear()
            try:
                self.win_cmd.addstr(0, 0, self.cmd)
            except Exception:
                self.cmd = ""
            self.win_cmd.refresh()
            curses.curs_set(1)

    def commands(self):
        # Notes commands
        if ":a " in self.cmd and len(self.notes) < self.win_notes.getmaxyx()[0]:
            self.notes.append(self.cmd[3:])
            self.drawInfoBox()
        elif ":d" == self.cmd and len(self.notes) > 1:
            self.notes.pop()
            self.drawInfoBox()
        elif ":d " in self.cmd and int(self.cmd[3:]) != 0:
            del self.notes[int(self.cmd[3:])]
            self.drawInfoBox()
        elif ":dd" == self.cmd and len(self.notes) > 1:
            self.notes = self.notes[0:1]
            self.drawInfoBox()
        elif ":f " in self.cmd:
            self.notes_finished[int(self.cmd[3:])] = True
            self.drawInfoBox()
        elif ":u " in self.cmd:
            self.notes_finished[int(self.cmd[3:])] = False
            self.drawInfoBox()
        self.win_notes.refresh()

        # Mail commands
        if self.cmd == ":o":
            self.mail_process = subprocess.Popen(['thunderbird', '-new-tab'], stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
        elif self.cmd == ":c":
            if self.mail_process is not None:
                self.mail_process.terminate()

        # exit command
        if self.cmd == ":q":
            return True  # Exit the while loop

        self.cmd = ""

    def refreshAll(self):
        self.win_title.refresh()
        self.win_version.refresh()
        self.win_day.refresh()
        self.win_time.refresh()
        self.win_date.refresh()
        self.win_battery.refresh()
        self.win_notes.refresh()
        self.win_cmd.refresh()
        self.win_mail.refresh()
        self.win_info.refresh()
        self.win.refresh()

    def clearAll(self):
        self.win_title.clear()
        self.win_version.clear()
        self.win_day.clear()
        self.win_time.clear()
        self.win_date.clear()
        self.win_battery.clear()
        self.win_notes.clear()
        self.win_cmd.clear()
        self.win_mail.clear()
        self.win_info.clear()
        self.win.clear()


t = TerMail()
