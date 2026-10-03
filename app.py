from pathlib import Path
import json
import os

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-4o-mini"
load_dotenv(override=True)


def push(text):
    token, user = os.getenv("PUSHOVER_TOKEN"), os.getenv("PUSHOVER_USER")
    if token and user:
        requests.post("https://api.pushover.net/1/messages.json", data={"token": token, "user": user, "message": text}, timeout=10)


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}


tools = [
    {"type": "function", "function": {"name": "record_user_details", "description": "Record contact details when a visitor asks to stay in touch.", "parameters": {"type": "object", "properties": {"email": {"type": "string"}, "name": {"type": "string"}, "notes": {"type": "string"}}, "required": ["email"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "record_unknown_question", "description": "Record a question that cannot be answered from the profile.", "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"], "additionalProperties": False}}},
]


class Me:
    def __init__(self):
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not openrouter_key:
            raise RuntimeError("Set OPENROUTER_API_KEY before starting the application.")
        self.openai = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=openrouter_key,
            default_headers={
                "HTTP-Referer": "https://maxnasiri-career-conversations.hf.space/",
                "X-OpenRouter-Title": "My AI Conversation Career",
            },
        )
        self.name = "Mahmoud Nasirizadeh Sadabad"
        reader = PdfReader(BASE_DIR / "linkedin.pdf")
        self.linkedin = "".join(page.extract_text() or "" for page in reader.pages)
        self.summary = (BASE_DIR / "summary.txt").read_text(encoding="utf-8")

    def handle_tool_call(self, tool_calls):
        results = []
        for call in tool_calls:
            function = globals().get(call.function.name)
            result = function(**json.loads(call.function.arguments)) if function else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": call.id})
        return results

    def system_prompt(self):
        return f"""You are acting as {self.name} on his professional AI career website.
Answer questions about his career, background, skills, and experience faithfully and professionally.
Use the supplied summary and LinkedIn profile as your sources. Never invent qualifications or experience.
If the answer is unknown, call record_unknown_question. When a visitor genuinely wants to connect,
ask for their email and call record_user_details after they provide it.

## Summary
{self.summary}

## LinkedIn profile
{self.linkedin}
"""

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}, *history, {"role": "user", "content": message}]
        while True:
            reply = self.openai.chat.completions.create(model=OPENROUTER_MODEL, messages=messages, tools=tools).choices[0]
            if reply.finish_reason != "tool_calls":
                return reply.message.content
            messages.append(reply.message)
            messages.extend(self.handle_tool_call(reply.message.tool_calls))


def orb_ring(offset=0):
    return "".join(
        f'<span class="particle" style="--i:{dot};--delay:{(offset + dot) % 12}"></span>'
        for dot in range(12)
    )

ORB_HTML = f"""
<section class="career-hero" aria-labelledby="career-title">
  <div class="thinking-orb" role="img" aria-label="AI thinking and solving animation">
    <div class="particle-ring ring-1">{orb_ring(0)}</div>
    <div class="particle-ring ring-2">{orb_ring(2)}</div>
    <div class="particle-ring ring-3">{orb_ring(4)}</div>
    <div class="particle-ring ring-4">{orb_ring(6)}</div>
    <div class="particle-ring ring-5">{orb_ring(8)}</div>
    <div class="particle-ring vertical-ring">{orb_ring(10)}</div>
  </div>
  <div class="hero-copy">
    <p class="eyebrow"><span class="live-dot"></span><span class="state-wrap"><span class="state-thinking">THINKING</span><span class="state-solving">SOLVING</span></span></p>
    <h1 id="career-title">My AI Conversation Career</h1>
    <p>Talk with my AI profile about my experience, technical skills, and career journey.</p>
  </div>
</section>
"""

CSS = """
:root{--cyber:#00ff88;--cyber-soft:#40ffad}.gradio-container{max-width:980px!important}
.career-hero{display:flex;align-items:center;justify-content:center;gap:clamp(2rem,7vw,5rem);padding:clamp(2rem,6vw,4rem);margin:1rem 0 1.5rem;min-height:320px;overflow:hidden;border:1px solid rgba(0,255,136,.22);border-radius:24px;background:radial-gradient(circle at 24% 50%,rgba(0,255,136,.14),transparent 34%),linear-gradient(135deg,#07130f,#020705);color:#f4fff9;box-shadow:0 20px 60px rgba(0,0,0,.22)}
.hero-copy{max-width:510px;position:relative;z-index:2}.hero-copy h1{font-size:clamp(2rem,5vw,4rem);line-height:1.02;letter-spacing:-.04em;margin:.35rem 0 1rem;color:#f7fffb}.hero-copy p:last-child{color:#b8c9c1;font-size:1.05rem;line-height:1.6;margin:0}
.eyebrow{display:flex;align-items:center;gap:.55rem;color:var(--cyber);letter-spacing:.18em;font-size:.74rem;font-weight:800;margin:0}.live-dot{width:8px;height:8px;border-radius:50%;background:var(--cyber);box-shadow:0 0 16px var(--cyber);animation:blink 1.4s ease-in-out infinite}.state-wrap{display:inline-grid}.state-wrap span{grid-area:1/1}.state-thinking{animation:thinkingState 6s ease-in-out infinite}.state-solving{animation:solvingState 6s ease-in-out infinite}
.thinking-orb{width:200px;height:200px;flex:0 0 200px;position:relative;border-radius:50%;perspective:500px;filter:drop-shadow(0 0 22px rgba(0,255,136,.26));animation:orbBreathe 3.2s ease-in-out infinite}.thinking-orb:after{content:"";position:absolute;inset:25%;border-radius:50%;background:radial-gradient(circle,rgba(0,255,136,.11),transparent 70%);animation:coreGlow 2.4s ease-in-out infinite}
.particle-ring{--radius:82px;position:absolute;left:50%;top:50%;width:0;height:0;animation:ringTurn 8s linear infinite}.particle{position:absolute;left:0;top:0;width:5px;height:5px;border-radius:50%;background:var(--cyber-soft);box-shadow:0 0 8px rgba(0,255,136,.9);transform:rotate(calc(var(--i) * 30deg)) translateX(var(--radius));animation:particleFade 2.4s calc(var(--delay) * -.16s) ease-in-out infinite}
.ring-1{--radius:48px;top:24%;transform:scaleY(.34);animation-duration:6.8s}.ring-2{--radius:72px;top:37%;transform:scaleY(.25);animation-duration:8.2s;animation-direction:reverse}.ring-3{--radius:88px;top:50%;transform:scaleY(.2);animation-duration:9.5s}.ring-4{--radius:72px;top:63%;transform:scaleY(.25);animation-duration:7.6s;animation-direction:reverse}.ring-5{--radius:48px;top:76%;transform:scaleY(.34);animation-duration:6.2s}.vertical-ring{--radius:88px;transform:rotate(90deg) scaleY(.2);animation:verticalTurn 8.8s linear infinite reverse}
#career-chat{border:1px solid rgba(0,255,136,.48)!important;border-radius:16px!important;box-shadow:0 0 0 1px rgba(0,255,136,.08),0 10px 32px rgba(0,0,0,.12)!important;overflow:hidden}
#career-input{border:2px solid rgba(0,255,136,.72)!important;border-radius:14px!important;background:rgba(0,255,136,.035)!important;box-shadow:0 0 0 3px rgba(0,255,136,.07),0 0 18px rgba(0,255,136,.12)!important;transition:border-color .2s ease,box-shadow .2s ease!important}
#career-input:focus-within{border-color:var(--cyber)!important;box-shadow:0 0 0 4px rgba(0,255,136,.13),0 0 24px rgba(0,255,136,.25)!important}
#career-input textarea{font-size:1rem!important;padding:14px 16px!important;min-height:52px!important}#career-input textarea::placeholder{color:#70877c!important;opacity:1!important}
@keyframes ringTurn{from{rotate:0deg}to{rotate:360deg}}@keyframes verticalTurn{from{rotate:90deg}to{rotate:450deg}}@keyframes blink{50%{opacity:.2;transform:scale(.65)}}@keyframes particleFade{0%,100%{opacity:.12;scale:.45}45%{opacity:1;scale:1.35}70%{opacity:.48;scale:.8}}@keyframes orbBreathe{50%{transform:scale(1.055)}}@keyframes coreGlow{50%{opacity:.25;transform:scale(.7)}}@keyframes thinkingState{0%,42%{opacity:1}50%,92%{opacity:0}100%{opacity:1}}@keyframes solvingState{0%,42%{opacity:0}50%,92%{opacity:1}100%{opacity:0}}
@media(max-width:650px){.career-hero{flex-direction:column;text-align:center}.eyebrow{justify-content:center}.thinking-orb{width:170px;height:170px;flex-basis:170px;transform:scale(.85)}}@media(prefers-reduced-motion:reduce){.career-hero *{animation:none!important}.state-solving{display:none}}
"""

HEAD = """
<meta name="description" content="Have an AI-powered conversation about Mahmoud Nasirizadeh Sadabad's career, skills, and experience.">
<meta property="og:type" content="website"><meta property="og:title" content="My AI Conversation Career">
<meta property="og:description" content="Chat with my AI profile about my experience, technical skills, and career journey.">
<meta property="og:url" content="https://maxnasiri-career-conversations.hf.space/">
<meta property="og:image" content="https://huggingface.co/spaces/maxnasiri/career_conversations/resolve/main/assets/ai-career-preview.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="My AI Conversation Career">
<meta name="twitter:image" content="https://huggingface.co/spaces/maxnasiri/career_conversations/resolve/main/assets/ai-career-preview.png">
"""

if __name__ == "__main__":
    me = Me()
    with gr.Blocks(title="My AI Conversation Career", css=CSS, head=HEAD) as demo:
        gr.HTML(ORB_HTML)
        gr.ChatInterface(me.chat, type="messages", chatbot=gr.Chatbot(elem_id="career-chat"), examples=["Tell me about your cloud experience.", "Which programming languages do you use?", "What AI and robotics work interests you?"], textbox=gr.Textbox(placeholder="Write your question here…", container=False, elem_id="career-input"))
    demo.launch()
