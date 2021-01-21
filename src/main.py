import curses
from curses import textpad
import time
import imaplib
import email
from email.header import decode_header
import pyfiglet
import subprocess
import concurrent.futures
from multiprocessing import Process
import credentials_real as cred


class TerMail:
    def __init__(self):
        self.bar = '█'  # an extended ASCII 'fill' character
        self.stdscr = curses.initscr()
        self.cmd = "this is your command line!"
        self.IMAPSERVER = cred.IMAPSERVER
        self.USER = cred.USER
        self.PASSWORD = cred.PASSWORD
        self.unreadcount = [] * 10
        self.subject = [] * len(self.IMAPSERVER) * 5
        self.from_ = [] * len(self.IMAPSERVER) * 5
        self.mail_process = None
        curses.wrapper(self.__main__)

    def __main__(self, stdscr):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

        x, y = stdscr.getmaxyx()

        self.win_day = stdscr.subwin(20, 200, 5, 7)
        self.win2 = stdscr.subwin(30, 200, 15, 5)
        self.win_cmd = stdscr.subwin(1, 117, 57, 2)
        self.win_mail = stdscr.subwin(80, int(y / 2) + 10, 5, 50)
        print(x - 10)

        # run program
        self.printClock()
        self.printBoxes(stdscr)
        self.printHelp()
        self.stdscr.refresh()

        p = Process(target=self.cmdinput)
        p.start()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i in range(0, len(self.IMAPSERVER)):
                executor.submit(self.getMail, self.IMAPSERVER[i], i)
        executor.shutdown(wait=True)
        self.stdscr.clear()
        self.printEmail()
        self.stdscr.refresh()

        p.join()

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
            return False

    def printBoxes(self, stdscr):
        h, w = stdscr.getmaxyx()
        textpad.rectangle(stdscr, 1, 1, int(h / 2), int(w / 2))
        textpad.rectangle(stdscr, int(h / 2) + 1, 1, h - 2, int(w / 2))
        textpad.rectangle(stdscr, 1, int(w / 2) + 1, h - 2, w - 1)
        textpad.rectangle(stdscr, h - 4, 1, h - 5, int(w / 2))

    def printHelp(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(int(h / 2) + 3, 2, "TerMail - Options:", curses.A_BOLD)
        self.stdscr.addstr(int(h / 2) + 5, 2, ":ur [pos]              set unread flag on specified pos of mails")
        self.stdscr.addstr(int(h / 2) + 6, 2, ":r [pos]               set read flag on specified pos of mails")
        self.stdscr.addstr(int(h / 2) + 7, 2,
                           ":ur [pos1][pos2]       set unread flag on specified pos1 of mails to specified pos2 mail")
        self.stdscr.addstr(int(h / 2) + 8, 2,
                           ":r [pos1][pos2]        set read flag on specified pos1 of mails to specified pos2 mail")
        self.stdscr.addstr(int(h / 2) + 9, 2, ":urall                 set unread flag on all unread mails")
        self.stdscr.addstr(int(h / 2) + 10, 2, ":rall                  set read flag on all unread mails")
        self.stdscr.addstr(int(h / 2) + 11, 2, ":a [note]              add note [note] to window")
        self.stdscr.addstr(int(h / 2) + 12, 2, ":d [pos]               delete note on [pos] on window")
        self.stdscr.addstr(int(h / 2) + 13, 2, ":d                     deletes last note on window")
        self.stdscr.addstr(int(h / 2) + 14, 2, ":o                     open mail service")
        self.stdscr.addstr(int(h / 2) + 15, 2, ":c                     close mail service")
        self.stdscr.addstr(int(h / 2) + 16, 2, ":q                     close Program")

    def printClock(self):
        try:
            self.win_day.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%A"), font="starwars"), curses.A_BOLD)
            self.win2.addstr(0, 0, pyfiglet.figlet_format(time.strftime("%H :%M"), font="starwars"), curses.A_BOLD)
        except Exception as e:
            self.cmd = e

    def printEmail(self):
        abstand = 5
        h, w = self.stdscr.getmaxyx()
        for i in range(0, len(self.IMAPSERVER)):
            unread = int(len(self.subject) / len(self.IMAPSERVER))
            self.win_mail.addstr(3 + (i * unread * 2) + (i * abstand), 1,
                                 str(self.USER[i])[0:int(w / 2) - 3],
                                 curses.color_pair(1))
            self.win_mail.addstr(4 + (i * unread * 2) + (i * abstand), 1,
                                 "Unread E-Mails: " + str(self.unreadcount[i]), curses.A_BOLD)
            for j in range(0, unread):
                if j < self.unreadcount[i]:
                    self.stdscr.addstr(5 + (j * 2) + (i * unread * 2) + (i * abstand), int(w / 2) + 2,
                                       "Subject: " + str(self.subject[j + (i * unread)][0:int(w / 2) - 15]),
                                       curses.color_pair(2))
                    self.stdscr.addstr(6 + (j * 2) + (i * unread * 2) + (i * abstand), int(w / 2) + 2,
                                       "From: " + str(self.from_[j + (i * unread)][0:int(w / 2) - 15]),
                                       curses.color_pair(2))
                else:
                    self.stdscr.addstr(5 + (j * 2) + (i * unread * 2) + (i * abstand), int(w / 2) + 2,
                                       "Subject: " + str(self.subject[j + (i * unread)][0:int(w / 2) - 15]))
                    self.stdscr.addstr(6 + (j * 2) + (i * unread * 2) + (i * abstand), int(w / 2) + 2,
                                       "From: " + str(self.from_[j + (i * unread)][0:int(w / 2) - 15]))

    def cmdinput(self):
        # print instruction for cmd
        self.win_cmd.addstr(0, 0, self.cmd, curses.color_pair(1))
        self.win_cmd.refresh()

        # read input and catch control c
        while True:
            try:
                c = self.stdscr.getch()
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
