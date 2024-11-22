## E2E自动化用例生成

### 配置

在`local.yml`中配置测试环境 knowledgeSeeker 服务的地址，替换 app.yml 中的

```yaml
  KnowledgeSeeker:
    base_url: http://10.65.178.107:5500
    user: chatgpt-server
    token: ks-fs43kLO03dm3nx
```

### knowledgeSeeker作用

用来进行e2e自动化生成的数据检索,项目地址:

```yaml
http://code.sangfor.org/test/ATT/devops/chatgpt/KnowledgeSeeker
```

### 方案

```yaml
https://docs.atrust.sangfor.com/pages/viewpage.action?pageId=351282751
```

### 数据库表说明

- `ai_e2e_case_task`用来存生成任务记录，一次调用一条记录
- `ai_e2e_case_task_events` 表示一次生成任务不同阶段的事件
    - 通过`ai_e2e_case_task_id`和主记录关联
    - `data`记录过程中输入输出的json数据
    - 当前只有检索和生成阶段记录了，手工用例校验没有用ai去校验，ai过于严格
