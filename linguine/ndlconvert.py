#!/usr/bin/env python3

import sys
import os
import datetime

import argparse

from .data import loaddata, writedata

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=str,
                        help="Output filename")

    parser.add_argument("file", type=str, nargs="+",
                        help="The file names to read in")


    args = parser.parse_args()
    data = loaddata(args.file)
    writedata(data, args.output)

if __name__ == "__main__":
    sys.exit(main())
