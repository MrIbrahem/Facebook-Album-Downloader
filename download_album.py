import os
import sys
import time
import timeit
import requests
from PIL import Image
from six.moves.queue import Queue
from threading import Thread
from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from six.moves import range
from six.moves import input
from pathlib import Path

Dir = Path(__file__).parent
cookies = {}
baseURL = "http://facebook.com/"
username = ""
password = ""
albumLink = "https://www.facebook.com/aalaaragabdesigns/posts/510169624089508"
albumName = "u"
albumUser = ""
max_workers = 8


class DownloadWorker(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            link = self.queue.get()
            r = requests.get('https://www.facebook.com/photo/download/?fbid=' + link, cookies=cookies)
            i = Image.open(StringIO(r.content))
            i.save(Dir / albumName / (link + '.jpg'))
            self.queue.task_done()


if __name__ == "__main__":

    print("[Facebook Album Downloader v1.1]")
    start = timeit.default_timer()

    extensions = webdriver.ChromeOptions()
    # hide images
    prefs = {
        "profile.managed_default_content_settings.images": 2, 
        "profile.default_content_setting_values.notifications": 2
        }

    extensions.add_experimental_option("prefs", prefs)

    browser = webdriver.Chrome(options=extensions)
    # browser = webdriver.Chrome(options=extensions)
    browser.implicitly_wait(1)

    print("[Loading Album]")
    browser.get(albumLink)

    # get album name
    albumName = browser.find_element_by_class_name("fbPhotoAlbumTitle").text

    # create album path
    if not (Dir / albumName).exists():
        (Dir / albumName).mkdir(parents=True, exist_ok=True)

    queue = Queue()

    for x in range(max_workers):
        worker = DownloadWorker(queue)
        worker.daemon = True
        worker.start()

    print("[Getting Image Links]")

    # scroll to bottom
    previousHeight = 0
    reachedEnd = 0

    while reachedEnd != None:
        browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        currentHeight = browser.execute_script("return document.body.scrollHeight")

        if previousHeight == currentHeight:
            reachedEnd = None

        previousHeight = currentHeight
        time.sleep(0.6)

    linkImages = browser.execute_script("list = []; Array.prototype.forEach.call(document.querySelectorAll('.uiMediaThumb'), function(el) { var src = el.getAttribute('id'); if(src && src.indexOf('pic_') > -1) list.push(src.split('_')[1]); }); return list;")
    totalImages = len(linkImages)

    print("[Found: " + str(len(linkImages)) + "]")

    for fullRes in linkImages:
        queue.put(fullRes)

    browser.quit()

    print("[Downloading...]")
    queue.join()

    stop = timeit.default_timer()
    print("[Time taken: %ss]" % str(stop - start))
    input("Press any key to continue...")
