from __future__ import annotations
import json, threading, time
from .computer import Computer, ActionError
from .ollama_client import OllamaClient, OllamaError

SENSITIVE_WORDS = ("delete", "remove permanently", "erase", "send", "email", "message", "publish", "post publicly", "purchase", "buy", "pay", "payment", "install", "uninstall", "security setting", "firewall", "irreversible")

class AgentStopped(Exception): pass

class AutonomousAgent:
    def __init__(self, config: dict, computer: Computer, emit, approval, pause_event: threading.Event, stop_event: threading.Event):
        self.config=config; self.computer=computer; self.emit=emit; self.approval=approval
        self.pause_event=pause_event; self.stop_event=stop_event
        self.client=OllamaClient(config["ollama_url"], timeout=min(240, int(config["task_timeout_seconds"])))
    def _check(self, started):
        if self.stop_event.is_set(): raise AgentStopped("Stopped by user.")
        if time.monotonic()-started > self.config["task_timeout_seconds"]: raise TimeoutError("Task time limit reached.")
        while self.pause_event.is_set():
            if self.stop_event.wait(.2): raise AgentStopped("Stopped by user.")
            if time.monotonic()-started > self.config["task_timeout_seconds"]: raise TimeoutError("Task time limit reached while paused.")
    def _confirm(self, prompt: str) -> bool:
        answer=self.approval(prompt, 180)
        if answer is None: return False
        return bool(answer)
    def run(self, instruction: str) -> str:
        started=time.monotonic(); history=[]
        self.emit("status", "Checking local Ollama connection…")
        models=self.client.models()
        planner=self.config["planner_model"]; vision=self.config["vision_model"]
        if planner not in models: raise OllamaError(f"Planner model '{planner}' is not installed. Install it with the documented Ollama pull command.")
        if vision not in models: raise OllamaError(f"Vision model '{vision}' is not installed. Install it with the documented Ollama pull command.")
        self.emit("status", "Creating a concise task plan…")
        prefs=self.config.get("preferences", {})
        plan_prompt=("You are OmniPilot, a local desktop task planner. Return ONLY JSON: {\"steps\":[\"...\"]}. "
            "Make a short, practical plan (2-8 steps). Do not include commands or assume actions have happened. "
            "Respect privacy and never ask to bypass security. Answer in the user's language.\n"
            f"User instruction: {instruction}\nPreferences: {json.dumps(prefs,ensure_ascii=False)}")
        plan_obj=self.client.parse_json(self.client.generate(planner, plan_prompt))
        plan=plan_obj.get("steps", [])
        if not isinstance(plan,list) or not plan: plan=[instruction]
        plan=[str(x)[:300] for x in plan[:8]]
        self.emit("plan", plan)
        errors=0; last_result="Task just started."
        for step in range(1, self.config["max_steps"]+1):
            self._check(started)
            self.emit("progress", (step, self.config["max_steps"]))
            self.emit("status", f"Observing screen · action {step}/{self.config['max_steps']}")
            try: screenshot=self.computer.screenshot()
            except ActionError as e:
                if any(x in instruction.casefold() for x in ("file", "folder", "workspace", "create a", "write a")):
                    screenshot=None
                    last_result=f"Screen capture unavailable in this environment: {e}. File workspace operations remain possible."
                else: raise
            self.emit("screenshot", screenshot)
            prompt=("You control a Windows 11 desktop using exactly ONE bounded action at a time. Return ONLY one JSON object. "
                "Allowed types: click{x,y,button}, move{x,y}, type{text}, key{key}, scroll{amount}, wait{seconds}, "
                "open_app{name}, open_url{url}, list_files{path}, read_file{path}, create_file{path,content}, "
                "edit_file{path,content}, move_file{path,destination}, delete_file{path}, done{summary}, ask_user{question}. "
                "For coordinates, use the actual screenshot pixel dimensions and target visible controls. Never guess if the screen is unclear: wait, observe, or ask_user. "
                "The workspace file tools accept only relative paths within the configured workspace; use them for file operations rather than shell commands. "
                "Never execute shell, scripts, arbitrary commands, or access credentials. Never send/publish/pay/install/delete or change security settings without setting requires_confirmation=true. "
                "Use only the exact user-approved task; do not expand its scope. After an action, the next turn will show a fresh screenshot. "
                "When success is clearly verified, return {\"type\":\"done\",\"summary\":\"...\"}. "
                "Action JSON may include a short 'reason' and 'target' for audit.\n"
                f"USER GOAL: {instruction}\nPLAN: {json.dumps(plan,ensure_ascii=False)}\n"
                f"COMPLETED ACTION HISTORY: {json.dumps(history[-8:],ensure_ascii=False)}\nLAST RESULT: {last_result}\n"
                f"Screenshot image dimensions are {self.computer.last_image_size}; desktop input dimensions are {self.computer.last_screen_size}. "
                "Give click/move coordinates in screenshot-image pixels; the controller scales them to desktop pixels. "
                f"Respond in the user's language. Current step {step} of {self.config['max_steps']}.")
            try:
                raw=self.client.generate(vision,prompt,image=screenshot)
                action=self.client.parse_json(raw)
                kind=str(action.get("type", "")).lower()
                if kind=="done":
                    summary=str(action.get("summary", "Task completed and verified."))[:1000]
                    self.emit("status", "Task complete."); return summary
                if kind=="ask_user":
                    question=str(action.get("question", "The agent needs clarification."))[:1000]
                    summary="Clarification needed before continuing: " + question + "\nNo further action was taken. Submit a new task with the missing detail."
                    self.emit("status", "Waiting for clarification; no further action taken.")
                    return summary
                self._check(started)
                action_text=" ".join(str(action.get(k,"")) for k in ("type","reason","target","url","name","path","destination"))
                task_text=instruction.casefold()+" "+action_text.casefold()
                sensitive=bool(action.get("requires_confirmation",False)) or kind=="delete_file" or any(word in task_text for word in SENSITIVE_WORDS)
                if sensitive:
                    description=f"Confirm sensitive action: {kind}. Target/details: {action_text[:700]}\n\nOmniPilot will proceed only if you approve."
                    if not self._confirm(description):
                        last_result="Sensitive action declined; it was not executed. Continue with safe alternatives if possible."
                        history.append({"step":step,"action":kind,"result":"declined by user"})
                        continue
                if kind in {"click", "move"} and screenshot is not None:
                    image_w,image_h=self.computer.last_image_size; desktop_w,desktop_h=self.computer.last_screen_size
                    if image_w and image_h and desktop_w and desktop_h:
                        action["x"]=round(int(action.get("x",-1))*desktop_w/image_w)
                        action["y"]=round(int(action.get("y",-1))*desktop_h/image_h)
                self.emit("activity", {"step":step,"action":action})
                last_result=self.computer.perform(action)
                errors=0
                history.append({"step":step,"action":kind,"result":last_result[:700]})
                self.emit("activity_result", last_result)
            except (ActionError, OllamaError, ValueError, TypeError, KeyError) as e:
                errors+=1; last_result=f"Action error ({errors}/2): {e}"
                self.emit("error", last_result)
                if errors>=2:
                    raise RuntimeError(f"Repeated errors; stopping safely. Last error: {e}") from e
        raise RuntimeError(f"Reached the maximum of {self.config['max_steps']} actions without verified completion. The task was stopped safely.")
