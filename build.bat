@echo off
echo 正在打包网易云音乐NCM转换器...
echo.

echo 第一步：使用uv运行PyInstaller...
uv run pyinstaller build.spec --clean --noconfirm

echo.
echo 打包完成！
echo 可执行文件位置: dist\NCM转换器.exe
echo.

pause
