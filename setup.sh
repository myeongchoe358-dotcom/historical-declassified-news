#!/bin/bash

# 快速启动脚本

echo "====================================="
echo "全球历史解密信息收集系统"
echo "====================================="

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3"
    exit 1
fi

echo "Python版本:"
python3 --version

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "
正在创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "
正在安装依赖..."
pip install -r requirements.txt

# 配置环境变量
if [ ! -f ".env" ]; then
    echo "
正在创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件并填入你的配置信息"
fi

# 初始化数据库
echo "
正在初始化数据库..."
python3 data_crawler.py

echo "
====================================="
echo "✅ 初始化完成！"
echo "====================================="
echo "
运行模式选择:"
echo "1. 测试模式: python3 scheduler.py test"
echo "2. 生产模式: python3 scheduler.py"
echo "
====================================="
