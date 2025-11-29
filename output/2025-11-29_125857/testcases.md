# 测试用例文档

> 生成时间: 2025-11-29 12:58:57
> 接口数量: 14
> 用例总数: 98

---

## API: GET /v1/config-templates

**接口说明**: 采集指纹模板分页 - 分页查询采集指纹模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-001 | 正常查询-默认分页 | 系统中存在模板数据 | `params={}` (必填), 不传page和perPage | 200, 返回第1页10条数据 | P0 |
| TC-002 | 正常查询-指定分页 | 系统中存在模板数据 | `page=2&perPage=20&params={}` | 200, 返回第2页20条数据 | P0 |
| TC-003 | 正常查询-带筛选条件 | 系统中存在模板数据 | `params={"templateName":"测试模板"}` | 200, 返回符合条件的数据 | P0 |
| TC-004 | 必填参数缺失-params | 无 | 不传params参数 | 400, 提示params参数必填 | P1 |
| TC-005 | 参数类型错误-page为字符串 | 无 | `page=abc&params={}` | 400, 提示page类型错误 | P1 |
| TC-006 | 参数类型错误-perPage为字符串 | 无 | `perPage=xyz&params={}` | 400, 提示perPage类型错误 | P1 |
| TC-007 | 边界测试-page为0 | 无 | `page=0&params={}` | 400, 提示page无效或自动调整为1 | P2 |
| TC-008 | 边界测试-page为负数 | 无 | `page=-1&params={}` | 400, 提示page无效 | P2 |
| TC-009 | 边界测试-perPage为0 | 无 | `perPage=0&params={}` | 400, 提示perPage无效 | P2 |
| TC-010 | 边界测试-perPage超大值 | 无 | `perPage=10000&params={}` | 200, 返回数据或限制最大值 | P2 |
| TC-011 | 边界测试-page超出总页数 | 系统中存在少量数据 | `page=9999&params={}` | 200, 返回空数据列表 | P2 |

---

## API: POST /v1/config-templates

**接口说明**: 添加模板 - 添加基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-012 | 正常添加模板 | 无 | `{"templateName":"新模板","templateDesc":"描述","templateType":1}` | 200, success=true, 返回创建的模板 | P0 |
| TC-013 | 正常添加-完整字段 | 无 | `{"templateName":"完整模板","templateVer":"1.0","templateDesc":"描述","templateType":1,"isDefault":0,"isUse":1,"specification":"规范"}` | 200, success=true | P0 |
| TC-014 | 必填参数缺失-请求体为空 | 无 | `{}` 或不传body | 400, 提示必填字段缺失 | P1 |
| TC-015 | 参数类型错误-templateType为字符串 | 无 | `{"templateName":"测试","templateType":"abc"}` | 400, 提示类型错误 | P1 |
| TC-016 | 参数类型错误-isDefault为字符串 | 无 | `{"templateName":"测试","isDefault":"yes"}` | 400, 提示类型错误 | P1 |
| TC-017 | 边界测试-templateName为空字符串 | 无 | `{"templateName":""}` | 400, 提示名称不能为空 | P2 |
| TC-018 | 边界测试-templateName超长 | 无 | `{"templateName":"a"*1000}` (超长字符串) | 400, 提示名称超出长度限制 | P2 |
| TC-019 | 边界测试-templateName特殊字符 | 无 | `{"templateName":"<script>alert(1)</script>"}` | 200或400, 特殊字符被过滤或拒绝 | P2 |
| TC-020 | 业务规则-重复名称 | 已存在同名模板 | `{"templateName":"已存在的模板名"}` | 400, 提示模板名称已存在 | P1 |

---

## API: PUT /v1/config-templates

**接口说明**: 编辑模板 - 编辑基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-021 | 正常编辑模板 | 存在可编辑的模板 | `{"pkCollectTemplate":"existing-id","templateName":"修改后名称"}` | 200, success=true | P0 |
| TC-022 | 正常编辑-修改多个字段 | 存在可编辑的模板 | `{"pkCollectTemplate":"existing-id","templateName":"新名称","templateDesc":"新描述","templateVer":"2.0"}` | 200, success=true | P0 |
| TC-023 | 必填参数缺失-请求体为空 | 无 | `{}` 或不传body | 400, 提示必填字段缺失 | P1 |
| TC-024 | 必填参数缺失-无主键ID | 存在模板 | `{"templateName":"测试"}` (不含pkCollectTemplate) | 400, 提示模板ID必填 | P1 |
| TC-025 | 边界测试-模板ID不存在 | 无 | `{"pkCollectTemplate":"non-exist-id","templateName":"测试"}` | 404或400, 提示模板不存在 | P1 |
| TC-026 | 边界测试-templateName为空 | 存在模板 | `{"pkCollectTemplate":"existing-id","templateName":""}` | 400, 提示名称不能为空 | P2 |
| TC-027 | 业务规则-修改为已存在名称 | 存在多个模板 | `{"pkCollectTemplate":"id1","templateName":"模板2的名称"}` | 400, 提示名称已存在 | P1 |

---

## API: DELETE /v1/config-templates/{templateId}

**接口说明**: 删除模板 - 删除基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-028 | 正常删除模板 | 存在可删除的模板 | `templateId=existing-id` | 200, success=true | P0 |
| TC-029 | 必填参数缺失-templateId为空 | 无 | `templateId=` 或不传 | 400或404, 提示参数必填 | P1 |
| TC-030 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id` | 404或400, 提示模板不存在 | P1 |
| TC-031 | 边界测试-templateId为特殊字符 | 无 | `templateId=<script>` | 400, 参数格式错误 | P2 |
| TC-032 | 业务规则-删除默认模板 | 存在默认模板 | `templateId=default-template-id` | 400, 提示不能删除默认模板或需先取消默认 | P1 |
| TC-033 | 业务规则-删除使用中模板 | 模板正在被任务使用 | `templateId=in-use-template-id` | 400, 提示模板正在使用中 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/enable

**接口说明**: 启用模板 - 启用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-034 | 正常启用模板 | 存在已禁用的模板 | `templateId=disabled-template-id` | 200, success=true | P0 |
| TC-035 | 启用已启用的模板 | 模板已是启用状态 | `templateId=enabled-template-id` | 200, 幂等操作成功或提示已启用 | P0 |
| TC-036 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 参数必填 | P1 |
| TC-037 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id` | 404或400, 模板不存在 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/disable

**接口说明**: 禁用模板 - 禁用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-038 | 正常禁用模板 | 存在已启用的模板 | `templateId=enabled-template-id` | 200, success=true | P0 |
| TC-039 | 禁用已禁用的模板 | 模板已是禁用状态 | `templateId=disabled-template-id` | 200, 幂等操作成功或提示已禁用 | P0 |
| TC-040 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 参数必填 | P1 |
| TC-041 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id` | 404或400, 模板不存在 | P1 |
| TC-042 | 业务规则-禁用默认模板 | 存在默认模板 | `templateId=default-template-id` | 400, 提示不能禁用默认模板 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/default

**接口说明**: 设置默认模板 - 将指定模板设置为默认

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-043 | 正常设置默认模板 | 存在非默认模板 | `templateId=non-default-id` | 200, success=true, 原默认模板取消默认 | P0 |
| TC-044 | 设置已是默认的模板 | 模板已是默认 | `templateId=current-default-id` | 200, 幂等操作成功 | P0 |
| TC-045 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 参数必填 | P1 |
| TC-046 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id` | 404或400, 模板不存在 | P1 |
| TC-047 | 业务规则-设置禁用模板为默认 | 存在禁用状态模板 | `templateId=disabled-template-id` | 400, 提示禁用模板不能设为默认 | P1 |

---

## API: GET /v1/config-templates/{templateId}/{optType}/basic

**接口说明**: 查询模板基本信息 - 根据模板ID查询模板基本信息

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-048 | 正常查询模板信息 | 存在模板 | `templateId=existing-id&optType=view` | 200, 返回模板详细信息 | P0 |
| TC-049 | 正常查询-不同optType | 存在模板 | `templateId=existing-id&optType=edit` | 200, 返回可编辑的模板信息 | P0 |
| TC-050 | 必填参数缺失-templateId为空 | 无 | `templateId=&optType=view` | 400或404, 参数必填 | P1 |
| TC-051 | 必填参数缺失-optType为空 | 无 | `templateId=existing-id&optType=` | 400或404, 参数必填 | P1 |
| TC-052 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id&optType=view` | 404或400, 模板不存在 | P1 |
| TC-053 | 边界测试-optType无效值 | 存在模板 | `templateId=existing-id&optType=invalid` | 400, 提示optType无效 | P2 |

---

## API: GET /v1/config-templates/{templateId}/list

**接口说明**: 查询模板指纹列表 - 分页查询模板下的指纹列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-054 | 正常查询-默认分页 | 模板下存在指纹 | `templateId=existing-id` | 200, 返回第1页10条指纹 | P0 |
| TC-055 | 正常查询-带筛选条件 | 模板下存在指纹 | `templateId=existing-id&checkItemName=检查项&riskLevel=HIGH` | 200, 返回符合条件的指纹 | P0 |
| TC-056 | 正常查询-带排序 | 模板下存在指纹 | `templateId=existing-id&field=createTime&order=desc` | 200, 返回按时间倒序的数据 | P0 |
| TC-057 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 参数必填 | P1 |
| TC-058 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id` | 404或400, 模板不存在 | P1 |
| TC-059 | 边界测试-page为负数 | 存在模板 | `templateId=existing-id&page=-1` | 400, page参数无效 | P2 |
| TC-060 | 边界测试-checkItemName特殊字符 | 存在模板 | `templateId=existing-id&checkItemName=%27OR%201=1` | 200, 正常返回(SQL注入防护) | P2 |

---

## API: GET /v1/config-templates/choose

**接口说明**: 指纹分页列表 - 查询指纹分页列表（已选/未选）

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-061 | 正常查询-已选指纹 | 模板下有已选指纹 | `tempId=existing-id&selected=true` | 200, 返回已选指纹列表 | P0 |
| TC-062 | 正常查询-未选指纹 | 存在可选指纹 | `tempId=existing-id&selected=false` | 200, 返回未选指纹列表 | P0 |
| TC-063 | 正常查询-带筛选 | 存在指纹 | `tempId=existing-id&fingerType=type1&assetTypeCode=OS` | 200, 返回符合条件的指纹 | P0 |
| TC-064 | 参数类型错误-page为字符串 | 无 | `page=abc` | 400, 类型错误 | P1 |
| TC-065 | 边界测试-perPage超大值 | 存在指纹 | `perPage=99999` | 200, 返回数据或限制最大值 | P2 |

---

## API: POST /v1/config-templates/isExist

**接口说明**: 唯一性校验 - 校验模板名称是否重复

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-066 | 正常校验-名称不存在 | 无同名模板 | `checkType=name&checkValue=新模板名&id=` | 200, entity=false(不存在) | P0 |
| TC-067 | 正常校验-名称已存在 | 存在同名模板 | `checkType=name&checkValue=已存在模板名&id=` | 200, entity=true(已存在) | P0 |
| TC-068 | 正常校验-编辑时排除自身 | 编辑现有模板 | `checkType=name&checkValue=当前模板名&id=current-id` | 200, entity=false(排除自身) | P0 |
| TC-069 | 必填参数缺失-checkType | 无 | `checkValue=test&id=` | 400, 参数必填 | P1 |
| TC-070 | 必填参数缺失-checkValue | 无 | `checkType=name&id=` | 400, 参数必填 | P1 |
| TC-071 | 必填参数缺失-id | 无 | `checkType=name&checkValue=test` | 400, 参数必填 | P1 |
| TC-072 | 边界测试-checkValue为空字符串 | 无 | `checkType=name&checkValue=&id=` | 400, 校验值不能为空 | P2 |
| TC-073 | 边界测试-checkType无效值 | 无 | `checkType=invalid&checkValue=test&id=` | 400, checkType无效 | P2 |

---

## API: PUT /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加全部指纹 - 为模板添加全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-074 | 正常添加全部指纹 | 存在可添加的指纹 | `templateId=existing-id`, body: `{}` | 200, 返回添加数量 | P0 |
| TC-075 | 必填参数缺失-templateId | 无 | `templateId=`, body: `{}` | 400或404, 参数必填 | P1 |
| TC-076 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id`, body: `{}` | 404或400, 模板不存在 | P1 |
| TC-077 | 边界测试-无可添加指纹 | 模板已添加所有指纹 | `templateId=full-template-id`, body: `{}` | 200, entity=0 | P2 |

---

## API: PATCH /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加选中指纹 - 为模板添加选中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-078 | 正常添加选中指纹 | 存在可添加的指纹 | `templateId=existing-id`, body: `{"ids":["fp1","fp2"]}` | 200, 返回添加数量 | P0 |
| TC-079 | 必填参数缺失-templateId | 无 | `templateId=`, body: `{"ids":["fp1"]}` | 400或404, 参数必填 | P1 |
| TC-080 | 必填参数缺失-请求体为空 | 存在模板 | `templateId=existing-id`, body: `{}` | 400, 请指定要添加的指纹 | P1 |
| TC-081 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id`, body: `{"ids":["fp1"]}` | 404或400, 模板不存在 | P1 |
| TC-082 | 边界测试-指纹ID不存在 | 存在模板 | `templateId=existing-id`, body: `{"ids":["non-exist-fp"]}` | 200或400, 跳过不存在的或报错 | P2 |

---

## API: PUT /v1/config-templates/temps/{templateId}

**接口说明**: 删除全部指纹 - 删除模板中的全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-083 | 正常删除全部指纹 | 模板下有指纹 | `templateId=existing-id`, body: `{}` | 200, 返回删除数量 | P0 |
| TC-084 | 必填参数缺失-templateId | 无 | `templateId=`, body: `{}` | 400或404, 参数必填 | P1 |
| TC-085 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id`, body: `{}` | 404或400, 模板不存在 | P1 |
| TC-086 | 边界测试-模板无指纹 | 模板下无指纹 | `templateId=empty-template-id`, body: `{}` | 200, entity=0 | P2 |

---

## API: PATCH /v1/config-templates/temps/{templateId}

**接口说明**: 批量删除指纹 - 批量删除模板中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-087 | 正常批量删除指纹 | 模板下有指纹 | `templateId=existing-id`, body: `{"ids":["fp1","fp2"]}` | 200, 返回删除数量 | P0 |
| TC-088 | 必填参数缺失-templateId | 无 | `templateId=`, body: `{"ids":["fp1"]}` | 400或404, 参数必填 | P1 |
| TC-089 | 必填参数缺失-请求体为空 | 存在模板 | `templateId=existing-id`, body: `{}` | 400, 请指定要删除的指纹 | P1 |
| TC-090 | 边界测试-templateId不存在 | 无 | `templateId=non-exist-id`, body: `{"ids":["fp1"]}` | 404或400, 模板不存在 | P1 |
| TC-091 | 边界测试-指纹ID不存在 | 存在模板 | `templateId=existing-id`, body: `{"ids":["non-exist-fp"]}` | 200或400, 跳过或报错 | P2 |

---

## API: GET /v1/config-template/globalConf

**接口说明**: 获取全局配置 - 获取基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-092 | 正常获取全局配置 | 已配置全局配置 | 无参数 | 200, 返回TaskGlobalConfig | P0 |
| TC-093 | 获取默认全局配置 | 未配置过全局配置 | 无参数 | 200, 返回默认配置值 | P0 |

---

## API: POST /v1/config-template/globalConf

**接口说明**: 保存全局配置 - 保存基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-094 | 正常保存全局配置 | 无 | `{"saveOriginalResult":true,"pageShowOriginalResult":true,"enableAssetTypeCheck":false,"originalResultSaveType":1,"taskRedundancyTime":30,"pointCount":100}` | 200, success=true | P0 |
| TC-095 | 必填参数缺失-请求体为空 | 无 | `{}` 或不传body | 400, 请求体不能为空 | P1 |
| TC-096 | 参数类型错误-布尔值为字符串 | 无 | `{"saveOriginalResult":"yes"}` | 400, 类型错误 | P1 |
| TC-097 | 边界测试-taskRedundancyTime为负数 | 无 | `{"taskRedundancyTime":-1}` | 400, 值无效 | P2 |
| TC-098 | 边界测试-originalResultSaveTypeEnum无效值 | 无 | `{"originalResultSaveTypeEnum":"INVALID"}` | 400, 枚举值无效(只允许FILE/DB) | P2 |

---

## API: GET /v1/config-template/task

**接口说明**: 查询任务模板列表 - 查询用于任务的模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-099 | 正常查询任务模板列表 | 存在可用于任务的模板 | 无参数 | 200, 返回模板列表数组 | P0 |
| TC-100 | 查询空列表 | 无可用于任务的模板 | 无参数 | 200, 返回空数组 | P0 |

---

## 测试用例汇总

| 接口 | P0用例数 | P1用例数 | P2用例数 | 合计 |
|------|---------|---------|---------|------|
| GET /v1/config-templates | 3 | 2 | 6 | 11 |
| POST /v1/config-templates | 2 | 3 | 4 | 9 |
| PUT /v1/config-templates | 2 | 3 | 2 | 7 |
| DELETE /v1/config-templates/{templateId} | 1 | 4 | 1 | 6 |
| PATCH /v1/config-templates/{templateId}/enable | 2 | 2 | 0 | 4 |
| PATCH /v1/config-templates/{templateId}/disable | 2 | 3 | 0 | 5 |
| PATCH /v1/config-templates/{templateId}/default | 2 | 3 | 0 | 5 |
| GET /v1/config-templates/{templateId}/{optType}/basic | 2 | 3 | 1 | 6 |
| GET /v1/config-templates/{templateId}/list | 3 | 2 | 2 | 7 |
| GET /v1/config-templates/choose | 3 | 1 | 1 | 5 |
| POST /v1/config-templates/isExist | 3 | 3 | 2 | 8 |
| PUT /v1/config-templates/selectTemplate/{templateId} | 1 | 2 | 1 | 4 |
| PATCH /v1/config-templates/selectTemplate/{templateId} | 1 | 3 | 1 | 5 |
| PUT /v1/config-templates/temps/{templateId} | 1 | 2 | 1 | 4 |
| PATCH /v1/config-templates/temps/{templateId} | 1 | 3 | 1 | 5 |
| GET /v1/config-template/globalConf | 2 | 0 | 0 | 2 |
| POST /v1/config-template/globalConf | 1 | 2 | 2 | 5 |
| GET /v1/config-template/task | 2 | 0 | 0 | 2 |
| **合计** | **34** | **41** | **25** | **100** |

---

## 附录：数据模型参考

### AcCollectTemplate (模板信息)
| 字段 | 类型 | 说明 |
|------|------|------|
| pkCollectTemplate | string | 模板主键ID |
| templateName | string | 模板名称 |
| templateVer | string | 模板版本 |
| templateDesc | string | 模板描述 |
| templateType | int32 | 模板类型 |
| isDefault | int32 | 是否默认 |
| isUse | int32 | 是否启用 |
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
