# flake8: noqa
import json

from peewee import fn
from config import Config
from common.constant import ConfigurationConstant
from services.system.configuration_service import ConfigurationService


class AddUTConfig:

    @classmethod
    def run(cls):
        cls.insert_data()

    @classmethod
    def insert_data(cls):
        """添加ut配置到配置表，匹配列表配置"""
        ut_config = Config().ut
        sdk_config = ut_config.get("sdk", {})
        use_model = ut_config.get("use_model", "")
        model_data = ut_config.get("models", {}).get(use_model, {})

        data = list()
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_RESULT_FILE_SPC,
            attribute_value=ut_config.get("ut_result_file_spc"),
            desc="单测结果文件命名间隔符，用于根据文件名切割获取对应数据：文件名，方法命名，用例号",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_USE_MODEL,
            attribute_value=use_model,
            desc="当前使用的模型",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_LANGUAGE,
            attribute_value=json.dumps(ut_config.get("language", {})),
            desc="单测支持的语言配置",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_MAX_POINT,
            attribute_value=sdk_config.get("max_point"),
            desc="单测生成最大测试点设置",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_REQ_TIMEOUT,
            attribute_value=sdk_config.get("req_timeout"),
            desc="sdk请求模型超时时间",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_REQ_TIMES,
            attribute_value=sdk_config.get("req_times"),
            desc="sdk请求次数，用于重试判断",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_MAX_WORKERS,
            attribute_value=model_data.get("max_workers"),
            desc="当前模型的最大并发数控制",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_TOKEN_LENGTH,
            attribute_value=json.dumps(model_data.get("token_length", {})),
            desc="当前使用模型token配置",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_POINT_TEMPLATE,
            attribute_value=model_data.get("point_template"),
            desc="当前使用模型获取测试点prompt模板",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_CASE_TEMPLATE,
            attribute_value=model_data.get("case_template"),
            desc="当前使用模型获取测试用例prompt模板",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_PLUGIN_JETB_MIN_VERSION,
            attribute_value="1.0.1",
            desc="jetbrains 单测插件最小版本",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_PLUGIN_VSCODE_MIN_VERSION,
            attribute_value="1.0.1",
            desc="vscode 单测插件最小版本",
        ))
        data.append(dict(
            deleted=False,
            belong_type=ConfigurationConstant.UT_RULES,
            attribute_key=ConfigurationConstant.UT_OPEN_DEPT,
            attribute_value=1.0,
            desc="单测生成 灰度放开的部门",
        ))

        for prompt_data in data:
            value = ConfigurationService.get_configuration(
                prompt_data['belong_type'], prompt_data['attribute_key'])
            if value:
                print(prompt_data['attribute_key'] + "配置已经存在")
            else:
                ConfigurationService.create(**prompt_data)
                print(prompt_data['attribute_key'] + "配置写入成功")

        # UT_OPEN_DEPT 的 belong_type 统一改成 UT_RULES
        dept_result = ConfigurationService.dao.get_or_none(belong_type=ConfigurationConstant.PERMISSION_TYPE,
                                                           attribute_key=ConfigurationConstant.UT_OPEN_DEPT)
        if dept_result:
            ConfigurationService.update_by_id(dept_result.id, belong_type=ConfigurationConstant.UT_RULES)
            print("权限控制字段更新成功")
