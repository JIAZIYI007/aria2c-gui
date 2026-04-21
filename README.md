# Aria2 GUI 下载器

一个基于 PyQt5 的 aria2c 图形界面，支持直接下载模式（非 RPC），实时显示进度和速度。

## 功能特点

- 手动选择 aria2c 可执行文件路径（自动保存）
- 自定义下载保存目录
- 实时显示下载进度条和速度
- 支持终止下载（断点续传）
- 下载完成后弹出提示并可直接打开保存目录

## 运行要求

- Python 3.6+
- PyQt5
- aria2c（需单独安装）

## 安装与使用

1. 安装 aria2c：[官网下载](https://aria2.github.io/)
2. 安装 Python 依赖：
   ```bash
   pip install PyQt5
