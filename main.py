import gradio as gr
from typing import List
from scraper import scrape_website
from vector_store import create_vector_store, get_retriever
from rag_chain import setup_rag_chain
import logging
import os
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create assets directory if it doesn't exist
os.makedirs("assets", exist_ok=True)


class ChatBot:
    def __init__(self):
        self.chain = None
        self.vectorstore = None
        self.chat_history = []
        self.last_error = None

    def process_site(self, url: str):
        try:
            docs = scrape_website(url)
            self.vectorstore = create_vector_store(docs)
            self.chain = setup_rag_chain(get_retriever(self.vectorstore))
            self.chat_history = []
            return "✅ Ready! Ask short questions about this site.", ""
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.last_error = error_msg
            return "", error_msg

    def respond(self, message: str, chat_history: List):
        if not message.strip():
            return chat_history

        if self.last_error:
            chat_history.append((message, f"⚠️ System Error: {self.last_error}"))
            return chat_history

        if not self.chain:
            chat_history.append((message, "⚠️ Please process a website first"))
            return chat_history

        try:
            # Truncate long questions to save tokens
            truncated_msg = message[:150]  # Limit to 150 chars
            response = self.chain.invoke(truncated_msg)
            chat_history.append((message, response))
            return chat_history
        except Exception as e:
            error_msg = "⚠️ Rate limit exceeded - try shorter questions or wait a minute"
            if "rate_limit" not in str(e).lower():
                error_msg = f"❌ Error: {str(e)[:100]}..."  # Truncate long errors
            chat_history.append((message, error_msg))
            return chat_history
def create_interface():
    bot = ChatBot()

    # Custom CSS with compact layout
    css = """
    :root {
        --orange: #FF8C00;
        --light-bg: #FFFFFF;
        --light-accent: #F5F5F5;
        --text: #333333;
        --border: #E0E0E0;
    }
    .gradio-container {
        background-color: var(--light-bg) !important;
        color: var(--text) !important;
    }
    .chatbot {
        background-color: var(--light-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        height: 65vh !important;
        max-height: 65vh !important;
    }
    .user-message {
        background: var(--light-accent) !important;
        color: var(--text) !important;
        border-radius: 18px 18px 0 18px !important;
        padding: 8px 12px !important;
        margin-left: 20% !important;
        border: 1px solid var(--border) !important;
    }
    .bot-message {
        background: var(--light-accent) !important;
        color: var(--text) !important;
        border-radius: 18px 18px 18px 0 !important;
        padding: 8px 12px !important;
        margin-right: 20% !important;
        border: 1px solid var(--border) !important;
    }
    .textbox textarea {
        background-color: var(--light-bg) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        min-height: 40px !important;
        max-height: 80px !important;
        line-height: 1.4 !important;
    }
    button {
        background: var(--orange) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        height: auto !important;
    }
    .input-container {
        padding-top: 8px !important;
    }
    .title-container {
        text-align: center;
        margin-bottom: 12px !important;
    }
    .title {
        font-size: 2em !important;
    }
    .compact-row {
        gap: 8px !important;
        padding: 0 !important;
    }
    """

    with gr.Blocks(css=css) as demo:
        # Title with logo
        with gr.Column(elem_classes=["title-container"]):
            gr.Markdown("""
            <div>
                <span class="logo">🌐</span>
                <span class="title">Web Insight AI</span>
            </div>
            """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("**Website Setup**")
                url_input = gr.Textbox(
                    label="Enter Website URL",
                    placeholder="https://example.com",
                    lines=1,
                    max_lines=1
                )
                process_btn = gr.Button(
                    "Process Site",
                    variant="primary"
                )
                status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    elem_classes=["status"],
                    lines=1,
                    max_lines=1
                )

            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label=None,
                    bubble_full_width=False,
                    avatar_images=(
                        "assets/user.png",
                        "assets/bot.png"
                    ),
                    show_copy_button=True,
                    height="65vh"
                )
                with gr.Row(elem_classes=["compact-row"]):
                    msg = gr.Textbox(
                        placeholder="Type your question...",
                        show_label=False,
                        container=False,
                        scale=8,
                        lines=1,
                        max_lines=3
                    )
                    ask_btn = gr.Button(
                        "Ask",
                        variant="primary",
                        scale=1,
                        min_width=80
                    )
                clear_btn = gr.Button("Clear Chat", size="sm")

        # Event handlers
        process_btn.click(
            fn=bot.process_site,
            inputs=url_input,
            outputs=[status, status]
        )

        msg.submit(
            fn=bot.respond,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=False
        ).then(
            lambda: "",
            outputs=msg
        )

        ask_btn.click(
            fn=bot.respond,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=False
        ).then(
            lambda: "",
            outputs=msg
        )

        clear_btn.click(
            lambda: [],
            outputs=chatbot
        )

    return demo


if __name__ == "__main__":
    # Create default avatars if they don't exist
    if not os.path.exists("assets/user.png"):
        img = Image.new('RGB', (100, 100), color=(240, 240, 240))
        d = ImageDraw.Draw(img)
        d.text((50, 50), "👤", fill=(70, 70, 70), anchor="mm", font_size=40)
        img.save("assets/user.png")

    if not os.path.exists("assets/bot.png"):
        img = Image.new('RGB', (100, 100), color=(255, 165, 0))
        d = ImageDraw.Draw(img)
        d.text((50, 50), "🤖", fill=(255, 255, 255), anchor="mm", font_size=40)
        img.save("assets/bot.png")

    demo = create_interface()
    demo.launch()