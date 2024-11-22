#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import re
from common.utils.date_util import DateUtil

import openai

from common.constant import AskStreamConfig, ConfigurationConstant, GPTConstant, LLMType, PromptConstant
from common.exception.exceptions import ParameterConversionError, RequestError
from common.utils.llm_tool import compute_tokens
from common.utils.util import custom_retry
from common.utils.util import remove_duplicate_string, check_and_set_key_path
from services.conversation.conversation_service import ConversationService
from services.llm.llm_adatper.adatper_data import BaseModelData
from services.llm.llm_adatper.sensitive_words import SensitiveWords
from services.llm.statistics_token_service import StatisticsTokenService
from services.system.configuration_service import ConfigurationService


class BaseAdapter:
    provider = ""

    def __init__(self, model_data: BaseModelData):
        self.client = None
        self.model_data = model_data
        self.full_response_content = ""
        self.continue_count = 0
        self.can_continue = False
        self.completion_tokens = 1
        self.sensitive_words = SensitiveWords(self.get_content, self.update_content,
                                              need_sensitization=self.model_data.need_sensitization)

    def make_chat_completiont_data(self) -> dict:
        """
        Constructing session model request parameters
        """
        messages, user_req_token, input_token = ConversationService.assembly_context(
            max_input_tokens=self.model_data.max_input_tokens,
            conversation_id=self.model_data.conversation_id,
            req_messages=self.model_data.messages,
            carry_context=self.model_data.carry_context
        )

        self.model_data.token_number.input_token = input_token
        self.model_data.token_number.user_req_token = user_req_token
        messages = self.sensitive_words.sensitization_process_messages(messages)
        data = dict(
            model=self.model_data.model_name,
            stream=self.model_data.stream,
            messages=messages,
        )
        if self.model_data.seed is not None:
            data.update(seed=self.model_data.seed)
        if self.model_data.temperature is not None:
            data.update(temperature=self.model_data.temperature)
        if self.model_data.stop is not None:
            data.update(stop=self.model_data.stop)
        if self.model_data.max_tokens is not None:
            data.update(max_tokens=self.model_data.max_tokens)
        if self.model_data.timeout is not None:
            data.update(timeout=self.model_data.timeout)
        if self.model_data.response_format is not None:
            data.update(response_format=self.model_data.response_format)
        return data

    def make_completion_data(self) -> dict:
        """
        Build completion model request parameters
        """
        promot_tokens = compute_tokens(self.model_data.prompt)

        if self.model_data.max_input_tokens - promot_tokens < 0:
            raise Exception(PromptConstant.TOKENS_OVER_LENGTH)

        self.model_data.token_number.input_token = promot_tokens
        self.model_data.token_number.user_req_token = promot_tokens
        prompt = self.sensitive_words.sensitization_process(self.model_data.prompt)

        data = dict(
            model=self.model_data.model_name,
            stream=self.model_data.stream,
            prompt=prompt,
        )

        if self.model_data.seed is not None:
            data.update(seed=self.model_data.seed)
        if self.model_data.temperature is not None:
            data.update(temperature=self.model_data.temperature)
        if self.model_data.stop is not None:
            data.update(stop=self.model_data.stop)
        if self.model_data.max_tokens is not None:
            data.update(max_tokens=self.model_data.max_tokens)
        if self.model_data.timeout is not None:
            data.update(timeout=self.model_data.timeout)
        if self.model_data.response_format is not None:
            data.update(response_format=self.model_data.response_format)
        return data

    def make_embeddings_data(self) -> dict:
        """
        Constructing Vector Model Request Parameters
        """
        data = dict(
            model=self.model_data.model_name,
            input=self.model_data.input
        )
        if self.model_data.encoding_format is not None:
            data.update(encoding_format=self.model_data.encoding_format)
        return data

    @custom_retry(not_exception_type=(openai.BadRequestError,))
    def _get_chat_completion(self, data: dict):
        request_id = self.model_data.kw.get("request_id")
        logging.info(
            f'start request llm server, request_id:{request_id}, now_time:{DateUtil.get_now_yyyymmddhhmmss()}')
        completion_res = self.client.chat.completions.create(**data)
        logging.info(
            f'end request llm server, request_id:{request_id}, now_time:{DateUtil.get_now_yyyymmddhhmmss()}')
        return completion_res

    @custom_retry()
    def _get_completion(self, data: dict):
        completion_res = self.client.completions.create(**data)
        return completion_res

    @custom_retry()
    def _get_embedding(self, data: dict):
        embedding = self.client.embeddings.create(**data)
        return embedding

    def get_chat_completion(self):
        data = self.make_chat_completiont_data()
        try:
            completion_res = self._get_chat_completion(data)
        except openai.BadRequestError as e:
            logging.error(f"request llm server error, request_id:{self.model_data.kw.get('request_id')}, err: {e}")
            # 正则表达式模式，匹配 'message' 字段的内容
            pattern = r"'message': \"(.*?)\""
            # 使用 re.search 查找匹配的内容
            match = re.search(pattern, e.message)
            if match:
                # 提取并打印 'message' 字段的内容
                message_content = match.group(1)

            else:
                message_content = e.message
            raise ParameterConversionError(message_content)
        except Exception as e:
            raise RequestError(e)
        if self.model_data.stream:
            completion_res = self.sensitive_words.desensitization_process_stream(completion_res)
            res = self._process_completion_stream(completion_res)
        else:
            completion_res = self.sensitive_words.desensitization_process_blocking(completion_res)
            res = self._process_completion_blocking(completion_res)
        return res

    def get_completion(self):
        data = self.make_completion_data()
        try:
            completion_res = self._get_completion(data)
        except Exception as e:
            msg = f'{self.model_data.conversation_id},base_url:{self.model_data.model_url} error in ask_stream, msg={e}'
            raise RequestError(msg)
        if self.model_data.stream:
            completion_res = self.sensitive_words.desensitization_process_stream(completion_res)
            return self._process_completion_stream(completion_res)
        else:
            completion_res = self.sensitive_words.desensitization_process_blocking(completion_res)
            return self._process_completion_blocking(completion_res)

    def get_embedding(self):
        data = self.make_embeddings_data()
        try:
            completion_res = self._get_embedding(data)
        except Exception as e:
            msg = f'{self.model_data.conversation_id},base_url:{self.model_data.model_url} error in ask_stream, msg={e}'
            raise Exception(msg)
        return self.correct_completion_data_structure(completion_res)

    def get_finish_reason(self, response):
        """
        Reason for completion. Each reply contains a finic_response. The possible values for finish.rason are:
            Stop: API returned the complete model output.
            Length: Due to the max_token parameter or tag restrictions, the model output is incomplete.
            Content_filter: Due to the flag of the content filter, the content has been omitted.
            Null: API reply is still in progress or incomplete.
        """
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if len(choices):
                data = choices[0]
                if isinstance(data, dict):
                    return data.get("finish_reason")
        logging.warning(f"get_finish_reason, response Data structure exception, response:{response}")
        return None

    def check_continue(self, completion):
        if self.model_data.model_type == LLMType.CHAT_COMPLETION \
                and self.model_data.continue_generate \
                and self.get_finish_reason(completion) == 'length' \
                and self.continue_count <= GPTConstant.MAX_CONTINUE_COUNT:
            logging.info(f"{self.model_data.conversation_id}, completion is not complete, send 'continue', "
                         f"continue count: {self.continue_count}")
            return True
        return False

    def _process_completion_blocking(
            self,
            completion: dict,
    ) -> str:
        """
        Handling non streaming responses
        """
        if completion.get("choices") is None:
            raise Exception(f"{self.model_data.conversation_id}, ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception(f"{self.model_data.conversation_id}, ChatGPT API returned no choices")

        response_text = self.get_content(completion)
        if not response_text:
            raise Exception(f"{self.model_data.conversation_id}, ChatGPT API returned no text")
        self.full_response_content += response_text
        self.model_data.token_number.output_token = compute_tokens(response_text)
        # Related data records
        self.data_record(response_text)

        if self.check_continue(completion):
            response_text = self.get_content(completion)
            _completion = self.continue_generate(response_text)
            try:
                if isinstance(_completion, str):
                    _completion = json.loads(_completion)
            except Exception as e:
                logging.info(f'{self.model_data.conversation_id}, continue error: {str(e)}')
                raise Exception(f"{self.model_data.conversation_id}, continue error")

            new_response_text = self.get_content(_completion)
            try:
                self.full_response_content = self.merge_completion_content(self.full_response_content,
                                                                           new_response_text)
                check_and_set_key_path(completion, ['choices', 0, 'message', 'content'], self.full_response_content)
            except Exception as e:
                logging.info(f'{self.model_data.conversation_id}, continue error: {str(e)}')
            # The method will directly change the value in completion
        return self.correct_completion_data_structure(completion)

    def _process_completion_stream(
            self,
            completion,
    ) -> str:
        """
        Process streaming response
        """
        duplication_data = dict()
        # The generator below is missing one. Starting from 1,
        # it will maintain the same effect as not opening the stream
        completion_number = 1
        response_text = ""
        response = None
        have_chunk = False
        try:
            for response in completion:
                have_chunk = True
                if not response.get('id'):  # The first item is empty, skip processing
                    continue
                if response.get("choices") is None:
                    raise Exception(f"{self.model_data.conversation_id} API returned no choices")
                if len(response["choices"]) == 0:
                    raise Exception(f"{self.model_data.conversation_id} API returned no choices")
                content = self.get_content(response)
                if self.model_data.overlap_skip:
                    duplication_data.update(completion_number=completion_number)
                    duplication_res, duplication_data = self.check_for_duplication(content, **duplication_data)
                    if duplication_res:
                        logging.warning(f"{self.model_data.model_name}: There are a large number of invalid duplicates"
                                        f" in the output content of the model")
                        break
                completion_number += 1
                if content and isinstance(content, str):
                    response_text += content

                if self.get_finish_reason(response):
                    self.model_data.token_number.output_token = compute_tokens(response_text)
                    total_tokens = self.model_data.token_number.output_token + self.model_data.token_number.input_token
                    response["usage"] = {'completion_tokens': self.model_data.token_number.output_token,
                                         'prompt_tokens': self.model_data.token_number.input_token,
                                         'total_tokens': total_tokens
                                         }

                res = self.process_stream_response_data(self.correct_completion_data_structure(response))
                yield res

        except Exception as e:
            logging.error(f'{self.model_data.conversation_id}, error in ask_stream, msg={e}', exc_info=True)
            raise Exception(f"model server error: {e}")
        finally:
            if completion is not None and hasattr(completion, 'close'):
                logging.info(f"{self.model_data.conversation_id},close completion generator")
                completion.close()

            # Related data records
            if response_text:
                self.data_record(response_text)
            # If the model returns empty content, the key log is logged and no context information is recorded
            else:
                logging.error(f"request llm err, content null, conversation_id:{self.model_data.conversation_id}, "
                              f"have_chunk:{have_chunk}")

            if response and self.check_continue(response):
                yield from self.continue_generate(response_text)
            else:
                res = self.get_model_stream_res_done()
                yield res

    def check_for_duplication(self, content, **kwargs):
        """
        Prevent streaming responses from returning duplicate characters and end prematurely
        :param content:
        :param kwargs: loop_count，loop_start, loop_length, hash_tokens, hash_table
        :return:
        """
        is_duplication = False
        completion_number = kwargs.get("completion_number", 1)
        loop_start = kwargs.get("loop_start", -1)
        loop_length = kwargs.get("loop_length", -1)
        loop_count = kwargs.get("loop_count", -1)
        hash_tokens = kwargs.get("hash_tokens", {})
        hash_table = kwargs.get("hash_table", {})

        # 判断循环节
        if content in hash_table:
            if loop_start != -1 and content == hash_tokens[completion_number - loop_length]:
                if completion_number + 1 - loop_start == loop_length * 2:
                    loop_count += 1
                    # Loop count limit on the number of loops
                    if loop_count > AskStreamConfig.LOOP_COUNT_LIMIT:
                        logging.warning(f"{self.model_data.conversation_id}, ChatGPT API returned loop_count>8")
                        is_duplication = True
                    loop_start += loop_length
                else:
                    pass
            else:
                loop_start = hash_table[content]
                loop_length = completion_number - loop_start
        else:
            loop_start = -1
            loop_length = -1
            loop_count = 0
        hash_table[content] = completion_number
        hash_tokens[completion_number] = content
        completion_number += 1

        data = dict(
            completion_tokens=completion_number,
            loop_start=loop_start,
            loop_length=loop_length,
            loop_count=loop_count,
            hash_tokens=hash_tokens,
            hash_table=hash_table,
        )

        return is_duplication, data

    def continue_generate(self, generated_text):
        """
        Continue writing, continue generating
        """
        self.continue_count += 1
        prompt = ConfigurationService.get_prompt_template(ConfigurationConstant.CONTINUE_PROMPT)
        last_lines = generated_text.splitlines()
        last_line = ''
        # Take the last line of the generated code and add a continuation prompt. If it is empty, retrieve it from above
        i = -1
        while last_line.strip() == '' and len(last_lines) > abs(i):
            last_line = '\n'.join(last_lines[i:])
            i -= 1
        prompt = prompt.format(lastText=last_line)
        self.model_data.carry_context = True
        self.model_data.messages = [{'role': 'user', 'content': prompt}, ]

        logging.info(f'{self.model_data.conversation_id}, gpt continue. {self.continue_count}, prompt: {prompt}')
        completion_res = self.get_chat_completion()
        return completion_res

    @staticmethod
    def merge_completion_content(response_text, new_response_text):
        """
        Merge original content and continuation content
        : response_text: Original content
        : new_response_text: Continued content
        : return: merged content
        """
        # Last time a row list was generated
        pre_last_lines = response_text.splitlines()

        def get_response_text_lines(rt):
            # 首行内容、下一行内容
            if not isinstance(rt, list):
                rt = rt.splitlines()
            if len(rt) > 2:
                one_line, two_line = rt[0], rt[1]
                rt = rt[1:]
            elif len(rt) == 1:
                one_line = rt[0]
                two_line = ""
            else:
                one_line = two_line = ""
            return one_line, two_line, rt

        first_line, second_line, new_response_text_lines = get_response_text_lines(new_response_text)
        continue_first_line = first_line  # Continuation of the first line

        while re.search(r'```(.+)\n$', continue_first_line + '\n') \
                or continue_first_line == pre_last_lines[-2]:
            continue_first_line = second_line
            first_line, second_line, new_response_text_lines = get_response_text_lines(new_response_text_lines)

        pre_last_line = pre_last_lines[-1]
        overlap = remove_duplicate_string(pre_last_line, continue_first_line)
        new_response_text = "\n".join(new_response_text_lines)
        if continue_first_line[overlap:] == continue_first_line:
            all_content = response_text + continue_first_line[overlap:] + '\n' + new_response_text
        elif continue_first_line[overlap:] == "":
            all_content = response_text + new_response_text
        else:
            all_content = response_text + continue_first_line[overlap:] + '\n' + new_response_text
        return all_content

    def get_content(self, completion):
        if self.model_data.model_type == LLMType.CHAT_COMPLETION:

            if self.model_data.stream is True:
                return completion["choices"][0]["delta"].get("content", "")
            else:
                return completion["choices"][0]["message"].get("content", "")
        else:
            return completion["choices"][0].get("text", "")

    def update_content(self, completion, content):
        if self.model_data.model_type == LLMType.CHAT_COMPLETION:

            if self.model_data.stream is True:
                completion["choices"][0]["delta"]["content"] = content
            else:
                completion["choices"][0]["message"]["content"] = content
        else:
            completion["choices"]["text"] = content
        return completion

    def correct_completion_data_structure(self, completion):
        """
        Correction response data structure
        : param completion: raw response data
        Return: Corrected response data
        """

        if self.model_data.model_type == LLMType.CHAT_COMPLETION:
            return self.correct_data_structure_chat_completion(completion)
        if self.model_data.model_type == LLMType.COMPLETIONS:
            return self.correct_data_structure_completions(completion)
        if self.model_data.model_type == LLMType.EMBEDDING:
            return self.correct_data_structure_embedding(completion)

    def correct_data_structure_chat_completion(self, completion: dict):
        """
        矫正chat_completion响应数据结构
        :param completion: 原始响应数据
        :return: 矫正后的响应数据
        """
        completion.update(conversation_id=self.model_data.conversation_id)
        return json.dumps(completion)

    def correct_data_structure_completions(self, completion: dict):
        """
        Correcting chat_completion response data structure
        : param completion: raw response data
        Return: Corrected response data
        """
        return json.dumps(completion)

    def correct_data_structure_embedding(self, completion):
        """
        Correcting the embedding response data structure
        : param completion: raw response data
        Return: Corrected response data
        """
        return json.dumps(completion.model_dump())

    def data_record(self, output_text):
        """
        data record
        """
        # The conversation model only records the context
        if self.model_data.model_type == LLMType.CHAT_COMPLETION:
            ConversationService.record_context(model=self.model_data.model_identification,
                                               conversation_id=self.model_data.conversation_id,
                                               req_messages=self.model_data.messages,
                                               response_content=output_text)
        # Record the number of tokens used
        StatisticsTokenService.statistics_token(application_name=self.model_data.application_name,
                                                username=self.model_data.username,
                                                model_identification=self.model_data.model_identification,
                                                user_req_token=self.model_data.token_number.user_req_token,
                                                input_token=self.model_data.token_number.input_token,
                                                output_token=self.model_data.token_number.output_token
                                                )

    @staticmethod
    def process_stream_response_data(res: str):
        """
        The processing flow response data is consistent with the model return
        """
        return f"data: {res}\n\n"

    @staticmethod
    def get_model_stream_res_done():
        """
        The processing flow response data is consistent with the model return
        """
        return "data: [DONE]"
