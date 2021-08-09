#!/usr/bin/env python3

import json
import os
import functools
import AO3
import operator
import re
from colorama import Fore
import threading
import warnings
from time import sleep

# warnings.filterwarnings("ignore")

CACHE="cache.json"

def compose(*functions):
    def compose2(g, f):
        return lambda x: f(g(x))
    return functools.reduce(compose2, functions, lambda x: x)

def openJson(path):
    with open(path) as f:
        jsonf = json.load(f)
    return jsonf

def addWorks(d, work):
    d[work.title] = work.nchapters
    return d

def createCacheJsonFromWorks(works):
    return functools.reduce(addWorks, works, {})

def souldDownload(cacheDict, work):
    if not cacheDict or \
       not work.title in cacheDict:
        print(f"{Fore.LIGHTBLUE_EX}found new fanfic:{Fore.RESET} {work.title}")
        return True
    else:
        return cacheDict[work.title] < work.nchapters

def filterWorks(works):
    def filterWorks_(cacheDict):
        removedNotUpdated = [(work if souldDownload(cacheDict, work) else None ) for work in works]
        return list(filter(lambda work: operator.is_not(None, work), removedNotUpdated))
    return filterWorks_
def updateCacheFile(old):
    def updateCacheFile_(current):
        if not old:
            return current
        else:
            old.update(current)
            new = old
            return new
        print(Fore.RED+"you should note see this: out of if update"+Fore.RESET)
    return updateCacheFile_

def writeCacheFile(cacheFile):
    def writeCacheFile_(cacheDict):
        json.dump(cacheDict, cacheFile)
        return cacheDict
    return writeCacheFile_

def checkCacheFile(works):
    def checkCacheFile_(path):
        cacheFileExist = os.path.exists(path)
        if not cacheFileExist:
            cacheDict = {}
        elif cacheFileExist:
            cacheDict = openJson(path)

        with open(path, "w") as cacheFile:
            compose(
                createCacheJsonFromWorks,
                updateCacheFile(cacheDict.copy()),
                writeCacheFile(cacheFile),
            )(works)
        return cacheDict
    return checkCacheFile_

def filterWitchToDownload(works):
    directoryPath = compose(os.path.realpath, os.path.dirname)(__file__)
    return compose(
        lambda cache: os.path.join(directoryPath, cache),
        checkCacheFile(works),
        filterWorks(works),
    )(CACHE)

def downloadWorks__(filePath, dFormat, work):
    work.download_to_file(filePath, dFormat)
    sleep(.05)
    print(f"{Fore.LIGHTGREEN_EX}Finished downloading {work.title}{Fore.RESET}")

def downloadWorks(path, dFormat):
    def downloadWorks_(works):
        if len(works) == 0:
            print(Fore.GREEN+"No update found. You already are up to date! ⌣"+Fore.RESET)
            return None
        threads = []
        for work in works:
            print(f"{Fore.BLUE}downloading{Fore.RESET} {work.title}")
            fileName = f"{work.title}.{dFormat}".replace("/", "\\")
            filePath = os.path.join(path, fileName)
            newThread = threading.Thread(target=downloadWorks__, args=(filePath, dFormat, work))
            newThread.start()
            threads.append(newThread)
        for thread in threads:
            thread.join()
        print(Fore.GREEN+"You are up to date! ⌣ happy reading"+Fore.RESET)
        return None

    return downloadWorks_

def loadWorkMetadata(work):
    with warnings.catch_warnings(record=True) as w:
        work.reload(load_chapters=False)
        if len(w) != 0:
            print(f"{work.title} might take a while")
    sleep(.05)
    return None

def loadWorksMetadata(works):
    threads = []
    loadedWorks = []
    print(f"starting to check you {Fore.CYAN}{len(works)}{Fore.RESET} subsciption")
    for work in works:
        loadedWorks.append(work)
        newThread = threading.Thread(target=loadWorkMetadata, args=([work]))
        newThread.start()
        threads.append(newThread)
    for thread in threads:
        thread.join()
    return loadedWorks

def makePath(string):
    return compose(
        os.path.expanduser,
        os.path.expandvars,
    )(string)

def main():
    directoryPath = compose(os.path.realpath, os.path.dirname)(__file__)
    setup = openJson(os.path.join(directoryPath, "setup.json"))
    downloadPath = makePath(setup["downloadsPath"])
    os.makedirs(downloadPath, exist_ok=True),
    compose(
        lambda setup: AO3.Session(setup["username"], setup["password"]),
        lambda session: session.get_work_subscriptions(use_threading=True),
        loadWorksMetadata,
        filterWitchToDownload,
        downloadWorks(downloadPath, setup["format"]),
    )(setup)


if __name__ == "__main__":
    main()
