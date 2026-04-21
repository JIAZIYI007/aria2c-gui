import sys
import re
import os
import shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QProcess, QTimer, QSettings, QStandardPaths

class Aria2DirectGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aria2 直接下载管理器")
        self.resize(900, 550)
        self.process = None
        self.current_download_file = ""  # 记录当前下载的文件名（用于提示）
        
        self.settings = QSettings("MyCompany", "Aria2GUI")
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # aria2c 路径选择
        path_layout = QHBoxLayout()
        self.aria2_path_label = QLabel("aria2c 路径: 未选择")
        self.aria2_path_label.setWordWrap(True)
        self.select_aria2_btn = QPushButton("选择 aria2c")
        self.select_aria2_btn.clicked.connect(self.select_aria2_path)
        path_layout.addWidget(self.aria2_path_label, 3)
        path_layout.addWidget(self.select_aria2_btn, 1)
        layout.addLayout(path_layout)

        # 下载 URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("请输入下载链接，例如 http://speedtest.tele2.net/10MB.zip")
        layout.addWidget(self.url_edit)

        # 保存目录选择
        save_layout = QHBoxLayout()
        self.path_label = QLabel("保存目录: 未选择（将保存到程序所在目录）")
        self.path_btn = QPushButton("选择目录")
        self.path_btn.clicked.connect(self.select_save_dir)
        self.open_dir_btn = QPushButton("打开保存目录")
        self.open_dir_btn.clicked.connect(self.open_save_directory)
        save_layout.addWidget(self.path_label, 3)
        save_layout.addWidget(self.path_btn, 1)
        save_layout.addWidget(self.open_dir_btn, 1)
        layout.addLayout(save_layout)

        # 下载按钮
        self.download_btn = QPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        # 进度条和速度
        self.progress_bar = QProgressBar()
        self.speed_label = QLabel("速度: --")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.speed_label)

        # 终止按钮
        self.stop_btn = QPushButton("终止下载")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_download)
        layout.addWidget(self.stop_btn)

        # 日志输出
        self.log = QTextEdit()
        self.log.setMaximumHeight(200)
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("aria2c 输出:"))
        layout.addWidget(self.log)

        # 状态栏
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

    def load_settings(self):
        saved_path = self.settings.value("aria2c_path", "")
        if saved_path and os.path.exists(saved_path):
            self.aria2_path_label.setText(f"aria2c 路径: {saved_path}")
            self.aria2_path_label.setToolTip(saved_path)
        else:
            auto_path = shutil.which("aria2c")
            if auto_path:
                self.aria2_path_label.setText(f"aria2c 路径: {auto_path}")
                self.aria2_path_label.setToolTip(auto_path)
                self.settings.setValue("aria2c_path", auto_path)

        # 加载上次使用的保存目录（可选）
        saved_dir = self.settings.value("save_dir", "")
        if saved_dir and os.path.isdir(saved_dir):
            self.path_label.setText(f"保存目录: {saved_dir}")
            self.path_label.setToolTip(saved_dir)

    def select_aria2_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 aria2c 可执行文件", "", "可执行文件 (*.exe);;所有文件 (*)"
        )
        if file_path:
            self.aria2_path_label.setText(f"aria2c 路径: {file_path}")
            self.aria2_path_label.setToolTip(file_path)
            self.settings.setValue("aria2c_path", file_path)
            self.status_label.setText(f"已选择 aria2c: {os.path.basename(file_path)}")

    def select_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择下载保存目录")
        if dir_path:
            self.path_label.setText(f"保存目录: {dir_path}")
            self.path_label.setToolTip(dir_path)
            self.settings.setValue("save_dir", dir_path)

    def open_save_directory(self):
        """打开当前选择的保存目录（如果未选择则打开程序所在目录）"""
        save_dir = self.get_save_directory()
        if os.path.exists(save_dir):
            os.startfile(save_dir)  # Windows
            # 对于 Linux/macOS 可以使用 QDesktopServices.openUrl(QUrl.fromLocalFile(save_dir))
        else:
            QMessageBox.warning(self, "目录不存在", f"目录不存在：{save_dir}")

    def get_save_directory(self):
        """获取当前有效的保存目录（如果用户未选择，则使用程序所在目录）"""
        tooltip = self.path_label.toolTip()
        if tooltip and os.path.isdir(tooltip):
            return tooltip
        # 默认使用脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))

    def get_aria2c_path(self):
        label_text = self.aria2_path_label.text()
        if label_text.startswith("aria2c 路径: "):
            path = label_text[len("aria2c 路径: "):].strip()
            if path and os.path.exists(path):
                return path
        auto = shutil.which("aria2c")
        if auto:
            return auto
        return None

    def start_download(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入下载链接")
            return

        if self.process and self.process.state() == QProcess.Running:
            self.stop_download()

        aria2_path = self.get_aria2c_path()
        if not aria2_path:
            QMessageBox.information(self, "提示", "请先选择 aria2c 可执行文件路径")
            self.select_aria2_path()
            aria2_path = self.get_aria2c_path()
            if not aria2_path:
                return

        # 确定保存目录
        save_dir = self.get_save_directory()
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)

        # 构建命令行参数
        # 注意：-d 参数必须放在 URL 之前，且路径用引号包裹（QProcess 会自动处理空格，无需手动加引号）
        args = ["--summary-interval=1", "--console-log-level=error", "-d", save_dir, url]

        # 可选：添加 --continue=true 支持断点续传
        # args.insert(0, "--continue=true")

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        # 不要设置工作目录，让 aria2c 使用 -d 指定的目录
        # self.process.setWorkingDirectory(...)  # 移除这行

        self.process.readyReadStandardError.connect(self.on_aria2_error)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.finished.connect(self.download_finished)

        self.process.start(aria2_path, args)
        if not self.process.waitForStarted(3000):
            error_msg = self.process.errorString()
            QMessageBox.critical(self, "启动失败",
                                 f"无法启动 aria2c:\n{error_msg}\n路径: {aria2_path}")
            self.process = None
            return

        # 从 URL 中提取文件名（用于最终提示）
        self.current_download_file = url.split('/')[-1].split('?')[0]
        if not self.current_download_file:
            self.current_download_file = "未知文件"

        self.status_label.setText(f"下载中... 保存到: {save_dir}")
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.speed_label.setText("速度: --")
        self.log.clear()

    def on_aria2_error(self):
        if not self.process:
            return
        err_data = self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        if err_data:
            print("aria2c stderr:", err_data)
            self.log.append(f"[错误] {err_data}")
            # 非致命错误不覆盖状态栏

    def handle_stdout(self):
        if not self.process:
            return
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.log.insertPlainText(data)
        scrollbar = self.log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        lines = data.splitlines()
        for line in reversed(lines):
            if line.startswith("[#") and "%" in line:
                self.parse_progress(line)
                break

    def parse_progress(self, line):
        percent_match = re.search(r'\((\d+)%\)', line)
        if percent_match:
            self.progress_bar.setValue(int(percent_match.group(1)))
        speed_match = re.search(r'DL:([\d\.]+)([KM]?i?B)', line, re.IGNORECASE)
        if speed_match:
            val = float(speed_match.group(1))
            unit = speed_match.group(2).upper()
            if unit.startswith("K"):
                speed_text = f"{val:.1f} KB/s"
            elif unit.startswith("M"):
                speed_text = f"{val:.1f} MB/s"
            else:
                speed_text = f"{val:.0f} B/s"
            self.speed_label.setText(f"速度: {speed_text}")

    def stop_download(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(2000):
                self.process.kill()
        self.download_finished()

    def download_finished(self):
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        save_dir = self.get_save_directory()
        if self.process and self.process.exitCode() == 0:
            # 下载成功，尝试找到最终文件（可能带有 .aria2 临时文件，但主文件已存在）
            expected_file = os.path.join(save_dir, self.current_download_file)
            if os.path.exists(expected_file):
                file_size = os.path.getsize(expected_file) / (1024*1024)
                self.status_label.setText(f"下载完成！文件已保存到: {expected_file} ({file_size:.1f} MB)")
                QMessageBox.information(self, "下载完成", 
                                        f"文件已成功下载到：\n{expected_file}\n\n大小：{file_size:.1f} MB")
            else:
                # 可能文件名不同，让用户手动查看
                self.status_label.setText(f"下载完成！文件保存在: {save_dir}")
                QMessageBox.information(self, "下载完成", 
                                        f"下载已完成，文件保存在目录：\n{save_dir}\n\n请点击「打开保存目录」查看。")
        else:
            self.status_label.setText("下载已终止或出错")
        self.process = None

    def closeEvent(self, event):
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            self.process.waitForFinished(2000)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Aria2DirectGUI()
    win.show()
    sys.exit(app.exec_())