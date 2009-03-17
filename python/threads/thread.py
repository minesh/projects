#!/usr/bin/env python
"""This is the main process that will poll directories and dispatch Threads to
   handle the installation and testing
"""

import os
import time
import threading
import tempfile
import logging
from stat import S_ISREG, S_ISDIR, ST_MODE
import Queue

logging.basicConfig(level=logging.DEBUG)

COS_DIRS = ['/home/mipatel/threads/cos']
PXE_DIRS = ['/home/mipatel/threads/pxe']


# Mutex lock that guards the machines
MUTEX = threading.Lock()
COS_MACHINES = ['10.20.142.121']
PXE_MACHINES = ['10.20.142.122']

COS_QUEUE = Queue.Queue(0)
PXE_QUEUE = Queue.Queue(0)

ESX_KS_CFG = """# Tell anaconda to install rather than upgrade
install cdrom

# Clear partitions
clearpart --linux
#clearpart --firstdisk --overwritevmfs
#autopart --firstdisk

# Accept the VMware EULA
vmaccepteula

# Root password is 'password'
rootpw password

# Setup bootloader
bootloader --location=mbr

# Provide the network information for the installed OS
network --bootproto=static --ip=%(ipAddress)s --netmask=255.255.252.0
--gateway=10.20.143.253 --nameserver=10.20.148.1 --device=vmnic0

# Setup authentication
auth --enablemd5 --enableshadow

# Reboot after we are done
reboot

%post

# Enable root ssh login
sed -i "s:PermitRootLogin no:PermitRootLogin yes:" /etc/ssh/sshd_config
/etc/init.d/sshd restart
"""

class DirPoller(object):
   """A directory object that provides information about its contents"""
   def __init__(self, dirName):
      self.dirName = dirName
      self.previous = None

   def setPrevious(self, newPrevious):
      self.previous = newPrevious

   def getPrevious(self):
      return self.previous

   def listDirectory(self):
      return os.listdir(self.dirName)

   def getFilesAndDirs(self):
      """Returns the files and directories"""
      return [(os.stat(os.path.join(self.dirName, x)),
                  os.path.join(self.dirName, x)) for x in self.listDirectory()]

   def sortByModTime(self, files):
      """Returns the files and directories"""
      newFiles = [(os.path.getmtime(x), os.path.join(self.dirName, x))
                                                             for x in files]
      newFiles.sort()
      return newFiles

   def __getNewest(self, func):
      allFiles = self.getFilesAndDirs()
      # Retrieve just the files
      filesOnly = [path for st, path in allFiles if func(st[ST_MODE])]
      # Get modified time for the files
      sortedFiles = self.sortByModTime(filesOnly)
      try:
         # Last one is the newest, since its a tuple return the path
         return sortedFiles[-1][1]
      except IndexError:
         # No files or dirs
         return ""

   def getNewestFile(self):
      """Get the newest ISO File in the directory
         Returns: tuple
            (file_modification_time, file_name)
      """
      return self.__getNewest(S_ISREG)

   def getNewestDir(self):
      """Get the latest pxe folder in the directory path
         Returns: tuple
            (dir_modification_time, dir_name)
      """
      return self.__getNewest(S_ISDIR)

class ThreadScheduler(threading.Thread):
   """Scheduling thread to manage queue and spawn test threads"""

   def __init__(self, queue, machines):
      super(ThreadScheduler, self).__init__()
      self.queue = queue
      self.machines = machines

   def run(self):
        logging.debug("Starting Scheduler Thread %r" % self)
        while True:
           task = self.queue.get()
           while True:
              # We got an item, wait on lock for cos machine
              if len(self.machines):
                 MUTEX.acquire()
                 ip = self.machines.pop(0)
                 MUTEX.release()
                 # Set IP to the task
                 task.ip = ip
                 task.start()
                 break
              else:
                 # 5 minute power nap
                 time.sleep(5*60)

class ThreadCos(threading.Thread):
   """COS thread to run test on a specific machine"""

   def __init__(self, isoPath):
      super(ThreadCos, self).__init__()
      self.isoPath = isoPath
      self.isoName = os.path.basename(self.iso)
      # IP is set by the scheduler before running this thread
      self.ip = None

   def run(self):
      global COS_MACHINES, MUTEX
      assert self.ip, "NO IP set for the machine"
      logging.debug("Starting cos testing on IP:%r File:%r" %
                                             (self.ip, self.isoPath))
      self.createKickstartIso()

      # Put IP address back on GLOBAL LIST
      MUTEX.acquire()
      COS_MACHINES.append(self.ip)
      MUTEX.release()

      shutil.rmtree(tempDir)

   def createKickstartIso(self):
      mountDir = tempfile.mkdtemp()
      createIsoDir = tempfile.mkdtemp()
      os.system("sudo mount -o loop %s %s" % (self.isoPath, mountDir))
      # Destination directory must not exist when using copytree
      shutil.rmtree(createIsoDir)
      shutil.copytree(mountDir, createIsoDir)
      initrd = os.path.join(self.createIsoDir, 'isolinux', 'initrd')
      initrdimg = initrd + '.img'
      initrdcpio = initrd + '.cpio'
      os.system("sudo sh -c 'gunzip < %s > %s'" % (initrdimg, initrdcpio))

class ThreadPxe(threading.Thread):
   """PXE thread to run test on a specific machine"""

   def __init__(self, pxeDir):
      super(ThreadPxe, self).__init__()
      self.pxeDir = pxeDir
      self.ip = None

   def run(self):
      global PXE_MACHINES, MUTEX
      assert self.ip, "NO IP set for the machine"
      logging.debug("Starting pxe testing on IP:%r Dir:%r" %
                                             (self.ip, self.pxeDir))
      # extend IP address  back on GLOBAL LIST
      MUTEX.acquire()
      PXE_MACHINES.append(self.ip)
      MUTEX.release()

def pollCOS(pollers, q):
   for poller in pollers:
      newFile = poller.getNewestFile()
      if newFile == poller.getPrevious():
         continue
      logging.debug("COS: Found new file: %r" % newFile)
      poller.setPrevious(newFile)
      t = ThreadCos(newFile)
      q.put(t)

def pollPXE(pollers, q):
   for poller in pollers:
      poller.getNewestDir()
      newDir = poller.getNewestDir()
      if newDir == poller.getPrevious():
         continue
      logging.debug("PXE: Found new directory: %r" % newDir)
      poller.setPrevious(newDir)
      t = ThreadPxe(newDir)
      q.put(t)

def main():
   # Spawn the scheduler thread to manage the queues
   cosScheduler = ThreadScheduler(COS_QUEUE, COS_MACHINES)
   pxeScheduler = ThreadScheduler(PXE_QUEUE, PXE_MACHINES)
   cosScheduler.start()
   pxeScheduler.start()

   cosPollers = [DirPoller(item) for item in COS_DIRS]
   pxePollers = [DirPoller(item) for item in PXE_DIRS]


   while True:
      # Sleeps for 30 min
      #time.sleep(30*60)
      time.sleep(1)
      pollCOS(cosPollers, COS_QUEUE)
      pollPXE(pxePollers, PXE_QUEUE)



if __name__ == "__main__":
   main()

