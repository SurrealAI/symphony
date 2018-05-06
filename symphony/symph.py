from symphony.commandline import SymphonyParser
from symphony.engine import *
from symphony.kube import *
import sys


class SymphonyDefaultParser(SymphonyParser):
    def create_cluster(self):
        return Cluster.new('kube')

def main():
    SymphonyDefaultParser().main()


if __name__ == '__main__':
    main()
