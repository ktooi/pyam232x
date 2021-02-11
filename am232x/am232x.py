import time
import smbus
from logging import getLogger


logger = getLogger(__name__)
usleep = lambda x: time.sleep(x/1000000.0)


class AM232x(object):

    chip_addr = 0x5c

    # define wait micro sec.
    wait_wakeup = 800
    wait_writemode = 1500
    wait_readmode = 30
    wait_refresh = 2000000

    def __init__(self, name="am2321", bus=1, wakeup=True, retry_wait=1000, retry_num=10):
        self._i2c = smbus.SMBus(bus)
        self._bus = bus
        self._retry_wait = retry_wait
        self._retry_num = retry_num
        self._write_mode = False
        self._measured = False
        if wakeup:
            self.wakeup()

    def _write_retry(self, func, register, data):
        chip_addr = self.chip_addr
        cnt = 0
        while True:
            try:
                func(chip_addr, register, data)
                break
            except IOError as e:
                if cnt < self._retry_num:
                    usleep(self._retry_wait)
                    cnt += 1
                else:
                    raise e

    def _write_byte_data(self, register, data):
        i2c = self._i2c
        self._write_retry(i2c.write_byte_data, register, data)

    def _write_i2c_block_data(self, register, data_list):
        i2c = self._i2c
        self._write_retry(i2c.write_i2c_block_data, register, data_list)

    def _read_i2c_block_data(self, register, length):
        i2c = self._i2c
        chip_addr = self.chip_addr
        return i2c.read_i2c_block_data(chip_addr, register, length)

    def wakeup(self):
        self._write_byte_data(0x00, 0x00)
        usleep(self.wait_wakeup)

    def set_write_mode(self):
        self._write_byte_data(0x00, 0x00)
        self._write_mode = True
        usleep(self.wait_writemode)

    def measure(self):
        if not self._write_mode:
            self.set_write_mode()
        self._write_i2c_block_data(0x03, [0x00, 0x04])
        self._measured = True
        usleep(self.wait_readmode)

    def check_err(self):
        raw = self._raw
        code = raw[2]
        if code >= 0x80:
            raise ReceiveAM232xDataError(error_code=code, chip_name=self._name)

    def check_crc(self):
        raw = self._raw
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

    def read(self, check_err=True, check_crc=True):
        if not self._measured:
            self.measure()
        self._raw = self._read_i2c_block_data(0x00, 8)
        if check_err:
            self.check_err()
        if check_crc:
            self.check_crc()

    def _calc(self, high_idx, low_idx):
        if not hasattr(self, "_raw"):
            self.read()
        raw = self._raw
        return (raw[high_idx] << 8 | raw[low_idx]) / 10.0

    @property
    def humidity(self):
        return self._calc(2, 3)

    @property
    def temperature(self):
        return self._calc(4, 5)

    @property
    def discomfort(self):
        if not hasattr(self, "_discomfort"):
            hum = self.humidity
            temp = self.temperature
            self._discomfort = 0.81 * temp + 0.01 * hum * (0.99 * temp - 14.3) + 46.3
        return self._discomfort


def main():
    am232x = AM232x()
    print(am232x.temperature)
    print(am232x.humidity)
    print(am232x.discomfort)

if __name__ == '__main__':
    main()