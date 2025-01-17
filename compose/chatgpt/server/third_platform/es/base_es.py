#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/16 20:23
    :修改者: 苏德利 16646
    :更新时间: 2023/3/16 20:23
"""

import logging
import json
import os
from config import get_config
from common.exception.exceptions import EsIndexError
from common.utils.request_util import RequestUtil
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch_dsl.query import Q
from common.helpers.custom_json_encoder import CustomJSONEncoder
from common.utils.date_util import DateUtil

# pylint: disable=no-member
DOC = "_doc"
ES_HOST = get_config().get("es_server")
ES_PASSWORD = os.environ.get("ES_PASSWORD")
# 设置日志级别，因为在开发的时候，会将查询结果打印出来，碍眼
logging.getLogger("elasticsearch").setLevel(logging.INFO)
logging.getLogger("elasticsearch").info(f"ES_HOST: {ES_HOST},\nES_PASSWORD: {ES_PASSWORD}")

es = Elasticsearch(ES_HOST) if ES_PASSWORD is None else Elasticsearch([ES_HOST], http_auth=('elastic', ES_PASSWORD))
PROMPT_INDEX = get_config().get("prompt_es_index", "prompt")
CODE_COMPELTION_INDEX = get_config().get("code_completion_es_index", "code_completion")
CODE_COPY_INDEX = get_config().get("code_copy_es_index", "code_copy")
AI_REVIEW_INDEX = get_config().get("ai_review_es_index", "ai_review")
UT_CASE_INDEX = get_config().get("ut_case_es_index", "ut_case")
UT_PROMPT_INDEX = get_config().get("ut_prompt_es_index", "ut_prompt")
IDE_DATA_INDEX = get_config().get("ide_data_index", "ide_data")


class BaseESService:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.field_type_string = ["string", "rich", "userselect"]
        self.field_type_term = ["int", "fk", "select", "bool"]
        self.field_type_range = ["datetime", "date"]
        self.index = None
        self.s = None
        self.field_handler = None
        self.int_type = ["int"]
        self._doc = DOC
        self.escape_character = "\\"
        # 反斜杠要放到最前面 ，因为在其他特殊字符前都要加反斜杠
        self.special_characters = [
            "\\", "[", "]", "{", "}", "/", "^", "(", ")", "~", '"'
        ]

    def insert(self, obj_dict):
        """更新(或生成)数据到es"""
        try:
            if not ES_HOST:
                return
            if not obj_dict:
                return
            if obj_dict.get('id'):
                es.index(index=self.index, id=obj_dict['id'], refresh=True, body=obj_dict, doc_type=self._doc)
            else:
                es.index(index=self.index, refresh=True, body=obj_dict, doc_type=self._doc)
        except Exception as err:
            self.logger.error(f"添加es:{self.index}索引出现异常:{str(err)},obj:{obj_dict}")
            raise EsIndexError()

    def bulk_insert(self, objects):
        """
        批量插入  json.dumps(objects, self=CustomJSONEncoder)
        :param objects:
        :return:
        """
        self.logger.info(f"批量插入{len(objects)}条")
        insert_s = list()
        if objects and len(objects):
            for obj in objects:
                insert_s.append(
                    self._gen_update_str(self.index, obj["id"]) + "\n" + json.dumps(obj, cls=CustomJSONEncoder))
            es.bulk('\n'.join(insert_s) + '\n', index=self.index, doc_type=self._doc, refresh=True)

    def update_by_id(self, id, update_data):
        try:
            return es.update(index=self.index, id=id, body={'doc': update_data})
        except Exception as e:
            self.logger.error(f"修改es:{self.index} id :{id}, update_data:{update_data} 失败：{str(e)}")
            return None

    def _gen_update_str(self, index, doc_id, doc_type="_doc"):
        return json.dumps({
            "index": {
                "_index": index,
                "_type": doc_type,
                "_id": doc_id
            }
        })

    def update_settings(self):
        """
        更新settings
        :return:
        """
        RequestUtil.put(ES_HOST + "/_settings", json={
            "index.mapping.total_fields.limit": 3000
        })

    def update_mappings(self):
        """
        更新mappings
        :return:
        """
        RequestUtil.put(ES_HOST + "/" + self.index + "/_mapping", json={
            "properties": {
                "name": {
                    "type": "text",
                    "fielddata": True
                },
                "latest_version": {
                    "type": "text",
                    "fielddata": True
                }
            }
        })

    def get(self, obj_id):
        """获取es中指定id的数据"""
        try:
            res = es.get(index=self.index, doc_type=DOC, id=obj_id)
            return res["_source"] if res else None
        except Exception as ex:
            self.logger.info(f"未找到get_id:{str(ex)}")
            return None

    def if_have_to_delete_by_id(self, mid):
        """如果有就删除"""
        try:
            if es.exists(index=self.index, id=mid):
                es.delete(index=self.index, refresh=True, doc_type=self._doc, id=mid)
            return True
        except Exception as ex:
            self.logger.info(f"未找到if_have_to_delete_by_id:{str(ex)}")
            return False

    def delete(self, mid):
        """删除es中指定id数据"""
        try:
            es.delete(index=self.index, refresh=True, doc_type=self._doc, id=mid)
            return True
        except Exception as ex:
            self.logger.info(f"未找到delete:{str(ex)}")
            return False

    def delete_index(self):
        """删除es中指定索引"""
        try:
            es.indices.delete(index=self.index)
            return True
        except Exception as ex:
            self.logger.info(f"未找到delete_index:{str(ex)}")
            return False

    def special_character_processing(self, kwargs):
        """
        特殊字符参数处理,只针对字符串的处理
        :param kwargs:
        :return:
        """
        if not kwargs:
            return kwargs
        for key in kwargs.keys():
            value = kwargs[key]
            if isinstance(kwargs[key], str):
                for sc in self.special_characters:
                    if sc in value:
                        value = value.replace(sc, f"{self.escape_character}{sc}")
            kwargs[key] = value
        return kwargs

    def execute_query(self, query):
        """
        执行查询语句
        :param query: 查询参数集合封装
        """
        result = dict(
            rows=[],
            total=0
        )
        try:
            # self.logger.info(f"execute_query: {query.to_dict()}")
            t = query.execute().to_dict()
            res = [h["_source"] for h in t["hits"]["hits"]] if len(t["hits"]["hits"]) > 0 else []
            result = dict(
                rows=res,
                total=t["hits"]["total"]["value"]
            )
        except NotFoundError as err:
            if err.error == "index_not_found_exception":
                result["err_msg"] = "es索引没找到，请先创建索引"
        return result

    def gen_range(self, key, value):
        new_value = {}
        if value:
            new_value = {
                "gte": DateUtil.str_to_gmt_datetime_str(value.get("start")),
                "lte": DateUtil.str_to_gmt_datetime_str(value.get("end"))
            }
        return Q("range", **{key: new_value})

    def gen_match(self, key, value):
        return Q("match", **{key: value})

    def gen_term(self, key, value):
        return Q("term", **{key: value})

    def gen_terms(self, key, value):
        return Q("terms", **{key: value})

    def gen_term_or_terms(self, key, value):
        return self.gen_terms(key, value) if isinstance(value, list) else self.gen_term(key, value)

    def gen_query_string(self, key, value):
        if isinstance(value, list):
            return self.gen_terms(key, value)
        return Q("query_string", default_field=f"{key}.keyword", query=f'*{value}*')

    def gen_exists(self, key, value):
        return Q("exists", **{key: value})

    def list_page(self, page=1, page_size=20, sort_by=None, order_by='asc', must={}, must_not={}, should={},
                  paginate=True, must_ext={}):
        # 前端要求不分页时，此处默认设置 10000条返回记录，es默认只返回前10条
        if paginate is False or paginate is None:
            page = 1
            page_size = 10000
            paginate = True
        return self._gen_query(
            self.s, self.field_handler, page, page_size, sort_by, order_by, must, must_not, should, paginate, must_ext)

    @staticmethod
    def parse_paginate(query, page, page_size, sort_by, order_by, paginate):
        """
        解析排序和分页信息
        :param query: es实例对象
        :param page: 分页页码
        :param page_size: 分页单页大小
        :param paginate: 是否分页
        :param sort_by: 排序
        :param order_by: 排序
        """
        if paginate and page and page_size:
            query = query[((page - 1) * page_size):((page - 1) * page_size + page_size)]
        # self.logger.info(f"版本查询条件：must_query={must_query}")
        if sort_by:
            # 暂时支持一个字段，后续可以支持多个字段
            if isinstance(sort_by, str):
                if order_by == "desc":
                    sort_by = f"-{sort_by}"
                sort_by = [sort_by]
            # sort_by = [f'-{s}' if not s.startswith("-") else s for s in sort_by]
            query = query.sort(
                *sort_by
            )
        return query

    def _gen_query(self, es_search, field_handler, page, page_size, sort_by, order_by, must, must_not, should,
                   paginate, must_ext):
        """

        :param es_search:
        :param field_handler:
        :param page:
        :param page_size:
        :param sort_by:
        :param order_by: asc升序，desc降序
        :param must:
        :param must_not:
        :param should:
        :param paginate:
        :param must_ext: {key: value} 该值不经过处理，直接写入query
        :return:
        """
        query = es_search.query()
        self.special_character_processing(must)
        self.special_character_processing(should)
        must_query = self.gen_query_list(**must)
        should_query = self.gen_query_list(**should)
        new_q = Q("bool", must=must_query, should=should_query)
        query = query.query(new_q)
        query = self.parse_paginate(query, page, page_size, sort_by, order_by, paginate)
        return self.execute_query(query)

    def gen_query_list(self, **kwargs):
        must_or_should = []
        if kwargs:
            for key in kwargs.keys():
                q = self.assemble_query(key, kwargs.get(key))
                if q:
                    must_or_should.append(q)
        return must_or_should

    def assemble_query(self, key, value):
        """
        拼装query
        """
        field_type = self.field_handler.get_field_type(key)
        key = self.field_handler.gen_origin_field_key(key)
        if field_type in self.field_type_string and value:
            return self.gen_query_string(key, value)
        elif field_type in self.field_type_term and value:
            return self.gen_term_or_terms(key, value)
        elif field_type in self.field_type_range and value:
            return self.gen_range(key, value)
        elif field_type == "bool" and (value is False or value is True):
            return self.gen_term_or_terms(key, value)
        return None

    def assemble_must_and_should(self, must: list, should: list):
        return Q("bool", must=must, should=should, minimum_should_match=1)
