# 最小化测试：纯 Python 线程扫描 D 盘找"演示"
import os
import threading

results = []
lock = threading.Lock()
stop = False


def scan(path):
    global stop
    if stop:
        return
    try:
        with os.scandir(path) as it:
            for entry in it:
                if stop:
                    return
                try:
                    name = entry.name
                    if "演示" in name:
                        with lock:
                            results.append(entry.path)
                            print("FOUND:", entry.path)
                    if entry.is_dir(follow_symlinks=False):
                        scan(entry.path)
                except OSError:
                    continue
    except OSError:
        pass


t = threading.Thread(target=scan, args=("D:\\",))
t.start()
t.join()
print("total:", len(results))
