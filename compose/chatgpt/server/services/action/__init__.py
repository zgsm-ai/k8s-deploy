#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 陈烜 42766
    :时间: 2023/3/24 14:12
    :修改者: 陈烜 42766
    :更新时间: 2023/3/24 14:12
"""
from services.action.add_comment_service import AddCommentCodeStrategy
from services.action.add_debug_code_service import AddDebugCodeStrategy
from services.action.add_stronger_code_service import AddStrongerCodeStrategy
from services.action.api_test_case_service import ApiTestCaseStrategy, ApiTestSingleCaseStrategy, \
    ApiTestGenStepStrategy, ApiTestCaseModifyStrategy, ApiTestCaseRepeatVerifiedStrategy, \
    ApiTestPointDocInspectorStrategy, ApiTestGenODGStrategy, ApiTestParamTypeErrorVerifiedStrategy
from services.action.chat_service import ChatStrategy
from services.action.continue_service import ContinueStrategy
from services.action.explain_code_service import ExplainCodeStrategy
from services.action.advise_service import AdviseStrategy
from services.action.find_bugs_service import FindBugsStrategy
from services.action.generate_api_test_point import GenerateApiTestPointStrategy
from services.action.generate_api_test_set import GenerateApiTestSetStrategy
from services.action.generate_code_service import GenerateCodeStrategy
from services.action.generate_code_by_form_service import GenerateCodeByFormStrategy
from services.action.generate_code_by_ask_service import GenerateCodeByAskStrategy
from services.action.generate_unit_test_service import GenerateUnitTestStrategy
# e2e自动化用例action=============
from services.action.ai_e2e_case_service import AiE2EManualCaseCheckStrategy
from services.action.ai_e2e_case_service import AiE2EIdentifyRelationshipsStrategy
from services.action.ai_e2e_case_service import AiE2EStepIntentExtractStrategy
from services.action.ai_e2e_case_service import AiE2ERagFilterStrategy
from services.action.ai_e2e_case_service import AiE2ECaseGenStrategy
# e2e自动化用例action=============
from services.action.pick_common_func_service import PickCommonFuncStrategy
from services.action.js2ts_service import Js2TsStrategy
from services.action.optimize_code_service import OptimizeCodeStrategy
from services.action.lanjun_classification_service import LanjunClassificationStrategy
from services.action.base_service import ChatbotOptions
from services.action.review_service import ReviewStrategy
from services.action.scribe_dialogue_service import ScribeDialogueStrategy
from services.action.simplify_code_service import SimplifyCodeStrategy
from services.action.give_advice_service import GiveAdviceStrategy
from services.action.zhuge_normal_chat import NormalChatStrategy

strategy_map = {
    FindBugsStrategy.name: FindBugsStrategy,
    GenerateUnitTestStrategy.name: GenerateUnitTestStrategy,
    OptimizeCodeStrategy.name: OptimizeCodeStrategy,
    ExplainCodeStrategy.name: ExplainCodeStrategy,
    GenerateCodeStrategy.name: GenerateCodeStrategy,
    GenerateCodeByFormStrategy.name: GenerateCodeByFormStrategy,
    GenerateCodeByAskStrategy.name: GenerateCodeByAskStrategy,
    Js2TsStrategy.name: Js2TsStrategy,
    LanjunClassificationStrategy.name: LanjunClassificationStrategy,
    ChatStrategy.name: ChatStrategy,
    ApiTestCaseStrategy.name: ApiTestCaseStrategy,
    ApiTestPointDocInspectorStrategy.name: ApiTestPointDocInspectorStrategy,
    ApiTestCaseRepeatVerifiedStrategy.name: ApiTestCaseRepeatVerifiedStrategy,
    ApiTestParamTypeErrorVerifiedStrategy.name: ApiTestParamTypeErrorVerifiedStrategy,
    ApiTestGenODGStrategy.name: ApiTestGenODGStrategy,
    ApiTestCaseModifyStrategy.name: ApiTestCaseModifyStrategy,
    ApiTestGenStepStrategy.name: ApiTestGenStepStrategy,
    ApiTestSingleCaseStrategy.name: ApiTestSingleCaseStrategy,
    AiE2EManualCaseCheckStrategy.name: AiE2EManualCaseCheckStrategy,
    AiE2EIdentifyRelationshipsStrategy.name: AiE2EIdentifyRelationshipsStrategy,
    AiE2EStepIntentExtractStrategy.name: AiE2EStepIntentExtractStrategy,
    AiE2ERagFilterStrategy.name: AiE2ERagFilterStrategy,
    AiE2ECaseGenStrategy.name: AiE2ECaseGenStrategy,
    GenerateApiTestPointStrategy.name: GenerateApiTestPointStrategy,
    GenerateApiTestSetStrategy.name: GenerateApiTestSetStrategy,
    ReviewStrategy.name: ReviewStrategy,
    ScribeDialogueStrategy.name: ScribeDialogueStrategy,  # 在此不做实例化
    AddDebugCodeStrategy.name: AddDebugCodeStrategy,
    AddStrongerCodeStrategy.name: AddStrongerCodeStrategy,
    AddCommentCodeStrategy.name: AddCommentCodeStrategy,
    PickCommonFuncStrategy.name: PickCommonFuncStrategy,
    SimplifyCodeStrategy.name: SimplifyCodeStrategy,
    GiveAdviceStrategy.name: GiveAdviceStrategy,
    ContinueStrategy.name: ContinueStrategy,
    NormalChatStrategy.name: NormalChatStrategy,
    AdviseStrategy.name: AdviseStrategy,

}


def get_action_strategy(action):
    return strategy_map.get(action, ChatStrategy)()


__all__ = [
    'get_action_strategy',
    'ChatbotOptions',
    'strategy_map',
]
