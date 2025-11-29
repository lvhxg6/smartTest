# 测试用例文档

> 生成时间: 2025-11-29 13:05:18
> 接口数量: 18
> 用例总数: 127

---

## API-01: GET /v1/config-templates

**功能**: 采集指纹模板分页查询

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-001 | 正常分页查询-默认参数 | 系统中存在模板数据 | `params={}` (必填), 不传page和perPage | 200, 返回第1页，每页10条数据 | P0 |
| TC-002 | 正常分页查询-指定分页 | 系统中存在模板数据 | `page=2&perPage=20&params={}` | 200, 返回第2页，每页20条数据 | P0 |
| TC-003 | 正常查询-带筛选条件 | 系统中存在模板数据 | `params={"templateName":"测试模板"}` | 200, 返回符合条件的模板列表 | P0 |
| TC-004 | 必填参数缺失-params为空 | 无 | 不传params参数 | 400, 提示params参数必填 | P1 |
| TC-005 | 参数类型错误-page非整数 | 无 | `page=abc&params={}` | 400, 提示page参数类型错误 | P1 |
| TC-006 | 参数类型错误-perPage非整数 | 无 | `perPage=xyz&params={}` | 400, 提示perPage参数类型错误 | P1 |
| TC-007 | 边界测试-page为0 | 无 | `page=0&params={}` | 400, 提示page必须大于0 | P2 |
| TC-008 | 边界测试-page为负数 | 无 | `page=-1&params={}` | 400, 提示page必须大于0 | P2 |
| TC-009 | 边界测试-perPage为0 | 无 | `perPage=0&params={}` | 400, 提示perPage必须大于0 | P2 |
| TC-010 | 边界测试-perPage超大值 | 无 | `perPage=10000&params={}` | 200或400, 根据系统限制返回 | P2 |
| TC-011 | 边界测试-page超大值无数据 | 无 | `page=999999&params={}` | 200, 返回空数据列表 | P2 |

---

## API-02: PUT /v1/config-templates

**功能**: 编辑基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-012 | 正常编辑模板 | 存在可编辑的模板 | `{"pkCollectTemplate":"tpl-001","templateName":"更新后的模板","templateDesc":"描述"}` | 200, success=true, 返回更新后的模板信息 | P0 |
| TC-013 | 编辑模板-修改全部字段 | 存在可编辑的模板 | 包含所有可编辑字段的完整JSON | 200, success=true | P0 |
| TC-014 | 必填参数缺失-RequestBody为空 | 无 | 空请求体 | 400, 提示请求体不能为空 | P1 |
| TC-015 | 参数类型错误-templateType非整数 | 无 | `{"templateType":"abc"}` | 400, 提示类型错误 | P1 |
| TC-016 | 参数类型错误-isDefault非整数 | 无 | `{"isDefault":"yes"}` | 400, 提示类型错误 | P1 |
| TC-017 | 边界测试-templateName为空字符串 | 无 | `{"pkCollectTemplate":"tpl-001","templateName":""}` | 400, 提示模板名称不能为空 | P2 |
| TC-018 | 边界测试-templateName超长 | 无 | `{"templateName":"a"*1000}` | 400, 提示名称长度超限 | P2 |
| TC-019 | 边界测试-templateDesc特殊字符 | 无 | `{"templateDesc":"<script>alert(1)</script>"}` | 200或400, 应正确处理/转义特殊字符 | P2 |
| TC-020 | 编辑不存在的模板 | 无 | `{"pkCollectTemplate":"not-exist-id"}` | 404或400, 提示模板不存在 | P1 |

---

## API-03: POST /v1/config-templates

**功能**: 添加基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-021 | 正常添加模板-必填字段 | 无 | `{"templateName":"新模板","templateType":1}` | 200, success=true, 返回新建模板信息 | P0 |
| TC-022 | 正常添加模板-全部字段 | 无 | 包含所有字段的完整JSON | 200, success=true | P0 |
| TC-023 | 必填参数缺失-RequestBody为空 | 无 | 空请求体 | 400, 提示请求体不能为空 | P1 |
| TC-024 | 必填参数缺失-templateName为空 | 无 | `{"templateType":1}` | 400, 提示模板名称必填 | P1 |
| TC-025 | 参数类型错误-templateType非整数 | 无 | `{"templateName":"模板","templateType":"one"}` | 400, 提示类型错误 | P1 |
| TC-026 | 边界测试-templateName为空字符串 | 无 | `{"templateName":"","templateType":1}` | 400, 提示模板名称不能为空 | P2 |
| TC-027 | 边界测试-templateName超长 | 无 | `{"templateName":"a"*1000}` | 400, 提示名称长度超限 | P2 |
| TC-028 | 边界测试-templateName特殊字符 | 无 | `{"templateName":"测试<>&\"'模板"}` | 200或400, 应正确处理特殊字符 | P2 |
| TC-029 | 重复添加-模板名称重复 | 已存在同名模板 | `{"templateName":"已存在的模板名"}` | 400, 提示模板名称已存在 | P1 |

---

## API-04: DELETE /v1/config-templates/{templateId}

**功能**: 删除基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-030 | 正常删除模板 | 存在可删除的模板 | `templateId=tpl-001` | 200, success=true | P0 |
| TC-031 | 删除不存在的模板 | 无 | `templateId=not-exist-id` | 404或400, 提示模板不存在 | P1 |
| TC-032 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-033 | 边界测试-templateId特殊字符 | 无 | `templateId=../../../etc` | 400, 拒绝非法路径 | P2 |
| TC-034 | 边界测试-templateId超长 | 无 | `templateId=a*1000` | 400, 提示ID格式错误 | P2 |
| TC-035 | 删除默认模板 | 模板为默认模板 | `templateId=default-tpl` | 400, 提示默认模板不能删除（业务规则） | P1 |
| TC-036 | 删除正在使用的模板 | 模板被任务引用 | `templateId=in-use-tpl` | 400, 提示模板正在使用中（业务规则） | P1 |

---

## API-05: PATCH /v1/config-templates/{templateId}/enable

**功能**: 启用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-037 | 正常启用禁用状态的模板 | 模板处于禁用状态 | `templateId=disabled-tpl` | 200, success=true, 模板状态变为启用 | P0 |
| TC-038 | 启用已启用的模板 | 模板已启用 | `templateId=enabled-tpl` | 200, success=true（幂等操作） | P1 |
| TC-039 | 启用不存在的模板 | 无 | `templateId=not-exist-id` | 404或400, 提示模板不存在 | P1 |
| TC-040 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-041 | 边界测试-templateId特殊字符 | 无 | `templateId=<script>` | 400, 拒绝非法字符 | P2 |

---

## API-06: PATCH /v1/config-templates/{templateId}/disable

**功能**: 禁用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-042 | 正常禁用启用状态的模板 | 模板处于启用状态 | `templateId=enabled-tpl` | 200, success=true, 模板状态变为禁用 | P0 |
| TC-043 | 禁用已禁用的模板 | 模板已禁用 | `templateId=disabled-tpl` | 200, success=true（幂等操作） | P1 |
| TC-044 | 禁用不存在的模板 | 无 | `templateId=not-exist-id` | 404或400, 提示模板不存在 | P1 |
| TC-045 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-046 | 禁用默认模板 | 模板为默认模板 | `templateId=default-tpl` | 400, 提示默认模板不能禁用（业务规则） | P1 |
| TC-047 | 禁用正在使用的模板 | 模板被任务引用 | `templateId=in-use-tpl` | 400, 提示模板正在使用中（业务规则） | P1 |

---

## API-07: PATCH /v1/config-templates/{templateId}/default

**功能**: 将指定模板设置为默认

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-048 | 正常设置默认模板 | 模板存在且启用 | `templateId=tpl-001` | 200, success=true, 该模板成为默认模板 | P0 |
| TC-049 | 设置已是默认的模板为默认 | 模板已是默认 | `templateId=current-default` | 200, success=true（幂等操作） | P1 |
| TC-050 | 设置不存在的模板为默认 | 无 | `templateId=not-exist-id` | 404或400, 提示模板不存在 | P1 |
| TC-051 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-052 | 设置禁用状态模板为默认 | 模板处于禁用状态 | `templateId=disabled-tpl` | 400, 提示禁用模板不能设为默认（业务规则） | P1 |

---

## API-08: GET /v1/config-templates/{templateId}/{optType}/basic

**功能**: 根据模板ID查询模板基本信息

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-053 | 正常查询模板基本信息 | 模板存在 | `templateId=tpl-001&optType=view` | 200, 返回模板基本信息 | P0 |
| TC-054 | 不同optType查询 | 模板存在 | `templateId=tpl-001&optType=edit` | 200, 返回对应类型的信息 | P0 |
| TC-055 | 查询不存在的模板 | 无 | `templateId=not-exist-id&optType=view` | 404或400, 提示模板不存在 | P1 |
| TC-056 | 必填参数缺失-templateId为空 | 无 | `templateId=&optType=view` | 400或404, 路径参数无效 | P1 |
| TC-057 | 必填参数缺失-optType为空 | 无 | `templateId=tpl-001&optType=` | 400或404, 路径参数无效 | P1 |
| TC-058 | 参数错误-optType无效值 | 无 | `templateId=tpl-001&optType=invalid` | 400, 提示optType值无效 | P2 |
| TC-059 | 边界测试-templateId特殊字符 | 无 | `templateId=../..&optType=view` | 400, 拒绝非法路径 | P2 |

---

## API-09: GET /v1/config-templates/{templateId}/list

**功能**: 分页查询模板下的指纹列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-060 | 正常查询-默认分页 | 模板存在且有指纹 | `templateId=tpl-001` | 200, 返回第1页，每页10条指纹 | P0 |
| TC-061 | 正常查询-指定分页 | 模板存在 | `templateId=tpl-001&page=2&perPage=20` | 200, 返回第2页，每页20条 | P0 |
| TC-062 | 正常查询-带筛选条件 | 模板存在 | `templateId=tpl-001&checkItemName=密码&riskLevel=high` | 200, 返回符合条件的指纹 | P0 |
| TC-063 | 正常查询-带排序 | 模板存在 | `templateId=tpl-001&field=createTime&order=desc` | 200, 返回按创建时间降序排列 | P1 |
| TC-064 | 查询不存在的模板指纹 | 无 | `templateId=not-exist-id` | 404或400, 提示模板不存在 | P1 |
| TC-065 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-066 | 边界测试-page为负数 | 无 | `templateId=tpl-001&page=-1` | 400, 提示page必须大于0 | P2 |
| TC-067 | 边界测试-perPage为0 | 无 | `templateId=tpl-001&perPage=0` | 400, 提示perPage必须大于0 | P2 |
| TC-068 | 边界测试-checkItemName特殊字符 | 无 | `templateId=tpl-001&checkItemName=%00%0a` | 200或400, 应正确处理特殊字符 | P2 |

---

## API-10: GET /v1/config-templates/choose

**功能**: 查询指纹分页列表（已选/未选）

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-069 | 正常查询-默认分页 | 系统有指纹数据 | 无参数或`page=1&perPage=10` | 200, 返回指纹列表 | P0 |
| TC-070 | 查询已选指纹 | 模板已选择指纹 | `tempId=tpl-001&selected=true` | 200, 返回已选指纹列表 | P0 |
| TC-071 | 查询未选指纹 | 模板有未选指纹 | `tempId=tpl-001&selected=false` | 200, 返回未选指纹列表 | P0 |
| TC-072 | 按指纹类型筛选 | 系统有指纹数据 | `fingerType=os` | 200, 返回指定类型指纹 | P1 |
| TC-073 | 按资产类型筛选 | 系统有指纹数据 | `assetTypeCode=linux` | 200, 返回指定资产类型指纹 | P1 |
| TC-074 | 按检查项名称搜索 | 系统有指纹数据 | `checkItemName=密码策略` | 200, 返回匹配的指纹 | P1 |
| TC-075 | 带排序查询 | 系统有指纹数据 | `field=name&order=asc` | 200, 返回按名称升序排列 | P1 |
| TC-076 | 边界测试-page非整数 | 无 | `page=abc` | 400, 提示参数类型错误 | P2 |
| TC-077 | 边界测试-perPage超大值 | 无 | `perPage=100000` | 200或400, 根据系统限制 | P2 |

---

## API-11: POST /v1/config-templates/isExist

**功能**: 校验模板名称是否重复

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-078 | 名称不存在-新增场景 | 无同名模板 | `checkType=name&checkValue=新模板&id=` | 200, entity=false（不存在） | P0 |
| TC-079 | 名称已存在-新增场景 | 存在同名模板 | `checkType=name&checkValue=已有模板&id=` | 200, entity=true（已存在） | P0 |
| TC-080 | 名称存在但是自己-编辑场景 | 编辑现有模板 | `checkType=name&checkValue=当前模板名&id=tpl-001` | 200, entity=false（排除自己） | P0 |
| TC-081 | 必填参数缺失-checkType为空 | 无 | `checkType=&checkValue=test&id=1` | 400, 提示checkType必填 | P1 |
| TC-082 | 必填参数缺失-checkValue为空 | 无 | `checkType=name&checkValue=&id=1` | 400, 提示checkValue必填 | P1 |
| TC-083 | 必填参数缺失-id为空 | 无 | `checkType=name&checkValue=test&id=` | 200, 作为新增场景处理 | P1 |
| TC-084 | 边界测试-checkValue超长 | 无 | `checkType=name&checkValue=a*1000&id=` | 200或400, 返回校验结果 | P2 |
| TC-085 | 边界测试-checkValue特殊字符 | 无 | `checkType=name&checkValue=<>&"'&id=` | 200, 正确校验特殊字符名称 | P2 |

---

## API-12: PUT /v1/config-templates/selectTemplate/{templateId}

**功能**: 为模板添加全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-086 | 正常添加全部指纹 | 模板存在，有可添加指纹 | `templateId=tpl-001`, body=`{}` | 200, success=true, 返回添加数量 | P0 |
| TC-087 | 添加到不存在的模板 | 无 | `templateId=not-exist`, body=`{}` | 404或400, 提示模板不存在 | P1 |
| TC-088 | 必填参数缺失-templateId为空 | 无 | `templateId=`, body=`{}` | 400或404, 路径参数无效 | P1 |
| TC-089 | 必填参数缺失-RequestBody为空 | 无 | `templateId=tpl-001`, 无body | 400, 提示请求体必填 | P1 |
| TC-090 | 重复添加全部指纹 | 模板已有全部指纹 | `templateId=full-tpl`, body=`{}` | 200, 返回0或幂等处理 | P2 |

---

## API-13: PATCH /v1/config-templates/selectTemplate/{templateId}

**功能**: 为模板添加选中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-091 | 正常添加选中指纹 | 模板存在 | `templateId=tpl-001`, body=`{"ids":["fp-001","fp-002"]}` | 200, success=true, 返回添加数量 | P0 |
| TC-092 | 添加到不存在的模板 | 无 | `templateId=not-exist`, body=`{"ids":["fp-001"]}` | 404或400, 提示模板不存在 | P1 |
| TC-093 | 添加不存在的指纹 | 模板存在 | `templateId=tpl-001`, body=`{"ids":["not-exist-fp"]}` | 400, 提示指纹不存在 | P1 |
| TC-094 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-095 | 必填参数缺失-ids为空数组 | 无 | `templateId=tpl-001`, body=`{"ids":[]}` | 400, 提示未选择指纹 | P2 |
| TC-096 | 重复添加相同指纹 | 指纹已在模板中 | `templateId=tpl-001`, body=`{"ids":["existing-fp"]}` | 200, 幂等处理，忽略重复 | P2 |

---

## API-14: PUT /v1/config-templates/temps/{templateId}

**功能**: 删除模板中的全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-097 | 正常删除全部指纹 | 模板存在且有指纹 | `templateId=tpl-001`, body=`{}` | 200, success=true, 返回删除数量 | P0 |
| TC-098 | 删除不存在模板的指纹 | 无 | `templateId=not-exist`, body=`{}` | 404或400, 提示模板不存在 | P1 |
| TC-099 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-100 | 必填参数缺失-RequestBody为空 | 无 | `templateId=tpl-001`, 无body | 400, 提示请求体必填 | P1 |
| TC-101 | 删除空模板的指纹 | 模板无指纹 | `templateId=empty-tpl`, body=`{}` | 200, 返回0 | P2 |

---

## API-15: PATCH /v1/config-templates/temps/{templateId}

**功能**: 批量删除模板中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-102 | 正常批量删除指纹 | 模板存在且有指纹 | `templateId=tpl-001`, body=`{"ids":["fp-001","fp-002"]}` | 200, success=true, 返回删除数量 | P0 |
| TC-103 | 删除不存在模板的指纹 | 无 | `templateId=not-exist`, body=`{"ids":["fp-001"]}` | 404或400, 提示模板不存在 | P1 |
| TC-104 | 删除不存在的指纹 | 模板存在 | `templateId=tpl-001`, body=`{"ids":["not-exist-fp"]}` | 200或400, 忽略不存在的或报错 | P1 |
| TC-105 | 必填参数缺失-templateId为空 | 无 | `templateId=` | 400或404, 路径参数无效 | P1 |
| TC-106 | 必填参数缺失-ids为空数组 | 无 | `templateId=tpl-001`, body=`{"ids":[]}` | 400, 提示未选择指纹 | P2 |

---

## API-16: GET /v1/config-template/globalConf

**功能**: 获取基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-107 | 正常获取全局配置 | 系统已初始化 | 无参数 | 200, success=true, 返回TaskGlobalConfig对象 | P0 |
| TC-108 | 首次获取-未配置 | 系统未配置过 | 无参数 | 200, 返回默认配置或空 | P1 |

---

## API-17: POST /v1/config-template/globalConf

**功能**: 保存基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-109 | 正常保存全局配置 | 无 | `{"saveOriginalResult":true,"pageShowOriginalResult":false,"enableAssetTypeCheck":true,"originalResultSaveType":1,"taskRedundancyTime":30,"pointCount":100}` | 200, success=true, 返回保存后的配置 | P0 |
| TC-110 | 保存配置-仅部分字段 | 无 | `{"saveOriginalResult":true}` | 200, success=true | P1 |
| TC-111 | 必填参数缺失-RequestBody为空 | 无 | 空请求体 | 400, 提示请求体不能为空 | P1 |
| TC-112 | 参数类型错误-saveOriginalResult非布尔 | 无 | `{"saveOriginalResult":"yes"}` | 400, 提示类型错误 | P1 |
| TC-113 | 参数类型错误-originalResultSaveType非整数 | 无 | `{"originalResultSaveType":"file"}` | 400, 提示类型错误 | P1 |
| TC-114 | 边界测试-taskRedundancyTime为负数 | 无 | `{"taskRedundancyTime":-1}` | 400, 提示值必须大于等于0 | P2 |
| TC-115 | 边界测试-pointCount为0 | 无 | `{"pointCount":0}` | 400或200, 根据业务规则 | P2 |
| TC-116 | 边界测试-pointCount超大值 | 无 | `{"pointCount":999999999}` | 400或200, 根据系统限制 | P2 |
| TC-117 | 枚举值测试-originalResultSaveTypeEnum有效值 | 无 | `{"originalResultSaveTypeEnum":"FILE"}` | 200, 正确处理枚举值 | P1 |
| TC-118 | 枚举值测试-originalResultSaveTypeEnum无效值 | 无 | `{"originalResultSaveTypeEnum":"INVALID"}` | 400, 提示枚举值无效 | P1 |

---

## API-18: GET /v1/config-template/task

**功能**: 查询用于任务的模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-119 | 正常查询任务模板列表 | 系统存在模板 | 无参数 | 200, success=true, 返回模板列表 | P0 |
| TC-120 | 查询-无可用模板 | 系统无模板或全部禁用 | 无参数 | 200, 返回空列表 | P1 |

---

## 通用测试用例（适用于所有接口）

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-121 | 请求方法错误 | 无 | 对GET接口发送POST请求 | 405 Method Not Allowed | P1 |
| TC-122 | Content-Type错误 | 无 | POST/PUT请求使用text/plain | 415 Unsupported Media Type | P1 |
| TC-123 | 请求体JSON格式错误 | 无 | `{"name": invalid}` | 400, JSON解析错误 | P1 |
| TC-124 | 请求头缺失Accept | 无 | 不带Accept头 | 200, 默认返回JSON | P2 |
| TC-125 | 并发请求测试 | 无 | 同时发送多个相同请求 | 正确处理并发，无数据异常 | P2 |
| TC-126 | 超长URL测试 | 无 | URL长度超过8000字符 | 414 URI Too Long 或 400 | P2 |
| TC-127 | SQL注入测试 | 无 | 参数值包含`'; DROP TABLE --` | 正常返回，不执行SQL | P1 |

---

## 用例统计

| API编号 | 接口路径 | 用例数量 |
|---------|----------|----------|
| API-01 | GET /v1/config-templates | 11 |
| API-02 | PUT /v1/config-templates | 9 |
| API-03 | POST /v1/config-templates | 9 |
| API-04 | DELETE /v1/config-templates/{templateId} | 7 |
| API-05 | PATCH /v1/config-templates/{templateId}/enable | 5 |
| API-06 | PATCH /v1/config-templates/{templateId}/disable | 6 |
| API-07 | PATCH /v1/config-templates/{templateId}/default | 5 |
| API-08 | GET /v1/config-templates/{templateId}/{optType}/basic | 7 |
| API-09 | GET /v1/config-templates/{templateId}/list | 9 |
| API-10 | GET /v1/config-templates/choose | 9 |
| API-11 | POST /v1/config-templates/isExist | 8 |
| API-12 | PUT /v1/config-templates/selectTemplate/{templateId} | 5 |
| API-13 | PATCH /v1/config-templates/selectTemplate/{templateId} | 6 |
| API-14 | PUT /v1/config-templates/temps/{templateId} | 5 |
| API-15 | PATCH /v1/config-templates/temps/{templateId} | 5 |
| API-16 | GET /v1/config-template/globalConf | 2 |
| API-17 | POST /v1/config-template/globalConf | 10 |
| API-18 | GET /v1/config-template/task | 2 |
| 通用 | 所有接口 | 7 |
| **总计** | **18个接口** | **127个用例** |

---

## 优先级分布

| 优先级 | 说明 | 用例数量 |
|--------|------|----------|
| P0 | 核心功能，必须通过 | 26 |
| P1 | 重要功能，应该通过 | 60 |
| P2 | 边界/异常场景，建议通过 | 41 |

---

## 备注

1. 本文档基于Swagger API定义生成，为契约测试用例
2. 业务规则相关的测试用例（如删除默认模板、禁用使用中模板等）需要根据实际业务逻辑调整
3. 认证相关测试未包含，因Swagger定义中未包含security配置
4. 测试数据中的具体ID值（如tpl-001）为示例，实际测试时需替换为真实数据
5. 部分边界测试的预期结果标注为"200或400"，需根据实际系统行为确认
