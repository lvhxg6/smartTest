# 测试用例文档

> 生成时间: 2025-11-29 12:46:48
> 接口数量: 14
> 用例总数: 98

---

## API: GET /v1/config-templates

**接口说明**: 采集指纹模板分页 - 分页查询采集指纹模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-001 | 正常查询-默认分页 | 系统中存在模板数据 | `params.templateName=测试模板` | 200, 返回PageDataHandBook结构，包含data数组、totalCount、pageCount、perPage、page | P0 |
| TC-002 | 正常查询-指定分页参数 | 系统中存在模板数据 | `page=2&perPage=20&params.templateName=模板` | 200, 返回第2页数据，每页20条 | P0 |
| TC-003 | 正常查询-多条件筛选 | 系统中存在模板数据 | `params.templateName=测试&params.isUse=1&params.isDefault=0` | 200, 返回符合所有条件的数据 | P1 |
| TC-004 | 正常查询-时间范围筛选 | 系统中存在模板数据 | `params.updateStartTime=2025-01-01&params.updateEndTime=2025-12-31` | 200, 返回指定时间范围内更新的数据 | P1 |
| TC-005 | 正常查询-排序功能 | 系统中存在模板数据 | `params.field=createTime&params.order=desc` | 200, 返回按创建时间降序排列的数据 | P1 |
| TC-006 | 必填参数缺失-params | 无 | `page=1&perPage=10` (缺少params) | 400, 提示params参数必填 | P0 |
| TC-007 | 参数类型错误-page非整数 | 无 | `page=abc&perPage=10&params.templateName=测试` | 400, 提示page参数类型错误 | P1 |
| TC-008 | 参数类型错误-perPage非整数 | 无 | `page=1&perPage=xyz&params.templateName=测试` | 400, 提示perPage参数类型错误 | P1 |
| TC-009 | 边界测试-page为0 | 无 | `page=0&perPage=10&params.templateName=测试` | 400, 提示page参数无效或自动调整为1 | P2 |
| TC-010 | 边界测试-page为负数 | 无 | `page=-1&perPage=10&params.templateName=测试` | 400, 提示page参数无效 | P2 |
| TC-011 | 边界测试-perPage为0 | 无 | `page=1&perPage=0&params.templateName=测试` | 400, 提示perPage参数无效 | P2 |
| TC-012 | 边界测试-perPage超大值 | 无 | `page=1&perPage=10000&params.templateName=测试` | 200, 返回数据或限制为系统最大值 | P2 |
| TC-013 | 边界测试-templateName为空字符串 | 无 | `params.templateName=` | 200, 返回所有数据或空列表 | P2 |
| TC-014 | 边界测试-特殊字符 | 无 | `params.templateName=<script>alert(1)</script>` | 200, 正确处理特殊字符，无XSS风险 | P2 |
| TC-015 | 边界测试-超长字符串 | 无 | `params.templateName=(256字符以上)` | 400, 提示参数过长或200正常处理 | P2 |

---

## API: POST /v1/config-templates

**接口说明**: 添加模板 - 添加基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-016 | 正常创建模板-必填字段 | 模板名称不存在 | `{"templateName":"新模板","templateType":1}` | 200, success=true, 返回创建的HandBook对象 | P0 |
| TC-017 | 正常创建模板-完整字段 | 模板名称不存在 | `{"templateName":"完整模板","templateVer":"1.0","templateDesc":"描述","templateType":1,"isDefault":0,"isUse":1,"specification":"规范"}` | 200, success=true, 返回完整的模板信息 | P0 |
| TC-018 | 必填参数缺失-templateName | 无 | `{"templateType":1}` | 400, 提示templateName必填 | P0 |
| TC-019 | 必填参数缺失-请求体为空 | 无 | `{}` | 400, 提示必填参数缺失 | P0 |
| TC-020 | 参数类型错误-templateType非整数 | 无 | `{"templateName":"测试","templateType":"abc"}` | 400, 提示templateType类型错误 | P1 |
| TC-021 | 参数类型错误-isDefault非整数 | 无 | `{"templateName":"测试","isDefault":"yes"}` | 400, 提示isDefault类型错误 | P1 |
| TC-022 | 边界测试-templateName为空字符串 | 无 | `{"templateName":"","templateType":1}` | 400, 提示templateName不能为空 | P1 |
| TC-023 | 边界测试-templateName超长 | 无 | `{"templateName":"(256字符以上)","templateType":1}` | 400, 提示名称过长 | P2 |
| TC-024 | 边界测试-特殊字符 | 无 | `{"templateName":"测试<>&\"'","templateType":1}` | 200, 正确处理特殊字符 | P2 |
| TC-025 | 业务规则-模板名称重复 | 已存在同名模板 | `{"templateName":"已存在模板","templateType":1}` | 400, 提示模板名称已存在 | P0 |

---

## API: PUT /v1/config-templates

**接口说明**: 编辑模板 - 编辑基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-026 | 正常编辑模板 | 模板ID存在 | `{"pkCollectTemplate":"template-001","templateName":"修改后模板","templateType":1}` | 200, success=true, 返回更新后的HandBook对象 | P0 |
| TC-027 | 正常编辑-修改描述 | 模板ID存在 | `{"pkCollectTemplate":"template-001","templateDesc":"新描述"}` | 200, success=true | P0 |
| TC-028 | 必填参数缺失-pkCollectTemplate | 无 | `{"templateName":"测试"}` | 400, 提示缺少模板ID | P0 |
| TC-029 | 必填参数缺失-请求体为空 | 无 | `{}` | 400, 提示必填参数缺失 | P0 |
| TC-030 | 业务规则-模板不存在 | 无 | `{"pkCollectTemplate":"not-exist-id","templateName":"测试"}` | 404/400, 提示模板不存在 | P0 |
| TC-031 | 业务规则-修改为已存在名称 | 存在其他同名模板 | `{"pkCollectTemplate":"template-001","templateName":"已存在模板名"}` | 400, 提示模板名称已存在 | P1 |
| TC-032 | 参数类型错误-templateType非整数 | 无 | `{"pkCollectTemplate":"template-001","templateType":"invalid"}` | 400, 提示类型错误 | P1 |

---

## API: DELETE /v1/config-templates/{templateId}

**接口说明**: 删除模板 - 删除基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-033 | 正常删除模板 | 模板ID存在且可删除 | `templateId=template-001` | 200, success=true | P0 |
| TC-034 | 必填参数缺失-templateId | 无 | `templateId=` (空) | 400/404, 提示templateId必填 | P0 |
| TC-035 | 业务规则-模板不存在 | 无 | `templateId=not-exist-id` | 404/400, 提示模板不存在 | P0 |
| TC-036 | 业务规则-删除默认模板 | 模板为默认模板 | `templateId=default-template` | 400, 提示不能删除默认模板 | P1 |
| TC-037 | 业务规则-删除使用中模板 | 模板正在被任务使用 | `templateId=in-use-template` | 400, 提示模板正在使用中 | P1 |
| TC-038 | 边界测试-特殊字符ID | 无 | `templateId=../../../etc` | 400, 正确处理路径遍历攻击 | P2 |

---

## API: PATCH /v1/config-templates/{templateId}/enable

**接口说明**: 启用模板 - 启用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-039 | 正常启用模板 | 模板存在且处于禁用状态 | `templateId=template-001` | 200, success=true | P0 |
| TC-040 | 正常启用-已启用模板 | 模板已处于启用状态 | `templateId=enabled-template` | 200, success=true (幂等) | P1 |
| TC-041 | 必填参数缺失-templateId | 无 | `templateId=` | 400/404, 提示参数必填 | P0 |
| TC-042 | 业务规则-模板不存在 | 无 | `templateId=not-exist-id` | 404/400, 提示模板不存在 | P0 |

---

## API: PATCH /v1/config-templates/{templateId}/disable

**接口说明**: 禁用模板 - 禁用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-043 | 正常禁用模板 | 模板存在且处于启用状态 | `templateId=template-001` | 200, success=true | P0 |
| TC-044 | 正常禁用-已禁用模板 | 模板已处于禁用状态 | `templateId=disabled-template` | 200, success=true (幂等) | P1 |
| TC-045 | 必填参数缺失-templateId | 无 | `templateId=` | 400/404, 提示参数必填 | P0 |
| TC-046 | 业务规则-模板不存在 | 无 | `templateId=not-exist-id` | 404/400, 提示模板不存在 | P0 |
| TC-047 | 业务规则-禁用默认模板 | 模板为默认模板 | `templateId=default-template` | 400, 提示不能禁用默认模板 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/default

**接口说明**: 设置默认模板 - 将指定模板设置为默认

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-048 | 正常设置默认模板 | 模板存在且已启用 | `templateId=template-001` | 200, success=true, 该模板成为默认 | P0 |
| TC-049 | 业务规则-设置已禁用模板为默认 | 模板处于禁用状态 | `templateId=disabled-template` | 400, 提示禁用模板不能设为默认 | P1 |
| TC-050 | 业务规则-设置已是默认的模板 | 模板已是默认 | `templateId=current-default` | 200, success=true (幂等) | P1 |
| TC-051 | 必填参数缺失-templateId | 无 | `templateId=` | 400/404, 提示参数必填 | P0 |
| TC-052 | 业务规则-模板不存在 | 无 | `templateId=not-exist-id` | 404/400, 提示模板不存在 | P0 |

---

## API: GET /v1/config-templates/{templateId}/{optType}/basic

**接口说明**: 查询模板基本信息 - 根据模板ID查询模板基本信息

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-053 | 正常查询模板信息 | 模板存在 | `templateId=template-001&optType=view` | 200, 返回HandBook对象 | P0 |
| TC-054 | 正常查询-不同optType | 模板存在 | `templateId=template-001&optType=edit` | 200, 返回对应类型的信息 | P1 |
| TC-055 | 必填参数缺失-templateId | 无 | `optType=view` (缺少templateId) | 400/404, 提示参数必填 | P0 |
| TC-056 | 必填参数缺失-optType | 无 | `templateId=template-001` (缺少optType) | 400/404, 提示参数必填 | P0 |
| TC-057 | 业务规则-模板不存在 | 无 | `templateId=not-exist&optType=view` | 404/400, 提示模板不存在 | P0 |
| TC-058 | 参数验证-无效optType | 无 | `templateId=template-001&optType=invalid` | 400, 提示optType无效 | P1 |

---

## API: GET /v1/config-templates/{templateId}/list

**接口说明**: 查询模板指纹列表 - 分页查询模板下的指纹列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-059 | 正常查询-默认分页 | 模板存在且有指纹 | `templateId=template-001` | 200, 返回PageDataCheckitem结构 | P0 |
| TC-060 | 正常查询-指定分页 | 模板存在 | `templateId=template-001&page=2&perPage=20` | 200, 返回第2页数据 | P0 |
| TC-061 | 正常查询-条件筛选 | 模板存在 | `templateId=template-001&checkItemName=检查项&riskLevel=high` | 200, 返回符合条件的数据 | P1 |
| TC-062 | 正常查询-排序 | 模板存在 | `templateId=template-001&field=createTime&order=asc` | 200, 返回按时间升序的数据 | P1 |
| TC-063 | 必填参数缺失-templateId | 无 | `page=1&perPage=10` | 400/404, 提示templateId必填 | P0 |
| TC-064 | 业务规则-模板不存在 | 无 | `templateId=not-exist-id` | 404/400, 提示模板不存在 | P0 |
| TC-065 | 边界测试-模板无指纹 | 模板存在但无指纹 | `templateId=empty-template` | 200, 返回空data数组，totalCount=0 | P1 |

---

## API: GET /v1/config-templates/choose

**接口说明**: 指纹分页列表 - 查询指纹分页列表（已选/未选）

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-066 | 正常查询-已选指纹 | 模板存在 | `templateId=template-001&selected=true` | 200, 返回已选指纹列表 | P0 |
| TC-067 | 正常查询-未选指纹 | 模板存在 | `templateId=template-001&selected=false` | 200, 返回未选指纹列表 | P0 |
| TC-068 | 正常查询-按类型筛选 | 无 | `fingerType=type1&assetTypeCode=linux` | 200, 返回符合条件的指纹 | P1 |
| TC-069 | 正常查询-按名称搜索 | 无 | `checkItemName=密码策略` | 200, 返回包含关键字的指纹 | P1 |
| TC-070 | 正常查询-分页排序 | 无 | `page=1&perPage=50&field=name&order=asc` | 200, 返回排序后的分页数据 | P1 |
| TC-071 | 边界测试-无结果 | 无 | `checkItemName=不存在的指纹名称` | 200, 返回空data数组 | P2 |

---

## API: POST /v1/config-templates/isExist

**接口说明**: 唯一性校验 - 校验模板名称是否重复

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-072 | 正常校验-名称不存在 | 无同名模板 | `checkType=templateName&checkValue=新模板&id=` | 200, entity=false (不存在) | P0 |
| TC-073 | 正常校验-名称已存在 | 存在同名模板 | `checkType=templateName&checkValue=已存在模板&id=` | 200, entity=true (存在) | P0 |
| TC-074 | 正常校验-编辑时排除自身 | 当前模板名存在 | `checkType=templateName&checkValue=当前模板&id=current-id` | 200, entity=false (排除自身) | P0 |
| TC-075 | 必填参数缺失-checkType | 无 | `checkValue=测试&id=123` | 400, 提示checkType必填 | P0 |
| TC-076 | 必填参数缺失-checkValue | 无 | `checkType=templateName&id=123` | 400, 提示checkValue必填 | P0 |
| TC-077 | 必填参数缺失-id | 无 | `checkType=templateName&checkValue=测试` | 400, 提示id必填 | P0 |
| TC-078 | 边界测试-空checkValue | 无 | `checkType=templateName&checkValue=&id=` | 400, 提示checkValue不能为空 | P1 |

---

## API: PUT /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加全部指纹 - 为模板添加全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-079 | 正常添加全部指纹 | 模板存在，有未选指纹 | `templateId=template-001`, body: `{}` | 200, entity返回添加数量 | P0 |
| TC-080 | 必填参数缺失-templateId | 无 | body: `{}` | 400/404, 提示templateId必填 | P0 |
| TC-081 | 业务规则-模板不存在 | 无 | `templateId=not-exist`, body: `{}` | 404/400, 提示模板不存在 | P0 |
| TC-082 | 边界测试-已全部添加 | 模板已包含所有指纹 | `templateId=full-template`, body: `{}` | 200, entity=0 | P1 |

---

## API: PATCH /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加选中指纹 - 为模板添加选中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-083 | 正常添加选中指纹 | 模板存在 | `templateId=template-001`, body: `{"fingerIds":["f1","f2"]}` | 200, entity返回添加数量 | P0 |
| TC-084 | 必填参数缺失-templateId | 无 | body: `{"fingerIds":["f1"]}` | 400/404, 提示templateId必填 | P0 |
| TC-085 | 必填参数缺失-请求体 | 模板存在 | `templateId=template-001`, body: `{}` | 400, 提示缺少指纹ID | P0 |
| TC-086 | 业务规则-指纹ID不存在 | 模板存在 | `templateId=template-001`, body: `{"fingerIds":["invalid-id"]}` | 400, 提示指纹不存在 | P1 |
| TC-087 | 边界测试-添加已存在指纹 | 指纹已在模板中 | `templateId=template-001`, body: `{"fingerIds":["existing-f1"]}` | 200, 幂等处理或返回0 | P1 |

---

## API: PUT /v1/config-templates/temps/{templateId}

**接口说明**: 删除全部指纹 - 删除模板中的全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-088 | 正常删除全部指纹 | 模板存在且有指纹 | `templateId=template-001`, body: `{}` | 200, entity返回删除数量 | P0 |
| TC-089 | 必填参数缺失-templateId | 无 | body: `{}` | 400/404, 提示templateId必填 | P0 |
| TC-090 | 业务规则-模板不存在 | 无 | `templateId=not-exist`, body: `{}` | 404/400, 提示模板不存在 | P0 |
| TC-091 | 边界测试-模板无指纹 | 模板存在但无指纹 | `templateId=empty-template`, body: `{}` | 200, entity=0 | P1 |

---

## API: PATCH /v1/config-templates/temps/{templateId}

**接口说明**: 批量删除指纹 - 批量删除模板中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-092 | 正常批量删除指纹 | 模板存在且有指纹 | `templateId=template-001`, body: `{"fingerIds":["f1","f2"]}` | 200, entity返回删除数量 | P0 |
| TC-093 | 必填参数缺失-templateId | 无 | body: `{"fingerIds":["f1"]}` | 400/404, 提示templateId必填 | P0 |
| TC-094 | 必填参数缺失-请求体 | 模板存在 | `templateId=template-001`, body: `{}` | 400, 提示缺少指纹ID | P0 |
| TC-095 | 边界测试-删除不存在的指纹 | 模板存在 | `templateId=template-001`, body: `{"fingerIds":["not-in-template"]}` | 200, entity=0 或 400提示 | P1 |

---

## API: GET /v1/config-template/globalConf

**接口说明**: 获取全局配置 - 获取基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-096 | 正常获取全局配置 | 系统已初始化 | 无参数 | 200, 返回TaskGlobalConfig对象 | P0 |

---

## API: POST /v1/config-template/globalConf

**接口说明**: 保存全局配置 - 保存基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-097 | 正常保存全局配置 | 无 | `{"saveOriginalResult":true,"pageShowOriginalResult":true,"enableAssetTypeCheck":false,"originalResultSaveType":1,"taskRedundancyTime":30,"pointCount":100}` | 200, success=true, 返回保存后的配置 | P0 |
| TC-098 | 参数类型错误-布尔值非法 | 无 | `{"saveOriginalResult":"yes"}` | 400, 提示类型错误 | P1 |
| TC-099 | 参数类型错误-枚举值非法 | 无 | `{"originalResultSaveTypeEnum":"INVALID"}` | 400, 提示枚举值无效 | P1 |
| TC-100 | 边界测试-taskRedundancyTime负数 | 无 | `{"taskRedundancyTime":-1}` | 400, 提示参数无效 | P2 |
| TC-101 | 边界测试-pointCount为0 | 无 | `{"pointCount":0}` | 400, 提示参数无效或200接受 | P2 |

---

## API: GET /v1/config-template/task

**接口说明**: 查询任务模板列表 - 查询用于任务的模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-102 | 正常查询任务模板列表 | 存在可用模板 | 无参数 | 200, 返回HandBook数组 | P0 |
| TC-103 | 边界测试-无可用模板 | 无启用的模板 | 无参数 | 200, 返回空数组 | P1 |

---

## 测试用例统计

| 优先级 | 数量 | 说明 |
|--------|------|------|
| P0 | 45 | 核心功能，必须通过 |
| P1 | 38 | 重要功能，应当通过 |
| P2 | 15 | 边界场景，建议覆盖 |
| **总计** | **98** | - |

---

## 附录：数据模型说明

### AcCollectTemplate (模板信息)
| 字段 | 类型 | 说明 |
|------|------|------|
| pkCollectTemplate | string | 模板主键ID |
| templateName | string | 模板名称 |
| templateVer | string | 模板版本 |
| templateDesc | string | 模板描述 |
| templateType | int32 | 模板类型 |
| isDefault | int32 | 是否默认 (0/1) |
| isUse | int32 | 是否启用 (0/1) |
| specification | string | 规范 |

### TaskGlobalConfig (全局配置)
| 字段 | 类型 | 说明 |
|------|------|------|
| saveOriginalResult | boolean | 是否保存原始结果 |
| pageShowOriginalResult | boolean | 页面是否显示原始结果 |
| enableAssetTypeCheck | boolean | 是否启用资产类型检查 |
| originalResultSaveType | int32 | 原始结果保存类型 |
| originalResultSaveTypeEnum | enum | FILE/DB |
| taskRedundancyTime | int32 | 任务冗余时间 |
| pointCount | int32 | 点数 |
