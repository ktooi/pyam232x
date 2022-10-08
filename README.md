# pyam232x

[![Version](https://badge.fury.io/py/pyam232x.svg)](https://pypi.org/project/pyam232x/) [![Downloads](https://static.pepy.tech/personalized-badge/pyam232x?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/pyam232x) [![CodeQL](https://github.com/ktooi/pyam232x/workflows/CodeQL/badge.svg)](https://github.com/ktooi/pyam232x/actions?query=workflow%3ACodeQL+branch%3Amain) [![doctest](https://github.com/ktooi/pyam232x/workflows/doctest/badge.svg)](https://github.com/ktooi/pyam232x/actions?query=workflow%3Adoctest+branch%3Amain) [![pep8](https://github.com/ktooi/pyam232x/workflows/pep8/badge.svg)](https://github.com/ktooi/pyam232x/actions?query=workflow%3Apep8+branch%3Amain)

pyam232x は、 AM2321/AM2322 という温湿度センサーを制御する為のコマンドと API 一式です。

## Overview

このモジュールは、 AM2321/AM2322 から値を読み取って画面に出力するコマンドと、 AM2321/AM2322 を制御する為の API を提供します。

## Getting Started

### Prerequisites

本モジュールは AM2322 を実装済みの下記環境で動作確認を行っています。

*   Raspberry Pi 4 Model B (4GB)
*   OS:

    ```
    $ lsb_release -a
    No LSB modules are available.
    Distributor ID: Raspbian
    Description:    Raspbian GNU/Linux 10 (buster)
    Release:        10
    Codename:       buster
    ```
*   Python: 2.7.16, 3.7.3

### Installing

1.  pyam232x をインストールします。

    ```
    pip install pyam232x
    ```

以上。

### Usage

*   気温を取得する。

    ```
    $ am232x temperature
    17.9
    ```
*   湿度を取得する。

    ```
    $ am232x humidity
    35.1
    ```
*   不快指数を取得する。

    ```
    $ am232x discomfort
    66.282484
    ```
*   JSON 形式で気温、湿度、不快指数を取得する。

    ```
    $ am232x json
    {"discomfort": 66.282484, "temperature": 21.6, "humidity": 35.1}
    ```

## Configuration



## Authors

*   **Kodai Tooi** [GitHub](https://github.com/ktooi), [Qiita](https://qiita.com/ktooi)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
