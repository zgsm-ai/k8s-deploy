#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/19 20:41
"""
import logging

from common.exception.exceptions import NoResourceError
from common.utils.util import get_work_id_by_display_name, get_second_dept
from dao.system.ai_record_dao import AIRecordActionDao
from services.base_service import BaseService
from third_platform.services.analysis_service import analysis_service

logger = logging.getLogger(__name__)


class AIRecordActionService(BaseService):
    dao = AIRecordActionDao

    @classmethod
    def insert_db_ai_record(cls, data: dict, middle_process_records: list = None, prompt: str = '',
                            response_code: str = '',
                            response_id: str = ''):
        middle_process_records = middle_process_records or []
        work_id = get_work_id_by_display_name(data.get("display_name", ''))
        dept = analysis_service.get_user_multilevel_dept(work_id)
        insert_data = {
            'response_id': response_id,
            'action': data.get('action'),
            'display_name': data.get('display_name', ''),
            'dept': dept,
            'second_dept': get_second_dept(dept),
            'prompt': prompt,
            'origin_prompt': data.get('origin_prompt', ''),
            'code': data.get('code', ''),
            'language': data.get('language', ''),
            'response_code': response_code,
            'middle_process_records': middle_process_records,
            'git_path': data.get('git_path', ''),
        }

        main_record_response_id = data.get('response_id')
        # 有response_id参数时，更新追问数据；否则新建
        if main_record_response_id:
            insert_result = cls.dao.model(**insert_data).dict()
            cls.add_history(main_record_response_id, insert_result)
        else:
            cls.dao.create(**insert_data)
        return

    @classmethod
    def add_history(cls, response_id: str, data: dict):
        """添加追问数据并更新"""
        try:
            main_record = cls.dao.get_or_none(response_id=response_id)
            if not main_record:
                return False
            history = main_record.history
            history.append(data)
            cls.dao.update_by_id(main_record.id, **{'history': history})
        except Exception as e:
            logger.error(f'save history error: {str(e)}')
            return False

    @classmethod
    def list(cls, *args, **kwargs):
        prompt = kwargs.pop('prompt', '')
        display_name = kwargs.pop('display_name', '')
        display_names = display_name.split(',') if display_name else []
        git_path = kwargs.pop('git_path', '')
        conditions = ()
        if prompt:
            conditions += (cls.dao.model.prompt ** f'{cls.dao.model.like(prompt)}',)
        # 多人查询, or或查询
        if display_names:
            or_conditions = None
            for display_name in display_names:
                if not display_name:
                    continue
                like_condition = (cls.dao.model.display_name ** f'{cls.dao.model.like(display_name)}')
                if or_conditions is None:
                    or_conditions = like_condition
                else:
                    or_conditions |= like_condition
            if or_conditions is not None:
                conditions += (or_conditions,)
        if git_path:
            conditions += (cls.dao.model.git_path ** f'{cls.dao.model.like(git_path)}',)
        # 此时需要查拒绝原因有值的情况
        if 'process_state' in kwargs:
            conditions += (cls.dao.model.refusal_cause != '',)
        # 创建时间范围查询
        conditions += cls.process_time_range_query(field_name='created_at',
                                                   start_time=kwargs.pop('start_time', ''),
                                                   end_time=kwargs.pop('end_time', ''))
        kwargs['conditions'] = conditions
        return super().list(*args, **kwargs)

    @classmethod
    def update_with_accept(cls, accept_data):
        """只有接受场景。拒绝场景在另外接口"""
        response_id = accept_data.get('id', None)  # ide端传的参数是id
        is_accept = accept_data.get('isAccept', False)
        accept_num = accept_data.get('acceptNum', 0)
        accept_code = accept_data.get('acceptCode')

        if response_id and is_accept:
            record = cls.dao.get_or_none(response_id=response_id)
            if record:
                fields = {
                    'is_accept': is_accept,
                    'accept_num': accept_num
                }
                if accept_code is not None:
                    fields['response_code'] = accept_code
                cls.dao.update_by_id(mid=record.id, **fields)

    @classmethod
    def validate_fields(cls, fields):
        """校验创建数据参数"""
        rules = [
            {'label': 'response_id', 'type': str, 'length': 50},
            {'label': 'is_accept', 'type': bool, 'optional': True},
            {'label': 'accept_num', 'type': int, 'optional': True},
            {'label': 'refusal_cause', 'type': str, 'optional': True, 'length': 255},
            {'label': 'analysis_result', 'type': str, 'optional': True, 'length': 1000},
            {'label': 'process_state', 'type': bool, 'optional': True},
        ]
        return cls._validate(fields, rules)

    @classmethod
    def update_by_response_id(cls, **kwargs):
        response_id = kwargs.pop('response_id', '')
        record = cls.dao.get_or_none(response_id=response_id)
        if record:
            cls.dao.update_by_id(mid=record.id, **kwargs)
        else:
            raise NoResourceError()

    @classmethod
    def dept_list(cls):
        # 部门信息字段
        column = "dept"
        column_field = getattr(cls.dao.model, column, None)
        query = (cls.dao.model.select(column_field).group_by(column_field))
        dept_info_list = [getattr(q, column) for q in query]
        data = [{
            "key": dept_info,
            "label": dept_info.split("/")[-1]
        } for dept_info in dept_info_list]
        return data
