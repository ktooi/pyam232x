# -*- coding: utf-8 -*-
from __future__ import print_function
from argparse import ArgumentParser
import json
from logging import basicConfig, getLogger, DEBUG, INFO
from . import AM232x


# これはメインのファイルにのみ書く
basicConfig(level=INFO)
logger = getLogger(__name__)


def measure(am232x, args):
    am232x.measure()
    am232x.read()
    if not args.quick:
        am232x.measure()


def temperature(am232x, args):
    measure(am232x, args)
    print(am232x.temperature)


def humidity(am232x, args):
    measure(am232x, args)
    print(am232x.humidity)


def discomfort(am232x, args):
    measure(am232x, args)
    print(am232x.discomfort)


def default(am232x, args):
    print("temperature : {temp}".format(temp=am232x.temperature))
    print("humidity    : {hum}".format(hum=am232x.humidity))
    print("discomfort  : {dscf}".format(dscf=am232x.discomfort))


def to_json(am232x, args):
    mesg = json.dumps({"temperature": am232x.temperature,
                       "humidity": am232x.humidity,
                       "discomfort": am232x.discomfort})
    print(mesg)


def parse_args():
    parser = ArgumentParser(description=("Measure and show temperature, humidity and discomfort from AM2321/AM2322."))
    parser.add_argument('-d', '--debug', action='store_true', help="Show verbose messages.")
    parser.add_argument('-b', '--bus', dest="bus", type=int, default=1, help="Bus number.")
    parser.add_argument('-q', '--quick', dest="quick", action='store_true',
                        help="Quickly response mode. The response will be faster, but the output data will be outdated.")
    parser.set_defaults(func=default, subcommand="default")
    subparsers = parser.add_subparsers(dest="subcommand")

    # 共通となる引数を定義。
    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument('--unit', '-u', action='store_true', help="")

    subcmd_temp = subparsers.add_parser("temperature", parents=[common_parser], help="Output temperature.")
    subcmd_temp.set_defaults(func=temperature)

    subcmd_hum = subparsers.add_parser("humidity", parents=[common_parser], help="Output humidity.")
    subcmd_hum.set_defaults(func=humidity)

    subcmd_disc = subparsers.add_parser("discomfort", parents=[common_parser],
                                        help="Output discomfort that calculated with temperature and humidity.")
    subcmd_disc.set_defaults(func=discomfort)

    subcmd_disc = subparsers.add_parser("json", parents=[common_parser],
                                        help="Output data that temperature, humidity and discomfort within JSON format.")
    subcmd_disc.set_defaults(func=to_json)

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
    args = parse_args()
    if args.debug:
        logger.info("Set loglevel to debug.")
        logger.setLevel(DEBUG)
    if args.subcommand == "help":
        # ヘルプを表示して終了。
        args.func(args)
    am232x = AM232x(name="am232x", bus=args.bus)
    args.func(am232x, args)
