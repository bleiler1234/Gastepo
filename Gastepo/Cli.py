# -*- coding: utf-8 -*-
import argparse


def cli():
    parser = argparse.ArgumentParser(prog="Gastepo", description="Gastepo Command Line",
                                     epilog="Get Gastepo on GitHub [https://github.com/bleiler1234/gastepo]")
    parser.add_argument("run", help="run test on gestepo")
    parser.add_argument("-V", "--version", action="version", version='%(prog)s 1.0.0')
    parser.parse_args()


if __name__ == '__main__':
    cli()
