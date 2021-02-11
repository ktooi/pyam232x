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
        """ AM2321/AM2322 との I2C 通信を制御するメソッドです。

        このセンサーは頻繁に I2C 通信に失敗し IOError が送出されるので、 I2C 通信をリトライさせます。

        A読み込み
            func(func): I2C 通信を行う関数。
            args(tuple): func に渡す引数一式。
            retry_wait(int): リトライ時の待機時間。マイクロ秒で指定する。指定がない場合は、インスタンス初期化時の retry_wait が利用される。
            retry_num(int): 最大リトライ回数。指定がない場合は、インスタンス初期化時の retry_cnt が利用される。

        Raises:
            IOError: 最大リトライ回数に達してなお IOError が raise される場合に、最後に送出された IOError をそのまま呼び出し元に送出する。
        """
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
        """ AM2321/AM2322 に1バイト書き込みを行うメソッドです。

        Args:
            register(int): 書き込みを行うアドレス。
            data(int): 書き込みを行うデータ(1バイト)。
        """
        i2c = self._i2c
        args = (register, data)
        self._func_i2c_retry(func=i2c.write_byte_data, args=args)

    def _write_i2c_block_data(self, register, data_list):
        """ AM2321/AM2322 に複数バイト書き込みを行うメソッドです。

        Args:
            register(int): 書き込みを行うアドレス。
            data_list(list): 書き込みを行うデータ(1バイト)のリスト。
        """
        i2c = self._i2c
        args = (register, data_list)
        self._func_i2c_retry(func=i2c.write_i2c_block_data, args=args)

    def _read_i2c_block_data(self, register, length):
        """ AM2321/AM2322 からデータを読み出すメソッドです。

        Args:
            register(int): 読み込みを行うアドレス。
            length(int): 読み込むデータの長さ(バイト数)。

        Returns:
            list: 読み込んだデータ(バイト毎)のリスト。
        """
        i2c = self._i2c
        args = (register, length)
        return self._func_i2c_retry(func=i2c.read_i2c_block_data, args=args, retry_wait=200000)

    def wakeup(self):
        """ スリープ状態にある AM2321/AM2322 を動作させるシグナルを送出するメソッドです。"""
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
        """ AM2321/AM2322 を書き込みモードにするメソッドです。"""
        self._write_byte_data(0x00, 0x00)
        self._write_mode = True
        usleep(self.wait_writemode)

    def measure(self):
        """ AM2321/AM2322 に、データを計測する命令を送信するメソッドです。 """
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
        """ AM2321/AM2322 から受信したデータに、エラーコードが含まれていたら例外を送出するメソッドです。

        読み込んだデータに対してチェックを行うため、あらかじめ read() メソッドを実行しておく必要があります。
        (但し、 read() メソッド実行時に check_err フラグを明確に False に設定していない場合は、
        read() メソッド内でこのメソッドが呼び出されます。このため、通常はこのメソッドを個別に呼び出す必要はありません。)

        Raises:
            ReceiveAM232xDataError: 受信したデータにエラーコードが含まれていた場合に送出される Exception.
        """
        raw = self._raw_data
        code = raw[2]
        if code >= 0x80:
            raise ReceiveAM232xDataError(error_code=code, chip_name=self._name)

    def check_crc(self):
        """ AM2321/AM2322 から受信した CRC と、受信したデータを計算して得られた CRC に相違があった場合に例外を送出するメソッドです。

        読み込んだデータに対してチェックを行うため、あらかじめ read() メソッドを実行しておく必要があります。
        (但し、 read() メソッド実行時に check_crc フラグを明確に False に設定していない場合は、
        read() メソッド内でこのメソッドが呼び出されます。このため、通常はこのメソッドを個別に呼び出す必要はありません。)

        Raises:
            AM232xCrcCheckError: 受信した CRC と、受信したデータを計算して得られた CRC に相違があった場合に送出される Exception.
        """
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
        """ AM2321/AM2322 から計測したデータを読み出すメソッドです。

        Args:
            check_err(bool): check_err() メソッドを呼び出すか否か。デフォルトは True.
            check_crc(bool): check_crc() メソッドを呼び出すか否か。デフォルトは True.
            retry_num(int): 読み出し時に AM232xError を基底クラスにする例外が送出された場合に、最大でリトライする回数。
            retry_wait(int): 読み出し時に AM232xError を基底クラスにする例外が送出された場合に、リトライするまでの待機時間(マイクロ秒)。

        Raises:
            ReceiveAM232xDataError: 受信したデータにエラーコードが含まれていた場合に送出される Exception.
            AM232xCrcCheckError: 受信した CRC と、受信したデータを計算して得られた CRC に相違があった場合に送出される Exception.
        """
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
                        if isinstance(e, ReceiveAM232xDataError):
                            # 計測データが不正であるため、再計測させる。
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
        """ AM2321/AM2322 から受信したデータを計算し、必要な情報を取得する為のメソッドです。

        Args:
            high_idx(int): 上位バイトとして利用するデータのインデックス番号。
            low_idx(int): 下位バイトとして利用するデータのインデックス番号。

        Returns:
            float: 計算結果を戻します。
        """
        if not hasattr(self, "_raw_data"):
            self.read()
        raw = self._raw_data
        return (raw[high_idx] << 8 | raw[low_idx]) / 10.0

    def _del_properties(self):
        """ キャッシュした気温、湿度、不快指数を削除するメソッドです。

        AM2321/AM2322 で再計測した場合などに、データを更新する為にこのメソッドを呼び出します。
        通常は必要なタイミングで必要なメソッドから呼び出されるので、このメソッドを手動で呼び出す必要はないでしょう。
        """
        properties = ["_humidity", "_temperature", "_discomfort"]
        for p in properties:
            if hasattr(self, p):
                delattr(self, p)

    @property
    def humidity(self):
        """ 湿度を取得します。単位は%です。 """
        if not hasattr(self, "_humidity"):
            self._humidity = self._calc(2, 3)
        return self._humidity

    @property
    def temperature(self):
        """ 気温を取得します。単位は℃です。 """
        if not hasattr(self, "_temperature"):
            self._temperature = self._calc(4, 5)
        return self._temperature

    @property
    def discomfort(self):
        """ 不快指数を取得します。指数なので単位はありません。 """
        if not hasattr(self, "_discomfort"):
            hum = self.humidity
            temp = self.temperature
            self._discomfort = 0.81 * temp + 0.01 * hum * (0.99 * temp - 14.3) + 46.3
        return self._discomfort
