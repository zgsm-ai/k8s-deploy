#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import re
from dao.system.sensitivite_words_dao import SensitiveWordsDao


class SensitiveWords:
    dao = SensitiveWordsDao

    def __init__(self, get_content_func, update_content_func, need_sensitization: bool = True):
        self.need_sensitization = need_sensitization
        self.get_content_func = get_content_func
        self.update_content_func = update_content_func
        self.sensitization_data, _ = self.dao.get_sensitization_data()
        self.desensitization_data = list()
        self.max_length = self.find_max_length_string(self.sensitization_data) * 2
        self.sensitive_words = dict()

    @staticmethod
    def find_max_length_string(input_data: list) -> int:
        """
        获取字典中最大长度的字符串长度
        :param input_data: 输入的字典
        :return: 最大长度的字符串长度
        """
        max_length = 4
        for k, v in input_data:
            max_length = max(max_length, len(str(k)), len(str(v)))
        return max_length

    def sensitization_process(self, text):
        """
        敏化处理
        text: 需要敏化的文本
        """
        for target_word, replace_word in self.sensitization_data:
            if target_word in text:
                text = re.sub(target_word, replace_word, text)
                self.sensitive_words[target_word] = replace_word
                self.desensitization_data.append((replace_word, target_word))
        return text

    def desensitization_process(self, text):
        """
        脱敏处理
        text: 需要脱敏的文本
        """
        for target_word, replace_word in self.desensitization_data:
            if target_word in text:
                text = re.sub(target_word, replace_word, text)
        return text

    def sensitization_process_messages(self, messages: list):
        """
        敏感信息敏化
        :param messages:
        :return:
        """
        if not self.need_sensitization:
            return messages
        res = []
        for message in messages:
            message['content'] = self.sensitization_process(message['content'])
            res.append(message)
        return res

    def desensitization_process_blocking(self, completion):
        """
        敏感信息脱敏
        :param completion:
        :return:
        """
        completion = completion.model_dump()
        if not self.need_sensitization:
            return completion
        if self.sensitive_words:
            completion['sensitive_words'] = self.sensitive_words
        content = self.get_content_func(completion)
        text = self.desensitization_process(content)
        return self.update_content_func(completion, text)

    def desensitization_process_stream(self, completion):
        """
        敏感信息脱敏
        :param completion:
        :return:
        """

        response = None
        start_index = 0  # 记录处理到第几个字符
        processing_procedure = ""
        all_content = ""
        last_response = None  # 脱敏处理需要
        for response in completion:
            response = response.model_dump()
            if not self.need_sensitization:
                yield response
                continue

            if self.sensitive_words:
                response['sensitive_words'] = self.sensitive_words

            content = self.get_content_func(response)
            if not content or not isinstance(content, str):
                continue

            last_response = copy.deepcopy(response)
            processing_procedure += content
            all_content += content
            processing_procedure = self.desensitization_process(processing_procedure)

            now_length = len(processing_procedure)
            end_index = now_length - self.max_length
            if end_index > 0:
                res = processing_procedure[start_index:end_index]
                start_index = end_index
                yield self.update_content_func(response, res)

        # 处理积压的内容返回，以及模型最后一次content的返回
        if self.need_sensitization and response is not None:
            res = processing_procedure[start_index:]
            yield self.update_content_func(last_response, res)  # 返回最后一次有content的response

            if self.get_content_func(response) is None:
                yield response  # 返回最后一次没有content的response
