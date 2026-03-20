#!/bin/bash
# 每周更新 AI快报网站

cd /Users/qwerty/.openclaw/workspace-planner/ai-flash-news

# 生成最新内容
python3 generate.py

# Git 提交并推送
git add .
git diff --quiet && git diff --staged --quiet || {
    git commit -m "Update: $(date '+%Y-%m-%d %H:%M')"
    git push origin main
}

echo "更新完成: $(date)"