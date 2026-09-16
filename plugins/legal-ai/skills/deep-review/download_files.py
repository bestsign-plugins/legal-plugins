#!/usr/bin/env python3
"""MCP 合同深度审查文件下载脚本（替代 SKILL.md 内联 bash 下载逻辑）。

用法:
    python3 download_files.py <输出目录> <url1> [url2 ...]

入参 URL 必须是 `acquireDownloadTickets` 一次返回的全套直下地址（深度审查为 original + report 两份）：
凭证已编在 URL 里，脚本不再发送任何 Authorization 头（不依赖宿主客户端的 Token 缓存）。

行为:
- 从 Content-Disposition 响应头解析服务端文件名（支持 filename*=UTF-8'' 与 filename="..." 两种格式）
- 目标文件已存在时自动追加序号后缀（如 xxx_1.docx），避免覆盖
- 多个 URL 并行下载，完成后逐行打印每个文件的最终保存路径
- 下载失败时向 stderr 输出具体原因并返回非零退出码
"""

import concurrent.futures
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def parse_filename(headers):
    """从 Content-Disposition 响应头解析文件名，解析失败返回 None。"""
    disposition = headers.get("Content-Disposition", "")
    match = re.search(r"filename\*=UTF-8''([^;]+)", disposition, re.IGNORECASE)
    if match:
        return urllib.parse.unquote(match.group(1))
    match = re.search(r'filename="([^"]*)"', disposition, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def unique_path(directory, filename):
    """目标文件已存在时追加序号后缀，返回不冲突的保存路径。"""
    filepath = directory / filename
    if not filepath.exists():
        return filepath
    counter = 1
    while (directory / f"{filepath.stem}_{counter}{filepath.suffix}").exists():
        counter += 1
    return directory / f"{filepath.stem}_{counter}{filepath.suffix}"


def download_file(url, directory):
    """下载单个文件，返回最终保存路径；失败抛出异常。"""
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=120) as response:
        filename = parse_filename(response.headers)
        if not filename:
            filename = "download_" + str(int(time.time()))
        filepath = unique_path(directory, filename)
        filepath.write_bytes(response.read())
        return str(filepath)


def main():
    if len(sys.argv) < 3:
        print("用法: python3 download_files.py <输出目录> <url1> [url2 ...]", file=sys.stderr)
        return 2

    directory = Path(sys.argv[1])
    urls = sys.argv[2:]
    directory.mkdir(parents=True, exist_ok=True)

    failed = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
        futures = {executor.submit(download_file, url, directory): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                print(future.result())
            except urllib.error.HTTPError as exc:
                failed = True
                if exc.code in (401, 403):
                    print("下载失败（HTTP " + str(exc.code) + " 票据无效或已被使用，重新调用 acquireDownloadTickets 获取全套新 URL 后重试）: " + url, file=sys.stderr)
                elif exc.code == 404:
                    print("下载失败（404 文件不存在，审查报告可能未生成）: " + url, file=sys.stderr)
                else:
                    print("下载失败（HTTP " + str(exc.code) + "）: " + url, file=sys.stderr)
            except Exception as exc:
                failed = True
                print("下载失败: " + url + " -> " + str(exc), file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
