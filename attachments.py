#!/usr/bin/python

from __future__ import print_function
import argparse
import email
import getpass
import imaplib
import os

OK = 'OK'


def main(server, account, folder, save, directory, delete):

    # Login to email server
    imap = imaplib.IMAP4_SSL(server)
    try:
        ret, data = imap.login(account, getpass.getpass())
    except imaplib.IMAP4.error:
        print("Login to '{0}' for account '{1}' failed.".format(server, account))
        raise

    # Retrieve list of folders
    ret, folders = imap.list()
    if ret != OK:
        raise RuntimeError('Could not retrieve folder list ({0})'.format(ret))
    print('Folders:')
    print(folders)

    # Retrieve list of emails for given folder
    ret, data = imap.select(folder)
    if ret != OK:
        raise RuntimeError("Could not select folder - '{0}' : '{1}'".format(folder, data))

    # Iterate over each email
    ret, ids = imap.search(None, 'ALL')
    if ret != OK:
        raise RuntimeError('Could not retrieve email ids.')

    for message_id in ids[0].split():

        ret, data = imap.fetch(message_id, '(RFC822)')
        if ret != OK:
            raise RuntimeError('Could not retrieve email (id={0})'.format(message_id))

        message = email.message_from_string(data[0][1])

        # Report email subject, date, and attachments
        print('Message {0}:'.format(message_id))
        print('\tSubject: {0}'.format(message['Subject']))
        print('\tDate: {0}'.format(message['Date']))

        # Save attachments to given directory
        for part in message.walk():
            print(part.get_content_type())
            filename = part.get_filename()
            if filename and save:
                payload = part.get_payload(decode=True)
                with open(os.path.join(directory, filename), 'wb') as handle:
                    handle.write(payload)

        # Mark email as deleted
        if delete:
            imap.store(message_id, '+FLAGS', '\\Deleted')

    # Remove deleted emails
    if delete:
        imap.expunge()

    # Logout from email server
    imap.close()

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', default='imap.1and1.com')
    parser.add_argument('-a', '--account', default='inbox@lortons.net')
    parser.add_argument('-f', '--folder', required=True)
    parser.add_argument('-d', '--directory', default=os.getcwd())
    parser.add_argument('-x', '--delete', default=False, action='store_true')
    parser.add_argument('--save', default=False, action='store_true')

    args = parser.parse_args()

    main(args.server, args.account, args.folder, args.save, args.directory, args.delete)
