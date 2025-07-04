# Makefile for hugo-PaperMod 项目

# 启动本地预览
serve:
	hugo server --bind 0.0.0.0 --port 1313

# 自动批量填充/更新所有文章的日期（强制覆盖）
update-dates:
	python3 scripts/update_post_dates.py --force

# 只预览将要更新的日期，不实际写入
dryrun-dates:
	python3 scripts/update_post_dates.py --dry-run

# 生成静态站点
build:
	hugo

# 清理 public 目录
clean:
	rm -rf public

.PHONY: serve update-dates dryrun-dates build clean