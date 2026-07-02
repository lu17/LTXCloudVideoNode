# 文件名: LTXCloudVideoNode.py
# 存放位置: ComfyUI/custom_nodes/LTXCloudVideoNode/

import json
import time
import requests
import torch
import folder_paths
from comfy.utils import ProgressBar

class LTXCloudVideoNode:
    """
    调用云端LTX视频生成API的ComfyUI节点
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "A cinematic shot of a futuristic city at night",
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": "low quality, blurry, distorted",
                }),
                "size": (["1920*1088", "1280*720", "720*480"], {"default": "1920*1088"}),
                "duration": ("INT", {"default": 5, "min": 1, "max": 30}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 999999999}),
                "api_url": ("STRING", {
                    "default": "https://your-api-endpoint.com/hermes/api/v1/services/aigc/video-generation/video-synthesis",
                }),
                "api_token": ("STRING", {
                    "default": "your-api-token-here",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("video_url", "task_id")
    FUNCTION = "generate_video"
    CATEGORY = "我的节点/LTXCloud"

    def generate_video(self, prompt, negative_prompt, size, duration, seed, api_url, api_token):
        """
        调用云端API生成视频
        """
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "ltx-2.3-22b-dev",
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
            },
            "parameters": {
                "size": size,
                "duration": duration,
                "prompt_extend": False,
                "seed": seed if seed != -1 else None,
            },
        }

        print(f"[LTXCloud] 开始生成视频，时长={duration}秒，尺寸={size}")

        try:
            submit_resp = requests.post(api_url, json=payload, headers=headers, timeout=30)
            submit_resp.raise_for_status()
            submit_data = submit_resp.json()
            
            task_id = self._extract_task_id(submit_data)
            if not task_id:
                return (f"ERROR: 未找到task_id - {submit_data}", "")

            print(f"[LTXCloud] 任务已提交，task_id={task_id}")

            poll_url = api_url.replace("/video-synthesis", "") + "/tasks/" + task_id
            
            max_attempts = 120
            for attempt in range(max_attempts):
                time.sleep(15)
                
                poll_resp = requests.get(poll_url, headers=headers, timeout=30)
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()
                
                status = poll_data.get("task_status") or poll_data.get("status", "").upper()
                print(f"[LTXCloud] 尝试 {attempt+1}/{max_attempts}, 状态: {status}")
                
                if status == "SUCCEEDED":
                    video_url = self._extract_video_url(poll_data)
                    if video_url:
                        print(f"[LTXCloud] ✅ 视频生成成功: {video_url}")
                        return (video_url, task_id)
                    else:
                        return (f"ERROR: 任务成功但未找到视频URL", task_id)
                        
                elif status in ["FAILED", "CANCELED", "UNKNOWN"]:
                    error_msg = poll_data.get("message", "未知错误")
                    return (f"ERROR: 任务{status} - {error_msg}", task_id)
            
            return (f"ERROR: 轮询超时（{max_attempts*15}秒）", task_id)
            
        except requests.exceptions.RequestException as e:
            return (f"ERROR: 网络请求失败 - {str(e)}", "")
        except Exception as e:
            return (f"ERROR: {str(e)}", "")

    def _extract_task_id(self, data):
        if isinstance(data, dict):
            if data.get("task_id"):
                return str(data["task_id"])
            for key in ["data", "result", "output"]:
                if isinstance(data.get(key), dict) and data[key].get("task_id"):
                    return str(data[key]["task_id"])
        return None

    def _extract_video_url(self, data):
        if not isinstance(data, dict):
            return None
        
        for path in [
            lambda d: d.get("video_url"),
            lambda d: d.get("output", {}).get("video_url"),
            lambda d: d.get("data", [{}])[0].get("output", {}).get("video_url"),
            lambda d: d.get("result", {}).get("video_url"),
        ]:
            try:
                url = path(data)
                if url and isinstance(url, str) and url.startswith("http"):
                    return url
            except:
                continue
        return None


# ==========================================
# 节点注册（适配云端ComfyUI环境）
# ==========================================

NODE_CLASS_MAPPINGS = {
    "LTXCloudVideoNode": LTXCloudVideoNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXCloudVideoNode": "LTX 云端视频生成",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
