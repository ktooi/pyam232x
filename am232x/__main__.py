# -*- coding: utf-8 -*-
from __future__ import print_function
from argparse import ArgumentParser
from logging import basicConfig, getLogger, DEBUG, INFO
import yaml
from . import AM232x


# これはメインのファイルにのみ書く
basicConfig(level=INFO)

# これはすべてのファイルに書く
logger = getLogger(__name__)


def temperature(am232x, ns):
    pass


def humidity(am232x, ns):
    pass


def discomfort(am232x, ns):
    pass


def default(am232x, ns):
    pass


def json(am232x, ns):
    pass


def yaml(am232x, ns):
    pass


def parse_args():
    parser = ArgumentParser(description=("Measure and show temperature, humidity and discomfort from AM2321/AM2322."))
    parser.add_argument('-d', '--debug', action='store_true', help="Show verbose messages.")
    parser.add_argument('-b', '--bus', dest="bus", type=int, help="Bus number.")
    parser.set_defaults(func=default)
    subparsers = parser.add_subparsers(dest="subcommand")

    # 共通となる引数を定義。
    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument('--unit', '-u', action='store_true', help="")

    subcmd_temp = subparsers.add_parser("temperature", parents=[common_parser], help="TODO")
    subcmd_temp.set_defaults(func=temperature)

    subcmd_hum = subparsers.add_parser("humidity", parents=[common_parser], help="TODO")
    subcmd_hum.set_defaults(func=humidity)

    subcmd_disc = subparsers.add_parser("discomfort", parents=[common_parser], help="TODO")
    subcmd_disc.set_defaults(func=discomfort)

    subcmd_disc = subparsers.add_parser("json", parents=[common_parser], help="TODO")
    subcmd_disc.set_defaults(func=json)

    subcmd_disc = subparsers.add_parser("yaml", parents=[common_parser], help="TODO")
    subcmd_disc.set_defaults(func=yaml)

    # 以下、ヘルプコマンドの定義。

    # "help" 以外の subcommand のリストを保持する。
    # dict.keys() メソッドは list や tuple ではなく KeyView オブジェクトを戻す。
    # これは、対象となる dict の要素が変更されたときに、 KeyView オブジェクトの内容も変化してしまうので、
    # subparsers.choices の変更が反映されないように list 化したものを subcmd_list に代入しておく。
    subcmd_list = list(subparsers.choices.keys())

    subcmd_help = subparsers.add_parser("help", help="Help is shown.")
    # add_argument() の第一引数を "subcommand" としてはならない。
    # `mcbdsc help build` 等と実行した際に、
    # >>> args = parser.parse_args()
    # >>> args.subcommand
    # で "help" となってほしいが、この第一引数を "subcommand" にしてしまうとこの例では "build" となってしまう。
    # このため、ここでは第一引数を "subcmd" とし、 metavar="subcommand" とすることで
    # ヘルプ表示上は "subcommand" としたまま、 `args.subcommand` が "help" となるよう対応する。
    subcmd_help.add_argument("subcmd", metavar="subcommand", choices=subcmd_list, help="Command name which help is shown.")
    subcmd_help.set_defaults(func=lambda args: print(parser.parse_args([args.subcmd, '--help'])))

    return parser.parse_args()


def main():
    ns = parse_args()
    if ns.subcommand == "help":
        # ヘルプを表示して終了。
        ns.func(ns)
    am232x = AM232x(name="am232x", bus=ns.bus)
    ns.func(am232x, ns)