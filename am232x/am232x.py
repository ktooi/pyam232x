# -*- coding: utf-8 -*-
import time
import smbus
from logging import getLogger
from .exceptions import AM232xError, ReceiveAM232xDataError, AM232xCrcCheckError


logger = getLogger(__name__)
usleep = lambda x: time.sleep(x/1000000.0)


class AM232x(object):
    """ AM2321/AM2322 に対応する Python モジュールです。

    センサーから気温及び湿度を取得します。また、取得した気温及び湿度から不快指数を計算することもできます。

    Examples:

        次のようにシンプルに使うことができます。

        Simple usage is as follows.

        >>> from am232x import AM232x
        >>>
        >>> am232x = AM232x(name="am2322")
        >>>
        >>> am232x.humidity
        >>> am232x.temperature
        >>> am232x.discomfort

        次のように、センサーとの通信のタイミングを細かく制御することもできます。

        The timing of communication with the sensor can also be finely controlled, as shown below. 

        >>> from am232x import AM232x
        >>>
        >>> am232x = AM232x(name="am2322", wakeup=False)
        >>>
        >>> am232x.wakeup()
        >>> am232x.set_write_mode()
        >>> am232x.measure()
        >>> am232x.read()
        >>>
        >>> am232x.humidity
        >>> am232x.temperature
        >>> am232x.discomfort
    """

    # AM2321/AM2322 の I2C アドレス。
    # I2C address of AM2321/AM2322.
    chip_addr = 0x5c

    # define wait micro sec.
    wait_wakeup = 800
    wait_writemode = 1500
    wait_readmode = 30
    wait_refresh = 2000000

    def __init__(self, name="am232x", bus=1, wakeup=True, retry_wait=20000, retry_num=10):
        self._name = name
        self._i2c = smbus.SMBus(bus)
        self._bus = bus
        self._retry_wait = retry_wait
        self._retry_num = retry_num
        self._wakeup = False
        self._write_mode = False
        self._measured = False
        self._read_time = 0
        if wakeup:
            self.wakeup()

    def _func_i2c_retry(self, func, args, retry_wait=None, retry_num=None):
        chip_addr = self.chip_addr
        if retry_wait is None:
            retry_wait = self._retry_wait
        if retry_num is None:
            retry_num = self._retry_num
        cnt = 0
        while True:
            try:
                return func(chip_addr, *args)
            except IOError as e:
                if cnt < retry_num:
                    usleep(retry_wait)
                    cnt += 1
                    logger.debug(("{name} : Execute the \"{func}\" was failed. retry count: {cnt}/{limit}: Exception: {exception}"
                                  .format(name=self._name, func=func.__name__, cnt=cnt, limit=retry_num, exception=e)))
                else:
                    raise e

    def _write_byte_data(self, register, data):
        i2c = self._i2c
        args = (register, data)
        self._func_i2c_retry(func=i2c.write_byte_data, args=args)

    def _write_i2c_block_data(self, register, data_list):
        i2c = self._i2c
        args = (register, data_list)
        self._func_i2c_retry(func=i2c.write_i2c_block_data, args=args)

    def _read_i2c_block_data(self, register, length):
        i2c = self._i2c
        args = (register, length)
        return self._func_i2c_retry(func=i2c.read_i2c_block_data, args=args, retry_wait=200000)

    def wakeup(self):
        if self._wakeup:
            return
        i2c = self._i2c
        chip_addr = self.chip_addr
        cur_time = time.time()

        try:
            i2c.write_byte_data(chip_addr, 0x00, 0x00)
        except:
            pass  # wakeup は必ず通信が失敗する。これは AM2321/2322 の仕様。
        self._wakeup = True
        usleep(self.wait_wakeup)

    def set_write_mode(self):
        self._write_byte_data(0x00, 0x00)
        self._write_mode = True
        usleep(self.wait_writemode)

    def measure(self):
        self.wakeup()
        if not self._write_mode:
            self.set_write_mode()
        self._write_i2c_block_data(0x03, [0x00, 0x04])
        self._measured = True
        usleep(self.wait_readmode)
        if hasattr(self, "_raw_data"):
            # "_raw_data" を削除し、 self._calc() 実行時に再度 self.read() が実行されるようにする。
            delattr(self, "_raw_data")
        self._del_properties()

    def check_err(self):
        raw = self._raw_data
        code = raw[2]
        if code >= 0x80:
            raise ReceiveAM232xDataError(error_code=code, chip_name=self._name)

    def check_crc(self):
        raw = self._raw_data
        rcv_crcsum = raw[7] << 8 | raw[6]
        clc_crcsum = 0xffff

        for i in range(6):
            clc_crcsum ^= raw[i]
            for j in range(8):
                if (clc_crcsum & 1):
                    clc_crcsum = clc_crcsum >> 1
                    clc_crcsum ^= 0xa001
                else:
                    clc_crcsum = clc_crcsum >> 1

        if rcv_crcsum != clc_crcsum:
            raise AM232xCrcCheckError(recv_crc=rcv_crcsum, calc_crc=clc_crcsum, chip_name=self._name)

    def read(self, check_err=True, check_crc=True, retry_num=10, retry_wait=2000000):
        cnt = 0
        while True:
            if not self._measured:
                self.measure()
            if not hasattr(self, "_raw_data"):
                self._raw_data = self._read_i2c_block_data(0x00, 8)
                self._del_properties()
                self._wakeup = False
                self._write_mode = False
                self._read_time = time.time()
                try:
                    if check_err:
                        self.check_err()
                    if check_crc:
                        self.check_crc()
                except AM232xError as e:
                    if cnt < retry_num:
                        self._measured = False
                        cnt += 1
                        logger.debug(("{name} : AM232x error was occurred. retry count: {cnt}/{limit}, Exception: {exception}"
                                      .format(name=self._name, cnt=cnt, limit=retry_num, exception=e)))
                        usleep(retry_wait)
                        continue
                    else:
                        raise e

            return self._raw_data

    def _calc(self, high_idx, low_idx):
        if not hasattr(self, "_raw_data"):
            self.read()
        raw = self._raw_data
        return (raw[high_idx] << 8 | raw[low_idx]) / 10.0

    def _del_properties(self):
        properties = ["_humidity", "_temperature", "_discomfort"]
        for p in properties:
            if hasattr(self, p):
                delattr(self, p)

    @property
    def humidity(self):
        if not hasattr(self, "_humidity"):
            self._humidity = self._calc(2, 3)
        return self._humidity

    @property
    def temperature(self):
        if not hasattr(self, "_temperature"):
            self._temperature = self._calc(4, 5)
        return self._temperature

    @property
    def discomfort(self):
        if not hasattr(self, "_discomfort"):
            hum = self.humidity
            temp = self.temperature
            self._discomfort = 0.81 * temp + 0.01 * hum * (0.99 * temp - 14.3) + 46.3
        return self._discomfort
