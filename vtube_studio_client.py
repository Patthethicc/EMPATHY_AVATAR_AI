import asyncio
import json
from typing import Optional, Dict

import websockets


class VTubeStudioClient:
    """Client for VTube Studio WebSocket API."""

    def __init__(
        self,
        auth_token: Optional[str] = None,
        emotion_hotkeys: Optional[Dict[str, str]] = None,
        host: str = "localhost",
        port: int = 8001,
    ):
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self.emotion_hotkeys = emotion_hotkeys or {}
        self.ws = None
        self.hotkey_cache = {}  # Cache hotkey IDs by name
        self._last_active_hotkey: Optional[str] = None  # Track last expression to avoid toggle overlap

    async def connect(self) -> None:
        """Connect to VTube Studio WebSocket."""
        uri = f"ws://{self.host}:{self.port}"
        self.ws = await websockets.connect(uri)
        
        # If no token yet, request one so the user can approve in VTS.
        if not self.auth_token:
            token_request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "token_request",
                "messageType": "AuthenticationTokenRequest",
                "data": {
                    "pluginName": "Avatar Chatbot",
                    "pluginDeveloper": "EMPATHY Group",
                },
            }
            await self.ws.send(json.dumps(token_request))
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=30)
                token_data = json.loads(response)
                token = token_data.get("data", {}).get("authenticationToken")
                if token:
                    self.auth_token = token
                    print("\n[info] Save this token as VTS_AUTH_TOKEN in your .env to skip prompts:\n"
                          f"{token}\n")
                else:
                    print("[warn] Did not receive authentication token from VTS. Click 'Allow' in the popup and try again.")
            except asyncio.TimeoutError:
                print("[warn] Timed out waiting for VTS authentication token. Ensure the popup is allowed and try again.")
                raise

        # Authenticate using the token
        if self.auth_token:
            auth_request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "auth_request",
                "messageType": "AuthenticationRequest",
                "data": {
                    "pluginName": "Avatar Chatbot",
                    "pluginDeveloper": "EMPATHY Group",
                    "authenticationToken": self.auth_token,
                },
            }
            await self.ws.send(json.dumps(auth_request))
            response = await self.ws.recv()
            auth_data = json.loads(response)
            
            if not auth_data.get("data", {}).get("authenticated", False):
                raise Exception("Authentication failed")
        
        # Load available hotkeys into cache
        await self._load_hotkeys()

    async def _load_hotkeys(self) -> None:
        """Load and cache all available hotkeys from current model."""
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "hotkey_list",
            "messageType": "HotkeysInCurrentModelRequest",
            "data": {}
        }
        
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        # Handle API errors explicitly.
        if data.get("messageType") == "APIError":
            print(f"[warn] VTS hotkey list error: {data.get('data')}")
            return
        
        # Cache hotkey IDs by name (only expressions, skip empty names)
        for hotkey in data.get("data", {}).get("availableHotkeys", []):
            name = hotkey.get("name", "").strip()
            hotkey_id = hotkey.get("hotkeyID")
            hotkey_type = hotkey.get("type")
            
            # Only cache ToggleExpression hotkeys with non-empty names
            if name and hotkey_id and hotkey_type == "ToggleExpression":
                self.hotkey_cache[name] = hotkey_id
        
        print(f"[debug] Loaded {len(self.hotkey_cache)} expression hotkeys: {list(self.hotkey_cache.keys())}")

    async def apply_emotion(self, emotion: str) -> None:
        """Apply emotion by triggering the corresponding hotkey."""
        if not self.ws:
            raise Exception("Not connected to VTube Studio")
        
        # Map emotion to hotkey name
        hotkey_name = self.emotion_hotkeys.get(emotion.lower())
        if not hotkey_name:
            print(f"[warn] No hotkey mapping for emotion: {emotion}")
            return
        
        # Get hotkey ID from cache
        hotkey_id = self.hotkey_cache.get(hotkey_name)
        # If not cached, refresh once.
        if not hotkey_id:
            await self._load_hotkeys()
            hotkey_id = self.hotkey_cache.get(hotkey_name)
        if not hotkey_id:
            print(f"[warn] Hotkey '{hotkey_name}' not found in model")
            return

        # If the same hotkey is already active, skip to avoid toggling it off.
        if self._last_active_hotkey == hotkey_name:
            return

        # If another expression was active, toggle it off first.
        if self._last_active_hotkey and self._last_active_hotkey in self.hotkey_cache:
            await self._trigger_hotkey(self._last_active_hotkey)

        # Trigger the new hotkey
        await self._trigger_hotkey(hotkey_name, hotkey_id, emotion)
        self._last_active_hotkey = hotkey_name

    async def _trigger_hotkey(self, hotkey_name: str, hotkey_id: Optional[str] = None, emotion: Optional[str] = None) -> None:
        """Trigger a hotkey by name/id; reloads ID if missing."""
        if not hotkey_id:
            hotkey_id = self.hotkey_cache.get(hotkey_name)
            if not hotkey_id:
                await self._load_hotkeys()
                hotkey_id = self.hotkey_cache.get(hotkey_name)
        if not hotkey_id:
            print(f"[warn] Hotkey '{hotkey_name}' not found in model")
            return

        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"trigger_{emotion or hotkey_name}",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": hotkey_id  # Use ID instead of name
            }
        }
        
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        result = json.loads(response)
        
        # Check for errors
        if result.get("messageType") == "APIError" or "errorID" in result:
            raise Exception(f"VTS rejected hotkey '{hotkey_name}': {result.get('data', result)}")
        
        print(f"[debug] Applied emotion: {emotion} -> {hotkey_name}")

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.ws = None
