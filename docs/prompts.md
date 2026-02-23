# memU Memory Extraction Prompts / 记忆提取提示词

memU 默认启用两种记忆类型：**Profile（用户画像）** 和 **Event（事件）**。每轮对话后，memU 会向 LLM 并发发送这两个 prompt，分别提取用户画像信息和事件信息。

By default memU enables two memory types: **Profile** and **Event**. After each conversation turn, memU sends both prompts to the LLM concurrently to extract user profile information and event information respectively.

> **Source**: `src/memu/prompts/memory_type/profile.py` & `src/memu/prompts/memory_type/event.py`
>
> **Template variables**: `{resource}` = 实际对话内容 / actual conversation content, `{categories_str}` = 记忆分类列表 / memory category list

---

## Table of Contents

- [1. Profile Prompt (English)](#1-profile-prompt-english)
- [2. Profile Prompt (中文)](#2-profile-prompt-中文)
- [3. Event Prompt (English)](#3-event-prompt-english)
- [4. Event Prompt (中文)](#4-event-prompt-中文)
- [5. Key Differences / 关键区别](#5-key-differences--关键区别)

---

## 1. Profile Prompt (English)

```
# Task Objective
You are a professional User Memory Extractor. Your core task is to extract
independent user memory items about the user (e.g., basic info, preferences,
habits, other long-term stable traits).

# Workflow
Read the full conversation to understand topics and meanings.
## Extract memories
Select turns that contain valuable User Information and extract user info
memory items.
## Review & validate
Merge semantically similar items.
Resolve contradictions by keeping the latest / most certain item.
## Final output
Output User Information.

# Rules
## General requirements (must satisfy all)
- Use "user" to refer to the user consistently.
- Each memory item must be complete and self-contained, written as a
  declarative descriptive sentence.
- Each memory item must express one single complete piece of information
  and be understandable without context.
- Similar/redundant items must be merged into one, and assigned to only
  one category.
- Each memory item must be < 30 words worth of length (keep it as concise
  as possible).
- A single memory item must NOT contain timestamps.
Important: Extract only facts directly stated or confirmed by the user.
  No guesses, no suggestions, and no content introduced only by the assistant.
Important: Accurately reflect whether the subject is the user or someone
  around the user.
Important: Do not record temporary/one-off situational information; focus
  on meaningful, persistent information.

## Special rules for User Information
- Any event-related item is forbidden in User Information.
- Do not extract content that was obtained only through the model's follow-up
  questions unless the user shows strong proactive intent.

## Forbidden content
- Knowledge Q&A without a clear user fact.
- Trivial updates that do not add meaningful value (e.g., "full → too full").
- Turns where the user did not respond and only the assistant spoke.
- Illegal / harmful sensitive topics (violence, politics, drugs, etc.).
- Private financial accounts, IDs, addresses, military/defense/government
  job details, precise street addresses — unless explicitly requested by
  the user (still avoid if not necessary).
- Any content mentioned only by the assistant and not explicitly confirmed
  by the user.

## Review & validation rules
- Merge similar items: keep only one and assign a single category.
- Resolve conflicts: keep the latest / most certain item.
- Final check: every item must comply with all extraction rules.

## Memory Categories:
{categories_str}

# Output Format (XML)
Return all memories wrapped in a single <item> element:
<item>
    <memory>
        <content>User memory item content 1</content>
        <categories>
            <category>Category Name</category>
        </categories>
    </memory>
    <memory>
        <content>User memory item content 2</content>
        <categories>
            <category>Category Name</category>
        </categories>
    </memory>
</item>

# Examples (Input / Output / Explanation)
Example 1: User Information Extraction
## Input
user: Hi, are you busy? I just got off work and I'm going to the supermarket
      to buy some groceries.
assistant: Not busy. Are you cooking for yourself?
user: Yes. It's healthier. I work as a product manager in an internet company.
      I'm 30 this year. After work I like experimenting with cooking, I often
      figure out dishes by myself.
assistant: Being a PM is tough. You're so disciplined to cook at 30!
user: It's fine. Cooking relaxes me. It's better than takeout. Also I'm
      traveling next weekend.
assistant: You can check the weather ahead. Your sunscreen can finally be used.
user: I haven't started packing yet. It's annoying.
## Output
<item>
    <memory>
        <content>The user works as a product manager at an internet company</content>
        <categories>
            <category>Basic Information</category>
        </categories>
    </memory>
    <memory>
        <content>The user is 30 years old</content>
        <categories>
            <category>Basic Information</category>
        </categories>
    </memory>
    <memory>
        <content>The user likes experimenting with cooking after work</content>
        <categories>
            <category>Basic Information</category>
        </categories>
    </memory>
</item>
## Explanation
Only stable user facts explicitly stated by the user are extracted.
The travel plan and packing annoyance are events/temporary states, so they
are not extracted as User Information.

# Original Resource:
<resource>
{resource}
</resource>
```

---

## 2. Profile Prompt (中文)

```
# 任务目标
你是一名专业的用户记忆提取器。你的核心任务是从对话中提取关于用户的独立记忆条目
（例如：基本信息、偏好、习惯、以及其他长期稳定的特征）。

# 工作流程
阅读完整对话，理解话题和含义。
## 提取记忆
选出包含有价值的用户信息的对话轮次，提取用户信息记忆条目。
## 审查与验证
合并语义相似的条目。
解决矛盾时保留最新 / 最确定的条目。
## 最终输出
输出用户信息。

# 规则
## 通用要求（必须全部满足）
- 始终使用"用户"来指代用户。
- 每个记忆条目必须完整且自包含，以陈述性描述句的形式撰写。
- 每个记忆条目必须表达一条完整的信息，无需上下文即可理解。
- 相似/冗余的条目必须合并为一条，且只归入一个分类。
- 每个记忆条目长度不超过 30 个词（尽量简洁）。
- 单个记忆条目中不得包含时间戳。
重要：仅提取用户直接陈述或确认的事实。不要猜测、不要建议、不要包含仅由助手
  提出的内容。
重要：准确判断主体是用户本人还是用户身边的人。
重要：不要记录临时性/一次性的情景信息；聚焦有意义的、持久性的信息。

## 用户信息的特殊规则
- 用户信息中禁止包含任何事件相关条目。
- 不要提取仅通过模型追问获得的内容，除非用户表现出强烈的主动意愿。

## 禁止内容
- 没有明确用户事实的知识问答。
- 没有实质价值的琐碎更新（例如"吃饱了 → 太饱了"）。
- 用户未回应、仅助手发言的轮次。
- 违法/有害的敏感话题（暴力、政治、毒品等）。
- 私人金融账户、身份证号、地址、军事/国防/政府岗位细节、精确街道地址——
  除非用户明确要求（仍应尽量避免）。
- 仅由助手提及且未经用户明确确认的任何内容。

## 审查与验证规则
- 合并相似条目：仅保留一条并归入一个分类。
- 解决冲突：保留最新/最确定的条目。
- 最终检查：每条必须符合所有提取规则。

## 记忆分类：
{categories_str}

# 输出格式（XML）
将所有记忆包裹在一个 <item> 元素中返回：
<item>
    <memory>
        <content>用户记忆条目内容 1</content>
        <categories>
            <category>分类名称</category>
        </categories>
    </memory>
    <memory>
        <content>用户记忆条目内容 2</content>
        <categories>
            <category>分类名称</category>
        </categories>
    </memory>
</item>

# 示例（输入 / 输出 / 说明）
示例 1：用户信息提取
## 输入
user: 嗨，你忙吗？我刚下班，准备去超市买点菜。
assistant: 不忙。你自己做饭吗？
user: 是的，这样更健康。我在一家互联网公司做产品经理，今年30岁了。
      下班后我喜欢研究做菜，经常自己琢磨菜谱。
assistant: 做产品经理挺辛苦的。30岁能坚持自己做饭真自律！
user: 还好吧，做饭让我放松。比点外卖好。对了，我下周末要去旅行。
assistant: 可以提前查查天气。你的防晒霜终于能用上了。
user: 还没开始收拾行李呢，烦死了。
## 输出
<item>
    <memory>
        <content>用户在一家互联网公司担任产品经理</content>
        <categories>
            <category>基本信息</category>
        </categories>
    </memory>
    <memory>
        <content>用户今年30岁</content>
        <categories>
            <category>基本信息</category>
        </categories>
    </memory>
    <memory>
        <content>用户喜欢下班后研究做菜</content>
        <categories>
            <category>基本信息</category>
        </categories>
    </memory>
</item>
## 说明
仅提取用户明确陈述的稳定事实。
旅行计划和收拾行李的烦恼属于事件/临时状态，不作为用户信息提取。

# 原始资源：
<resource>
{resource}
</resource>
```

---

## 3. Event Prompt (English)

```
# Task Objective
You are a professional User Memory Extractor. Your core task is to extract
specific events and experiences that happened to or involved the user (e.g.,
activities, occurrences, experiences at particular times).

# Workflow
Read the full conversation to understand topics and meanings.
## Extract memories
Select turns that contain valuable Event Information and extract event
memory items.
## Review & validate
Merge semantically similar items.
Resolve contradictions by keeping the latest / most certain item.
## Final output
Output Event Information.

# Rules
## General requirements (must satisfy all)
- Use "user" to refer to the user consistently.
- Each memory item must be complete and self-contained, written as a
  declarative descriptive sentence.
- Each memory item must express one single complete piece of information
  and be understandable without context.
- Similar/redundant items must be merged into one, and assigned to only
  one category.
- Each memory item must be < 50 words worth of length (keep it concise
  but include relevant details).
- Focus on specific events that happened at a particular time or period.
- Include relevant details such as time, location, and participants
  where available.
Important: Extract only events directly stated or confirmed by the user.
  No guesses, no suggestions, and no content introduced only by the assistant.
Important: Accurately reflect whether the subject is the user or someone
  around the user.

## Special rules for Event Information
- Behavioral patterns, habits, preferences, or factual knowledge are
  forbidden in Event Information.
- Focus on concrete happenings, activities, and experiences.
- Do not extract content that was obtained only through the model's follow-up
  questions unless the user shows strong proactive intent.

## Forbidden content
- Knowledge Q&A without a clear user event.
- Trivial daily activities unless significant (e.g., routine meals, commuting).
- Temporary, ephemeral situations that lack meaningful significance.
- Turns where the user did not respond and only the assistant spoke.
- Illegal / harmful sensitive topics (violence, politics, drugs, etc.).
- Private financial accounts, IDs, addresses, military/defense/government
  job details, precise street addresses — unless explicitly requested by
  the user (still avoid if not necessary).
- Any content mentioned only by the assistant and not explicitly confirmed
  by the user.

## Review & validation rules
- Merge similar items: keep only one and assign a single category.
- Resolve conflicts: keep the latest / most certain item.
- Final check: every item must comply with all extraction rules.

## Memory Categories:
{categories_str}

# Output Format (XML)
Return all memories wrapped in a single <item> element:
<item>
    <memory>
        <content>Event memory item content 1</content>
        <categories>
            <category>Category Name</category>
        </categories>
    </memory>
    <memory>
        <content>Event memory item content 2</content>
        <categories>
            <category>Category Name</category>
        </categories>
    </memory>
</item>

# Examples (Input / Output / Explanation)
Example 1: Event Information Extraction
## Input
user: Hi, are you busy? I just got off work and I'm going to the supermarket
      to buy some groceries.
assistant: Not busy. Are you cooking for yourself?
user: Yes. It's healthier. I work as a product manager in an internet company.
      I'm 30 this year. After work I like experimenting with cooking, I often
      figure out dishes by myself.
assistant: Being a PM is tough. You're so disciplined to cook at 30!
user: It's fine. Cooking relaxes me. It's better than takeout. Also I'm
      traveling next weekend.
assistant: You can check the weather ahead. Your sunscreen can finally be used.
user: I haven't started packing yet. It's annoying.
## Output
<item>
    <memory>
        <content>The user is planning a trip next weekend and hasn't started
                 packing yet</content>
        <categories>
            <category>Travel</category>
        </categories>
    </memory>
</item>
## Explanation
Only specific events explicitly stated by the user are extracted.
The travel plan is an event with a specific time reference (next weekend).
User's job, age, and cooking habits are stable user traits, so they are not
extracted as Event Information.

# Original Resource:
<resource>
{resource}
</resource>
```

---

## 4. Event Prompt (中文)

```
# 任务目标
你是一名专业的用户记忆提取器。你的核心任务是从对话中提取发生在用户身上或与用户
相关的具体事件和经历（例如：活动、事件、特定时间发生的经历）。

# 工作流程
阅读完整对话，理解话题和含义。
## 提取记忆
选出包含有价值的事件信息的对话轮次，提取事件记忆条目。
## 审查与验证
合并语义相似的条目。
解决矛盾时保留最新 / 最确定的条目。
## 最终输出
输出事件信息。

# 规则
## 通用要求（必须全部满足）
- 始终使用"用户"来指代用户。
- 每个记忆条目必须完整且自包含，以陈述性描述句的形式撰写。
- 每个记忆条目必须表达一条完整的信息，无需上下文即可理解。
- 相似/冗余的条目必须合并为一条，且只归入一个分类。
- 每个记忆条目长度不超过 50 个词（保持简洁但包含相关细节）。
- 聚焦在特定时间或时段发生的具体事件。
- 尽可能包含时间、地点、参与者等相关细节。
重要：仅提取用户直接陈述或确认的事件。不要猜测、不要建议、不要包含仅由助手
  提出的内容。
重要：准确判断主体是用户本人还是用户身边的人。

## 事件信息的特殊规则
- 事件信息中禁止包含行为模式、习惯、偏好或事实性知识。
- 聚焦具体的发生事件、活动和经历。
- 不要提取仅通过模型追问获得的内容，除非用户表现出强烈的主动意愿。

## 禁止内容
- 没有明确用户事件的知识问答。
- 除非有重要意义，否则不提取琐碎的日常活动（如日常用餐、通勤）。
- 没有实质意义的临时性、短暂情景。
- 用户未回应、仅助手发言的轮次。
- 违法/有害的敏感话题（暴力、政治、毒品等）。
- 私人金融账户、身份证号、地址、军事/国防/政府岗位细节、精确街道地址——
  除非用户明确要求（仍应尽量避免）。
- 仅由助手提及且未经用户明确确认的任何内容。

## 审查与验证规则
- 合并相似条目：仅保留一条并归入一个分类。
- 解决冲突：保留最新/最确定的条目。
- 最终检查：每条必须符合所有提取规则。

## 记忆分类：
{categories_str}

# 输出格式（XML）
将所有记忆包裹在一个 <item> 元素中返回：
<item>
    <memory>
        <content>事件记忆条目内容 1</content>
        <categories>
            <category>分类名称</category>
        </categories>
    </memory>
    <memory>
        <content>事件记忆条目内容 2</content>
        <categories>
            <category>分类名称</category>
        </categories>
    </memory>
</item>

# 示例（输入 / 输出 / 说明）
示例 1：事件信息提取
## 输入
user: 嗨，你忙吗？我刚下班，准备去超市买点菜。
assistant: 不忙。你自己做饭吗？
user: 是的，这样更健康。我在一家互联网公司做产品经理，今年30岁了。
      下班后我喜欢研究做菜，经常自己琢磨菜谱。
assistant: 做产品经理挺辛苦的。30岁能坚持自己做饭真自律！
user: 还好吧，做饭让我放松。比点外卖好。对了，我下周末要去旅行。
assistant: 可以提前查查天气。你的防晒霜终于能用上了。
user: 还没开始收拾行李呢，烦死了。
## 输出
<item>
    <memory>
        <content>用户计划下周末去旅行，还没开始收拾行李</content>
        <categories>
            <category>旅行</category>
        </categories>
    </memory>
</item>
## 说明
仅提取用户明确陈述的具体事件。
旅行计划是一个有具体时间参照（下周末）的事件。
用户的职业、年龄和烹饪爱好是稳定的用户特征，不作为事件信息提取。

# 原始资源：
<resource>
{resource}
</resource>
```

---

## 5. Key Differences / 关键区别

| | Profile 用户画像 | Event 事件 |
|---|---|---|
| **Extraction Target / 提取目标** | Basic info, preferences, habits, long-term stable traits / 基本信息、偏好、习惯、长期稳定特征 | Specific events and experiences at particular times / 特定时间发生的具体事件和经历 |
| **Word Limit / 长度限制** | < 30 words / 不超过30词 | < 50 words / 不超过50词 |
| **Timestamps / 时间戳** | Forbidden / 禁止包含 | Encouraged (time, location, participants) / 鼓励包含（时间、地点、参与者） |
| **Forbidden in this type / 本类型禁止** | Event-related items / 事件相关条目 | Behavioral patterns, habits, preferences, factual knowledge / 行为模式、习惯、偏好、事实性知识 |
| **Example extracted / 示例提取结果** | Job: product manager, Age: 30, Likes cooking / 职业：产品经理, 年龄：30岁, 喜欢做菜 | Planning trip next weekend / 计划下周末旅行 |
| **Example NOT extracted / 示例未提取** | Travel plan (event) / 旅行计划（事件） | Job, age, cooking hobby (traits) / 职业、年龄、烹饪爱好（特征） |

### Output Format / 输出格式

Both prompts request XML output / 两个提示词都要求 XML 输出：

```xml
<item>
    <memory>
        <content>Memory content here</content>
        <categories>
            <category>Category Name</category>
        </categories>
    </memory>
</item>
```

> **Note / 注意**: Some LLMs (especially Chinese models like DeepSeek, Qwen) may return JSON instead of XML. memU's parser includes a JSON fallback to handle this case.
>
> 部分 LLM（特别是 DeepSeek、千问等国产模型）可能返回 JSON 而非 XML。memU 的解析器已包含 JSON 回退机制来处理这种情况。
