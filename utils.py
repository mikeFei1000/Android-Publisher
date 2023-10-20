import hashlib
import os


def readFile(file_path):
    file = open(file_path, encoding="utf-8")
    fileTxt = file.read()
    file.close()
    return fileTxt


def writeFile(file_name, txt):
    dir = os.path.dirname(file_name)
    if len(dir) != 0:
        if not os.path.exists(dir):
            os.makedirs(dir)
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(txt)


def getFileMD5(file_path):
    m = hashlib.md5()
    with open(file_path, 'rb') as f:
        for line in f:
            m.update(line)
    return m.hexdigest()
