#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugo文章Front Matter自动填充工具
自动为文章添加创建时间、作者和分类信息
"""

import os
import re
import datetime
from pathlib import Path
import subprocess
from typing import Optional, Tuple, List

# 配置信息
CONFIG = {
    "author": "Panda",
    "content_dirs": [ "content/posts"],
    "category_mapping": {
        "想法": "创意想法",
        "vpn": "VPN技术",
        "acm": "算法竞赛",
        "macos": "macOS",
        "server": "服务器",
        "工具": "工具使用",
        "ros2": "ROS2 技术文档"
    }
}

# ==================== 文件处理函数 ====================

def get_file_creation_time(file_path: Path) -> datetime.datetime:
    """获取文件的创建时间"""
    try:
        # 优先使用文件系统创建时间
        stat = file_path.stat()
        # 在macOS上使用st_birthtime，在其他系统上使用st_ctime
        if hasattr(stat, 'st_birthtime'):
            return datetime.datetime.fromtimestamp(stat.st_birthtime)
        else:
            return datetime.datetime.fromtimestamp(stat.st_ctime)
    except Exception:
        # 如果获取失败，使用当前时间
        return datetime.datetime.now()

def get_category_from_path(file_path: Path) -> str:
    """从文件路径推断分类"""
    # 获取文件的父目录名作为分类
    parent_dir = file_path.parent.name
    
    # 使用配置中的映射
    if parent_dir in CONFIG["category_mapping"]:
        return CONFIG["category_mapping"][parent_dir]
    
    # 如果没有映射，直接使用目录名
    return parent_dir

# ==================== Front Matter 处理函数 ====================

def parse_front_matter(content: str) -> Tuple[dict, str]:
    """解析Front Matter，返回元数据和内容"""
    # 匹配YAML Front Matter
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        yaml_content = match.group(1)
        markdown_content = match.group(2)
        
        # 改进的YAML解析，支持列表
        metadata = {}
        current_key = None
        current_list = []
        
        for line in yaml_content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是列表项
            if line.startswith('- ') and current_key:
                current_list.append(line[2:].strip())
                continue
            elif current_list:
                # 结束当前列表
                metadata[current_key] = current_list
                current_list = []
                current_key = None
            
            # 检查是否是键值对
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # 检查值是否为空（可能是列表的开始）
                if not value:
                    current_key = key
                    current_list = []
                else:
                    metadata[key] = value
        
        # 处理最后的列表
        if current_list:
            metadata[current_key] = current_list
        
        return metadata, markdown_content
    else:
        return {}, content

def generate_front_matter(metadata: dict, file_path: Path) -> str:
    """生成Front Matter"""
    # 获取文件创建时间
    creation_time = get_file_creation_time(file_path)
    
    # 只添加缺失的字段，已存在的字段保持不变
    if 'title' not in metadata:
        metadata['title'] = file_path.stem
    if 'date' not in metadata:
        metadata['date'] = creation_time.strftime('%Y-%m-%d %H:%M')
    if 'author' not in metadata:
        metadata['author'] = CONFIG["author"]
    if 'categories' not in metadata:
        metadata['categories'] = [get_category_from_path(file_path)]
    
    # 生成YAML格式的Front Matter
    yaml_lines = ['---']
    for key, value in metadata.items():
        if isinstance(value, list):
            yaml_lines.append(f'{key}:')
            for item in value:
                yaml_lines.append(f'  - {item}')
        else:
            yaml_lines.append(f'{key}: {value}')
    yaml_lines.append('---')
    
    return '\n'.join(yaml_lines)

def update_file_front_matter(file_path: Path) -> bool:
    """更新单个文件的Front Matter"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析现有Front Matter
        metadata, markdown_content = parse_front_matter(content)
        
        # 生成新的Front Matter
        new_front_matter = generate_front_matter(metadata, file_path)
        
        # 组合新内容
        new_content = f"{new_front_matter}\n{markdown_content}"
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ 已更新: {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ 更新失败 {file_path}: {e}")
        return False

# ==================== 主处理函数 ====================

def scan_and_update_files():
    """扫描并更新所有文件"""
    total_files = 0
    updated_files = 0
    
    for content_dir in CONFIG["content_dirs"]:
        dir_path = Path(content_dir)
        if not dir_path.exists():
            print(f"警告: 目录不存在 {content_dir}")
            continue
        
        # 扫描所有.md文件
        for md_file in dir_path.rglob("*.md"):
            total_files += 1
            if update_file_front_matter(md_file):
                updated_files += 1
    
    print(f"\n处理完成: {updated_files}/{total_files} 个文件已更新")

# ==================== 主程序入口 ====================

if __name__ == "__main__":
    print("Hugo Front Matter 自动填充工具")
    print("=" * 40)
    scan_and_update_files()
