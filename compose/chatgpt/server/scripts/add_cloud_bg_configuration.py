# flake8: noqa
from peewee import fn

from services.system.configuration_service import ConfigurationService


class AddCloudBgRepoMatchList:
    repo_conf_data_attribute_key = "cloud_bg_repo_match_list"
    cloud_bg_api_url_attribute_key = "cloud_bg_api_url"

    @classmethod
    def run(cls):
        cls.insert_data()

    @classmethod
    def insert_data(cls):
        """添加云BG仓库，匹配列表配置"""
        repo_conf_data = {'deleted': False, 'belong_type': 'permission',
                          'attribute_key': cls.repo_conf_data_attribute_key,
                          'attribute_value': '["(git@|http:\\/\\/)(\\w+\\.)?code\\.sangfor\\.org[:|/]VT/aCMP.*"]', 'desc': "云BG仓库，匹配列表"}
        api_url_data = {'deleted': False, 'belong_type': 'permission',
                        'attribute_key': cls.cloud_bg_api_url_attribute_key,
                        'attribute_value': "http://200.200.24.219:3001/api/chat/editor", 'desc': "云BG ai 接口地址"}

        data = [repo_conf_data, api_url_data]

        for prompt_data in data:
            data = ConfigurationService.get_configuration(
                prompt_data['belong_type'], prompt_data['attribute_key'])
            if data:
                print(prompt_data['attribute_key'] + "配置已经存在")
            else:
                # 获取下一个可用的id
                max_id = ConfigurationService.dao.model.select(fn.MAX(ConfigurationService.dao.model.id)).scalar()
                next_id = max_id + 1 if max_id else 1
                prompt_data['id'] = next_id
                ConfigurationService.create(**prompt_data)
                print(prompt_data['attribute_key'] + "配置写入成功")
