# -*- coding: utf-8 -*-
import argparse
import os
import shutil


def init_skeleton(args):
    try:
        shutil.copytree(os.path.dirname(os.path.abspath(__file__)), os.path.join(args.project, "Gastepo"))
        print("[O(∩_∩)O]: Bingo!!! The project was initialized successfully, It is located on {}.".format(args.project))
    except Exception:
        print("[(o´ﾟ□ﾟ`o)]: Damn!!! An exception occurred while initializing the project directory.")


def cli():
    parser = argparse.ArgumentParser(prog="Gastepo", description="%(prog)s Command Line",
                                     epilog="Get %(prog)s on GitHub [https://github.com/bleiler1234/gastepo]")

    parser.add_argument("-V", "--version", action="version", version='%(prog)s 0.0.1',
                        help="show release version and exit")
    parser.add_argument("start", help="Start with %(prog)s.")

    subparsers = parser.add_subparsers(help="")

    skeleton_parser = subparsers.add_parser("skeleton", help="Initialize project with %(prog)s Skeleton.")
    skeleton_parser.add_argument("-p", "--project", nargs="?", help='specify project directory')
    skeleton_parser.set_defaults(func=init_skeleton)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    cli()
