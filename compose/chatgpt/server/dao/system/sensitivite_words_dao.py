#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dao.base_dao import BaseDao
from models.system.sensitive_words import SensitiveWords


class SensitiveWordsDao(BaseDao):
    model = SensitiveWords

    @classmethod
    def get_sensitization_data(cls):
        """
        获取敏化数据
        """
        sensitization_data = list()
        desensitization_data = list()
        query, _ = cls.list(deleted=False)

        for each in query:
            sensitization_data.append((each.sensitive_words, each.permutation_words))
            desensitization_data.append((each.permutation_words, each.sensitive_words))

        # 根据敏感词长度降序排序
        sensitization_data.sort(key=lambda x: len(x[0]), reverse=True)
        desensitization_data.sort(key=lambda x: len(x[0]), reverse=True)

        return sensitization_data, desensitization_data
