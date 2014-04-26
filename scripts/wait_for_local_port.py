import socket
import subprocess
import sys
import time

import logbook


def _wait_for_local_port(port, retries=60, sleep_between_retries=5):
    for retry in xrange(retries):
        if retry > 0:
            logbook.info("Could not connect. Retrying...")
            time.sleep(sleep_between_retries)

        logbook.info("Trying port {}", port)
        try:
            s = socket.socket()
            s.connect(("127.0.0.1", port))
        except socket.error:
            pass
        else:
            logbook.info("Successfully connected.")
            return
    subprocess.call("sudo netstat -nap | grep LISTEN", shell=True)
    sys.exit("Could not connect to local port {}".format(port))

if __name__ == "__main__":
    _wait_for_local_port(int(sys.argv[1]))
