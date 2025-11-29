# 测试用例文档

> 生成时间: 2025-11-29 13:22:47
> 接口数量: 14
> 用例总数: 98

---

## API: GET /v1/config-templates

**接口说明**: 采集指纹模板分页 - 分页查询采集指纹模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-001 | 正常分页查询-默认参数 | 系统中存在模板数据 | params={} (必填), page和perPage使用默认值 | 200, 返回PageDataHandBook结构，包含data数组、totalCount、pageCount等 | P0 |
| TC-002 | 正常分页查询-指定页码和每页数量 | 系统中存在模板数据 | params={}, page=2, perPage=20 | 200, 返回第2页数据，每页20条 | P0 |
| TC-003 | 正常查询-带筛选条件templateName | 系统中存在指定名称模板 | params={"templateName": "测试模板"}, page=1, perPage=10 | 200, 返回符合模板名称条件的数据 | P0 |
| TC-004 | 正常查询-带筛选条件isUse | 系统中存在启用/禁用模板 | params={"isUse": "1"}, page=1, perPage=10 | 200, 返回启用状态的模板 | P1 |
| TC-005 | 正常查询-带排序参数 | 系统中存在多条模板 | params={"field": "createTime", "order": "desc"} | 200, 按创建时间降序返回 | P1 |
| TC-006 | 异常-缺少必填参数params | 无 | 不传params参数 | 400, 提示params参数必填 | P0 |
| TC-007 | 边界-page为0 | 系统中存在模板数据 | params={}, page=0, perPage=10 | 400或返回第1页数据(根据实现) | P1 |
| TC-008 | 边界-page为负数 | 系统中存在模板数据 | params={}, page=-1, perPage=10 | 400, 参数错误 | P1 |
| TC-009 | 边界-perPage为0 | 系统中存在模板数据 | params={}, page=1, perPage=0 | 400, 参数错误 | P1 |
| TC-010 | 边界-perPage超大值 | 系统中存在模板数据 | params={}, page=1, perPage=10000 | 200, 返回数据或限制最大值 | P2 |
| TC-011 | 边界-page类型错误 | 无 | params={}, page="abc" | 400, 类型错误 | P1 |
| TC-012 | 边界-空数据查询 | 系统中无模板数据 | params={}, page=1, perPage=10 | 200, data为空数组，totalCount=0 | P1 |

---

## API: PUT /v1/config-templates

**接口说明**: 编辑模板 - 编辑基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-013 | 正常编辑模板-更新模板名称 | 存在待编辑的模板 | {"pkCollectTemplate": "existing-id", "templateName": "新模板名称", "templateVer": "1.0"} | 200, success=true, 返回更新后的模板信息 | P0 |
| TC-014 | 正常编辑模板-更新模板描述 | 存在待编辑的模板 | {"pkCollectTemplate": "existing-id", "templateDesc": "更新后的描述"} | 200, success=true | P0 |
| TC-015 | 正常编辑模板-更新多个字段 | 存在待编辑的模板 | {"pkCollectTemplate": "existing-id", "templateName": "名称", "templateDesc": "描述", "templateType": 1} | 200, success=true | P1 |
| TC-016 | 异常-缺少请求体 | 无 | 不传requestBody | 400, 请求体必填 | P0 |
| TC-017 | 异常-空请求体 | 无 | {} | 400, 缺少必要字段 | P0 |
| TC-018 | 异常-模板ID不存在 | 无对应ID的模板 | {"pkCollectTemplate": "non-existing-id", "templateName": "测试"} | 404或400, 模板不存在 | P0 |
| TC-019 | 边界-templateName为空字符串 | 存在待编辑的模板 | {"pkCollectTemplate": "existing-id", "templateName": ""} | 400, 模板名称不能为空 | P1 |
| TC-020 | 边界-templateName超长 | 存在待编辑的模板 | {"pkCollectTemplate": "existing-id", "templateName": "A"*500} | 400, 名称长度超限 | P2 |
| TC-021 | 边界-templateName包含特殊字符 | 存在待编辑的模板 | {"pkCollectTemplate": "existing-id", "templateName": "<script>alert(1)</script>"} | 400或200(XSS过滤) | P1 |
| TC-022 | 异常-templateType类型错误 | 存在待编辑的模板 | {"pkCollectTemplate": "existing-id", "templateType": "invalid"} | 400, 类型错误 | P1 |
| TC-023 | 异常-请求体格式错误 | 无 | 非JSON格式字符串 | 400, JSON解析错误 | P1 |

---

## API: POST /v1/config-templates

**接口说明**: 添加模板 - 添加基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-024 | 正常添加模板-必填字段 | 无 | {"templateName": "新模板", "templateVer": "1.0"} | 200, success=true, 返回新建模板信息含ID | P0 |
| TC-025 | 正常添加模板-全部字段 | 无 | {"templateName": "完整模板", "templateVer": "1.0", "templateDesc": "描述", "templateType": 1, "isDefault": 0, "isUse": 1} | 200, success=true | P0 |
| TC-026 | 异常-缺少请求体 | 无 | 不传requestBody | 400, 请求体必填 | P0 |
| TC-027 | 异常-空请求体 | 无 | {} | 400, 缺少必要字段 | P0 |
| TC-028 | 异常-模板名称重复 | 已存在同名模板 | {"templateName": "已存在的模板名"} | 400, 模板名称已存在 | P0 |
| TC-029 | 边界-templateName为空字符串 | 无 | {"templateName": ""} | 400, 模板名称不能为空 | P1 |
| TC-030 | 边界-templateName只有空格 | 无 | {"templateName": "   "} | 400, 模板名称不能为空 | P1 |
| TC-031 | 边界-templateName超长 | 无 | {"templateName": "A"*500} | 400, 名称长度超限 | P2 |
| TC-032 | 边界-templateDesc超长 | 无 | {"templateName": "测试", "templateDesc": "A"*5000} | 400或200(截断) | P2 |
| TC-033 | 异常-templateType无效值 | 无 | {"templateName": "测试", "templateType": 999} | 400, 类型值无效 | P1 |

---

## API: DELETE /v1/config-templates/{templateId}

**接口说明**: 删除模板 - 删除基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-034 | 正常删除模板 | 存在待删除的模板 | templateId="existing-template-id" | 200, success=true | P0 |
| TC-035 | 异常-模板ID不存在 | 无 | templateId="non-existing-id" | 404或400, 模板不存在 | P0 |
| TC-036 | 异常-模板ID为空 | 无 | templateId="" | 404或400, 路径错误 | P0 |
| TC-037 | 异常-删除默认模板 | 存在默认模板 | templateId="default-template-id" | 400, 不能删除默认模板 | P1 |
| TC-038 | 异常-删除正在使用的模板 | 模板被任务引用 | templateId="in-use-template-id" | 400, 模板正在使用中 | P1 |
| TC-039 | 边界-templateId包含特殊字符 | 无 | templateId="<script>" | 400, ID格式无效 | P2 |
| TC-040 | 边界-templateId为SQL注入 | 无 | templateId="1' OR '1'='1" | 400, ID格式无效(防注入) | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/enable

**接口说明**: 启用模板 - 启用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-041 | 正常启用模板 | 存在禁用状态的模板 | templateId="disabled-template-id" | 200, success=true, 模板状态变为启用 | P0 |
| TC-042 | 正常-对已启用模板再次启用 | 模板已是启用状态 | templateId="enabled-template-id" | 200, success=true(幂等) | P1 |
| TC-043 | 异常-模板ID不存在 | 无 | templateId="non-existing-id" | 404或400, 模板不存在 | P0 |
| TC-044 | 异常-模板ID为空 | 无 | templateId="" | 404, 路径错误 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/disable

**接口说明**: 禁用模板 - 禁用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-045 | 正常禁用模板 | 存在启用状态的模板 | templateId="enabled-template-id" | 200, success=true, 模板状态变为禁用 | P0 |
| TC-046 | 正常-对已禁用模板再次禁用 | 模板已是禁用状态 | templateId="disabled-template-id" | 200, success=true(幂等) | P1 |
| TC-047 | 异常-模板ID不存在 | 无 | templateId="non-existing-id" | 404或400, 模板不存在 | P0 |
| TC-048 | 异常-禁用默认模板 | 存在默认模板 | templateId="default-template-id" | 400, 不能禁用默认模板 | P1 |
| TC-049 | 异常-禁用正在使用的模板 | 模板被任务引用 | templateId="in-use-template-id" | 400, 模板正在使用中无法禁用 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/default

**接口说明**: 设置默认模板 - 将指定模板设置为默认

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-050 | 正常设置默认模板 | 存在非默认模板 | templateId="normal-template-id" | 200, success=true, 该模板成为默认 | P0 |
| TC-051 | 正常-对已是默认的模板设置 | 模板已是默认 | templateId="current-default-id" | 200, success=true(幂等) | P1 |
| TC-052 | 异常-模板ID不存在 | 无 | templateId="non-existing-id" | 404或400, 模板不存在 | P0 |
| TC-053 | 异常-设置禁用模板为默认 | 模板处于禁用状态 | templateId="disabled-template-id" | 400, 禁用模板不能设为默认 | P1 |

---

## API: GET /v1/config-templates/{templateId}/{optType}/basic

**接口说明**: 查询模板基本信息 - 根据模板ID查询模板基本信息

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-054 | 正常查询模板基本信息 | 存在对应模板 | templateId="existing-id", optType="view" | 200, 返回模板基本信息 | P0 |
| TC-055 | 正常查询-不同optType | 存在对应模板 | templateId="existing-id", optType="edit" | 200, 返回对应操作类型的信息 | P1 |
| TC-056 | 异常-模板ID不存在 | 无 | templateId="non-existing-id", optType="view" | 404或400, 模板不存在 | P0 |
| TC-057 | 异常-optType无效 | 存在对应模板 | templateId="existing-id", optType="invalid" | 400, optType无效 | P1 |
| TC-058 | 异常-参数缺失 | 无 | 缺少templateId或optType | 404, 路径错误 | P1 |

---

## API: GET /v1/config-templates/{templateId}/list

**接口说明**: 查询模板指纹列表 - 分页查询模板下的指纹列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-059 | 正常查询指纹列表-默认分页 | 模板下存在指纹 | templateId="existing-id" | 200, 返回PageDataCheckitem，默认第1页10条 | P0 |
| TC-060 | 正常查询-指定分页参数 | 模板下存在指纹 | templateId="existing-id", page=2, perPage=20 | 200, 返回第2页20条数据 | P0 |
| TC-061 | 正常查询-带筛选checkItemName | 模板下存在指纹 | templateId="existing-id", checkItemName="密码策略" | 200, 返回符合条件的指纹 | P1 |
| TC-062 | 正常查询-带筛选riskLevel | 模板下存在指纹 | templateId="existing-id", riskLevel="high" | 200, 返回高风险指纹 | P1 |
| TC-063 | 正常查询-带排序 | 模板下存在指纹 | templateId="existing-id", field="createTime", order="desc" | 200, 按时间降序返回 | P1 |
| TC-064 | 异常-模板ID不存在 | 无 | templateId="non-existing-id" | 404或400, 模板不存在 | P0 |
| TC-065 | 边界-模板下无指纹 | 模板存在但无指纹 | templateId="empty-template-id" | 200, data为空数组 | P1 |

---

## API: GET /v1/config-templates/choose

**接口说明**: 指纹分页列表 - 查询指纹分页列表（已选/未选）

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-066 | 正常查询-已选指纹 | 存在已选指纹 | tempId="template-id", selected="1" | 200, 返回已选中的指纹列表 | P0 |
| TC-067 | 正常查询-未选指纹 | 存在未选指纹 | tempId="template-id", selected="0" | 200, 返回未选中的指纹列表 | P0 |
| TC-068 | 正常查询-按指纹类型筛选 | 存在不同类型指纹 | fingerType="baseline" | 200, 返回指定类型指纹 | P1 |
| TC-069 | 正常查询-按资产类型筛选 | 存在不同资产类型 | assetTypeCode="linux" | 200, 返回Linux相关指纹 | P1 |
| TC-070 | 正常查询-组合筛选 | 存在符合条件数据 | tempId="id", selected="1", fingerType="baseline", checkItemName="密码" | 200, 返回符合所有条件的指纹 | P1 |
| TC-071 | 边界-无匹配数据 | 无 | checkItemName="不存在的名称" | 200, data为空数组 | P1 |

---

## API: PUT /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加全部指纹 - 为模板添加全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-072 | 正常添加全部指纹 | 存在模板和待添加指纹 | templateId="existing-id", body={} | 200, success=true, 返回添加数量 | P0 |
| TC-073 | 异常-模板ID不存在 | 无 | templateId="non-existing-id", body={} | 404或400, 模板不存在 | P0 |
| TC-074 | 边界-无可添加指纹 | 所有指纹已添加 | templateId="full-template-id", body={} | 200, entity=0 | P1 |
| TC-075 | 异常-缺少请求体 | 存在模板 | templateId="existing-id", 无body | 400, 请求体必填 | P1 |

---

## API: PATCH /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加选中指纹 - 为模板添加选中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-076 | 正常添加选中指纹 | 存在模板和待添加指纹 | templateId="existing-id", body={"ids": ["finger-1", "finger-2"]} | 200, success=true, 返回添加数量 | P0 |
| TC-077 | 异常-模板ID不存在 | 无 | templateId="non-existing-id", body={"ids": ["finger-1"]} | 404或400, 模板不存在 | P0 |
| TC-078 | 异常-指纹ID不存在 | 存在模板 | templateId="existing-id", body={"ids": ["non-existing-finger"]} | 400, 指纹不存在 | P1 |
| TC-079 | 边界-空选择列表 | 存在模板 | templateId="existing-id", body={"ids": []} | 200, entity=0或400 | P1 |
| TC-080 | 边界-重复添加已有指纹 | 指纹已存在于模板 | templateId="existing-id", body={"ids": ["already-added"]} | 200, 幂等处理或返回0 | P2 |

---

## API: PUT /v1/config-templates/temps/{templateId}

**接口说明**: 删除全部指纹 - 删除模板中的全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-081 | 正常删除全部指纹 | 模板中存在指纹 | templateId="existing-id", body={} | 200, success=true, 返回删除数量 | P0 |
| TC-082 | 异常-模板ID不存在 | 无 | templateId="non-existing-id", body={} | 404或400, 模板不存在 | P0 |
| TC-083 | 边界-模板无指纹 | 模板中无指纹 | templateId="empty-template-id", body={} | 200, entity=0 | P1 |

---

## API: PATCH /v1/config-templates/temps/{templateId}

**接口说明**: 批量删除指纹 - 批量删除模板中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-084 | 正常批量删除指纹 | 模板中存在待删除指纹 | templateId="existing-id", body={"ids": ["finger-1", "finger-2"]} | 200, success=true, 返回删除数量 | P0 |
| TC-085 | 异常-模板ID不存在 | 无 | templateId="non-existing-id", body={"ids": ["finger-1"]} | 404或400, 模板不存在 | P0 |
| TC-086 | 异常-指纹ID不存在 | 存在模板 | templateId="existing-id", body={"ids": ["non-existing"]} | 400或200(部分成功) | P1 |
| TC-087 | 边界-空删除列表 | 存在模板 | templateId="existing-id", body={"ids": []} | 200, entity=0或400 | P1 |

---

## API: POST /v1/config-templates/isExist

**接口说明**: 唯一性校验 - 校验模板名称是否重复

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-088 | 正常校验-名称不存在 | 无同名模板 | checkType="name", checkValue="新模板", id="" | 200, entity=false(不存在) | P0 |
| TC-089 | 正常校验-名称已存在 | 存在同名模板 | checkType="name", checkValue="已存在模板", id="" | 200, entity=true(已存在) | P0 |
| TC-090 | 正常校验-编辑时排除自身 | 编辑已有模板 | checkType="name", checkValue="当前模板名", id="current-id" | 200, entity=false(排除自身) | P0 |
| TC-091 | 异常-缺少checkType | 无 | checkValue="测试", id="" | 400, checkType必填 | P0 |
| TC-092 | 异常-缺少checkValue | 无 | checkType="name", id="" | 400, checkValue必填 | P0 |
| TC-093 | 异常-缺少id | 无 | checkType="name", checkValue="测试" | 400, id必填 | P0 |
| TC-094 | 边界-checkValue为空字符串 | 无 | checkType="name", checkValue="", id="" | 400或200, entity=false | P1 |

---

## API: GET /v1/config-template/globalConf

**接口说明**: 获取全局配置 - 获取基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-095 | 正常获取全局配置 | 系统已初始化 | 无参数 | 200, 返回TaskGlobalConfig对象 | P0 |

---

## API: POST /v1/config-template/globalConf

**接口说明**: 保存全局配置 - 保存基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-096 | 正常保存全局配置 | 无 | {"saveOriginalResult": true, "pageShowOriginalResult": false, "enableAssetTypeCheck": true, "originalResultSaveType": 1, "taskRedundancyTime": 30, "pointCount": 100} | 200, success=true | P0 |
| TC-097 | 异常-缺少请求体 | 无 | 无body | 400, 请求体必填 | P0 |
| TC-098 | 异常-字段类型错误 | 无 | {"saveOriginalResult": "yes"} | 400, 类型错误 | P1 |

---

## API: GET /v1/config-template/task

**接口说明**: 查询任务模板列表 - 查询用于任务的模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-099 | 正常查询任务模板列表 | 存在可用模板 | 无参数 | 200, 返回HandBook数组 | P0 |
| TC-100 | 边界-无可用模板 | 无启用的模板 | 无参数 | 200, entity为空数组 | P1 |
