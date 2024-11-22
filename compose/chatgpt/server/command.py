#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    服务初始化命令集

    :作者: 苏德利 16646
    :时间: 2023/3/14 14:35
    :修改者: 苏德利 16646
    :更新时间: 2023/3/14 14:35
"""

import click
from flask.cli import FlaskGroup
from app import create_app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    click.echo('===> chatGpt server')


@cli.command()
@click.option('--force/--unforce', default=False)
def initdb(force):
    """初始化数据库"""
    from db.help import initialize_db
    initialize_db(force)
    click.echo('数据库初始化成功')


@cli.command()
def dropdb():
    """删除所有表"""
    from db.help import drop_tables
    drop_tables()
    click.echo('数据库表删除成功')


@cli.command()
def cleardb():
    """清空数据"""
    from db.help import truncate_tables
    truncate_tables()
    click.echo('数据库清空成功')


@cli.command()
@click.option('--name', help='migration name')
def create_migration(name):
    """新建迁移文件"""
    from db.help import get_router, create_migration
    router = get_router()
    create_migration(router, name)


@cli.command()
@click.option('--name', help='migration name')
def migrate(name):
    """迁移数据库"""
    from db.help import get_router, migrate
    router = get_router()
    migrate(router, name)


@cli.command()
@click.option('--name', help='insert_advice_prompt')
def insert_advice_prompt(name):
    from scripts.add_advcie_prompt_configuration import AddAdvicePrompt
    AddAdvicePrompt.run()


@cli.command()
@click.option('--name', help='insert_cloud_bg_repo_match_list')
def insert_cloud_bg_repo_match_list(name):
    from scripts.add_cloud_bg_configuration import AddCloudBgRepoMatchList
    AddCloudBgRepoMatchList.run()


@cli.command()
@click.option('--name', help='insert_ut_config')
def insert_ut_config(name):
    from scripts.add_ut_config_configuration import AddUTConfig
    AddUTConfig.run()


@cli.command()
@click.option('--name', help='add_or_update_api_test_configuration')
def api_config(name):
    # python command.py api-config 把代码中的prompt模板更新到数据库中
    from scripts.add_or_update_api_test_configuration import ApiTestConfigurationHandler
    ApiTestConfigurationHandler.run()


@cli.command()
@click.option('--name', help='clear_all_prompt_template_cache')
def clear_prompt_cache(name):
    # python command.py clear-prompt-cache 缓存的prompt模板清空
    from scripts.add_or_update_api_test_configuration import ApiTestConfigurationHandler
    ApiTestConfigurationHandler.clear_all_action_strategy_prompt_template_cache()


if __name__ == "__main__":
    cli()
