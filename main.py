import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QLabel, 
                             QListWidget, QProgressBar, QTextEdit, 
                             QFileDialog, QMessageBox, QGroupBox)
from PySide6.QtCore import QThread, Signal, Qt
from ncmdump import dump

class SimpleTheme:
    """简洁主题样式"""
    
    @staticmethod
    def get_style():
        return """
        /* 主窗口样式 */
        QMainWindow {
            background-color: #f8f9fa;
        }
        
        /* 分组框样式 */
        QGroupBox {
            font-weight: bold;
            font-size: 13px;
            color: #495057;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 8px;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: #495057;
            background-color: white;
        }
        
        /* 按钮样式 */
        QPushButton {
            background-color: #007bff;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 12px;
            border-radius: 6px;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #0056b3;
        }
        
        QPushButton:pressed {
            background-color: #004085;
        }
        
        QPushButton:disabled {
            background-color: #6c757d;
            color: #dee2e6;
        }
        
        /* 开始转换按钮 */
        QPushButton#convertButton {
            background-color: #28a745;
            font-size: 13px;
            padding: 12px 24px;
            min-width: 120px;
        }
        
        QPushButton#convertButton:hover {
            background-color: #1e7e34;
        }
        
        /* 清空按钮 */
        QPushButton#clearButton {
            background-color: #ffc107;
            color: #212529;
        }
        
        QPushButton#clearButton:hover {
            background-color: #e0a800;
        }
        
        /* 文件列表样式 */
        QListWidget {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 5px;
            font-size: 12px;
            selection-background-color: #e3f2fd;
        }
        
        QListWidget::item {
            padding: 6px;
            border-bottom: 1px solid #f8f9fa;
        }
        
        QListWidget::item:hover {
            background-color: #f8f9fa;
        }
        
        QListWidget::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        
        /* 进度条样式 */
        QProgressBar {
            border: 1px solid #dee2e6;
            border-radius: 6px;
            text-align: center;
            font-size: 11px;
            background-color: white;
            height: 22px;
        }
        
        QProgressBar::chunk {
            background-color: #28a745;
            border-radius: 5px;
        }
        
        /* 文本编辑器样式 */
        QTextEdit {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 8px;
            font-size: 11px;
            font-family: "Consolas", "Courier New", monospace;
        }
        
        /* 标签样式 */
        QLabel {
            color: #495057;
            font-size: 12px;
        }
        
        /* 状态标签样式 */
        QLabel#statusLabel {
            font-weight: bold;
            color: #28a745;
            padding: 6px 12px;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
        }
        
        /* 输出路径标签样式 */
        QLabel#outputLabel {
            color: #6c757d;
            font-style: italic;
            padding: 4px;
        }
        """

class ConversionWorker(QThread):
    """音乐文件转换工作线程"""
    progress_updated = Signal(int)
    file_converted = Signal(str, str)  # 原文件名, 转换状态
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, files, output_dir):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        
    def run(self):
        try:
            for i, file_path in enumerate(self.files):
                try:
                    # 获取输入文件的基本名称（不含扩展名）
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # 创建输出路径生成函数
                    def output_path_generator(input_path, meta):
                        # 根据元数据确定输出格式
                        format_ext = meta.get('format', 'mp3')
                        # 在指定的输出目录中生成完整的输出路径
                        output_filename = f"{base_name}.{format_ext}"
                        return os.path.join(self.output_dir, output_filename)
                    
                    # 使用ncmdump转换文件，传入路径生成函数
                    result = dump(file_path, output_path_generator, skip=False)
                    
                    if result and os.path.exists(result):
                        self.file_converted.emit(os.path.basename(file_path), f"成功 -> {os.path.basename(result)}")
                    else:
                        self.file_converted.emit(os.path.basename(file_path), "转换失败")
                        
                except Exception as e:
                    self.file_converted.emit(os.path.basename(file_path), f"错误: {str(e)}")
                
                # 更新进度
                progress = int((i + 1) / len(self.files) * 100)
                self.progress_updated.emit(progress)
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class NCMTransferGUI(QMainWindow):
    """网易云音乐文件转换器主界面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.files_to_convert = []
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("网易云音乐NCM文件转换器")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(700, 500)
        
        # 应用简洁主题
        self.setStyleSheet(SimpleTheme.get_style())
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel("网易云音乐NCM文件转换器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 文件选择按钮布局
        file_button_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("选择NCM文件")
        self.select_files_btn.clicked.connect(self.select_files)
        
        self.clear_files_btn = QPushButton("清空列表")
        self.clear_files_btn.setObjectName("clearButton")
        self.clear_files_btn.clicked.connect(self.clear_files)
        
        file_button_layout.addWidget(self.select_files_btn)
        file_button_layout.addWidget(self.clear_files_btn)
        file_button_layout.addStretch()
        
        file_layout.addLayout(file_button_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        file_layout.addWidget(self.file_list)
        
        main_layout.addWidget(file_group)
        
        # 输出目录选择
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout(output_group)
        
        self.output_label = QLabel("输出目录: 未选择")
        self.output_label.setObjectName("outputLabel")
        self.select_output_btn = QPushButton("选择输出目录")
        self.select_output_btn.clicked.connect(self.select_output_dir)
        
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.select_output_btn)
        
        main_layout.addWidget(output_group)
        
        # 转换控制
        control_layout = QHBoxLayout()
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setObjectName("convertButton")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)
        
        control_layout.addWidget(self.convert_btn)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        
        # 日志区域
        log_group = QGroupBox("转换日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        main_layout.addWidget(self.status_label)
        
        # 初始化输出目录
        self.output_dir = ""
        
    def select_files(self):
        """选择NCM文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "选择NCM文件", 
            "", 
            "NCM文件 (*.ncm);;所有文件 (*)"
        )
        
        if files:
            self.files_to_convert.extend(files)
            # 去重
            self.files_to_convert = list(set(self.files_to_convert))
            self.update_file_list()
            self.log_text.append(f"已添加 {len(files)} 个文件")
            
    def clear_files(self):
        """清空文件列表"""
        self.files_to_convert.clear()
        self.update_file_list()
        self.log_text.append("已清空文件列表")
        
    def update_file_list(self):
        """更新文件列表显示"""
        self.file_list.clear()
        for file_path in self.files_to_convert:
            self.file_list.addItem(os.path.basename(file_path))
        
        # 更新转换按钮状态
        self.update_convert_button()
        
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir = dir_path
            self.output_label.setText(f"输出目录: {dir_path}")
            self.update_convert_button()
            self.log_text.append(f"输出目录设置为: {dir_path}")
            
    def update_convert_button(self):
        """更新转换按钮状态"""
        self.convert_btn.setEnabled(
            len(self.files_to_convert) > 0 and self.output_dir != ""
        )
        
    def start_conversion(self):
        """开始转换"""
        if not self.files_to_convert or not self.output_dir:
            QMessageBox.warning(self, "警告", "请选择文件和输出目录")
            return
            
        # 禁用转换按钮
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("转换中...")
        self.log_text.append("开始转换...")
        
        # 创建并启动工作线程
        self.worker = ConversionWorker(self.files_to_convert, self.output_dir)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_converted.connect(self.on_file_converted)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.start()
        
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        
    def on_file_converted(self, filename, status):
        """处理单个文件转换完成"""
        self.log_text.append(f"{filename}: {status}")
        
    def on_conversion_finished(self):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.status_label.setText("转换完成")
        self.log_text.append("所有文件转换完成!")
        
        # 显示完成对话框
        msg = QMessageBox(self)
        msg.setWindowTitle("转换完成")
        msg.setText("所有文件转换完成！")
        msg.setInformativeText(f"转换后的文件保存在:\n{self.output_dir}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.addButton("打开目录", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        
        result = msg.exec()
        if result == 0:  # 打开目录按钮
            os.startfile(self.output_dir)
        
    def on_conversion_error(self, error_msg):
        """处理转换错误"""
        self.convert_btn.setEnabled(True)
        self.status_label.setText("转换出错")
        self.log_text.append(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", f"转换过程中出错: {error_msg}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("NCM Transfer")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("NCM Transfer")
    app.setApplicationDisplayName("网易云音乐NCM文件转换器")
    
    # 设置应用样式
    app.setStyle('Fusion')  # 使用现代样式
    
    # 创建主窗口
    window = NCMTransferGUI()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
