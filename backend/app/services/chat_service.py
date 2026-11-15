"""
Chat Service — Manages SLM text generation and conversation persistence.

Uses pinned DistilGPT2 (82M) per Doc 01 (§6) & 04 (§5).
"""

from pathlib import Path
import time
import torch
import torch.nn.functional as F
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.config import settings
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse
from ml.inference.engine import inference_engine


class ChatService:
    """Singleton SLM generation service delegating to InferenceEngine & ModelRegistry."""

    async def handle_chat(
        self,
        request: ChatRequest,
        db: AsyncSession,
        user_id: int | None = None,
    ) -> ChatResponse:
        """Processes a chat request using active registry deployment and persists messages to SQLite."""
        reply_text, model_ver, p_tokens, g_tokens, ms = inference_engine.generate(
            prompt=request.prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
        )

        # Ensure user exists for message & lineage tracking
        from app.services.consent_service import consent_service
        from app.services.lineage_service import lineage_service

        if not user_id:
            user = await consent_service.get_or_create_default_user(db)
            user_id = user.id

        # Create or find conversation
        conv_id = request.conversation_id
        if not conv_id:
            conv = Conversation(user_id=user_id, title=request.prompt[:40])
            db.add(conv)
            await db.flush()
            conv_id = conv.id

        # Save user message
        user_msg = Message(
            conversation_id=conv_id,
            role="user",
            content=request.prompt,
        )
        # Save assistant message
        bot_msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content=reply_text,
            model_version=model_ver,
        )
        db.add_all([user_msg, bot_msg])
        await db.commit()
        await db.refresh(user_msg)

        # Register data lineage for user message
        await lineage_service.register_message_lineage(
            message=user_msg,
            user_id=user_id,
            db=db,
        )

        return ChatResponse(
            response=reply_text,
            model_version=model_ver,
            conversation_id=conv_id,
            prompt_tokens=p_tokens,
            generated_tokens=g_tokens,
            inference_time_ms=ms,
        )


# Global singleton
chat_service = ChatService()
