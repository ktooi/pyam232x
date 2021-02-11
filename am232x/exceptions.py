# -*- coding: utf-8 -*-
class AM232xError(Exception):
    """ AM232x とのデータ送受信において、何らかのエラーが発生したことを示す Exception.

    am232x モジュールが投げる例外の基底クラスとして利用する。
    """


class ReceiveAM232xDataError(AM232xError):
    """ AM232x からデータを受信した際に、エラーが発生したことを示すエラーコードが含まれていたことを示す Exception.
    """

    def __init__(self, error_code, chip_name="am232x"):
        self._chip_name = chip_name
        self._error_code = error_code

    def __str__(self):
        return ("{chip_name} : Received error code : 0x{error_code:x}"
                .format(chip_name=self._chip_name, error_code=self._error_code))


class AM232xCrcCheckError(AM232xError):
    """ AM232x から受信した CRC と、受信したデータから計算した CRC に相違があることを示す Exception.
    """

    def __init__(self, recv_crc, calc_crc, chip_name="am232x"):
        self._chip_name = chip_name
        self._recv_crc = recv_crc
        self._calc_crc = calc_crc

    def __str__(self):
        return ("{chip_name} : CRC error : [receive : 0x{recv_crc:x}, calculate : 0x{calc_crc:x}]"
                .format(chip_name=self._chip_name, recv_crc=self._recv_crc, calc_crc=self._calc_crc))
