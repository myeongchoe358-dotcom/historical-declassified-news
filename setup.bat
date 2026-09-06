@echo off
REM Windows启动脚本

echo ====================================
echo 全球历史解密信息收集系统
echo ====================================

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python
    exit /b 1
)

echo Python版本:
python --version

REM 创建虚拟环境
if not exist "venv" (
    echo.
    echo 正在创��虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo.
echo 正在安装依赖...
pip install -r requirements.txt

REM 配置环境变量
if not exist ".env" (
    echo.
    echo 正在创建 .env 文件...
    copy .env.example .env
    echo 请编辑 .env 文件并填入你的配置信息
)

REM 初始化数据库
echo.
echo 正在初始化数据库...
python data_crawler.py

echo.
echo ====================================
echo 初始化完成！
echo ====================================
echo.
echo 运行模式选择:
echo 1. 测试模式: python scheduler.py test
echo 2. 生产模式: python scheduler.py
echo.
echo ====================================
pause
