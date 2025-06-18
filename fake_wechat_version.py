import os
import sys
import winreg  # 新增注册表模块
import subprocess  # 新增
import time  # 新增
import json  # 新增
from typing import Union
from pymem import Pymem
from pymem.exception import MemoryReadError

current_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
version = os.path.join(current_directory, 'config.json')
name = 'WeChat.exe'

def scan_for_offsets(wx: Pymem, base_address: int, hex_value: int, total_size: int = 0x10000000,
                     chunk_size: int = 0x1000000) -> list:
    """
    分块扫描内存以找到指定十六进制值的偏移地址。

    参数:
        wx (Pymem): 用于与进程内存交互的 Pymem 实例。
        base_address (int): 模块的基地址。
        hex_value (int): 要扫描的目标十六进制值。
        total_size (int, 可选): 总的扫描范围大小，默认为 0x10000000 (256MB)。
        chunk_size (int, 可选): 每次扫描的块大小，默认为 0x1000000 (16MB)。

    返回:
        list: 找到的偏移地址列表。
    """
    offsets = []
    hex_bytes = hex_value.to_bytes(4, byteorder="little")
    overlap_size = len(hex_bytes) - 1
    previous_chunk_tail = b""

    for chunk_start in range(0, total_size, chunk_size):
        current_address = base_address + chunk_start
        try:
            current_chunk_size = min(chunk_size, total_size - chunk_start)
            memory = wx.read_bytes(current_address, current_chunk_size)
        except MemoryReadError:
            continue

        memory = previous_chunk_tail + memory
        for i in range(len(memory) - len(hex_bytes) + 1):
            if memory[i:i + len(hex_bytes)] == hex_bytes:
                offsets.append(chunk_start + i - len(previous_chunk_tail))

        previous_chunk_tail = memory[-overlap_size:]
        print(f"{chunk_start:08x} - {current_address:08x}...")

    return offsets


def fake_version(wx: Pymem, current_version: str, target_version: str):
    """
    修改 WeChatWin.dll 模块中特定内存地址的值以伪装目标版本。
    
    参数:
        wx (Pymem): 用于与进程内存交互的 Pymem 库实例。
        current_version (str): 当前版本对应的十六进制值（如"63080021"）
        target_version (str): 要伪装的版本字符串（如"3.9.12.51"）

    异常:
        Exception: 如果内存地址中的当前值与预期的默认值不匹配，
                   表示版本不匹配，将引发异常。

    注意:
        - 函数假定 WeChatWin.dll 模块已加载到进程内存中。
        - `convert_version_to_hex` 函数用于将版本字符串转换为十六进制表示。
        - 内存地址的默认值假定为 `0x63080021`。

    示例:
        wx = Pymem("WeChat.exe")
        fake_version(wx, "3.9.6.33", "3.9.12.51")
    """
    dll_base = 0
    print("开始寻找WeChatWin.dll")
    for m in list(wx.list_modules()):
        path = m.filename
        if path.endswith("WeChatWin.dll"):
            dll_base = m.lpBaseOfDll
            break

    # 动态扫描偏移地址
    print("动态扫描偏移地址")
    default_hex = int(current_version, 16)  # 直接解析十六进制字符串
    offsets = scan_for_offsets(wx, dll_base, default_hex)

    if not offsets:
        raise Exception("未找到目标偏移地址，请确认版本是否正确")
    print(f"找到偏移地址: {[hex(offset) for offset in offsets]}")

    target_hex = int(convert_version_to_hex(target_version), 16)

    for offset in offsets:
        addr = dll_base + offset
        v = wx.read_uint(addr)
        if v == target_hex:
            continue
        elif v != default_hex:
            raise Exception("传入的当前版本不匹配")

        wx.write_uint(addr, target_hex)

    print(f"微信版本伪装从 {current_version} 到 {target_version} 完成")


def convert_version_to_hex(version: str) -> str:
    """
    将版本号转换为特定格式的值。
    例如：'3.9.10.27' -> '63090c33'

    :param version: 版本号字符串，格式为 'x.y.z.w'
    :return: 转换后的值字符串
    """
    parts = version.split(".")
    value = "6" + "".join(
        f"{int(part):x}".zfill(1 if i == 0 else 2) for i, part in enumerate(parts)
    )
    return value


def read_json_file(file_path: str) -> Union[dict, None]:
    """
    读取 JSON 文件并返回解析后的数据

    Args:
        file_path: JSON 文件的路径

    Returns:
        解析后的 JSON 数据（字典格式），如果读取失败则返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
    except Exception as e:
        print(f"读取 JSON 文件时发生错误: {e}")
    return None


if __name__ == "__main__":
    args = sys.argv[1:]
    current = None
    target = None

    for arg in args:
        if arg.startswith("c="):
            current = arg.split("=")[1]
        elif arg.startswith("t="):
            target = arg.split("=")[1]

    current_hex = convert_version_to_hex(current) if current else None
    install_path = None  # 新增安装路径变量

    if not current_hex:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Tencent\WeChat")
            value, regtype = winreg.QueryValueEx(key, "Version")
            current_hex = f"{value:08x}"
            # 读取安装路径
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"读取注册表失败: {e}")
            sys.exit(1)

    if not target:
        try:
            target = read_json_file("config.json")["version"]
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            sys.exit(1)

    if not current_hex or not target:
        print("请提供参数:\n\tc: 当前版本\n\tt:目标版本\n例如：\n\tpython fake_wechat_version.py c=3.9.6.33 t=3.9.12.51")
        sys.exit(1)

    # 新增启动微信逻辑
    if install_path:
        wechat_exe = os.path.join(install_path, name)
        if os.path.exists(wechat_exe):
            num = 10
            print(f"启动微信进程: {wechat_exe}")
            subprocess.Popen(wechat_exe)
            # 新增进程检测逻辑
            while True:
                try:
                    if num <= 0:
                        print("微信进程启动失败")
                        sys.exit(1)
                    output = subprocess.check_output(
                        ['tasklist', '/FI', f'IMAGENAME eq {name}'],
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    print('检查微信进程...')
                    if name in output:
                        print('微信进程已启动')
                        break
                except:
                    pass
                time.sleep(0.5)
                num -= 0.5
        else:
            print(f"警告: {name} 未找到于 {wechat_exe}")

    try:
        print("读取微信程序内存...")
        pm = Pymem(name)
        print("微信程序已读取，开始伪装版本")
        fake_version(pm, current_hex, target)
    except Exception as e:
        print(f"{e}\n请确认输入的版本号正确，并确认微信程序已经打开！")
        #  pyinstaller --onefile .\fake_wechat_version.py
