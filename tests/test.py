import email
import imaplib
from email.header import decode_header
import time
import concurrent.futures

IMAPSERVER = ['imap.gmail.com', 'imap.tfobz.net']  # , 'imap.tfobz.net']
USER = ['markus.telser99@gmail.com', 'markus.telser@tfobz.net']  # , 'markus.telser@tfobz.net']
PASSWORD = ["niajayrsrxmixhjw", "tlsmkst29"]  # , "tlsmkst29"]
sub = [] * len(IMAPSERVER) * 5

unreadcount = [] * len(IMAPSERVER) * 5
subject = [] * len(IMAPSERVER) * 5
from_ = [] * len(IMAPSERVER) * 5

t1 = time.perf_counter()

# def getMail(IMAPSERVER,j):
global subject
mail = imaplib.IMAP4_SSL(IMAPSERVER)
mail.login(USER[j], PASSWORD[j])
status, m = mail.select("INBOX")  # connect to inbox.
status, v = mail.search(None, '(UNSEEN)')
unreadcount.append(len(v[0].split()));
print("Runde", j)
messages = int(m[0])
for i in range(messages, messages - 5, -1):
    res, msg = mail.fetch(str(i), "(RFC822)")
    # print(str(msg))
    # print()
N = 5
k = 0
for i in range(messages, messages - N, -1):
    # fetch the email message by IDfor j in range(0, len(IMAPSERVER)):
    for resp in msg:
        if isinstance(resp, tuple):
            # parse a bytes email into a message object
            msg = email.message_from_bytes(resp[1])
            # decode the email subject and from
            sub = decode_header(msg["Subject"])[0][0]
            fr = msg.get("From")
            if isinstance(sub, bytes):
                sub = sub.decode('utf-8')
            from_.append(fr)
            subject.append(sub)
            k = k + 1

# j = 0
# for mail in (IMAPSERVER):
#    getMail(mail,j)
#    j= j+1


t2 = time.perf_counter()

for i in from_:
    print(i)

print(t2 - t1)
