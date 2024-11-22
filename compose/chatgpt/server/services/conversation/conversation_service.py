#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from common.constant import PromptConstant, ConversationRole, ConfigurationConstant
from common.utils.llm_tool import get_message_tokens
from dao.system.conversation_dao import ConversationDao
from services.system.configuration_service import ConfigurationService


class ConversationService:
    dao = ConversationDao

    @classmethod
    def record_context(cls, model, conversation_id, req_messages, response_content):
        """
        Record contextual information
        : model: Model
        : conversation_id: conversation id
        : req_messages: model requests messages
        : response_content: Model response text
        :return:
        """
        for message in req_messages:
            role = message.get("role")
            content = message.get("content")
            if role == ConversationRole.SYSTEM:
                obj = cls.dao.get_or_none(conversation_id=conversation_id, role=role)
                if obj:
                    obj.content = content
                    obj.save()
                    continue

            cls.dao.create(conversation_id=conversation_id,
                           role=role,
                           content=content,
                           model=model)
        cls.dao.create(conversation_id=conversation_id,
                       role=ConversationRole.ASSISTANT,
                       content=response_content,
                       model=model)

    @classmethod
    def assembly_context(
            cls, max_input_tokens,
            conversation_id,
            req_messages,
            carry_context: bool = False
    ) -> (list, int, int):
        """
        Assemble contextual information
        : carry_context: Used to determine whether context is carried
        :return:
        """
        # 获取当前请求的用户提问 system_message、us
        system_message = dict()
        user_messages = list()
        for message in req_messages:
            if message.get("role") == ConversationRole.SYSTEM:
                system_message = message
            if message.get("role") == ConversationRole.USER:
                user_messages.append(message)

        if not system_message:
            obj = cls.dao.get_or_none(conversation_id=conversation_id, role=ConversationRole.SYSTEM)
            if obj:
                system_message = dict(role=obj.role, content=obj.content)

        num_tokens = 0
        system_message_token = get_message_tokens(system_message) if system_message else 0
        user_message_token = 0
        for user_message in user_messages:
            user_message_token += get_message_tokens(user_message)
        num_tokens = num_tokens + system_message_token + user_message_token
        user_req_token = input_token = num_tokens
        # Does it exceed tokens without adding historical context
        if max_input_tokens - num_tokens < 0:
            raise Exception(PromptConstant.TOKENS_OVER_LENGTH)

        all_messages = list()
        # Query historical context
        if carry_context:

            queue, _ = cls.dao.list(conversation_id=conversation_id, sort_by="id", sort_to="desc",
                                    page=1, per=cls.get_max_context_num())
            # Assembly history context
            for each in queue:
                if each.role == ConversationRole.SYSTEM:
                    continue
                data = dict(
                    role=each.role,
                    content=each.content,
                )
                num_tokens += get_message_tokens(data)
                if max_input_tokens - num_tokens < 0:
                    break
                input_token = num_tokens
                all_messages.insert(0, data)
        # Ensure that the context is question-and-answer. If it starts with an answer, remove the answer
        if len(all_messages) and all_messages[0].get("role", "") == ConversationRole.ASSISTANT:
            del all_messages[0]
        # Assembly system_message、user_message
        if system_message:
            all_messages.insert(0, system_message)
        all_messages.extend(user_messages)
        return all_messages, user_req_token, input_token

    @staticmethod
    def clean_up_expired_contexts():
        """
        Clean up expired session records
        :return:
        """
        try:
            logging.info("Clean up expired session records")
            timeout = 3 * 24 * 60 * 60
            timeout_date = datetime.now() - timedelta(seconds=timeout)
            conditions = ((ConversationDao.model.created_at < timeout_date),)
            queue, _ = ConversationDao.list(conditions=conditions)
            delete_id_list = [each.id for each in queue]
            ConversationDao.model.delete().where(ConversationDao.model.id << delete_id_list).execute()
        except Exception as e:
            logging.error(f"Clean up expired session records failed, error: {e}")

    @classmethod
    def get_max_context_num(cls):
        context_max_num = ConfigurationService.get_configuration(belong_type=ConfigurationConstant.CONTEXT_BELONG_TYPE,
                                                                 attribute_key=ConfigurationConstant.CONTEXT_MAX_NUM)
        context_max_num = int(context_max_num) if context_max_num else 10
        return context_max_num
