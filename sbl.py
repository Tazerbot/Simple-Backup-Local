#! /bin/python3
#   __________  _
#  / ____|  _ \| |
# | (___ | |_) | |
#  \___ \|  _ <| |
#  ____) | |_) | |____
# |_____/|____/|______|
#
# http://tazerbot.zapto.org:2000/Jverm/SB-Local/blob/master/sbl.py
#
# If adding functions, make sure that init()
# and confirmconf() are run before ANYTHING that needs
# data_dir to be populated.
#
# Threading work starting 16/06
#
import sys
import threading
import os
import time
import argparse
import subprocess
from subprocess import CalledProcessError


class color:  # Colors for printing
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# Constants!
version = 'You think I\'m that organized?'
date = time.strftime("%d-%m-%I:%M")
SB_DIR = os.getenv("HOME") + "/.SB/"
mount_dir = SB_DIR + 'mnt/'


# I plan on implementing this at a later date.
r_exclude = 'Windows', 'System32', 'Intel', "'Program Files'",
"'Program Files (x86)'", "ProgramData", "'System Volume Information'",
"'Documents and Settings'", 'hiberfile.sys', 'pagefile.sys', 'swapfile.sys',
'Recovery', "'$Recycle.Bin'", "PerfLogs"

#  Check for the required config directories.

if not os.path.exists(SB_DIR):
    os.mkdir(SB_DIR)

if not os.path.exists(mount_dir):
    os.mkdir(mount_dir)

while not os.path.isfile(os.getenv("HOME") + '/.SB/sb.conf'):
    data_dir = input('Where would you like the data to be'
                     ' backed up to?\n: ')

    if os.path.exists(data_dir):
        break

    if not os.path.exists(data_dir):
        print('That directory doesn\'t exist')
        continue


def confirmconf():  # Checks if the conf file exists.
                    # If not, makes it and asks for config
    global data_folder

    if os.path.isfile(SB_DIR + 'sb.conf'):
        with open(SB_DIR + 'sb.conf', 'r') as data_file:
            data_folder = data_file.readlines(0)
            data_folder = data_folder[0]

    if not os.path.isfile(SB_DIR + 'sb.conf'):
        configfile(data_folder)
        with open(SB_DIR + 'sb.conf', 'r') as data_file:
            data_folder = data_file.readlines(0)
            data_folder = data_folder[0]


def main():  # argparse stuff
    parser = argparse.ArgumentParser(description='Move some bits')

    parser.add_argument('-r', '--reconfig',
                        help='Removes the config file to change it',
                        action='store_true')  # <----

    parser.add_argument('-t', '--time', type=str,
                        help='Prints the date/time of specified backup \
                        by name', action='store', metavar='name')

    parser.add_argument('-d', '--dir', action='store_true',
                        help='Prints the currently configured backup \
                        directory. If not configured, configures.')

    parser.add_argument('-l', '--list', help='List all backups \
                        that have been run.', action='store_true')

    parser.add_argument('-s', '--size', help='List size of specified backup',
                        action='store', metavar='name')

    parser.add_argument('-v', '--version', help='List the version number.',
                        action='store_true')

    parser.add_argument('-a', '--admin',
                        help='Mounts a hard drive and enables admin acct.',
                        action='store_true')

    parser.add_argument('-L', '--load',
                        help='Checks the data directory for backups made without SB.',
                        action='store_true')

    parser.add_argument('-T', '--test',
                        help='Smart-test a hard drive.',
                        action='store_true')

    args = parser.parse_args()

    if args.version:
        print('Version? ' + version)
        exit()

    elif args.reconfig:  # Nukes the config file and re-writes it w/ user input
        reconfig()
        confirmconf()
        exit()

    elif args.dir:  # Prints the backup location
        C = SB_DIR + 'sb.conf'
        if os.path.isfile(C):
            F = open(SB_DIR + 'sb.conf')
            L = F.readlines()
            F.close()
            print('Backup dir = ' + L[0])
            exit()
        if not os.path.isfile(C):
            print('Config not initialized. Do it now.')
            confirmconf()
            exit()

    elif args.time:  # Prints the time the backup was started
        F = open(SB_DIR + args.time + '.dat', 'r')
        Fdate = F.readlines()
        print(args.time + ' data was backed up ' + Fdate[2])
        F.close()
        exit()

    elif args.list:  # lists all the backups that have been logged
        print('Listing previous backups.')
        subprocess.call('ls -l ' + SB_DIR + '*.dat', shell=True)
        exit()

    elif args.size:  # Prints the size of the specified backup
        F = open(SB_DIR + args.size + '.dat', 'r')
        Fsize = F.readlines()
        print(Fsize[3])
        F.close()
        exit()

    elif args.admin:  # Mounts a windows drive and enables the admin acct
        print(color.RED + '\nEnabling admin account.\n' + color.END)
        confirmconf()
        mount()
        admin()
        umount()

    elif args.load:
        confirmconf()
        load_nonsb()
        exit()

    elif args.test:
        print(color.RED + '\nTesting HDD\n' + color.END)
        get_info()
        exit()

    elif args:  # Runs normally. Mounts a drive and copies data from/to it.
        confirmconf()
        mount()
        point()
        umount()


def detect(part):
    while True:
        try:
            blkid = str(subprocess.check_output('lsblk -f ' + '/dev/' + part, shell=True))
            if 'ntfs' in blkid:
                print(color.RED + '\nDetected NTFS\n' + color.END)
                return 1
                break
            elif 'hfs' in blkid:
                print(color.RED + '\nDetected HFS\n' + color.END)
                return 2
                break
            elif 'vfat' in blkid:
                print(color.RED + '\nDetected VFAT\n' + color.END)
                return 3
                break
            else:
                print(color.RED + '\nWeird FS\n' + color.END)
                return 666
                break

        except CalledProcessError:
            print(color.RED + 'Pausing for 10 seconds.')
            time.sleep(10)
            continue


def mount():
    subprocess.call("lsblk", shell=True)
    while 'Incorrect Input':
        part = input('What partition would you like to mount?\n[s'
                     'da1,sdx4/N]: ')

        dev = ''.join([i for i in part if not i.isdigit()])

        if os.path.exists('/sys/block/' + dev + '/' + part):
            fs = detect(part)

            if fs == 1:
                subprocess.call('sudo ntfsfix /dev/' + part, shell=True)
                subprocess.call('sudo mount -o remove_hiberfile /dev/' + part + ' ' + mount_dir, shell=True)

            if fs == 2:
                exit_code = subprocess.call('sudo mount -t hfsplus /dev/' + part + ' ' + mount_dir, shell=True)
                if exit_code == 32:
                    print('Dirty filesystem, forcing fsck on partition...')
                    time.sleep(2)
                    subprocess.call('sudo fsck -f /dev/' + part, shell=True)
                    subprocess.call('sudo mount -t hfsplus /dev/' + part + ' ' + mount_dir, shell=True)

            if fs == 3:
                exit_code = subprocess.call('sudo mount -t vfat /dev/' + part + ' ' + mount_dir, shell=True)

            if fs == 666:
                print('Partition unknown / not implemented yet.')
            break

        if part in ['N', 'n']:
            print('\nExiting...')
            break

        else:
            print('Enter a valid partition.')
            time.sleep(.5)
            continue


def point():  # The main point of the program, backs up or restores data from a partition
    global name
    global BR

    old = mount_dir + "Windows.old/Users/"
    name = input("What is the customers name? ")

    BR = input('Are you backing up or restoring?\n[B/r]').upper()
    if BR == 'B':
        if os.path.exists(data_folder + "/" + name):
            print('\n')
            print('This data seems to be backed up already. \n'
                  'Figure it out or name it something else.\n')
            subprocess.call('sudo umount ' + mount_dir, shell=True)
            exit()
        # else:
        #     print('Backup folder does not exists, creating...\n')
        #     subprocess.call('sudo mkdir -p ' + data_folder + '/' + name, shell=True)
        fdu = input('Full disk or just users??\n[F/U]: ').upper()
        if fdu == 'U':
            source = mount_dir + 'Users'
            dest = data_folder.rstrip() + '/' + name.rstrip()
            dest = dest.rstrip()
            if os.path.exists(old):
                print('.old files exist on root of drive!!')
                yn = input('Would you like to back up these files?\n: ').upper()
                if yn == 'Y':
                    source = source + ' ' + old
        if fdu == 'F':
            source = mount_dir + '*'
            dest = data_folder.rstrip() + '/' + name.rstrip()

    if BR == 'R':
        source = data_folder + '/' + name
        dest = mount_dir + 'Data/'

    # file_transfer(source, dest)

    if BR == 'B':
        if not os.path.exists(dest):
            print('Creating Directory...')
            print(dest)
            os.system('mkdir -p ' + dest)

    subprocess.call("sudo rsync -ah --progress --ignore-existing " + source +
                    " " + dest, shell=True)

    detailfile(name, BR)

    if BR == 'B':
        print('The data has been moved.\n')
        print('Setting new owner permissions on backed up files...')
        user = os.getenv('USER')
        subprocess.call('sudo chown -R ' + user + ':' + user + ' ' + dest, shell=True)


def file_transfer(source, dest):
    subprocess.call("sudo rsync -ah --progress --ignore-existing " + source +
                    " " + dest, shell=True)


def admin():  # Allows you to enable the admin account
    sam1 = mount_dir + 'Windows/System32/config/SAM'
    sam2 = mount_dir + 'Windows/System32/config/sam'
    print('We will now enable the admin account. ')

    if os.path.isfile(sam1):
        subprocess.call('chntpw ' + sam1, shell=True)

    if os.path.isfile(sam2):
        subprocess.call('chntpw ' + sam2, shell=True)

    op = open(mount_dir + 'disable_admin.bat', 'w')
    op.write('net user administrator /active:no')
    op.close()

    print(os.linesep)
    print('Placed bat file at C:/disable_admin.bat. '
          'Run this file \nwhen you are done to disable '
          'the admin account.')
    print(os.linesep)
    time.sleep(.2)


def detailfile(name, BR):  # Writes size, time, and backup/restore to the data file.
    input('Ready to calculate size?\n: ')
    S = os.popen('sudo du -sh ' + data_folder +  # Size value.
                 '/' + name).read()

    op = open(SB_DIR + name + '.dat', 'w')
    op.write(name + '\n')
    op.write(BR + '\n')
    op.write(time.strftime("%d-%m %I:%M\n"))
    op.write(S + '\n')
    op.close


def umount():  # unmounts the partition when it is done the backup.
    x = input('Ready to umount?\n: ').lower()
    if x == 'y':
        subprocess.call('sudo umount ' + mount_dir, shell=True)
        print('Partition unmounted.')


def configfile(data_dir):  # Writes the backup drive location into a file for later reading
    F = open(SB_DIR + 'sb.conf', 'w')
    F.write(data_dir)
    F.close


def reconfig():  # Removes old config
    print('Removing old config file.')
    subprocess.call('rm -f ' + SB_DIR + 'sb.conf', shell=True)


def load_nonsb():
    backups = os.system('ls  ' + data_folder)
    for i in str(backups):
        print(i)


def get_info():
    while True:
        subprocess.call('lsblk', shell=True)
        disk = input('Which disk would you like to test?\n[sda, sdb, etc...]: ').lower()
        disk = '/dev/' + disk
        if not os.path.exists(disk):
            print('Disk does not exist. Try a different ID.')
            continue
        else:
            test_type = input('Long or short test?\n[l/s]')
            if test_type == 'l':
                test = 'long'
            if test_type == 's':
                test = 'short'
            test_drive(disk, test)


def test_drive(disk, test):
    try:
        subprocess.call('sudo smartctl --test=' + test + ' ' + disk, shell=True)
        print(str(test.capitalize()) + ' testing ' + disk)
        subprocess.call('sudo watch -n .5 smartctl --log=selftest ' + disk, shell=True)
    except PermissionError:
        print('\nClosing...')
        exit()


def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor


if __name__ == '__main__':
    main()
