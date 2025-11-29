# 测试用例文档

> 生成时间: 2025-11-29 12:51:47
> 接口数量: 14
> 用例总数: 98

---

## API: GET /v1/config-templates

**接口说明**: 采集指纹模板分页 - 分页查询采集指纹模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-001 | 正常查询-默认分页 | 系统中存在模板数据 | `params={}` (必填), 使用默认page=1, perPage=10 | 200, 返回PageDataHandBook结构，包含data数组、totalCount、pageCount、perPage、page | P0 |
| TC-002 | 正常查询-指定分页参数 | 系统中存在多页模板数据 | `page=2&perPage=20&params={}` | 200, 返回第2页数据，每页20条 | P0 |
| TC-003 | 正常查询-带筛选条件 | 存在指定模板 | `params={"templateName":"测试模板","isUse":"1"}` | 200, 返回符合条件的模板列表 | P0 |
| TC-004 | 正常查询-带排序参数 | 存在多条模板 | `params={"field":"createTime","order":"desc"}` | 200, 返回按创建时间降序排列的数据 | P1 |
| TC-005 | 异常-缺少必填参数params | 无 | `page=1&perPage=10` (不传params) | 400, 缺少必填参数params | P0 |
| TC-006 | 边界-page为0 | 无 | `page=0&perPage=10&params={}` | 400, 页码必须大于0 或 返回第1页数据 | P1 |
| TC-007 | 边界-page为负数 | 无 | `page=-1&perPage=10&params={}` | 400, 页码参数非法 | P1 |
| TC-008 | 边界-perPage为0 | 无 | `page=1&perPage=0&params={}` | 400, 每页数量必须大于0 | P1 |
| TC-009 | 边界-perPage为负数 | 无 | `page=1&perPage=-5&params={}` | 400, 每页数量参数非法 | P1 |
| TC-010 | 边界-perPage超大值 | 无 | `page=1&perPage=10000&params={}` | 200, 返回数据或限制最大值 | P2 |
| TC-011 | 边界-page超出范围 | 数据总共2页 | `page=999&perPage=10&params={}` | 200, 返回空data数组 | P2 |
| TC-012 | 异常-page类型错误 | 无 | `page=abc&perPage=10&params={}` | 400, 参数类型错误 | P1 |
| TC-013 | 边界-空数据查询 | 系统无模板数据 | `params={}` | 200, data为空数组, totalCount=0 | P1 |

---

## API: POST /v1/config-templates

**接口说明**: 添加模板 - 添加基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-014 | 正常添加模板-必填字段 | 无同名模板 | `{"templateName":"测试模板001","templateType":1}` | 200, success=true, 返回新建模板信息 | P0 |
| TC-015 | 正常添加模板-全字段 | 无同名模板 | `{"templateName":"完整模板","templateVer":"1.0","templateDesc":"描述","templateType":1,"isDefault":0,"isUse":1,"specification":"规范"}` | 200, success=true, 返回完整模板信息 | P0 |
| TC-016 | 异常-缺少RequestBody | 无 | 不传请求体 | 400, 请求体不能为空 | P0 |
| TC-017 | 异常-RequestBody为空对象 | 无 | `{}` | 400, 缺少必填字段 | P0 |
| TC-018 | 异常-模板名称为空 | 无 | `{"templateName":"","templateType":1}` | 400, 模板名称不能为空 | P0 |
| TC-019 | 异常-模板名称为null | 无 | `{"templateName":null,"templateType":1}` | 400, 模板名称不能为空 | P1 |
| TC-020 | 边界-模板名称超长 | 无 | `{"templateName":"a"*256,"templateType":1}` | 400, 模板名称长度超限 | P1 |
| TC-021 | 边界-模板名称特殊字符 | 无 | `{"templateName":"<script>alert(1)</script>","templateType":1}` | 400, 模板名称包含非法字符 或 200并转义存储 | P1 |
| TC-022 | 异常-templateType类型错误 | 无 | `{"templateName":"测试","templateType":"abc"}` | 400, 参数类型错误 | P1 |
| TC-023 | 异常-JSON格式错误 | 无 | `{"templateName":测试}` (非法JSON) | 400, JSON解析错误 | P1 |
| TC-024 | 边界-isDefault边界值 | 无 | `{"templateName":"测试","templateType":1,"isDefault":99}` | 400, isDefault值非法 或 200正常处理 | P2 |

---

## API: PUT /v1/config-templates

**接口说明**: 编辑模板 - 编辑基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-025 | 正常编辑模板 | 存在pkCollectTemplate=T001的模板 | `{"pkCollectTemplate":"T001","templateName":"更新后名称","templateType":1}` | 200, success=true, 返回更新后模板 | P0 |
| TC-026 | 正常编辑-部分字段更新 | 存在模板T001 | `{"pkCollectTemplate":"T001","templateDesc":"新描述"}` | 200, 仅描述字段更新 | P0 |
| TC-027 | 异常-缺少模板ID | 无 | `{"templateName":"测试"}` (不含pkCollectTemplate) | 400, 缺少模板ID | P0 |
| TC-028 | 异常-模板ID不存在 | 无此ID的模板 | `{"pkCollectTemplate":"NOT_EXIST","templateName":"测试"}` | 400/404, 模板不存在 | P0 |
| TC-029 | 异常-RequestBody为空 | 无 | 不传请求体 | 400, 请求体不能为空 | P0 |
| TC-030 | 边界-更新为重复名称 | 存在模板A和模板B | `{"pkCollectTemplate":"A_ID","templateName":"模板B的名称"}` | 400, 模板名称已存在 | P1 |
| TC-031 | 边界-模板ID为空字符串 | 无 | `{"pkCollectTemplate":"","templateName":"测试"}` | 400, 模板ID不能为空 | P1 |

---

## API: DELETE /v1/config-templates/{templateId}

**接口说明**: 删除模板 - 删除基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-032 | 正常删除模板 | 存在templateId=T001的模板 | `templateId=T001` | 200, success=true | P0 |
| TC-033 | 异常-模板ID不存在 | 无此ID模板 | `templateId=NOT_EXIST` | 400/404, 模板不存在 | P0 |
| TC-034 | 异常-模板ID为空 | 无 | `templateId=` (空字符串) | 400/404, 路径参数无效 | P1 |
| TC-035 | 边界-删除默认模板 | 存在默认模板 | `templateId=DEFAULT_TEMPLATE_ID` | 400, 默认模板不能删除 或 200成功删除 | P1 |
| TC-036 | 边界-删除正在使用的模板 | 模板被任务引用 | `templateId=IN_USE_ID` | 400, 模板正在使用中，无法删除 | P1 |
| TC-037 | 边界-templateId含特殊字符 | 无 | `templateId=../../../etc` | 400, 参数非法 | P2 |

---

## API: PATCH /v1/config-templates/{templateId}/enable

**接口说明**: 启用模板 - 启用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-038 | 正常启用已禁用模板 | 存在已禁用的模板T001 | `templateId=T001` | 200, success=true, isUse=1 | P0 |
| TC-039 | 边界-启用已启用模板 | 模板T001已启用 | `templateId=T001` | 200, 操作幂等，保持启用状态 | P1 |
| TC-040 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST` | 400/404, 模板不存在 | P0 |
| TC-041 | 异常-模板ID为空 | 无 | `templateId=` | 400/404, 路径参数无效 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/disable

**接口说明**: 禁用模板 - 禁用基线核查模板

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-042 | 正常禁用已启用模板 | 存在已启用的模板T001 | `templateId=T001` | 200, success=true, isUse=0 | P0 |
| TC-043 | 边界-禁用已禁用模板 | 模板T001已禁用 | `templateId=T001` | 200, 操作幂等，保持禁用状态 | P1 |
| TC-044 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST` | 400/404, 模板不存在 | P0 |
| TC-045 | 边界-禁用默认模板 | 存在默认模板 | `templateId=DEFAULT_ID` | 400, 默认模板不能禁用 或 200成功禁用 | P1 |

---

## API: PATCH /v1/config-templates/{templateId}/default

**接口说明**: 设置默认模板 - 将指定模板设置为默认

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-046 | 正常设置默认模板 | 存在非默认模板T001 | `templateId=T001` | 200, success=true, isDefault=1 | P0 |
| TC-047 | 边界-设置已是默认的模板 | T001已是默认模板 | `templateId=T001` | 200, 操作幂等 | P1 |
| TC-048 | 业务-切换默认模板 | T001是默认，T002非默认 | `templateId=T002` | 200, T002变为默认，T001取消默认 | P0 |
| TC-049 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST` | 400/404, 模板不存在 | P0 |
| TC-050 | 边界-设置禁用模板为默认 | T001已禁用 | `templateId=T001` | 400, 禁用模板不能设为默认 或 200成功 | P1 |

---

## API: GET /v1/config-templates/{templateId}/{optType}/basic

**接口说明**: 查询模板基本信息 - 根据模板ID查询模板基本信息

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-051 | 正常查询模板信息 | 存在模板T001 | `templateId=T001&optType=view` | 200, 返回模板基本信息 | P0 |
| TC-052 | 正常查询-不同optType | 存在模板T001 | `templateId=T001&optType=edit` | 200, 返回编辑模式下的模板信息 | P0 |
| TC-053 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST&optType=view` | 400/404, 模板不存在 | P0 |
| TC-054 | 异常-optType非法 | 存在模板T001 | `templateId=T001&optType=invalid` | 400, optType参数非法 | P1 |
| TC-055 | 异常-templateId为空 | 无 | `templateId=&optType=view` | 400/404, 路径参数无效 | P1 |

---

## API: GET /v1/config-templates/{templateId}/list

**接口说明**: 查询模板指纹列表 - 分页查询模板下的指纹列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-056 | 正常查询-默认分页 | 模板T001下有指纹 | `templateId=T001` | 200, 返回PageDataCheckitem | P0 |
| TC-057 | 正常查询-带分页参数 | 模板T001下有多页指纹 | `templateId=T001&page=2&perPage=20` | 200, 返回第2页数据 | P0 |
| TC-058 | 正常查询-带筛选条件 | 存在指定类型指纹 | `templateId=T001&assetTypeIds=AT001&riskLevel=high` | 200, 返回符合条件的指纹 | P0 |
| TC-059 | 正常查询-带排序 | 存在多条指纹 | `templateId=T001&field=createTime&order=desc` | 200, 按时间降序排列 | P1 |
| TC-060 | 正常查询-按检查项名称筛选 | 存在指定名称指纹 | `templateId=T001&checkItemName=密码策略` | 200, 返回名称匹配的指纹 | P1 |
| TC-061 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST` | 400/404, 模板不存在 | P0 |
| TC-062 | 边界-模板无指纹 | 模板T001下无指纹 | `templateId=T001` | 200, data为空数组 | P1 |

---

## API: GET /v1/config-templates/choose

**接口说明**: 指纹分页列表 - 查询指纹分页列表（已选/未选）

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-063 | 正常查询-已选指纹 | 模板T001有已选指纹 | `tempId=T001&selected=1` | 200, 返回已选指纹列表 | P0 |
| TC-064 | 正常查询-未选指纹 | 存在未选指纹 | `tempId=T001&selected=0` | 200, 返回未选指纹列表 | P0 |
| TC-065 | 正常查询-带分页 | 指纹数量超过一页 | `tempId=T001&page=1&perPage=20` | 200, 返回分页数据 | P0 |
| TC-066 | 正常查询-按指纹类型筛选 | 存在不同类型指纹 | `tempId=T001&fingerType=baseline` | 200, 返回指定类型指纹 | P1 |
| TC-067 | 正常查询-按资产类型筛选 | 存在不同资产指纹 | `tempId=T001&assetTypeCode=linux` | 200, 返回指定资产类型指纹 | P1 |
| TC-068 | 正常查询-按检查项名称搜索 | 存在指定名称指纹 | `tempId=T001&checkItemName=SSH` | 200, 返回名称包含SSH的指纹 | P1 |
| TC-069 | 边界-不传tempId | 无 | `selected=1` | 200, 返回所有已选指纹 或 400参数错误 | P2 |

---

## API: PUT /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加全部指纹 - 为模板添加全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-070 | 正常添加全部指纹 | 模板T001存在，有可添加指纹 | `templateId=T001`, body=`{}` | 200, success=true, entity返回添加数量 | P0 |
| TC-071 | 边界-已无可添加指纹 | 模板T001已包含全部指纹 | `templateId=T001`, body=`{}` | 200, entity=0 | P1 |
| TC-072 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST`, body=`{}` | 400/404, 模板不存在 | P0 |
| TC-073 | 异常-缺少RequestBody | 模板T001存在 | `templateId=T001`, 不传body | 400, 请求体不能为空 | P1 |

---

## API: PATCH /v1/config-templates/selectTemplate/{templateId}

**接口说明**: 添加选中指纹 - 为模板添加选中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-074 | 正常添加选中指纹 | 模板T001存在 | `templateId=T001`, body=`{"ids":["F001","F002"]}` | 200, success=true, entity=2 | P0 |
| TC-075 | 边界-添加空列表 | 模板T001存在 | `templateId=T001`, body=`{"ids":[]}` | 200, entity=0 | P1 |
| TC-076 | 边界-部分指纹已存在 | F001已在模板中 | `templateId=T001`, body=`{"ids":["F001","F002"]}` | 200, 仅添加F002，entity=1 | P1 |
| TC-077 | 异常-指纹ID不存在 | 无F999指纹 | `templateId=T001`, body=`{"ids":["F999"]}` | 400, 指纹不存在 或 200忽略无效ID | P1 |
| TC-078 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST`, body=`{"ids":["F001"]}` | 400/404, 模板不存在 | P0 |

---

## API: PUT /v1/config-templates/temps/{templateId}

**接口说明**: 删除全部指纹 - 删除模板中的全部指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-079 | 正常删除全部指纹 | 模板T001有指纹 | `templateId=T001`, body=`{}` | 200, success=true, entity返回删除数量 | P0 |
| TC-080 | 边界-模板无指纹 | 模板T001无指纹 | `templateId=T001`, body=`{}` | 200, entity=0 | P1 |
| TC-081 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST`, body=`{}` | 400/404, 模板不存在 | P0 |

---

## API: PATCH /v1/config-templates/temps/{templateId}

**接口说明**: 批量删除指纹 - 批量删除模板中的指纹

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-082 | 正常批量删除指纹 | 模板T001有F001,F002 | `templateId=T001`, body=`{"ids":["F001","F002"]}` | 200, success=true, entity=2 | P0 |
| TC-083 | 边界-删除空列表 | 模板T001存在 | `templateId=T001`, body=`{"ids":[]}` | 200, entity=0 | P1 |
| TC-084 | 边界-部分指纹不在模板中 | F001在模板中，F999不在 | `templateId=T001`, body=`{"ids":["F001","F999"]}` | 200, 仅删除F001, entity=1 | P1 |
| TC-085 | 异常-模板ID不存在 | 无此模板 | `templateId=NOT_EXIST`, body=`{"ids":["F001"]}` | 400/404, 模板不存在 | P0 |

---

## API: POST /v1/config-templates/isExist

**接口说明**: 唯一性校验 - 校验模板名称是否重复

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-086 | 正常校验-名称不存在 | 无同名模板 | `checkType=name&checkValue=新模板&id=` | 200, entity=false (不重复) | P0 |
| TC-087 | 正常校验-名称已存在 | 存在"测试模板" | `checkType=name&checkValue=测试模板&id=` | 200, entity=true (重复) | P0 |
| TC-088 | 正常校验-排除自身 | T001名为"测试模板" | `checkType=name&checkValue=测试模板&id=T001` | 200, entity=false (排除自身不算重复) | P0 |
| TC-089 | 异常-缺少checkType | 无 | `checkValue=测试&id=` | 400, 缺少必填参数checkType | P0 |
| TC-090 | 异常-缺少checkValue | 无 | `checkType=name&id=` | 400, 缺少必填参数checkValue | P0 |
| TC-091 | 异常-缺少id | 无 | `checkType=name&checkValue=测试` | 400, 缺少必填参数id | P0 |
| TC-092 | 边界-checkValue为空字符串 | 无 | `checkType=name&checkValue=&id=` | 400, 校验值不能为空 | P1 |

---

## API: GET /v1/config-template/globalConf

**接口说明**: 获取全局配置 - 获取基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-093 | 正常获取全局配置 | 存在全局配置 | 无参数 | 200, 返回TaskGlobalConfig对象 | P0 |
| TC-094 | 边界-无全局配置 | 系统初始化，无配置 | 无参数 | 200, 返回默认配置或entity为null | P1 |

---

## API: POST /v1/config-template/globalConf

**接口说明**: 保存全局配置 - 保存基线全局配置

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-095 | 正常保存全局配置 | 无 | `{"saveOriginalResult":true,"pageShowOriginalResult":true,"enableAssetTypeCheck":false,"originalResultSaveType":1,"taskRedundancyTime":30,"pointCount":100}` | 200, success=true, 返回保存后的配置 | P0 |
| TC-096 | 异常-缺少RequestBody | 无 | 不传请求体 | 400, 请求体不能为空 | P0 |
| TC-097 | 边界-originalResultSaveTypeEnum非法值 | 无 | `{"originalResultSaveTypeEnum":"INVALID"}` | 400, 枚举值非法，仅支持FILE或DB | P1 |
| TC-098 | 边界-taskRedundancyTime为负数 | 无 | `{"taskRedundancyTime":-1}` | 400, 冗余时间不能为负数 | P1 |

---

## API: GET /v1/config-template/task

**接口说明**: 查询任务模板列表 - 查询用于任务的模板列表

| 用例ID | 场景 | 前置条件 | 测试数据 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-099 | 正常查询任务模板 | 存在启用的模板 | 无参数 | 200, 返回HandBook列表 | P0 |
| TC-100 | 边界-无可用模板 | 所有模板已禁用 | 无参数 | 200, entity为空数组 | P1 |

---

## 测试覆盖统计

| 测试类型 | 用例数量 |
|----------|----------|
| 正向测试 | 35 |
| 参数验证 | 28 |
| 边界测试 | 30 |
| 业务规则 | 5 |
| **总计** | **98** |

## 优先级分布

| 优先级 | 用例数量 | 说明 |
|--------|----------|------|
| P0 | 42 | 核心功能，必须通过 |
| P1 | 45 | 重要功能，应该通过 |
| P2 | 11 | 边界场景，建议通过 |

## 注意事项

1. **认证说明**: 当前Swagger定义未包含security配置，如实际接口需要认证，请补充以下测试：
   - 无Token访问
   - 错误Token访问
   - Token过期访问

2. **数据准备**: 执行测试前需准备测试数据，包括：
   - 至少3个测试模板（含默认模板、启用模板、禁用模板）
   - 至少10条指纹数据
   - 全局配置初始化

3. **测试顺序建议**:
   - 先执行GET接口的P0用例验证查询功能
   - 再执行POST创建数据
   - 最后执行PUT/PATCH/DELETE修改和删除操作

4. **清理策略**: 测试完成后清理测试数据，避免影响后续测试
