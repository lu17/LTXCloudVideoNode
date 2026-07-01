# LTX Cloud Video Node

ComfyUI自定义节点，用于调用云端LTX视频生成API。

## 安装方式
通过 ComfyUI Manager -> Install via Git URL 安装

## 输入参数
- `prompt`: 正向提示词
- `negative_prompt`: 反向提示词
- `size`: 视频尺寸 (1920*1088, 1280*720, 720*480)
- `duration`: 视频时长 (1-30秒)
- `seed`: 随机种子 (-1为随机)
- `api_url`: 云端API地址
- `api_token`: 认证令牌

## 输出
- `video_url`: 生成的视频URL
- `task_id`: 任务ID