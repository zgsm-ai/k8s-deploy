#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/25 14:14
查找e2e自动化相关上下文
"""
import json
import logging
from typing import Dict, Optional, List, Callable, Union

from bot.bot_util import compute_tokens
from services.ai_e2e.manual_case import ManualCase
from third_platform.knowledge_seeker.e2e_case_manager import E2ECaseKsManager

logger = logging.getLogger(__name__)


class CaseContextAssembly:
    # 所有分段
    ALL_SECTION = ["前置条件", "步骤", "期望结果", "后置条件"]
    # 属于步骤的分段，需要查找关联内容
    STEP_SECTION = ["前置条件", "步骤", "后置条件"]

    def __init__(self, manual_case: ManualCase, task_id: int):
        self.task_id = task_id
        # 手工用例
        self.manual_case = manual_case
        # 关键字集合
        self.associated_keyword_dict = dict()
        # 关联步骤集合
        self.associated_steps_dict = dict()
        self.associated_cli_dict = dict()
        self.associated_api_dict = dict()

    def context_assembly(self, callback: Callable = None):
        # 转换数据结构
        case_associated_structure = self.manual_case.convert_to_structure()
        case_associated_structure = self.get_case_associated(case_associated_structure)
        # 生成prompt的参数
        test_case = self.manual_case.format_markdown()

        associated_keywords = self.associated_keyword_dict
        associated_steps = self.associated_steps_dict
        associated_cli = self.associated_cli_dict
        associated_api = self.associated_api_dict

        associated_graph = self.convert_to_graph(
            case_associated_structure["前置条件"],
            case_associated_structure["步骤"],
            case_associated_structure["后置条件"]
        )
        if callback:
            # 执行回调方法记录
            callback(
                test_case=test_case,
                before_cut=dict(
                    associated_keywords=associated_keywords,
                    associated_steps=associated_steps,
                    associated_cli=associated_cli,
                    associated_api=associated_api,
                    associated_graph=associated_graph
                )
            )
        # 计算 token 并进行上下下文的删减
        cutter = ContextCutter(self.task_id, associated_keywords, associated_steps,
                               associated_cli, associated_api, associated_graph)
        (associated_keywords,
         associated_steps,
         associated_cli,
         associated_api,
         associated_graph) = cutter.cut_context()
        if callback:
            # 执行回调方法记录
            callback(
                after_cut=dict(
                    associated_keywords=associated_keywords,
                    associated_steps=associated_steps,
                    associated_cli=associated_cli,
                    associated_api=associated_api,
                    associated_graph=associated_graph
                )
            )
        return test_case, associated_keywords, associated_steps, associated_cli, associated_api, associated_graph

    def get_case_associated(self,
                            case_associated_structure: Dict[str, List[dict]]
                            ) -> Optional[Dict[str, List[dict]]]:
        for section, step_list in case_associated_structure.items():
            if section in self.STEP_SECTION:
                for step_dict in step_list:
                    # 直接修改dict中associated_keyword，associated_cli，associated_steps， associated_api 内容
                    self.get_case_step_associated(step_dict)
        return case_associated_structure

    def get_case_step_associated(self, step_dict: dict):
        """
        调用 knowledgeSeeker 检索用例的关联信息
        直接修改掉 step_dict 中的 associated_keyword，associated_cli，associated_steps， associated_api 字段
        @param step_dict:
        @return:
        """
        step_desc = step_dict["content"]
        name = step_dict["name"]
        step_intent = []
        if name in self.manual_case.case_intent_cache:
            step_intent = self.manual_case.case_intent_cache[name]
        # TODO: 检索的接口待优化，当前参数设计比较乱
        data = {
            "action": ["step", "keyword"],
            "case_module": self.manual_case.case_module,
            "product_id": self.manual_case.product_id,
            "product_name": self.manual_case.product_name,
            "step_desc": step_desc,
            "step_intent": step_intent,
        }
        res = E2ECaseKsManager.get_step_associated_info(**data)
        vector_result = res.get("vector_result", {})
        fulltext_result = res.get("fulltext_result", {})
        self.handle_result(step_dict, vector_result)
        self.handle_result(step_dict, fulltext_result, False)

    def handle_result(self, step_dict: dict, result: dict, is_get_score: bool = True):
        # 处理关键字keyword
        associated_keyword = result.get("keyword") if result.get("keyword", None) else []
        keywords_name = []

        for k in associated_keyword:
            kw_name = k["name"]
            kw = {
                "name": kw_name
            }
            if is_get_score:
                kw["score"] = k["score"]
            keywords_name.append(kw)
            self.associated_keyword_dict[kw_name] = k["detail"]
        if isinstance(step_dict["associated_keyword"], list):
            step_dict["associated_keyword"].extend(keywords_name)
        else:
            step_dict["associated_keyword"] = keywords_name

        # 处理 cli
        associated_cli = result.get("cli") if result.get("cli", None) else []
        cli_names = []

        for c in associated_cli:
            c_name = c["name"]
            cli = {
                "name": c_name
            }
            if is_get_score:
                cli["score"] = c["score"]
            cli_names.append(cli)
            if c_name not in self.associated_cli_dict:
                self.associated_cli_dict[c_name] = c["detail"]

        if isinstance(step_dict["associated_cli"], list):
            step_dict["associated_cli"].extend(cli_names)
        else:
            step_dict["associated_cli"] = cli_names

        # 处理 api
        associated_api = result.get("api") if result.get("api", None) else []
        api_names = []

        for a in associated_api:
            a_name = a["name"]
            api = {
                "name": a_name
            }
            if is_get_score:
                api["score"] = a["score"]
            api_names.append(api)
            self.associated_api_dict[a_name] = a["detail"]

        if isinstance(step_dict["associated_api"], list):
            step_dict["associated_api"].extend(api_names)
        else:
            step_dict["associated_api"] = api_names

        # 处理 step 以及步骤种的 cli, api, keyword
        associated_steps = result.get("step", [])
        step_ids = []
        for s in associated_steps:
            step_id = s["uuid"]
            step = {
                "uuid": step_id
            }
            if is_get_score:
                step["score"] = s["score"]
            step_ids.append(step)
            step_keywords = s["step_keywords"]
            step_cli = s["step_cli"]
            step_api = s["step_api"]
            for item in step_keywords:
                name = item["name"]
                self.associated_keyword_dict[name] = item["detail"]
            for item in step_cli:
                name = item["name"]
                if name not in self.associated_cli_dict:
                    self.associated_cli_dict[name] = item["detail"]
            for item in step_api:
                name = item["name"]
                self.associated_api_dict[name] = item["detail"]
            self.associated_steps_dict[step_id] = {
                "case_code": s["case_code"],
                "step_desc": s["step_desc"],
                "uuid": s["uuid"],
                "step_expect": s["step_expect"],
                "step_cli": [item["name"] for item in s["step_cli"]],
                "step_api": [item["name"] for item in s["step_api"]],
                "step_keywords": [item["name"] for item in s["step_keywords"]],
            }

        if isinstance(step_dict["associated_steps"], list):
            step_dict["associated_steps"].extend(step_ids)
        else:
            step_dict["associated_steps"] = step_ids

    @staticmethod
    def convert_to_graph(pre_conditions, steps, post_conditions):
        map_dict = {}

        def data_to_map(data):
            for entry in data:
                step_num = entry['name']
                associated_steps = entry['associated_steps']
                associated_cli = entry['associated_cli']
                associated_api = entry['associated_api']
                associated_keyword = entry['associated_keyword']
                map_dict[step_num] = {
                    "相似历史步骤": associated_steps,
                    "相似关键字": associated_keyword,
                    "相似cli": associated_cli,
                    "相似api": associated_api,
                }

        for s in [pre_conditions, steps, post_conditions]:
            data_to_map(s)

        return map_dict


class ContextCutter:
    """
    上下文规则: https://docs.atrust.sangfor.com/pages/viewpage.action?pageId=365579462
    """

    MAX_TOKEN = 40000
    # 相似度评分，当前是 bge-base-zh 模型和e2e语料的经验来定的，后续需要进一步优化
    MAX_STEP_SCORE = 0.9
    MAX_DOCS_SCORE = 0.91

    def __init__(self, task_id, associated_keywords, associated_steps, associated_cli, associated_api,
                 associated_graph):
        self.task_id = task_id
        self.associated_keywords = associated_keywords
        self.associated_steps = associated_steps
        self.associated_cli = associated_cli
        self.associated_api = associated_api
        self.associated_graph = associated_graph

    def cut_context(self):
        self.cut_cli()
        self.cut_api()
        self.cut_steps()
        self.cut_keywords()
        c_tokens = compute_tokens(self.content)
        index = 0
        while c_tokens > self.MAX_TOKEN:
            logger.info(
                f"[e2e自动化用例生成]task:{self.task_id},token数[{c_tokens}]超过[{self.MAX_TOKEN}],进行第{index}次删减上下文")
            if index == 0:
                # 第一次按相似度删减
                self.cut_by_policy('score')
            elif index == 1:
                # 第二次按个数删减，每个步骤只保留2个结果
                self.cut_by_policy('count', retain_count=2)
            elif index == 2:
                # 第3次按个数删减，每个步骤只保留1个结果
                self.cut_by_policy('count', retain_count=1)
            else:
                logger.error(f"[e2e自动化用例生成]task:{self.task_id},上下文删减后仍超限,token数:[{c_tokens}]")
                break
            index += 1
            c_tokens = compute_tokens(self.content)

            logger.info(
                f"[e2e自动化用例生成]task:{self.task_id},第{index}次删减上下文结束,token数:[{c_tokens}]")
        return (self.associated_keywords, self.associated_steps,
                self.associated_cli, self.associated_api, self.associated_graph)

    def cut_by_policy(self, delete_policy: str, retain_count: int = 1):
        def update_delete_status(items: list, score_key: str, identifier_key: str, delete_dict: dict,
                                 score_threshold: Optional[Union[int, float]] = None):
            # 按评分删除策略
            if delete_policy == 'score':
                if not score_threshold or not isinstance(score_threshold, float):
                    return items
                retained_items = []
                for item in items:
                    identifier = item[identifier_key]
                    # TODO: 没有评分字段的不进行删减, 全文索引检索到的没有加评分，这两个评分维度不一样，不放一起比较
                    score = item.get(score_key, None)
                    if score and score < score_threshold:
                        if identifier not in delete_dict:
                            delete_dict[identifier] = True
                    else:
                        delete_dict[identifier] = False
                        retained_items.append(item)
                return retained_items

            # 按数量删除策略
            elif delete_policy == 'count':
                # TODO: 没有评分字段的不进行删减, 全文索引检索到的没有加评分，这两个评分维度不一样，不放一起比较
                has_score_items = [item for item in items if item.get(score_key, None)]
                no_score_items = [item for item in items if not item.get(score_key, None)]
                # 按评分排序，从高到低
                sorted_items = sorted(has_score_items, key=lambda x: x[score_key], reverse=True)
                # 选择前retain_count个项目保留
                retained_items = sorted_items[:retain_count]
                retained_items.extend(no_score_items)
                retained_identifiers = {item[identifier_key] for item in retained_items}

                for item in items:
                    identifier = item[identifier_key]
                    if identifier in retained_identifiers:
                        delete_dict[identifier] = False
                    else:
                        if identifier not in delete_dict:
                            delete_dict[identifier] = True

                # 返回保留的项目列表
                return retained_items

            else:
                raise ValueError(f"Unsupported delete_policy: {delete_policy}")

        def delete_keys_from_dict(data_dict: dict, delete_dict: dict):
            for key in list(delete_dict.keys()):  # 放在一个list中，避免运行时修改字典
                if delete_dict[key]:
                    if key in data_dict:
                        del data_dict[key]

        is_delete_step = {}
        is_delete_keyword = {}
        is_delete_cli = {}
        is_delete_api = {}

        for step_num, s in self.associated_graph.items():
            s["相似历史步骤"] = update_delete_status(
                s["相似历史步骤"], "score", "uuid", is_delete_step, self.MAX_STEP_SCORE)
            s["相似关键字"] = update_delete_status(
                s["相似关键字"], "score", "name", is_delete_keyword, self.MAX_DOCS_SCORE)
            s["相似cli"] = update_delete_status(
                s["相似cli"], "score", "name", is_delete_cli, self.MAX_DOCS_SCORE)
            s["相似api"] = update_delete_status(
                s["相似api"], "score", "name", is_delete_api, self.MAX_DOCS_SCORE)

            # 相似步骤中保留的步骤，保留其关联的关键字、CLI和API
            for step in s["相似历史步骤"]:
                step_uuid = step["uuid"]
                if step_uuid in self.associated_steps:
                    step_dict = self.associated_steps[step_uuid]
                    for k in step_dict["step_keywords"]:
                        is_delete_keyword[k] = False
                    for cli in step_dict["step_cli"]:
                        is_delete_cli[cli] = False
                    for api in step_dict["step_api"]:
                        is_delete_api[api] = False

        # 因为删除步骤有关联CLI和API，因此要把步骤中删除的CLI和API如果没有复用的则也删掉
        for k, v in is_delete_step.items():
            if v:
                step = self.associated_steps[k]
                for cli in step["step_cli"]:
                    if cli not in is_delete_cli:
                        is_delete_cli[cli] = True
                for api in step["step_api"]:
                    if api not in is_delete_api:
                        is_delete_api[api] = True
                for kw in step["step_keywords"]:
                    if kw not in is_delete_keyword:
                        is_delete_keyword[kw] = True
        # 删除状态为 True 的键
        delete_keys_from_dict(self.associated_steps, is_delete_step)
        delete_keys_from_dict(self.associated_keywords, is_delete_keyword)
        delete_keys_from_dict(self.associated_cli, is_delete_cli)
        delete_keys_from_dict(self.associated_api, is_delete_api)

    def cut_cli(self):
        # 去除掉2级以下的子命令文档
        error_docs_name = []
        for cli_name, detail in self.associated_cli.items():
            try:
                docs_dict = json.loads(detail)
                if "subcommand" in docs_dict:
                    subcommands = docs_dict["subcommand"]
                    if len(subcommands) > 1:
                        # 二级命令会携带一级命令，并且二级命令只保留自己
                        # 非二级命令都把二级以下子命令去除
                        for sub_c in subcommands:
                            if "subcommand" in sub_c:
                                sub_c["subcommand"] = []
                self.associated_cli[cli_name] = json.dumps(docs_dict, ensure_ascii=False)

            except json.decoder.JSONDecodeError:
                error_docs_name.append(cli_name)
                logger.error(f"[e2e自动化用例生成] CLI名字为【{cli_name}】的文档不完整")
        for name in error_docs_name:
            del self.associated_cli[name]

    def cut_api(self):
        # 去掉所有的output内容
        error_docs_name = []
        for api_name, detail in self.associated_api.items():
            try:
                docs_dict = json.loads(detail)
                docs_dict.pop("outputSamples", None)
                docs_dict.pop("outputParams", None)
                self.associated_api[api_name] = json.dumps(docs_dict, ensure_ascii=False)

            except json.decoder.JSONDecodeError:
                error_docs_name.append(api_name)
                logger.error(f"[e2e自动化用例生成] API名字为【{api_name}】的文档不完整")
        for name in error_docs_name:
            del self.associated_api[name]

    def cut_steps(self):
        # 留空，暂时不处理
        pass

    def cut_keywords(self):
        # 留空，暂时不处理
        pass

    @property
    def content(self):
        return (
            f"{self.associated_keywords}"
            f"{self.associated_steps}"
            f"{self.associated_cli}"
            f"{self.associated_api}"
            f"{self.associated_graph}"
        )
