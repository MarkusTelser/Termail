import curses
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
from multiprocessing import Process
import credentials_real as cred


class TerMail:
    def __init__(self):
        self.bar = '█'  # an extended ASCII 'fill' character
        self.cmd = "this is your command line!"
        self.IMAPSERVER = cred.IMAPSERVER
        self.USER = cred.USER
        self.PASSWORD = cred.PASSWORD
        self.unreadcount = [] * 10
        self.subject = [] * len(self.IMAPSERVER) * 5
        self.from_ = [] * len(self.IMAPSERVER) * 5
        self.mail_process = None
        curses.wrapper(self.__main__)

    def __main__(self, win):
        self.win = win
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
        y, x = self.win.getmaxyx()

        self.win_day = self.win.subwin(8, int(x / 2) - 2, 2, 2)
        self.win_day.bkgd(' ', curses.color_pair(2) | curses.A_BOLD)
        self.win_time = self.win.subwin(8, int(x / 6), 10, 2)
        self.win_date = self.win.subwin(8, int(x / 4) - 8, 10, int(x / 6) + 2)
        self.win_battery = self.win.subwin(8, int(x / 8) - 2, 10, int(x / 6) + int(x / 4) - 6)
        self.win_notes = self.win.subwin(10, int(x / 2) - 2, 20, 2)
        self.win_cmd = self.win.subwin(1, int(x / 2) - 2, y - 3, 2)
        self.win_mail = self.win.subwin(y - 4, int(x / 2) - 2, 2, int(x / 2) + 2)
        self.win_info = self.win.subwin(int(y / 2) - 7, int(x / 2) - 2, int(y / 2) + 2, 2)

        self.drawInfoBox()
        self.printBoxes()
        self.drawHelpBox()
        self.win.refresh()
        self.win_day.refresh()
        self.win_mail.refresh()
        self.win_time.refresh()
        self.win_cmd.refresh()
        self.win_info.refresh()
        self.win_notes.refresh()
        self.win_date.refresh()
        self.win_battery.refresh()

        tr = threading.Thread(target=self.cmdinput)
        tr.start()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i in range(0, len(self.IMAPSERVER)):
                executor.submit(self.getMail, self.IMAPSERVER[i], i)
        executor.shutdown(wait=True)

        self.printBoxes()
        self.printEmail()
        self.win.refresh()
        # self.win_mail.refresh()

        tr.join()

    def getMail(self, IMAPSERVER, i):
        try:
            mail = imaplib.IMAP4_SSL(IMAPSERVER)
            mail.login(self.USER[i], self.PASSWORD[i])
            status, m = mail.select("INBOX")  # connect to inbox.
            status, v = mail.search(None, '(UNSEEN)')
            self.unreadcount.append(len(v[0].split()))
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

    def printBoxes(self):
        h, w = self.win.getmaxyx()
        textpad.rectangle(self.win, 1, 1, int(h / 2), int(w / 2))
        textpad.rectangle(self.win, int(h / 2) + 1, 1, h - 2, int(w / 2))
        textpad.rectangle(self.win, 1, int(w / 2) + 1, h - 2, w - 1)
        textpad.rectangle(self.win, h - 4, 1, h - 5, int(w / 2))

    def drawHelpBox(self):
        h, w = self.win.getmaxyx()
        self.win_info.addstr(1, 1, "TerMail - Options:", curses.A_BOLD)
        self.win_info.addstr(3, 1, ":ur [pos]              set unread flag on specified pos of mails")
        self.win_info.addstr(4, 1, ":r [pos]               set read flag on specified pos of mails")
        self.win_info.addstr(5, 1,
                             ":ur [pos1][pos2]       set unread flag on specified pos1 of mails to specified pos2 mail")
        self.win_info.addstr(6, 1,
                             ":r [pos1][pos2]        set read flag on specified pos1 of mails to specified pos2 mail")
        self.win_info.addstr(7, 1, ":urall                 set unread flag on all unread mails")
        self.win_info.addstr(8, 1, ":rall                  set read flag on all unread mails")
        self.win_info.addstr(9, 1, ":a [note]              add note [note] to window")
        self.win_info.addstr(10, 1, ":d [pos]               delete note on [pos] on window")
        self.win_info.addstr(11, 1, ":d                     deletes last note on window")
        self.win_info.addstr(12, 1, ":o                     open mail service")
        self.win_info.addstr(13, 1, ":c                     close mail service")
        self.win_info.addstr(14, 1, ":q                     close Program")

    def drawInfoBox(self):
        self.win_day.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%A"), font="starwars"), curses.A_BOLD)
        self.win_time.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%H:%M"), font="starwars"), curses.A_BOLD)
        self.win_date.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%d.%m.%g"), font="starwars"), curses.A_BOLD)
        self.win_battery.addstr(1, 5, "Battery:")
        self.win_battery.addstr(2, 5, "-percentage:")
        self.win_battery.addstr(3, 5, "  " + str(round(psutil.sensors_battery().percent, 2)) + "%")
        self.win_battery.addstr(4, 5, "-plugged in:")
        self.win_battery.addstr(5, 5, "  " + str(psutil.sensors_battery().power_plugged))
        self.win_notes.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%g"), font="starwars"), curses.A_BOLD)

    def printEmail(self):
        abstand = 5
        h, w = self.win.getmaxyx()
        for i in range(0, len(self.IMAPSERVER)):
            unread = int(len(self.subject) / len(self.IMAPSERVER))
            self.win_mail.addstr(1 + (i * unread * 2) + (i * abstand), 1,
                                 str(self.USER[i])[0:int(w / 2) - 3],
                                 curses.color_pair(1))
            self.win_mail.addstr(2 + (i * unread * 2) + (i * abstand), 1,
                                 "Unread E-Mails: " + str(self.unreadcount[i]), curses.A_BOLD)
            for j in range(0, unread):
                if j < self.unreadcount[i]:
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
        self.win_cmd.addstr(0, 0, self.cmd, curses.color_pair(1))
        self.win_cmd.refresh()

        # read input and catch control c
        while True:
            try:
                c = self.win.getch()
            except KeyboardInterrupt:
                return False
            # catch nothing typed in time
            if c == curses.ERR:
                pass
            elif c == 10:  # Enter
                if self.cmd == ":q":
                    return False  # Exit the while loop
                elif self.cmd == ":o":
                    self.mail_process = subprocess.Popen(['thunderbird', '-new-tab'], stdout=subprocess.DEVNULL,
                                                         stderr=subprocess.STDOUT)
                elif self.cmd == ":c":
                    if self.mail_process is not None:
                        self.mail_process.terminate()
                self.cmd = ""
            elif self.cmd == "this is your command line!":
                self.cmd = chr(c)
            elif c == 27:
                self.cmd = "this is your command line!"
            elif c == curses.KEY_RESIZE:  # if window gets resized so it doesnt print weird characters
                pass
            elif c == 127:
                self.cmd = self.cmd[:-1]
            else:
                self.cmd += chr(c)

            # draw to window and refresh
            self.win_cmd.clear()
            try:
                self.win_cmd.addstr(0, 0, self.cmd, curses.color_pair(1))
            except Exception:
                self.cmd = ""
            self.win_cmd.refresh()
            curses.curs_set(1)


t = TerMail()
