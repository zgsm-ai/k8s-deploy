#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    划词功能验证工具
    脚本中有11个场景，及验证的正则（脚本执行时间长，轮询5次大约需要1H）

    :作者: 黄伟伦z24224
    :时间: 2023/10/21 12:00
    :修改者: 黄伟伦z24224
    :更新时间: 2023/10/21 12:00
"""

import re

import requests

query1 = "为这个表格每一行最后一列增加编辑功能，点击编辑打开抽屉，抽屉内容是一个表单"
selectCode1 = """<template>
    <div v-set-height>
        <IxProTable
            auto-height
            get-key="appName"
            empty-cell="-"
            :spin="spin"
            :columns="columns"
            :data-source="tableList"
            :pagination="pagination"
            :layout-tool="false"
            virtual
            ellipsis>



            <IxAlert slot="header" type="offline" class="con-mb-2">
                {{ $i('sa.control.branch_manage.table.detail_appflow_tips') }}
            </IxAlert>
        </IxProTable>
    </div>
</template>
<script lang="ts" setup>
import type { PostGetVpnFlowTrendReq, GetGetAppFluxStatisticResList } from 'api/bos/vpnStatus.bo';
import VpnStatusApi from 'api/mods/vpnStatus.mod';

import { valueAddUnit } from 'src/util/tool';
import { useIduxTable } from 'portal/hooks';
import { sortEnum } from 'src/module/mod_branch_manage/common/const';

import AppTrend from './trend.vue';

type PropsParams = Partial<PostGetVpnFlowTrendReq & {name: string; startTime: number; endTime: number}>;
const props = withDefaults(defineProps<{
    params: PropsParams;
}>(), {
    params: () => ({})
});

const sortParams = reactive({
    sortField: '',
    sort: ''
});
const columns = [
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_name'),
        dataKey: 'appName',
        minWidth: 120,
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_total'),
        dataKey: 'traffic',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'traffic';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_send'),
        dataKey: 'send',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'send';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_recv'),
        dataKey: 'recv',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'recv';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    }
];

const {
    pagination,
    spin,
    tableList,
    debounceLoadTableData
} = useIduxTable({
    observableParams: computed(() => {
        return {
            sn: props.params.sn,
            tunnelId: props.params.tunnelId,
            startTime: props.params.startTime,
            endTime: props.params.endTime,
            role: props.params.role,
            ...sortParams
        };
    }),
    request: VpnStatusApi.getGetAppFluxStatistic
});


onMounted(() => {
    debounceLoadTableData();
});
</script>"""
generate_code_pattern1 = ["useDrawerForm", "IxForm", r"dataKey: ['\"]operation['\"]"]
description_pattern1 = [r"打开一个抽屉，抽屉内容是表单，展示遮罩，可以点击非抽屉部分关闭抽屉；表单抽屉；内容为表单的抽屉", r"表格编辑功能，编辑后打开抽屉"]

query2 = "在表格头部处增加刷新表格功能"
selectCode2 = """<template>
    <div v-set-height>
        <IxProTable
            auto-height
            get-key="appName"
            empty-cell="-"
            :spin="spin"
            :columns="columns"
            :data-source="tableList"
            :pagination="pagination"
            :layout-tool="false"
            virtual
            ellipsis>



            <IxAlert slot="header" type="offline" class="con-mb-2">
                {{ $i('sa.control.branch_manage.table.detail_appflow_tips') }}
            </IxAlert>
        </IxProTable>
    </div>
</template>
<script lang="ts" setup>
import type { PostGetVpnFlowTrendReq, GetGetAppFluxStatisticResList } from 'api/bos/vpnStatus.bo';
import VpnStatusApi from 'api/mods/vpnStatus.mod';

import { valueAddUnit } from 'src/util/tool';
import { useIduxTable } from 'portal/hooks';
import { sortEnum } from 'src/module/mod_branch_manage/common/const';

import AppTrend from './trend.vue';

type PropsParams = Partial<PostGetVpnFlowTrendReq & {name: string; startTime: number; endTime: number}>;
const props = withDefaults(defineProps<{
    params: PropsParams;
}>(), {
    params: () => ({})
});

const sortParams = reactive({
    sortField: '',
    sort: ''
});
const columns = [
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_name'),
        dataKey: 'appName',
        minWidth: 120,
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_total'),
        dataKey: 'traffic',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'traffic';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_send'),
        dataKey: 'send',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'send';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_recv'),
        dataKey: 'recv',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'recv';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    }
];

const {
    pagination,
    spin,
    tableList,
    debounceLoadTableData
} = useIduxTable({
    observableParams: computed(() => {
        return {
            sn: props.params.sn,
            tunnelId: props.params.tunnelId,
            startTime: props.params.startTime,
            endTime: props.params.endTime,
            role: props.params.role,
            ...sortParams
        };
    }),
    request: VpnStatusApi.getGetAppFluxStatistic
});


onMounted(() => {
    debounceLoadTableData();
});
</script>"""
generate_code_pattern2 = [r"click=['\"]refreshTable['\"]"]
description_pattern2 = [r"点击刷新按钮，表格重新请求数据，并回到表格第一页；表格刷新"]

query3 = "表格增加一列启用以及一列禁用列，支持启用和禁用选中的表格项"
selectCode3 = """<template>
    <div v-set-height>
        <IxProTable
            auto-height
            get-key="appName"
            empty-cell="-"
            :spin="spin"
            :columns="columns"
            :data-source="tableList"
            :pagination="pagination"
            :layout-tool="false"
            virtual
            ellipsis>



            <IxAlert slot="header" type="offline" class="con-mb-2">
                {{ $i('sa.control.branch_manage.table.detail_appflow_tips') }}
            </IxAlert>
        </IxProTable>
    </div>
</template>
<script lang="ts" setup>
import type { PostGetVpnFlowTrendReq, GetGetAppFluxStatisticResList } from 'api/bos/vpnStatus.bo';
import VpnStatusApi from 'api/mods/vpnStatus.mod';

import { valueAddUnit } from 'src/util/tool';
import { useIduxTable } from 'portal/hooks';
import { sortEnum } from 'src/module/mod_branch_manage/common/const';

import AppTrend from './trend.vue';

type PropsParams = Partial<PostGetVpnFlowTrendReq & {name: string; startTime: number; endTime: number}>;
const props = withDefaults(defineProps<{
    params: PropsParams;
}>(), {
    params: () => ({})
});

const sortParams = reactive({
    sortField: '',
    sort: ''
});
const columns = [
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_name'),
        dataKey: 'appName',
        minWidth: 120,
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_total'),
        dataKey: 'traffic',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'traffic';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_send'),
        dataKey: 'send',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'send';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_recv'),
        dataKey: 'recv',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'recv';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    }
];

const {
    pagination,
    spin,
    tableList,
    debounceLoadTableData
} = useIduxTable({
    observableParams: computed(() => {
        return {
            sn: props.params.sn,
            tunnelId: props.params.tunnelId,
            startTime: props.params.startTime,
            endTime: props.params.endTime,
            role: props.params.role,
            ...sortParams
        };
    }),
    request: VpnStatusApi.getGetAppFluxStatistic
});


onMounted(() => {
    debounceLoadTableData();
});
</script>"""
generate_code_pattern3 = [r"click=['\"]handleStatus\(selectedRowKeys",
                          r'const\s*{\s*selectedRowKeys\s*}\s*=\s*useIduxTableSelect\(\)']
description_pattern3 = [r"表格启禁用功能，可以批量操作，也可以单个操作"]

query4 = "抽屉支持编辑和详情状态，点击编辑展示表单，点击取消展示详情内容"
selectCode4 = """<template>
    <IxDrawer
        :visible.sync="drawVisible"
        :class="drawCustomCls"
        :header="drawTitle"
        :mask-closable="wrapperClosable"
        :mask="showDrawerMask"
        :width="640"
        :destroy-on-hide="true"
        :on-after-close="resetRecord">



        <ModifyStrategyForm
            ref="form"
            :record-data="props.recordData"
            :is-edit="stateMap.isEditState" />

        <template #footer>
            <IxButton mode="primary"
                      size="md"
                      :ga-data="$i('global.ok.button')"
                      :loading="saveBtnLoading"
                      @click="save">
                <span>{{ $i('global.ok.button') }}</span>
            </IxButton>
            <IxButton size="md"
                      :ga-data="$i('global.cancel.button')"
                      @click="cancel">
                <span>{{ $i('global.cancel.button') }}</span>
            </IxButton>
        </template>
    </IxDrawer>
</template>

<script lang="ts" setup>
import ModifyStrategyForm from './form.vue';
import { useDrawerForm, useState, DrawerState } from 'portal/hooks';
interface Props {
    visible: boolean;
    state: string;
    recordData: Record<string, any>;
}
const props = withDefaults(defineProps<Props>(), {
    visible: false,
    state: DrawerState.init,
    templateId: ''
});
const emit = defineEmits(['reset-record']);
let {
    drawVisible,
    showDrawerMask,
    wrapperClosable,
    saveBtnLoading,
    form,
    save,
    cancel
} = useDrawerForm(props, emit, { isHiddenDetail: ref(true) });

const resetRecord = () => {
    emit('reset-record');
};
const {state} = toRefs(props);
const {drawCustomCls, drawTitle, stateMap} = useState(state);
</script>"""
generate_code_pattern4 = [r"#footer", r"v-if=['\"]stateMap.isEditState['\"]", r"v-if=['\"]stateMap.isViewState['\"]"]
description_pattern4 = [r"一个可以改变状态的抽屉，点击编辑，抽屉展示表单内容，点击取消，抽屉隐藏表单内容，展示文本详情内容切换状态后抽屉的title也会发生变化；可改变状态的抽屉；改变抽屉的状态"]

query5 = "表格请求数据时，添加加载状态，显示遮罩"
selectCode5 = """<template>
    <div v-set-height>
        <IxProTable
            auto-height
            get-key="appName"
            empty-cell="-"
            :columns="columns"
            :data-source="tableList"
            :pagination="pagination"
            :layout-tool="false"
            virtual
            ellipsis>



            <IxAlert slot="header" type="offline" class="con-mb-2">
                {{ $i('sa.control.branch_manage.table.detail_appflow_tips') }}
            </IxAlert>
        </IxProTable>
    </div>
</template>
<script lang="ts" setup>
import type { PostGetVpnFlowTrendReq, GetGetAppFluxStatisticResList } from 'api/bos/vpnStatus.bo';
import VpnStatusApi from 'api/mods/vpnStatus.mod';

import { valueAddUnit } from 'src/util/tool';
import { useIduxTable } from 'portal/hooks';
import { sortEnum } from 'src/module/mod_branch_manage/common/const';

import AppTrend from './trend.vue';

type PropsParams = Partial<PostGetVpnFlowTrendReq & {name: string; startTime: number; endTime: number}>;
const props = withDefaults(defineProps<{
    params: PropsParams;
}>(), {
    params: () => ({})
});

const sortParams = reactive({
    sortField: '',
    sort: ''
});
const columns = [
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_name'),
        dataKey: 'appName',
        minWidth: 120,
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_total'),
        dataKey: 'traffic',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'traffic';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_send'),
        dataKey: 'send',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'send';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_recv'),
        dataKey: 'recv',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'recv';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    }
];

const {
    pagination,
    tableList,
    debounceLoadTableData
} = useIduxTable({
    observableParams: computed(() => {
        return {
            sn: props.params.sn,
            tunnelId: props.params.tunnelId,
            startTime: props.params.startTime,
            endTime: props.params.endTime,
            role: props.params.role,
            ...sortParams
        };
    }),
    request: VpnStatusApi.getGetAppFluxStatistic
});


onMounted(() => {
    debounceLoadTableData();
});
</script>"""
generate_code_pattern5 = [r"spin=['\"]spin['\"]"]
description_pattern5 = [r"表格在请求数据时，此时表格处于加载状态，并展示遮罩；表格加载状态；表格遮罩"]

query6 = "表格支持选中行"
selectCode6 = """<template>
    <div v-set-height>
        <IxProTable
            auto-height
            get-key="appName"
            empty-cell="-"
            :columns="columns"
            :data-source="tableList"
            :pagination="pagination"
            :layout-tool="false"
            virtual
            ellipsis>



            <IxAlert slot="header" type="offline" class="con-mb-2">
                {{ $i('sa.control.branch_manage.table.detail_appflow_tips') }}
            </IxAlert>
        </IxProTable>
    </div>
</template>
<script lang="ts" setup>
import type { PostGetVpnFlowTrendReq, GetGetAppFluxStatisticResList } from 'api/bos/vpnStatus.bo';
import VpnStatusApi from 'api/mods/vpnStatus.mod';

import { valueAddUnit } from 'src/util/tool';
import { useIduxTable } from 'portal/hooks';
import { sortEnum } from 'src/module/mod_branch_manage/common/const';

import AppTrend from './trend.vue';

type PropsParams = Partial<PostGetVpnFlowTrendReq & {name: string; startTime: number; endTime: number}>;
const props = withDefaults(defineProps<{
    params: PropsParams;
}>(), {
    params: () => ({})
});

const sortParams = reactive({
    sortField: '',
    sort: ''
});
const columns = [
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_name'),
        dataKey: 'appName',
        minWidth: 120,
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_total'),
        dataKey: 'traffic',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'traffic';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_send'),
        dataKey: 'send',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'send';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_recv'),
        dataKey: 'recv',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'recv';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    }
];

const {
    pagination,
    tableList,
    debounceLoadTableData
} = useIduxTable({
    observableParams: computed(() => {
        return {
            sn: props.params.sn,
            tunnelId: props.params.tunnelId,
            startTime: props.params.startTime,
            endTime: props.params.endTime,
            role: props.params.role,
            ...sortParams
        };
    }),
    request: VpnStatusApi.getGetAppFluxStatistic
});


onMounted(() => {
    debounceLoadTableData();
});
</script>"""
generate_code_pattern6 = [r"selected-row-keys.sync=['\"]selectedRowKeys['\"]",
                          r'const\s*{\s*selectedRowKeys\s*}\s*=\s*useIduxTableSelect\(\)']
description_pattern6 = [r"记录表格选中的行，将已选中的行，同步记录在selectedRowKeys里；表格选中行；表格勾选项；表格已选中的数据；选中条数：0"]

query7 = "表格支持勾选，并能清除勾选"
selectCode7 = """<template>
    <div v-set-height>
        <IxProTable
            auto-height
            get-key="appName"
            empty-cell="-"
            :columns="columns"
            :data-source="tableList"
            :pagination="pagination"
            :layout-tool="false"
            virtual
            ellipsis>

            <IxAlert slot="header" type="offline" class="con-mb-2">
                {{ $i('sa.control.branch_manage.table.detail_appflow_tips') }}
            </IxAlert>
        </IxProTable>
    </div>
</template>
<script lang="ts" setup>
import type { PostGetVpnFlowTrendReq, GetGetAppFluxStatisticResList } from 'api/bos/vpnStatus.bo';
import VpnStatusApi from 'api/mods/vpnStatus.mod';

import { valueAddUnit } from 'src/util/tool';
import { useIduxTable } from 'portal/hooks';
import { sortEnum } from 'src/module/mod_branch_manage/common/const';

import AppTrend from './trend.vue';

type PropsParams = Partial<PostGetVpnFlowTrendReq & {name: string; startTime: number; endTime: number}>;
const props = withDefaults(defineProps<{
    params: PropsParams;
}>(), {
    params: () => ({})
});

const sortParams = reactive({
    sortField: '',
    sort: ''
});
const columns = [
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_name'),
        dataKey: 'appName',
        minWidth: 120,
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_total'),
        dataKey: 'traffic',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'traffic';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_send'),
        dataKey: 'send',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'send';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_recv'),
        dataKey: 'recv',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'recv';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    }
];

const {
    pagination,
    tableList,
    debounceLoadTableData
} = useIduxTable({
    observableParams: computed(() => {
        return {
            sn: props.params.sn,
            tunnelId: props.params.tunnelId,
            startTime: props.params.startTime,
            endTime: props.params.endTime,
            role: props.params.role,
            ...sortParams
        };
    }),
    request: VpnStatusApi.getGetAppFluxStatistic
});


onMounted(() => {
    debounceLoadTableData();
});
</script>"""
generate_code_pattern7 = [r"@click=['\"]clearSelect['\"]", r"selected-row-keys.sync=['\"]selectedRowKeys['\"]",
                          r'const { selectedRowKeys(.*?)clearSelect } = useIduxTableSelect\(\);']
description_pattern7 = [r"清除表格所有勾选项状态，将已勾选的表格行状态设置为未勾选；清除表格已勾选行；清除表格已勾选数据；清除表格勾选项"]

query8 = "表格增加姓名、年龄、性别，支持伸缩宽度，且年龄支持排序"
selectCode8 = """<template>
    <div v-set-height>
        <IxProTable
            auto-height
            get-key="appName"
            empty-cell="-"
            :columns="columns"
            :data-source="tableList"
            :pagination="pagination"
            :layout-tool="false"
            virtual
            ellipsis>



            <IxAlert slot="header" type="offline" class="con-mb-2">
                {{ $i('sa.control.branch_manage.table.detail_appflow_tips') }}
            </IxAlert>
        </IxProTable>
    </div>
</template>
<script lang="ts" setup>
import type { PostGetVpnFlowTrendReq, GetGetAppFluxStatisticResList } from 'api/bos/vpnStatus.bo';
import VpnStatusApi from 'api/mods/vpnStatus.mod';

import { valueAddUnit } from 'src/util/tool';
import { useIduxTable } from 'portal/hooks';
import { sortEnum } from 'src/module/mod_branch_manage/common/const';

import AppTrend from './trend.vue';

type PropsParams = Partial<PostGetVpnFlowTrendReq & {name: string; startTime: number; endTime: number}>;
const props = withDefaults(defineProps<{
    params: PropsParams;
}>(), {
    params: () => ({})
});

const sortParams = reactive({
    sortField: '',
    sort: ''
});
const columns = [
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_name'),
        dataKey: 'appName',
        minWidth: 120,
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_total'),
        dataKey: 'traffic',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'traffic';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_send'),
        dataKey: 'send',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'send';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    },
    {
        title: $i('sa.control.branch_manage.table.detail_appflow_table_recv'),
        dataKey: 'recv',
        customCell: ({ value }) => {
            return valueAddUnit(value.value, value.unit);
        },
        sortable: {
            onChange: currOrderBy => {
                sortParams.sort = sortEnum[currOrderBy] ?? '';
                sortParams.sortField = 'recv';
            }
        },
        minWidth: 100,
        align: 'end',
        resizable: true,
    }
];

const {
    pagination,
    tableList,
    debounceLoadTableData
} = useIduxTable({
    observableParams: computed(() => {
        return {
            sn: props.params.sn,
            tunnelId: props.params.tunnelId,
            startTime: props.params.startTime,
            endTime: props.params.endTime,
            role: props.params.role,
            ...sortParams
        };
    }),
    request: VpnStatusApi.getGetAppFluxStatistic
});


onMounted(() => {
    debounceLoadTableData();
});
</script>"""
generate_code_pattern8 = [r'(gender|性别)', r"sortable", r"traffic"]
description_pattern8 = [r"表格】"]

query9 = "编写一个表单抽屉，表单内容是姓名、年龄、性别，支持提交表单并显示遮罩"
selectCode9 = ""
generate_code_pattern9 = [r'(gender|性别)', r":mask=['\"]showDrawerMask['\"]", r":loading=['\"]saveBtnLoading['\"]"]
description_pattern9 = [r"点击确认将提交抽屉的表单数据，对表单进行校验及发起请求，确定按钮状态将变为提交中，知道提交请求完成；表单抽屉的提交；提交表单抽屉的数据；表单抽屉保存数据",
                        r"打开一个抽屉，抽屉内容是表单，展示遮罩，可以点击非抽屉部分关闭抽屉；表单抽屉；内容为表单的抽屉"]

query10 = "生成一个表单，包含性别、年龄、姓名三个表单项"
selectCode10 = ""
generate_code_pattern10 = [r'(gender|性别)', r"<IxForm "]
description_pattern10 = [r"表单】"]

query11 = "为这个表单增加姓名、年薪、身高表单项"
selectCode11 = """<template>
    <IxForm ref="form"
            v-auto-form
            class="wan-form"
            :control="formGroup"
            message-tooltip>
        <div class="common-form-title--bar">
            {{ $i('sa.control.network_interface.share.wan.form.subtitle_base_info') }}
        </div>
        <IxFormItem :label="$i('sa.control.network_interface.share.wan.form.name')">
            <IxInput trim control="name" :placeholder="$i('common.placeholder.input')" />
        </IxFormItem>
        <IxFormItem :label="$i('sa.control.network_interface.share.wan.form.desc')">
            <IxInput trim control="desc" :placeholder="$i('common.placeholder.optional')" />
        </IxFormItem>
        <div class="common-form-title--bar">
            {{ $i('sa.control.network_interface.share.wan.form.subtitle_bandwidth') }}
        </div>
        <IxFormItem :label="$i('sa.control.network_interface.share.wan.form.up')">
            <IxInputNumber :min="1"
                           :max="32000"
                           :step="100"
                           :precision="0"
                           control="bandwidthUpValue">
                <template #addonAfter>
                    <IxSelect class="con-w-[100px]"
                              :data-source="BandWidthTypeArray"
                              control="bandwidthUpUnit" />
                </template>
            </IxInputNumber>
        </IxFormItem>
        <IxFormItem :label="$i('sa.control.network_interface.share.wan.form.down')">
            <IxInputNumber :min="1"
                           :max="32000"
                           :step="100"
                           :precision="0"
                           control="bandwidthDownValue">
                <template #addonAfter>
                    <IxSelect class="con-w-[100px]"
                              :data-source="BandWidthTypeArray"
                              control="bandwidthDownUnit" />
                </template>
            </IxInputNumber>
        </IxFormItem>
        <div class="common-form-title--bar">
            {{ $i('sa.control.network_interface.share.wan.form.subtitle_scope') }}
        </div>
        <IxFormItem :label="$i('sa.control.network_interface.share.wan.form.subtitle_scope')">
            <BranchDeviceSelectTree control="applyScope"
                                    size="md"
                                    get-key="id"
                                    :placeholder="$i('global.select.dropdown')"
                                    :tree-disabled="isTreeDisabled" />
        </IxFormItem>
    </IxForm>
</template>



<script setup lang="ts">
import pick from 'lodash-es/pick';
import { DrawerState } from 'src/hooks/use_idux_drawer/const';
import {useFormGroup, Validators} from 'portal/idux';
import {BAND_WIDTH_UNIT, MovePort, DEFAULT_BAND_WIDTH_VALUE, BandWidthTypeArray} from '../const';
import { devVersionOverReq } from 'src/util/tool';
import { nameValidator } from 'src/util/ix_validator';
import BranchDeviceSelectTree from 'src/module/mod_config_update_log/comp/branch_device_select_tree.vue';
import { GetDeviceTreeResDefDeviceTreeData } from 'src/api/bos/showbranch.bo';
import NetworkinterfaceApi from 'api/mods/networkinterface.mod';

const props = withDefaults(defineProps<{
    record?: {id: string};
    state: DrawerState;
}>(), {
    state: DrawerState.add
});

const { required, rangeLength, maxLength } = Validators;

const formGroup = useFormGroup({
    name: ['', [required, nameValidator, rangeLength(1, 20)]],
    desc: ['', [nameValidator, maxLength(100)]],
    bandwidthUpValue: [DEFAULT_BAND_WIDTH_VALUE.up, required],
    bandwidthUpUnit: [BAND_WIDTH_UNIT.Mbps, required],
    bandwidthDownValue: [DEFAULT_BAND_WIDTH_VALUE.down, required],
    bandwidthDownUnit: [BAND_WIDTH_UNIT.Mbps, required],
    applyScope: [[] as string[]]
});

const wanList = shallowRef<string[]>([]);  // 可选wan列表
const selectedList = shallowRef<string[]>([]);  // 在其他地方已选的列表
const detailScopes = shallowRef<string[]>([]);  // 当前编辑已选的分支

const fetchDetail = async () => {
    const formData = await NetworkinterfaceApi.getNetworkinterfaceshare({id: props.record?.id || ''});
    const formatData = pick(formData, ['applyScope', 'desc', 'name']);
    formData.bandwidth.forEach(bandWidth => {
        if (bandWidth.type === MovePort.up) {
            formatData.bandwidthUpValue = bandWidth.value;
            formatData.bandwidthUpUnit = bandWidth.unit;
        } else {
            formatData.bandwidthDownValue = bandWidth.value;
            formatData.bandwidthDownUnit = bandWidth.unit;
        }
    });
    detailScopes.value = formData.applyScope || [];
    formGroup.setValue(formatData);
};

const fetchFilterBranch = async () => {
    const res = await NetworkinterfaceApi.getSnfilter();
    selectedList.value = res.selectedList || [];
    wanList.value = res.wanList || [];
};

const isTreeDisabled = (node: GetDeviceTreeResDefDeviceTreeData & {
    disabledTip?: string;
}) => {
    node.disabledTip = '';
    if (detailScopes.value.includes(node.id)) {  // 优先级高：已经选过的不禁用
        return false;
    }
    if (node.isLeaf) {  // 叶子节点情况
        if (!wanList.value.includes(node.id)) {    // 无开通wan口的分支不可再选
            node.disabledTip = $i('sa.control.network_interface.share.wan.form.subtitle_scope_disable_no_open_wan');
        }
        if (selectedList.value.includes(node.id)) {    // 在其他地方选了分支不可再选
            node.disabledTip = $i('sa.control.network_interface.share.wan.form.subtitle_scope_disable_has_wan');
        }
        if (!devVersionOverReq(node.softVer)) {   // 版本号过低不可选
            node.disabledTip = $i('sa.control.branch_manage.tree.node_disabled_tip');
        }
    } else {
        // @ts-ignore
        if (!node.children?.length || node.children.every(item => item.disabledTip)) {  // 没有子项不可选择
            node.disabledTip = $i('sa.control.device_controller.ip_address_orch_tab_custom_form_branch_empty_err_tip');
        }
    }
    return !!node.disabledTip;
};

const isValid = () => {
    if (!formGroup.valid.value) {
        formGroup.markAsDirty();
        return false;
    }
    return true;
};

const formRequest = () => {
    const formData = formGroup.getValue();
    const payload = pick(formData, ['applyScope', 'desc', 'name']);
    payload.bandwidth = [
        {type: MovePort.up, value: formData.bandwidthUpValue, unit: formData.bandwidthUpUnit},
        {type: MovePort.down, value: formData.bandwidthDownValue, unit: formData.bandwidthDownUnit}
    ];
    if (props.state === DrawerState.edit) {
        return NetworkinterfaceApi.putNetworkinterfaceshare({...payload, id: props.record?.id});
    } else if (props.state === DrawerState.add) {
        // todo: interface写死sd-wan,下个版本再放开
        return NetworkinterfaceApi.postNetworkinterfaceshare({...payload, interface: 'WAN'});
    }
};

onMounted(() => {
    if (props.state === DrawerState.edit) {
        fetchDetail();
    }
    fetchFilterBranch();
});

defineExpose({
    isValid,
    formRequest
});
</script>

<style lang="less" scoped>
.wan-form {
    .ix-form-item {
        flex-wrap: nowrap;
        margin-bottom: 8px;
    }
}
</style>"""
generate_code_pattern11 = [r"(salary|年薪)"]
description_pattern11 = [r"表格】"]

merge_code_pattern = [r"...existing", r"...Existing", r'\/\/\s\.\.\.', r"<!-- ... -->", r"// Existing", r"!-- Existing",
                      r"// ...原有代码..."]
type_name_map = {'vector_recall': "向量召回描述", 'filter_desc': "过滤向量描述", 'generate_code': "生成代码", 'merge_code': "合并代码/还原代码"}


class ScribeCopilot:

    def __init__(self):
        self.verification_result = {}
        self.server_url = "http://10.65.134.104:5002"
        self.server_url_prod = "https://chatgpt.sangfor.com"
        self.api_key = "MTU2ODQ6cWlhbmxpdWFwaWtleTrpu4TkvJ/kvKZ6MjQyMjQ6MTcxMzM="
        self.headers = {
            'api-Key': self.api_key,
            'Content-Type': 'application/json'
        }

    def scribe_response(self, scene_id, code, host, language="vue"):
        """调用划词接口"""
        body = {
            "language": language,
            "code": code,
            "custom_instructions": "",
            "prompt": eval(f"query{scene_id}"),
            "action": "scribe",
            "stream": False,
            "collection_list": ["sase", "idux"]
        }
        self.headers.update({"action": "scribe"})
        response = requests.post(f"{host}/api/v2/completion", headers=self.headers, json=body)
        return response.json()

    def scribe_example(self, scene_id, host, response_id):
        """
        获取：向量库匹配的示例、gpt筛选后的示例、生成的代码、合并之后的代码
        通过detection检测数据是否符合要求
        """
        params = {
            "action": "scribe",
            "response_id": response_id,
            "prompt": eval(f"query{scene_id}")
        }
        response = requests.get(f"{host}/api/ai_record/actions", headers=self.headers, params=params).json()
        middle_process_records = response["data"][0]["middle_process_records"]
        desc_list = []
        for record in middle_process_records:

            if record["type"] == "vector_recall":
                desc_list = [string.strip().split('\n')[0] for string in record["result"]]
                self.detection("\n".join(desc_list), eval(f"description_pattern{scene_id}"), scene_id, record["type"])
            elif record["type"] == "filter_desc":
                query_number = record["result"].split('、')
                if query_number[0].isdigit():
                    try:
                        serial_list = list(map(int, query_number))
                    except ValueError:
                        pattern = r'^\d+'  # 匹配每一行的第一个数字
                        matches = re.findall(pattern, record["result"], re.MULTILINE)
                        serial_list = list(map(int, matches))
                    if serial_list:
                        content = "\n".join([desc_list[serial - 1] for serial in serial_list])
                        self.detection(content, eval(f"description_pattern{scene_id}"), scene_id, record["type"])
            elif record["type"] == "generate_code":
                self.detection(record["result"], eval(f"generate_code_pattern{scene_id}"), scene_id, record["type"])
            elif record["type"] == "merge_code":
                self.detection(record["result"], merge_code_pattern, scene_id, record["type"],
                               eval(f"generate_code_pattern{scene_id}"))
            else:
                pass

    def detection(self, content, pattern_list, scene_id, record_type, pattern_code_list=None):
        """
        验证对应场景的
        1、验证向量库匹配的示例描述是否准确
        2、验证gpt筛选的top5示例是否有包含期望示例
        3、验证生成的代码是否包含了核心部分
        4、验证合并后的代码是否还存在省略部分
        向verification_result中添加处理结果
        """
        detection_result = True
        if record_type == "merge_code":
            for pattern in pattern_list:
                if re.findall(pattern, content, re.DOTALL):
                    detection_result = False
            for pattern in pattern_code_list:
                if not re.findall(pattern, content, re.DOTALL):
                    detection_result = False
        else:
            for pattern in pattern_list:
                try:
                    if not re.findall(pattern, content, re.DOTALL):
                        detection_result = False
                except Exception as err:
                    print(f"错误： {err}， ", {"content": content})
                    detection_result = False
        # 记录结果，scene—{scene_id}：{record_type}：[detection_result]
        self.verification_result[f"scene—{scene_id}"] = self.verification_result.get(f"scene—{scene_id}", {})
        self.verification_result[f"scene—{scene_id}"][record_type] = self.verification_result[f"scene—{scene_id}"].get(
            record_type, [])
        self.verification_result[f"scene—{scene_id}"][record_type].append(detection_result)

    def polling_detection(self, env, poll_num):
        """轮询检测，记录结果"""
        for num in range(poll_num):
            for scene_id in range(1, 12):
                print(f"当前轮询次数{num + 1}，当前场景：{scene_id}， query:", eval(f"query{scene_id}"))
                select_code = eval(f"selectCode{scene_id}")
                host = self.server_url
                if env == "prod":
                    host = self.server_url_prod
                try:
                    response = self.scribe_response(scene_id, select_code, host)
                    response_id = response["data"]["id"]
                    print("response_id: ", response_id)
                    self.scribe_example(scene_id, host, response_id)
                except Exception as err:
                    print(f"场景{scene_id}生成代码失败, 错误： {err}")
        return self.verification_result


if __name__ == '__main__':
    # 执行方式，当前目录  python .\common\utils\scribe_scene_verification.py test 1
    import sys

    # 获取命令行参数
    args = sys.argv
    # 第一个参数是脚本的名称，忽略它
    # 第二个参数是 执行环境 prod|test
    # 第三个参数是 轮询次数 5
    env = "prod"
    poll_num = 5
    if len(args) > 1:
        env = args[1]
        poll_num = int(args[2])
    copilot = ScribeCopilot()
    verification_result = copilot.polling_detection(env, poll_num)
    print("verification_result: ", verification_result)
    for scene, result in verification_result.items():
        # type_name_map
        for k, v in result.items():
            if not all(v):
                print(f"场景{scene}中{type_name_map[k]}不合格")
